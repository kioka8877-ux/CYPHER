#!/usr/bin/env python3
"""
F02 CALIBAN — Visual Canvas Preview (Imperivm theme)
Parses timing.json, extracts countries/brands via LLM,
serves interactive HTML preview with Leaflet map + logo overlay.
POST /api/save → render_spec.json (merged, ready for DEATHWING).
"""

import json, os, sys, http.server, threading, urllib.request
from pathlib import Path

BASE        = Path(__file__).resolve().parents[2]
LION_OUT    = BASE / "F01_LION"  / "OUT"
CALIBAN_IN  = BASE / "F02_CALIBAN" / "IN"
CALIBAN_OUT = BASE / "F02_CALIBAN" / "OUT"
CALIBAN_OUT.mkdir(parents=True, exist_ok=True)

TIMING_PATH = CALIBAN_IN / "timing.json"
CONFIG_PATH = CALIBAN_IN / "config.json"

GW_URL = os.environ.get("AI_GATEWAY_BASE_URL", "")
GW_KEY = os.environ.get("AI_GATEWAY_API_KEY", "")

# ── country centroids (iso2 → {lat,lon,zoom}) ───────────────────────────────
CENTROIDS = {
  "US":{"lat":38.9,"lon":-77.0,"zoom":4},"DE":{"lat":51.2,"lon":10.5,"zoom":5},
  "JP":{"lat":36.2,"lon":138.3,"zoom":5},"KR":{"lat":35.9,"lon":127.8,"zoom":6},
  "FR":{"lat":46.2,"lon":2.2,"zoom":5},"IT":{"lat":42.8,"lon":12.6,"zoom":5},
  "SE":{"lat":60.1,"lon":18.6,"zoom":5},"CN":{"lat":35.9,"lon":104.2,"zoom":4},
  "CA":{"lat":56.1,"lon":-106.3,"zoom":4},"GB":{"lat":55.4,"lon":-3.4,"zoom":5},
  "AE":{"lat":23.4,"lon":53.8,"zoom":6},"TW":{"lat":23.7,"lon":120.9,"zoom":7},
  "CH":{"lat":46.8,"lon":8.2,"zoom":7},"NL":{"lat":52.1,"lon":5.3,"zoom":7},
  "ES":{"lat":40.5,"lon":-3.7,"zoom":6},"IN":{"lat":20.6,"lon":78.9,"zoom":4},
  "AU":{"lat":-25.3,"lon":133.8,"zoom":4},"SG":{"lat":1.3,"lon":103.8,"zoom":10},
  "FI":{"lat":61.9,"lon":25.7,"zoom":5},"DK":{"lat":56.3,"lon":9.5,"zoom":6},
  "BR":{"lat":-14.2,"lon":-51.9,"zoom":4},"TR":{"lat":38.9,"lon":35.2,"zoom":5},
  "GR":{"lat":39.1,"lon":21.8,"zoom":6},"BY":{"lat":53.7,"lon":27.9,"zoom":6},
}

BRAND_DOMAINS = {
  "apple":"apple.com","nike":"nike.com","coca-cola":"coca-cola.com",
  "mcdonald's":"mcdonalds.com","tesla":"tesla.com","bmw":"bmw.com",
  "mercedes-benz":"mercedes-benz.com","adidas":"adidas.com","toyota":"toyota.com",
  "sony":"sony.com","nintendo":"nintendo.com","samsung":"samsung.com",
  "hyundai":"hyundai.com","lg":"lg.com","airbus":"airbus.com",
  "louis vuitton":"louisvuitton.com","ferrari":"ferrari.com","gucci":"gucci.com",
  "lamborghini":"lamborghini.com","ikea":"ikea.com","volvo":"volvocars.com",
  "spotify":"spotify.com","tiktok":"tiktok.com","huawei":"huawei.com",
  "dji":"dji.com","shopify":"shopify.com","bombardier":"bombardier.com",
  "rolls-royce":"rolls-royce.com","burberry":"burberry.com",
  "british airways":"britishairways.com","emirates":"emirates.com",
  "tsmc":"tsmc.com","acer":"acer.com","nestle":"nestle.com",
  "rolex":"rolex.com","ubs":"ubs.com","philips":"philips.com",
  "heineken":"heineken.com","asml":"asml.com","zara":"zara.com",
  "santander":"santander.com","tata":"tata.com","reliance":"ril.com",
  "qantas":"qantas.com","atlassian":"atlassian.com","canva":"canva.com",
  "grab":"grab.com","singapore airlines":"singaporeair.com","nokia":"nokia.com",
  "kone":"kone.com","lego":"lego.com","maersk":"maersk.com","embraer":"embraer.com",
}


def logo_url(brand: str) -> str:
    domain = BRAND_DOMAINS.get(brand.lower(), "")
    if domain:
        return f"https://logo.clearbit.com/{domain}"
    return ""


def llm_extract(segments: list) -> list:
    """Ask LLM to extract country ISO codes + brand names per segment."""
    if not GW_URL or not GW_KEY:
        return [{"countries": [], "brands": []} for _ in segments]

    texts = [{"idx": i, "text": s.get("text", "")} for i, s in enumerate(segments)]
    prompt = (
        "For each segment, extract: 1) ISO2 country codes mentioned, "
        "2) brand/company names. Return JSON array matching input order: "
        '[{"idx":0,"countries":["US"],"brands":["Apple","Nike"]},...]\n\n'
        + json.dumps(texts)
    )
    payload = json.dumps({
        "model": "anthropic/claude-haiku-4.5",
        "messages": [
            {"role": "system", "content": "You extract structured data from text. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000, "temperature": 0
    }).encode()

    try:
        req = urllib.request.Request(
            f"{GW_URL}/api/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {GW_KEY}",
                     "Content-Type": "application/json",
                     "Accept-Encoding": "identity"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        raw = resp["choices"][0]["message"]["content"].strip()
        raw = raw[raw.find("["):raw.rfind("]")+1]
        return json.loads(raw)
    except Exception as e:
        print(f"[CALIBAN] LLM extract failed: {e}", file=sys.stderr)
        return [{"idx": i, "countries": [], "brands": []} for i in range(len(segments))]


def build_preview_data(timing: dict, config: dict) -> dict:
    segs = timing.get("segments", [])
    extracts = llm_extract(segs)
    extract_map = {e.get("idx", i): e for i, e in enumerate(extracts)}

    segments_out = []
    for i, seg in enumerate(segs):
        ex = extract_map.get(i, {"countries": [], "brands": []})
        countries = ex.get("countries", [])
        brands = ex.get("brands", [])

        # map center: first recognized country
        map_center = None
        for iso in countries:
            if iso in CENTROIDS:
                map_center = {**CENTROIDS[iso], "iso": iso}
                break
        if not map_center:
            map_center = {"lat": 20, "lon": 0, "zoom": 2, "iso": ""}

        # logos
        logos = []
        for b in brands[:4]:
            url = logo_url(b)
            if url:
                logos.append({"brand": b, "url": url})

        segments_out.append({
            "idx": i,
            "start": seg.get("start", 0),
            "end":   seg.get("end", 0),
            "text":  seg.get("text", ""),
            "countries": countries,
            "brands": brands,
            "logos": logos,
            "map_center": map_center,
            "sfx_trigger": False,
            "visual_file": "",
            "media_type": "logo",
        })

    return {
        "segments": segments_out,
        "meta": timing.get("meta", {}),
        "display": {
            "font":       config.get("subtitle_font", "Cinzel"),
            "font_color": config.get("subtitle_color", "#FFFFFF"),
            "font_size":  config.get("subtitle_size", 52),
            "position":   config.get("subtitle_position", "bottom"),
            "animation":  config.get("subtitle_animation", "ltr"),
            "visual_scale": config.get("visual_scale", 0.85),
        },
        "format":    config.get("format", "short"),
        "map_style": config.get("map_style", "satellite"),
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CYPHER — Gate 2 CALIBAN</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#050B08;color:#c8c8c0;font-family:'Segoe UI',sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
  #top-bar{background:#0a1a0f;border-bottom:1px solid #1a3020;padding:8px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0}
  #top-bar h1{color:#c8a96e;font-size:14px;letter-spacing:2px;font-weight:700;margin-right:auto}
  .ctrl-group{display:flex;align-items:center;gap:6px;font-size:11px;color:#8a8a7a}
  .ctrl-group select,.ctrl-group input[type=text],.ctrl-group input[type=number]{
    background:#0d1f12;border:1px solid #1a3020;color:#c8c8c0;padding:3px 6px;font-size:11px;border-radius:3px}
  #main{display:flex;flex:1;overflow:hidden}
  #seg-list{width:220px;background:#070f09;border-right:1px solid #1a3020;overflow-y:auto;flex-shrink:0}
  .seg-item{padding:8px 10px;border-bottom:1px solid #0d1a0f;cursor:pointer;transition:background .15s}
  .seg-item:hover{background:#0d1f12}
  .seg-item.active{background:#0f2a14;border-left:3px solid #c8a96e}
  .seg-time{font-size:9px;color:#5a7a60;font-family:monospace}
  .seg-text{font-size:10px;color:#9a9a8a;margin-top:2px;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .seg-tags{display:flex;flex-wrap:wrap;gap:3px;margin-top:3px}
  .tag{background:#0d2010;border:1px solid #1a4020;color:#6ab870;font-size:8px;padding:1px 5px;border-radius:2px}
  #preview-area{flex:1;display:flex;flex-direction:column;overflow:hidden}
  #canvas-wrap{flex:1;display:flex;gap:0;overflow:hidden}
  #map-frame{flex:1;position:relative;background:#050B08}
  #map{width:100%;height:100%}
  #video-frame{width:320px;flex-shrink:0;background:#050B08;border-left:1px solid #1a3020;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px;gap:12px}
  .vf-label{font-size:9px;color:#3a5a40;letter-spacing:1px;text-transform:uppercase;position:absolute;top:8px;left:10px}
  #logo-wrap{width:200px;height:120px;display:flex;align-items:center;justify-content:center;background:#0a1a0f;border:1px solid #1a3020;border-radius:4px;position:relative;overflow:hidden}
  #logo-wrap img{max-width:180px;max-height:100px;object-fit:contain}
  #logo-nav{display:flex;gap:6px;align-items:center}
  .logo-dot{width:7px;height:7px;border-radius:50%;background:#1a3020;cursor:pointer;transition:background .15s}
  .logo-dot.active{background:#c8a96e}
  #subtitle-preview{width:200px;text-align:center;border-top:1px solid #1a3020;padding-top:8px}
  #sfx-btn{padding:3px 10px;font-size:10px;border:1px solid #3a3020;background:#1a1008;color:#9a8060;border-radius:3px;cursor:pointer}
  #sfx-btn.on{border-color:#c8a96e;background:#2a1a05;color:#c8a96e}
  #countries-display{font-size:9px;color:#5a7a60;text-align:center}
  #bottom-bar{background:#0a1a0f;border-top:1px solid #1a3020;padding:8px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0}
  #seg-slider{flex:1;accent-color:#c8a96e}
  #seg-info{font-size:11px;color:#6a8a70;font-family:monospace;min-width:80px}
  #validate-btn{background:#8B0000;color:#fff;border:none;padding:8px 20px;font-size:12px;letter-spacing:1px;cursor:pointer;border-radius:3px;font-weight:700}
  #validate-btn:hover{background:#a00}
  #status{font-size:10px;color:#4a7a50}
</style>
</head>
<body>
<div id="top-bar">
  <h1>⚔ CYPHER — CALIBAN GATE II</h1>
  <div class="ctrl-group">
    <span>Font</span>
    <select id="c-font">
      <option>Cinzel</option><option>Arial Black</option>
      <option>Impact</option><option>Georgia</option>
    </select>
  </div>
  <div class="ctrl-group">
    <span>Color</span>
    <input type="text" id="c-color" value="#FFFFFF" style="width:70px">
  </div>
  <div class="ctrl-group">
    <span>Size</span>
    <input type="number" id="c-size" value="52" style="width:50px" min="24" max="96">
  </div>
  <div class="ctrl-group">
    <span>Position</span>
    <select id="c-pos"><option value="bottom">Bas</option><option value="center">Centre</option></select>
  </div>
  <div class="ctrl-group">
    <span>Anim</span>
    <select id="c-anim"><option value="ltr">Gauche→Droite</option><option value="none">Aucune</option><option value="fade">Fade</option></select>
  </div>
  <div class="ctrl-group">
    <span>Scale</span>
    <input type="number" id="c-scale" value="0.85" style="width:50px" min="0.3" max="1.5" step="0.05">
  </div>
</div>
<div id="main">
  <div id="seg-list" id="seg-list"></div>
  <div id="preview-area">
    <div id="canvas-wrap">
      <div id="map-frame"><div id="map"></div></div>
      <div id="video-frame">
        <span class="vf-label">Preview Frame</span>
        <div id="logo-wrap"><img id="logo-img" src="" alt="logo"></div>
        <div id="logo-nav"></div>
        <div id="subtitle-preview">
          <span id="subtitle-text" style="font-size:18px;color:#fff;font-family:Cinzel"></span>
        </div>
        <div id="countries-display"></div>
        <button id="sfx-btn" onclick="toggleSfx()">SFX ○</button>
      </div>
    </div>
  </div>
</div>
<div id="bottom-bar">
  <input type="range" id="seg-slider" min="0" value="0">
  <span id="seg-info">0 / 0</span>
  <span id="status"></span>
  <button id="validate-btn" onclick="validate()">VALIDER GATE 2 ▶</button>
</div>
<script>
const DATA = __DATA__;
const segs = DATA.segments;
let cur = 0;
let map, countryLayer;

// Init Leaflet
map = L.map('map', {zoomControl:false, attributionControl:false});
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
L.tileLayer(ESRI, {maxZoom:18}).addTo(map);
L.control.zoom({position:'bottomleft'}).addTo(map);

function buildSegList() {
  const el = document.getElementById('seg-list');
  segs.forEach((s,i) => {
    const d = document.createElement('div');
    d.className = 'seg-item' + (i===0?' active':'');
    d.id = 'si'+i;
    const t = s.start.toFixed(1)+'s → '+s.end.toFixed(1)+'s';
    let tags = s.countries.map(c=>`<span class="tag">${c}</span>`).join('') +
               s.brands.slice(0,3).map(b=>`<span class="tag" style="color:#c8a96e">${b}</span>`).join('');
    d.innerHTML = `<div class="seg-time">${i.toString().padStart(2,'0')} | ${t}</div>
      <div class="seg-text">${s.text.substring(0,50)}...</div>
      <div class="seg-tags">${tags}</div>`;
    d.onclick = () => goTo(i);
    el.appendChild(d);
  });
}

function goTo(i) {
  cur = i;
  document.querySelectorAll('.seg-item').forEach(e=>e.classList.remove('active'));
  const si = document.getElementById('si'+i);
  if(si){si.classList.add('active');si.scrollIntoView({block:'nearest'});}
  document.getElementById('seg-slider').value = i;
  document.getElementById('seg-info').textContent = `${i+1} / ${segs.length}`;
  updatePreview();
}

function updatePreview() {
  const s = segs[cur];
  // Map
  const mc = s.map_center;
  map.flyTo([mc.lat, mc.lon], mc.zoom||5, {duration:0.5});
  if(countryLayer){map.removeLayer(countryLayer);}

  // Logos
  const logoWrap = document.getElementById('logo-wrap');
  const logoImg  = document.getElementById('logo-img');
  const nav      = document.getElementById('logo-nav');
  nav.innerHTML  = '';
  if(s.logos.length > 0) {
    logoImg.src = s.logos[0].url;
    logoImg.onerror = () => { logoImg.src=''; logoImg.alt=s.logos[0].brand; };
    s.logos.forEach((l,j) => {
      const d = document.createElement('div');
      d.className = 'logo-dot' + (j===0?' active':'');
      d.onclick = () => {
        logoImg.src = l.url;
        nav.querySelectorAll('.logo-dot').forEach((dd,k)=>dd.classList.toggle('active',k===j));
      };
      nav.appendChild(d);
    });
  } else {
    logoImg.src=''; logoImg.alt='—';
  }

  // Subtitle
  const stEl = document.getElementById('subtitle-text');
  stEl.textContent = s.text.substring(0,60);
  stEl.style.fontFamily = document.getElementById('c-font').value;
  stEl.style.color      = document.getElementById('c-color').value;
  stEl.style.fontSize   = (document.getElementById('c-size').value/3)+'px';

  // Countries
  document.getElementById('countries-display').textContent = s.countries.join(' · ');

  // SFX
  const btn = document.getElementById('sfx-btn');
  btn.textContent = s.sfx_trigger ? 'SFX ●' : 'SFX ○';
  btn.className   = 'sfx-btn' + (s.sfx_trigger ? ' on' : '');
}

function toggleSfx() {
  segs[cur].sfx_trigger = !segs[cur].sfx_trigger;
  updatePreview();
}

// Controls live update
['c-font','c-color','c-size','c-pos','c-anim','c-scale'].forEach(id=>{
  document.getElementById(id).addEventListener('input', updatePreview);
});

document.getElementById('seg-slider').addEventListener('input', e => goTo(+e.target.value));
document.getElementById('seg-slider').max = segs.length - 1;

function validate() {
  const display = {
    font:       document.getElementById('c-font').value,
    font_color: document.getElementById('c-color').value,
    font_size:  +document.getElementById('c-size').value,
    position:   document.getElementById('c-pos').value,
    animation:  document.getElementById('c-anim').value,
    visual_scale: +document.getElementById('c-scale').value,
  };
  const payload = { segments: segs, display, format: DATA.format, map_style: DATA.map_style, meta: DATA.meta };
  document.getElementById('status').textContent = 'Envoi...';
  fetch('/api/save', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
    .then(r=>r.json())
    .then(d=>{ document.getElementById('status').textContent = d.ok ? '✓ render_spec.json sauvegardé' : '✗ '+d.error; })
    .catch(e=>{ document.getElementById('status').textContent = '✗ '+e; });
}

buildSegList();
goTo(0);
</script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    preview_data = {}

    def log_message(self, *a): pass

    def do_GET(self):
        html = HTML_TEMPLATE.replace("__DATA__", json.dumps(self.preview_data))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length))

        # Load original timing words
        timing = json.loads(TIMING_PATH.read_text()) if TIMING_PATH.exists() else {}
        words  = timing.get("words", [])

        segs = body.get("segments", [])
        # Merge sfx_trigger + media_type into segments
        for s in segs:
            s.setdefault("sfx_trigger", False)
            s.setdefault("media_type", "logo")

        render_spec = {
            "meta":     body.get("meta", timing.get("meta", {})),
            "words":    words,
            "segments": segs,
            "display":  body.get("display", {}),
            "format":   body.get("format", "short"),
            "map_style": body.get("map_style", "satellite"),
        }

        CALIBAN_OUT.mkdir(parents=True, exist_ok=True)
        (CALIBAN_OUT / "render_spec.json").write_text(json.dumps(render_spec, indent=2, ensure_ascii=False))
        (CALIBAN_OUT / "config_final.json").write_text(json.dumps(body.get("display", {}), indent=2))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

        threading.Thread(target=self.server.shutdown, daemon=True).start()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    if not TIMING_PATH.exists():
        # fallback: check LION_OUT
        lp = LION_OUT / "timing.json"
        if lp.exists():
            CALIBAN_IN.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(lp, TIMING_PATH)
        else:
            print("[CALIBAN] timing.json introuvable. Lancez d'abord gate1_done.")
            sys.exit(1)

    if not CONFIG_PATH.exists():
        lc = LION_OUT / "config.json"
        if lc.exists():
            import shutil
            shutil.copy(lc, CONFIG_PATH)
        else:
            CONFIG_PATH.write_text("{}")

    print("[CALIBAN] Analyse des segments en cours...", flush=True)
    timing = json.loads(TIMING_PATH.read_text())
    config = json.loads(CONFIG_PATH.read_text())
    data   = build_preview_data(timing, config)

    Handler.preview_data = data
    srv = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"[CALIBAN] Preview sur http://localhost:{port}", flush=True)
    print(f"[CALIBAN] {len(data['segments'])} segments | {data['format']} | {data['map_style']}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
