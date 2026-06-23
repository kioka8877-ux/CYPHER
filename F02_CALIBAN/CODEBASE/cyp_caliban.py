#!/usr/bin/env python3
"""F02 CALIBAN v6 — Preview visuel interactif CYPHER (lit timing.json réel)"""
import json, os, sys, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).resolve().parent

def find(names):
    for n in names:
        for d in [BASE / "IN", ROOT / "F01_LION/OUT", ROOT / "F02_CALIBAN/IN"]:
            p = d / n
            if p.exists():
                return p
    return None

# Country → ISO + coords
COUNTRY_MAP = {
    "united states": ("US", 38.9, -95.7, 4),
    "germany": ("DE", 51.2, 10.4, 5),
    "japan": ("JP", 36.2, 138.2, 5),
    "south korea": ("KR", 35.9, 127.8, 6),
    "france": ("FR", 46.2, 2.2, 5),
    "italy": ("IT", 42.8, 12.6, 5),
    "sweden": ("SE", 60.1, 18.6, 5),
    "china": ("CN", 35.9, 104.2, 4),
    "canada": ("CA", 56.1, -106.3, 4),
    "united kingdom": ("GB", 54.4, -3.4, 5),
    "uk": ("GB", 54.4, -3.4, 5),
    "united arab emirates": ("AE", 23.4, 53.8, 6),
    "uae": ("AE", 23.4, 53.8, 6),
    "taiwan": ("TW", 23.7, 120.9, 7),
    "switzerland": ("CH", 46.8, 8.2, 6),
    "netherlands": ("NL", 52.1, 5.3, 6),
    "spain": ("ES", 40.5, -3.7, 5),
    "india": ("IN", 20.6, 78.9, 4),
    "australia": ("AU", -25.3, 133.8, 4),
    "singapore": ("SG", 1.35, 103.82, 9),
    "finland": ("FI", 61.9, 25.7, 5),
    "denmark": ("DK", 56.3, 9.5, 6),
    "brazil": ("BR", -14.2, -51.9, 4),
}

# Brands → clearbit domain
BRAND_DOMAINS = {
    "apple": "apple.com", "nike": "nike.com", "coca-cola": "coca-cola.com",
    "mcdonald's": "mcdonalds.com", "tesla": "tesla.com",
    "bmw": "bmw.com", "mercedes-benz": "mercedes-benz.com", "adidas": "adidas.com",
    "toyota": "toyota.com", "sony": "sony.com", "nintendo": "nintendo.com",
    "samsung": "samsung.com", "hyundai": "hyundai.com", "lg": "lg.com",
    "airbus": "airbus.com", "louis vuitton": "louisvuitton.com", "capgemini": "capgemini.com",
    "ferrari": "ferrari.com", "gucci": "gucci.com", "lamborghini": "lamborghini.com",
    "ikea": "ikea.com", "volvo": "volvo.com", "spotify": "spotify.com",
    "tiktok": "tiktok.com", "huawei": "huawei.com", "dji": "dji.com",
    "shopify": "shopify.com", "bombardier": "bombardier.com",
    "rolls-royce": "rolls-royce.com", "burberry": "burberry.com", "british airways": "britishairways.com",
    "emirates": "emirates.com",
    "tsmc": "tsmc.com", "acer": "acer.com",
    "nestle": "nestle.com", "rolex": "rolex.com", "ubs": "ubs.com",
    "philips": "philips.com", "heineken": "heineken.com", "asml": "asml.com",
    "zara": "zara.com", "santander": "santander.com", "seat": "seat.com",
    "tata": "tata.com", "reliance": "ril.com",
    "qantas": "qantas.com", "atlassian": "atlassian.com", "canva": "canva.com",
    "grab": "grab.com", "singapore airlines": "singaporeair.com",
    "nokia": "nokia.com", "kone": "kone.com",
    "lego": "lego.com", "maersk": "maersk.com",
    "petrobras": "petrobras.com", "embraer": "embraer.com",
}

def parse_segment(seg):
    """Extract primary country + brands from segment text."""
    text = seg["text"].lower()
    country = iso = None
    lat = lon = 0.0
    zoom = 4
    for name, (c, la, lo, z) in COUNTRY_MAP.items():
        if name in text:
            country, iso, lat, lon, zoom = name, c, la, lo, z
            break
    brands = []
    for brand, domain in BRAND_DOMAINS.items():
        if brand in text:
            brands.append({"name": brand, "domain": domain,
                           "logo": f"https://logo.clearbit.com/{domain}"})
    return {
        "id": seg["id"],
        "text": seg["text"],
        "start": seg["start"],
        "end": seg["end"],
        "start_frame": seg.get("start_frame", 0),
        "end_frame": seg.get("end_frame", 0),
        "country": country or "unknown",
        "iso": iso or "",
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "brands": brands,
    }

# Load data
tp = find(["timing.json"])
cp = find(["config.json"])
if not tp:
    print("[CALIBAN] timing.json introuvable"); sys.exit(1)

TIMING = json.loads(tp.read_text())
CFG = json.loads(cp.read_text()) if cp else {}
META = TIMING.get("meta", {})
FMT = CFG.get("format", "short")
SEGS = [parse_segment(s) for s in TIMING.get("segments", [])]
EJ = json.dumps(SEGS, ensure_ascii=False)
METAJ = json.dumps(META, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>CYPHER F02 CALIBAN — Gate 2</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#050B08;color:#e0e0e0;font-family:'Cinzel',serif;display:flex;flex-direction:column;height:100vh;overflow:hidden}}
header{{background:#0a1a12;border-bottom:1px solid #1a3a22;padding:7px 16px;font-size:12px;color:#4a9a6a;letter-spacing:2px;flex-shrink:0;display:flex;justify-content:space-between;align-items:center}}
main{{display:flex;flex:1;overflow:hidden}}
#left{{width:260px;flex-shrink:0;background:#061009;border-right:1px solid #1a3a22;display:flex;flex-direction:column;overflow:hidden}}
#seg-list{{flex:1;overflow-y:auto;padding:6px}}
.si{{padding:6px 9px;border:1px solid #1a3a22;border-radius:4px;margin-bottom:4px;cursor:pointer;font-size:11px;transition:.15s}}
.si:hover,.si.act{{background:#0f2a18;border-color:#4a9a6a;color:#fff}}
.st{{color:#4a9a6a;font-size:9px;font-family:monospace}}
.sc{{color:#aaa;font-size:10px;margin-top:2px}}
#center{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px;overflow:hidden}}
#frame-wrap{{position:relative;background:#000;border:2px solid #1a3a22;overflow:hidden}}
#map{{width:100%;height:100%;position:absolute;top:0;left:0}}
#subtitle-bar{{position:absolute;bottom:0;left:0;right:0;padding:12px;text-align:center;z-index:1000;background:linear-gradient(transparent,rgba(0,0,0,.7))}}
#subtitle-text{{display:inline-block;padding:4px 12px;border-radius:3px}}
#logos-bar{{position:absolute;top:10px;right:10px;z-index:1000;display:flex;flex-direction:column;gap:6px}}
.logo-img{{width:44px;height:44px;background:#fff;border-radius:6px;padding:3px;object-fit:contain;border:1px solid #4a9a6a}}
#right{{width:240px;flex-shrink:0;background:#061009;border-left:1px solid #1a3a22;overflow-y:auto;padding:10px}}
.ctrl-group{{margin-bottom:12px}}
.ctrl-label{{font-size:10px;color:#4a9a6a;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px}}
select,input[type=text],input[type=color],input[type=range]{{width:100%;background:#0a1a12;border:1px solid #1a3a22;color:#e0e0e0;padding:4px;border-radius:3px;font-size:11px}}
input[type=range]{{padding:0}}
#btn-validate{{width:100%;background:#B30006;color:#fff;border:none;padding:10px;cursor:pointer;border-radius:4px;font-size:12px;letter-spacing:2px;margin-top:8px;text-transform:uppercase}}
#btn-validate:hover{{background:#d40007}}
.brand-list{{font-size:10px;color:#888;margin-top:3px}}
</style>
</head>
<body>
<header>
  <span>CYPHER // F02 CALIBAN // GATE 2</span>
  <span id="seg-info">— / {len(SEGS)} segments</span>
</header>
<main>
<!-- LEFT: segment list -->
<div id="left">
  <div style="padding:8px;border-bottom:1px solid #1a3a22;font-size:10px;color:#4a9a6a;letter-spacing:1px">SEGMENTS</div>
  <div id="seg-list"></div>
</div>

<!-- CENTER: video canvas -->
<div id="center">
  <div id="frame-wrap">
    <div id="map"></div>
    <div id="subtitle-bar"><span id="subtitle-text">—</span></div>
    <div id="logos-bar" id="logos-container"></div>
  </div>
  <div style="color:#4a9a6a;font-size:10px;margin-top:6px" id="seg-detail">Cliquer un segment</div>
</div>

<!-- RIGHT: controls -->
<div id="right">
  <div class="ctrl-group">
    <div class="ctrl-label">Format</div>
    <select id="c-format">
      <option value="short">Short 9:16</option>
      <option value="long">Long 16:9</option>
    </select>
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Style carte</div>
    <select id="c-mapstyle">
      <option value="sat">Satellite ESRI</option>
      <option value="topo">Topo</option>
      <option value="dark">Dark</option>
      <option value="light">Light</option>
    </select>
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Police</div>
    <select id="c-font">
      <option value="Cinzel">Cinzel</option>
      <option value="Arrila Black">Arrila Black</option>
      <option value="Impact">Impact</option>
      <option value="Georgia">Georgia</option>
      <option value="monospace">Monospace</option>
    </select>
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Couleur texte</div>
    <input type="color" id="c-color" value="#FFFFFF">
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Taille police</div>
    <input type="range" id="c-size" min="20" max="80" value="40">
    <span id="c-size-val" style="font-size:10px;color:#888">40px</span>
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Position sous-titre</div>
    <select id="c-pos">
      <option value="bottom">Bas</option>
      <option value="center">Centre</option>
      <option value="top">Haut</option>
    </select>
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Animation</div>
    <select id="c-anim">
      <option value="ltr">Gauche → Droite</option>
      <option value="fade">Fondu</option>
      <option value="none">Aucune</option>
    </select>
  </div>
  <div class="ctrl-group">
    <div class="ctrl-label">Scale visuels</div>
    <input type="range" id="c-scale" min="0.3" max="1.5" step="0.05" value="0.85">
    <span id="c-scale-val" style="font-size:10px;color:#888">0.85</span>
  </div>
  <button id="btn-validate" onclick="validate()">Valider Gate 2</button>
  <div id="val-msg" style="font-size:10px;color:#4a9a6a;margin-top:6px;text-align:center"></div>
</div>
</main>

<script>
const SEGS={EJ};
const META={METAJ};
const sfxState={{}};
let curIdx=0;
let map;

const TILES={{
  sat:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  topo:'https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png',
  dark:'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
  light:'https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
}};

function initMap(){{
  map=L.map('map',{{zoomControl:false,attributionControl:false}});
  L.tileLayer(TILES.sat,{{maxZoom:18}}).addTo(map);
}}

function getFrameSize(){{
  const fmt=document.getElementById('c-format').value;
  const maxH=window.innerHeight-120;
  if(fmt==='short'){{
    const h=Math.min(maxH,600);
    return [Math.round(h*9/16),h];
  }}else{{
    const w=Math.min(window.innerWidth-540,800);
    return [w,Math.round(w*9/16)];
  }}
}}

function resizeFrame(){{
  const fw=document.getElementById('frame-wrap');
  const [w,h]=getFrameSize();
  fw.style.width=w+'px';
  fw.style.height=h+'px';
  if(map)map.invalidateSize();
}}

function updateTiles(){{
  const style=document.getElementById('c-mapstyle').value;
  map.eachLayer(l=>map.removeLayer(l));
  L.tileLayer(TILES[style]||TILES.sat,{{maxZoom:18}}).addTo(map);
}}

function loadSegment(idx){{
  curIdx=idx;
  document.querySelectorAll('.si').forEach((e,i)=>e.classList.toggle('act',i===idx));
  document.getElementById('seg-info').textContent=(idx+1)+' / '+SEGS.length+' segments';
  const seg=SEGS[idx];
  // Map
  if(seg.lat||seg.lon)map.setView([seg.lat,seg.lon],seg.zoom||5,{{animate:true,duration:.6}});
  // Subtitle
  const txt=document.getElementById('subtitle-text');
  txt.textContent=seg.text;
  applySubtitleStyle();
  // Logos
  const lb=document.getElementById('logos-bar');
  lb.innerHTML='';
  (seg.brands||[]).slice(0,4).forEach(b=>{{
    const img=document.createElement('img');
    img.src=b.logo;
    img.alt=b.name;
    img.className='logo-img';
    img.onerror=()=>img.style.display='none';
    lb.appendChild(img);
  }});
  // Detail
  const brands=(seg.brands||[]).map(b=>b.name).join(', ');
  document.getElementById('seg-detail').textContent=
    (seg.country?seg.country.toUpperCase():'?')+' | '+seg.start.toFixed(2)+'s → '+seg.end.toFixed(2)+'s'+(brands?' | '+brands:'');
}}

function applySubtitleStyle(){{
  const txt=document.getElementById('subtitle-text');
  const pos=document.getElementById('c-pos').value;
  const bar=document.getElementById('subtitle-bar');
  const font=document.getElementById('c-font').value;
  const color=document.getElementById('c-color').value;
  const size=document.getElementById('c-size').value;
  txt.style.fontFamily=font;
  txt.style.color=color;
  txt.style.fontSize=size+'px';
  bar.style.bottom=pos==='bottom'?'0':pos==='top'?'auto':'40%';
  bar.style.top=pos==='top'?'0':'auto';
}}

function buildList(){{
  const list=document.getElementById('seg-list');
  list.innerHTML='';
  SEGS.forEach((s,i)=>{{
    const d=document.createElement('div');
    d.className='si'+(i===0?' act':'');
    const brands=(s.brands||[]).map(b=>b.name).join(', ');
    d.innerHTML=`<div><b>${{s.iso||'?'}}</b> ${{s.country?.toUpperCase()||'?'}}</div>
      <div class="st">${{s.start.toFixed(2)}}s → ${{s.end.toFixed(2)}}s</div>
      <div class="sc">${{brands.slice(0,40)||s.text.slice(0,40)}}</div>`;
    d.onclick=()=>loadSegment(i);
    list.appendChild(d);
  }});
}}

function validate(){{
  const payload={{
    format:document.getElementById('c-format').value,
    map_style:document.getElementById('c-mapstyle').value,
    font:document.getElementById('c-font').value,
    font_color:document.getElementById('c-color').value,
    font_size:parseInt(document.getElementById('c-size').value),
    position:document.getElementById('c-pos').value,
    animation:document.getElementById('c-anim').value,
    visual_scale:parseFloat(document.getElementById('c-scale').value),
    sfx_triggers:sfxState,
  }};
  fetch('/api/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}})
    .then(r=>r.json()).then(d=>{{
      document.getElementById('val-msg').textContent=d.ok?'render_spec.json sauvegardé ✓':'Erreur: '+d.error;
    }});
}}

// Live controls
document.getElementById('c-format').onchange=()=>{{resizeFrame();loadSegment(curIdx)}};
document.getElementById('c-mapstyle').onchange=updateTiles;
['c-font','c-color','c-pos','c-anim'].forEach(id=>document.getElementById(id).addEventListener('change',applySubtitleStyle));
document.getElementById('c-size').oninput=e=>{{
  document.getElementById('c-size-val').textContent=e.target.value+'px';
  applySubtitleStyle();
}};
document.getElementById('c-scale').oninput=e=>document.getElementById('c-scale-val').textContent=parseFloat(e.target.value).toFixed(2);

window.onresize=resizeFrame;
initMap();
buildList();
resizeFrame();
loadSegment(0);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path != "/api/save":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        out_dir = ROOT / "F02_CALIBAN/OUT"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Build render_spec (merge timing + gate2 settings)
        render_spec = {
            "meta": {**META, "run_id": CFG.get("run_id", ""), "format": body.get("format", FMT),
                     "map_style": body.get("map_style", "sat"), "total_segments": len(SEGS)},
            "segments": [
                {**s, "sfx_trigger": body.get("sfx_triggers", {}).get(str(s["id"]), False)}
                for s in SEGS
            ],
            "display": {
                "font": body.get("font", "Cinzel"),
                "font_color": body.get("font_color", "#FFFFFF"),
                "font_size": int(body.get("font_size", 40)),
                "position": body.get("position", "bottom"),
                "animation": body.get("animation", "ltr"),
                "visual_scale": float(body.get("visual_scale", 0.85)),
            },
            "map_config": {"style": body.get("map_style", "sat"), "country_fill": "#B30006",
                           "country_opacity": 0.6, "border_color": "#FFFFFF", "border_width": 2},
        }
        # Also write timing.json copy
        (out_dir / "render_spec.json").write_text(json.dumps(render_spec, indent=2, ensure_ascii=False))
        (out_dir / "config_final.json").write_text(json.dumps(body, indent=2, ensure_ascii=False))

        # Copy timing.json for downstream frégates
        import shutil
        src_timing = ROOT / "F01_LION/OUT/timing.json"
        if src_timing.exists():
            shutil.copy(src_timing, out_dir / "timing.json")

        resp = json.dumps({"ok": True, "render_spec": str(out_dir / "render_spec.json")}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resp)

        def stop():
            import time; time.sleep(0.5)
            server.shutdown()
        threading.Thread(target=stop, daemon=True).start()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
server = HTTPServer(("0.0.0.0", port), Handler)
print(f"[CALIBAN] Gate 2 preview → http://localhost:{port}")
server.serve_forever()
