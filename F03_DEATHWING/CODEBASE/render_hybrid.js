#!/usr/bin/env node
/**
 * CYPHER F03 DEATHWING — Hybrid Renderer (MapLibre travel chunks)
 *
 * Reads hybrid_spec.json, renders ONLY chunks with engine="cypher".
 * Each chunk = camera travel from point A to point B on satellite map.
 *
 * Usage:
 *   node render_hybrid.js --spec hybrid_spec.json --chunk 0 --output chunk_0.mp4
 *   node render_hybrid.js --spec hybrid_spec.json --output full_cypher.mp4
 */
'use strict';

const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

function parseArgs() {
  const args = process.argv.slice(2);
  const r = { spec: null, chunk: null, output: 'output.mp4', headed: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--spec') r.spec = args[++i];
    else if (args[i] === '--chunk') r.chunk = parseInt(args[++i], 10);
    else if (args[i] === '--output') r.output = args[++i];
    else if (args[i] === '--headed') r.headed = true;
  }
  return r;
}

async function main() {
  const opts = parseArgs();
  console.log('🎬 CYPHER DEATHWING — Hybrid Travel Renderer');

  // 1. Load hybrid spec
  const specPath = opts.spec
    ? path.resolve(opts.spec)
    : path.resolve(__dirname, 'assets', 'hybrid_spec.json');
  if (!fs.existsSync(specPath)) { console.error('❌ hybrid_spec.json missing:', specPath); process.exit(1); }
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf-8'));
  const { meta, cypher_config, chunks } = spec;

  // 2. Filter cypher chunks
  let cypherChunks = chunks.filter(c => c.engine === 'cypher');
  if (opts.chunk !== null) {
    cypherChunks = cypherChunks.filter(c => c.id === opts.chunk);
  }
  if (!cypherChunks.length) { console.error('❌ No cypher chunks to render'); process.exit(1); }
  console.log(`   Chunks: ${cypherChunks.map(c => `#${c.id} ${c.state_name}`).join(', ')}`);

  // 3. Load GeoJSON (for state highlights)
  const geoPath = path.resolve(__dirname, 'assets', 'ne_110m_admin_0_countries.geojson');
  const geojson = fs.existsSync(geoPath) ? JSON.parse(fs.readFileSync(geoPath, 'utf-8')) : null;

  // Also try US states geojson
  const statesGeoPath = path.resolve(__dirname, 'assets', 'us_states.geojson');
  const statesGeojson = fs.existsSync(statesGeoPath) ? JSON.parse(fs.readFileSync(statesGeoPath, 'utf-8')) : null;

  const fps = meta.fps;
  const width = meta.width || 1080;
  const height = meta.height || 1920;

  // 4. Launch browser
  const browser = await chromium.launch({
    headless: !opts.headed,
    args: ['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage',
           '--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']
  });
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();

  // 5. Load map page
  const htmlPath = path.resolve(__dirname, 'map_hybrid.html');
  await page.goto('file://' + htmlPath, { waitUntil: 'load' });
  console.log('🗺️  Waiting for map...');
  await page.waitForFunction(() => window.mapReady === true, { timeout: 60000 });
  console.log('✅ Map ready');

  // 6. Initialize hybrid mode
  await page.evaluate((data) => window.initHybrid(data), {
    cypher_config,
    chunks: cypherChunks,
    geojson: statesGeojson || geojson,
    fps,
    allChunks: chunks
  });
  await page.waitForFunction(() => window.hybridReady === true, { timeout: 30000 });
  console.log('✅ Hybrid initialized');

  // 7. Render each cypher chunk
  for (const chunk of cypherChunks) {
    const startFrame = Math.round(chunk.start * fps);
    const endFrame = Math.round(chunk.end * fps) - 1;
    const total = endFrame - startFrame + 1;
    const outFile = opts.chunk !== null
      ? opts.output
      : `chunk_${chunk.id}.mp4`;

    console.log(`\n🎞️  Chunk #${chunk.id} (${chunk.state_name}): frames ${startFrame}→${endFrame} (${total} frames, ${(total/fps).toFixed(1)}s)`);

    // Start FFmpeg
    const ffmpeg = spawn('ffmpeg', [
      '-y','-f','image2pipe','-framerate',String(fps),'-i','pipe:0',
      '-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','18',
      '-s', `${width}x${height}`, outFile
    ], { stdio: ['pipe','pipe','pipe'] });
    ffmpeg.stderr.on('data', d => {
      const m = d.toString();
      if (m.includes('Error')) console.error('FFmpeg:', m.trim());
    });

    // Render loop
    const t0 = Date.now();
    for (let f = startFrame; f <= endFrame; f++) {
      const t = f / fps;
      await page.evaluate((args) => window.applyTravelState(args.t, args.chunkId), { t, chunkId: chunk.id });
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

    ffmpeg.stdin.end();
    await new Promise((res, rej) => ffmpeg.on('close', c => c === 0 ? res() : rej(new Error('FFmpeg fail'))));
    const dur = ((Date.now()-t0)/1000).toFixed(1);
    const sz = fs.existsSync(outFile) ? (fs.statSync(outFile).size/1048576).toFixed(1)+'MB' : '?';
    console.log(`✅ ${outFile} (${sz}) in ${dur}s`);
  }

  await browser.close();
  console.log('\n✅ All cypher chunks rendered.');
}

main().catch(e => { console.error('❌', e.message); process.exit(1); });
