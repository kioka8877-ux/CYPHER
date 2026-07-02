#!/usr/bin/env node
/**
 * CYPHER F03 DEATHWING v9.0 — MapLibre GL + Playwright Renderer
 *
 * Renders geo-narrative video by:
 *  1. MapLibre GL map with Esri satellite tiles in Playwright headless
 *  2. jumpTo() frame-by-frame with ease-in-out-cubic interpolation
 *  3. Country highlight (fill + glow double layer)
 *  4. Logos scattered within country bounds, camera follows
 *  5. Word-by-word subtitles synced to word_frames
 *  6. Screenshots piped to FFmpeg → MP4
 *
 * Usage:
 *   node render.js --segments 0,1 --output preview.mp4
 *   node render.js --output full.mp4
 */
'use strict';

const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

function parseArgs() {
  const args = process.argv.slice(2);
  const r = { segments: null, output: 'output.mp4', headed: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--segments') r.segments = args[++i].split(',').map(Number);
    else if (args[i] === '--output') r.output = args[++i];
    else if (args[i] === '--headed') r.headed = true;
  }
  return r;
}

async function main() {
  const opts = parseArgs();
  console.log('🎬 CYPHER DEATHWING v9.0 — MapLibre Renderer');

  // 1. Load render spec
  const specPath = path.resolve(__dirname, 'assets', 'render_spec_v2.json');
  if (!fs.existsSync(specPath)) { console.error('❌ render_spec_v2.json missing'); process.exit(1); }
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf-8'));
  const { meta, display, map_config, segments } = spec;

  // 2. Load GeoJSON
  const geoPath = path.resolve(__dirname, 'assets', 'ne_110m_admin_0_countries.geojson');
  if (!fs.existsSync(geoPath)) { console.error('❌ GeoJSON missing'); process.exit(1); }
  const geojson = JSON.parse(fs.readFileSync(geoPath, 'utf-8'));

  // 3. Filter segments
  const tgt = opts.segments
    ? segments.filter(s => opts.segments.includes(s.id))
    : segments;
  if (!tgt.length) { console.error('❌ No segments'); process.exit(1); }
  console.log(`   Segments: ${tgt.map(s => s.iso).join(', ')} (${tgt.length})`);

  // 4. Resolve logo absolute paths
  const logosDir = path.resolve(__dirname, 'assets', 'logos');
  for (const seg of tgt) {
    for (const b of (seg.brands || [])) {
      const lp = path.join(logosDir, b.logo_file || '');
      b._logo_abs = fs.existsSync(lp) ? 'file://' + lp : null;
    }
  }

  // 5. Launch browser
  const browser = await chromium.launch({
    headless: !opts.headed,
    args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage',
           '--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']
  });
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();

  // 6. Load map page
  const htmlPath = path.resolve(__dirname, 'map.html');
  await page.goto('file://' + htmlPath, { waitUntil: 'load' });
  console.log('🗺️  Waiting for map...');
  await page.waitForFunction(() => window.mapReady === true, { timeout: 60000 });
  console.log('✅ Map ready');

  // 7. Initialize CYPHER
  await page.evaluate((data) => window.initCypher(data), {
    display, map_config, segments: tgt, geojson, fps: meta.fps, allSegments: segments
  });
  await page.waitForFunction(() => window.cypherReady === true, { timeout: 30000 });
  console.log('✅ CYPHER initialized');

  // 8. Frame range with absolute seamless continuity (no missing gap frames)
  const fps = meta.fps;
  const segIdx = segments.indexOf(tgt[tgt.length - 1]);
  const nextSeg = segIdx < segments.length - 1 ? segments[segIdx + 1] : null;

  const startFrame = Math.floor(tgt[0].start * fps);
  // If there's a next segment, end exactly 1 frame before its start to avoid overlap/gaps
  // If it's the last segment, render up to the absolute final frame of the video
  const endFrame = nextSeg
    ? Math.floor(nextSeg.start * fps) - 1
    : (meta.total_frames ? meta.total_frames - 1 : Math.ceil(tgt[tgt.length - 1].end * fps));

  const total = endFrame - startFrame + 1;
  console.log(`🎞️  Frames ${startFrame}→${endFrame} (${total} frames, ${(total/fps).toFixed(1)}s)`);

  // 9. Start FFmpeg
  const ffmpeg = spawn('ffmpeg', [
    '-y','-f','image2pipe','-framerate',String(fps),'-i','pipe:0',
    '-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','18',
    '-s','1080x1920', opts.output
  ], { stdio: ['pipe','pipe','pipe'] });
  ffmpeg.stderr.on('data', d => {
    const m = d.toString();
    if (m.includes('Error')) console.error('FFmpeg:', m.trim());
  });

  // 10. Render loop
  const t0 = Date.now();
  for (let f = startFrame; f <= endFrame; f++) {
    const t = f / fps;
    await page.evaluate(t => window.applyStateAtTime(t), t);
    try { await page.waitForFunction(() => window.map.areTilesLoaded(), { timeout: 5000 }); } catch(e) {}
    await page.waitForTimeout(20);
    const buf = await page.screenshot({ type: 'png' });
    ffmpeg.stdin.write(buf);
    const done = f - startFrame;
    if (done % 30 === 0 || f === endFrame) {
      const pct = ((done/total)*100).toFixed(1);
      const el = ((Date.now()-t0)/1000).toFixed(0);
      console.log(`   ${done}/${total} (${pct}%) ${el}s`);
    }
  }

  // 11. Finalize
  ffmpeg.stdin.end();
  await new Promise((res, rej) => ffmpeg.on('close', c => c === 0 ? res() : rej(new Error('FFmpeg fail'))));
  await browser.close();
  const dur = ((Date.now()-t0)/1000).toFixed(1);
  const sz = fs.existsSync(opts.output) ? (fs.statSync(opts.output).size/1048576).toFixed(1)+'MB' : '?';
  console.log(`\n✅ ${opts.output} (${sz}) in ${dur}s`);
}

main().catch(e => { console.error('❌', e.message); process.exit(1); });
