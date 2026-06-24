#!/usr/bin/env python3
"""F02 CALIBAN v7 — Preview visuel interactif CYPHER"""
import json, os, sys, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent

def find(names):
    for n in names:
        for d in [BASE / "IN", ROOT / "F01_LION/OUT", ROOT / "F02_CALIBAN/IN"]:
            p = d / n
            if p.exists():
                return p
    return None

COUNTRY_MAP = {
    "united states": ("US", 38.9, -95.7, 4), "germany": ("DE", 51.2, 10.4, 5),
    "japan": ("JP", 36.2, 138.2, 5), "south korea": ("KR", 35.9, 127.8, 6),
    "france": ("FR", 46.2, 2.2, 5), "italy": ("IT", 42.8, 12.6, 5),
    "sweden": ("SE", 60.1, 18.6, 5), "china": ("CN", 35.9, 104.2, 4),
    "canada": ("CA", 56.1, -106.3, 4), "united kingdom": ("GB", 54.4, -3.4, 5),
    "uk": ("GB", 54.4, -3.4, 5), "united arab emirates": ("AE", 23.4, 53.8, 6),
    "uae": ("AE", 23.4, 53.8, 6), "taiwan": ("TW", 23.7, 120.9, 7),
    "switzerland": ("CH", 46.8, 8.2, 6), "netherlands": ("NL", 52.1, 5.3, 6),
    "spain": ("ES", 40.5, -3.7, 5), "india": ("IN", 20.6, 78.9, 4),
    "australia": ("AU", -25.3, 133.8, 4), "singapore": ("SG", 1.35, 103.82, 9),
    "finland": ("FI", 61.9, 25.7, 5), "denmark": ("DK", 56.3, 9.5, 6),
    "brazil": ("BR", -14.2, -51.9, 4),
}

BRAND_DOMAINS = {
    "apple": "apple.com", "nike": "nike.com", "coca-cola": "coca-cola.com",
    "mcdonald's": "mcdonalds.com", "tesla": "tesla.com", "bmw": "bmw.com",
    "mercedes-benz": "mercedes-benz.com", "adidas": "adidas.com",
    "toyota": "toyota.com", "sony": "sony.com", "nintendo": "nintendo.com",
    "samsung": "samsung.com", "hyundai": "hyundai.com", "lg": "lg.com",
    "airbus": "airbus.com", "louis vuitton": "louisvuitton.com",
    "ferrari": "ferrari.com", "gucci": "gucci.com", "lamborghini": "lamborghini.com",
    "ikea": "ikea.com", "volvo": "volvo.com", "spotify": "spotify.com",
    "tiktok": "tiktok.com", "huawei": "huawei.com", "dji": "dji.com",
    "shopify": "shopify.com", "bombardier": "bombardier.com",
    "rolls-royce": "rolls-royce.com", "burberry": "burberry.com",
    "british airways": "britishairways.com", "emirates": "emirates.com",
    "tsmc": "tsmc.com", "acer": "acer.com", "nestle": "nestle.com",
    "rolex": "rolex.com", "ubs": "ubs.com", "philips": "philips.com",
    "heineken": "heineken.com", "asml": "asml.com", "zara": "zara.com",
    "tata": "tata.com", "reliance": "ril.com", "qantas": "qantas.com",
    "atlassian": "atlassian.com", "canva": "canva.com", "grab": "grab.com",
    "singapore airlines": "singaporeair.com", "nokia": "nokia.com",
    "lego": "lego.com", "maersk": "maersk.com", "embraer": "embraer.com",
}

def parse_segment(seg, words=None):
    text = seg["text"].lower()
    country = iso = None; lat = lon = 0.0; zoom = 4
    for name, (c, la, lo, z) in COUNTRY_MAP.items():
        if name in text:
            country, iso, lat, lon, zoom = name, c, la, lo, z; break
    fps = 30
    brands = []
    for brand, domain in BRAND_DOMAINS.items():
        if brand in text:
            # Find word_frame: first word in words list that matches brand name
            word_frame = seg.get("start_frame", int(seg["start"] * fps))
            if words:
                brand_words = brand.split()
                for w in words:
                    if w.get("word", "").lower().strip(".,!?") == brand_words[0]:
                        if w["start"] >= seg["start"] - 0.1 and w["start"] <= seg["end"] + 0.1:
                            word_frame = int(w["start"] * fps)
                            break
            brands.append({"name": brand, "domain": domain,
                           "logo": f"https://logo.clearbit.com/{domain}?size=80",
                           "word_frame": word_frame})
    return {"id": seg["id"], "text": seg["text"], "start": seg["start"], "end": seg["end"],
            "start_frame": seg.get("start_frame", 0), "end_frame": seg.get("end_frame", 0),
            "country": country or "unknown", "iso": iso or "", "lat": lat, "lon": lon,
            "zoom": zoom, "brands": brands}

tp = find(["timing.json"])
cp = find(["config.json"])
if not tp:
    print("[CALIBAN] timing.json introuvable"); sys.exit(1)

TIMING = json.loads(tp.read_text())
CFG = json.loads(cp.read_text()) if cp else {}
META = TIMING.get("meta", {})
FMT = CFG.get("format", "short")
WORDS = TIMING.get("words", [])
SEGS = [parse_segment(s, WORDS) for s in TIMING.get("segments", [])]
EJ = json.dumps(SEGS, ensure_ascii=False)
METAJ = json.dumps(META, ensure_ascii=False)
TOTAL_FRAMES = META.get("total_frames", 1800)

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
header{{background:#0a1a12;border-bottom:1px solid #1a3a22;padding:7px 16px;font-size:11px;color:#4a9a6a;letter-spacing:2px;flex-shrink:0;display:flex;justify-content:space-between;align-items:center}}
main{{display:flex;flex:1;overflow:hidden;min-height:0}}
#left{{width:220px;flex-shrink:0;background:#061009;border-right:1px solid #1a3a22;display:flex;flex-direction:column;overflow:hidden}}
#seg-list{{flex:1;overflow-y:auto;padding:6px}}
.si{{padding:6px 9px;border:1px solid #1a3a22;border-radius:4px;margin-bottom:4px;cursor:pointer;font-size:10px;transition:.15s}}
.si:hover,.si.act{{background:#0f2a18;border-color:#4a9a6a;color:#fff}}
.st{{color:#4a9a6a;font-size:9px;font-family:monospace}}
.sc{{color:#aaa;font-size:9px;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
#center{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:10px;overflow:hidden;gap:8px}}
#frame-wrap{{position:relative;background:#000;border:2px solid #1a3a22;overflow:hidden;flex-shrink:0}}
#map-div{{width:100%;height:100%;position:absolute;top:0;left:0}}
#subtitle-bar{{position:absolute;left:0;right:0;padding:10px;text-align:center;z-index:1000;background:linear-gradient(transparent,rgba(0,0,0,.75));pointer-events:none}}
#subtitle-text{{display:inline-block;padding:4px 12px;border-radius:3px;text-shadow:1px 1px 3px #000}}
#country-label{{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:1001;background:rgba(0,0,0,.65);padding:3px 10px;border-radius:3px;font-size:11px;color:#fff;letter-spacing:2px;pointer-events:none}}
/* Timeline */
#timeline-wrap{{width:100%;max-width:600px;display:flex;flex-direction:column;gap:4px}}
#timeline-bar{{width:100%;cursor:pointer;accent-color:#4a9a6a;height:18px}}
#timeline-info{{display:flex;justify-content:space-between;font-size:9px;color:#4a9a6a;font-family:monospace}}
/* Right panel */
#right{{width:220px;flex-shrink:0;background:#061009;border-left:1px solid #1a3a22;overflow-y:auto;padding:8px}}
.ctrl-group{{margin-bottom:10px}}
.ctrl-label{{font-size:9px;color:#4a9a6a;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;display:block}}
select,input[type=text],input[type=color],input[type=range]{{width:100%;background:#0a1a12;border:1px solid #1a3a22;color:#e0e0e0;padding:3px;border-radius:3px;font-size:10px}}
input[type=range]{{padding:0;accent-color:#4a9a6a}}
input[type=color]{{height:28px;cursor:pointer;padding:2px}}
.val-hint{{font-size:9px;color:#666;margin-top:1px}}
#btn-validate{{width:100%;background:#B30006;color:#fff;border:none;padding:9px;cursor:pointer;border-radius:4px;font-size:11px;letter-spacing:2px;margin-top:6px;text-transform:uppercase}}
#btn-validate:hover{{background:#d40007}}
#val-msg{{font-size:9px;color:#4a9a6a;margin-top:4px;text-align:center;min-height:14px}}
.seg-detail{{font-size:9px;color:#888;text-align:center;max-width:100%}}
.leaflet-marker-icon{{transition:transform .2s}}
</style>
</head>
<body>
<header>
  <span>CYPHER // F02 CALIBAN // GATE 2</span>
  <span id="seg-info">— / {len(SEGS)} segments · {TOTAL_FRAMES} frames</span>
</header>
<main>
<div id="left">
  <div style="padding:6px 8px;border-bottom:1px solid #1a3a22;font-size:9px;color:#4a9a6a;letter-spacing:1px">SEGMENTS</div>
  <div id="seg-list"></div>
</div>
<div id="center">
  <div id="frame-wrap">
    <div id="map-div"></div>
    <div id="country-label"></div>
    <div id="subtitle-bar"><span id="subtitle-text">—</span></div>
  </div>
  <div id="timeline-wrap">
    <input type="range" id="timeline-bar" min="0" max="{TOTAL_FRAMES}" value="0" oninput="scrubTimeline(this.value)">
    <div id="timeline-info">
      <span id="tl-frame">frame 0</span>
      <span id="tl-seg">seg —</span>
      <span id="tl-time">0.00s</span>
    </div>
  </div>
  <div id="seg-detail" class="seg-detail">Cliquer un segment ou déplacer la timeline</div>
</div>
<div id="right">
  <div class="ctrl-group">
    <label class="ctrl-label">Format</label>
    <select id="c-format" onchange="resizeFrame();loadSegment(curIdx)">
      <option value="short">Short 9:16</option>
      <option value="long">Long 16:9</option>
    </select>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Style carte</label>
    <select id="c-mapstyle" onchange="updateTiles()">
      <option value="sat">Satellite ESRI</option>
      <option value="dark">Dark CartoDB</option>
      <option value="light">Light OSM</option>
      <option value="topo">Topo</option>
    </select>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Couleur pays</label>
    <input type="color" id="c-country-color" value="#B30006" oninput="refreshCountryHighlight()">
    <span class="val-hint">highlight + contour blanc</span>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Police sous-titre</label>
    <select id="c-font" onchange="applySubtitleStyle()">
      <option value="Cinzel">Cinzel</option>
      <option value="'Arrila Black',Impact,sans-serif">Arrila Black</option>
      <option value="Impact,sans-serif">Impact</option>
      <option value="Georgia,serif">Georgia</option>
      <option value="monospace">Monospace</option>
    </select>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Couleur texte</label>
    <input type="color" id="c-color" value="#FFFFFF" oninput="applySubtitleStyle()">
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Taille police</label>
    <input type="range" id="c-size" min="18" max="72" value="38" oninput="document.getElementById('c-size-val').textContent=this.value+'px';applySubtitleStyle()">
    <span class="val-hint" id="c-size-val">38px</span>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Position sous-titre</label>
    <select id="c-pos" onchange="applySubtitleStyle()">
      <option value="bottom">Bas</option>
      <option value="center">Centre</option>
      <option value="top">Haut</option>
    </select>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Animation</label>
    <select id="c-anim">
      <option value="ltr">Gauche → Droite</option>
      <option value="fade">Fondu</option>
      <option value="none">Aucune</option>
    </select>
  </div>
  <div class="ctrl-group">
    <label class="ctrl-label">Scale visuels</label>
    <input type="range" id="c-scale" min="0.3" max="1.5" step="0.05" value="0.85" oninput="document.getElementById('c-scale-val').textContent=parseFloat(this.value).toFixed(2)">
    <span class="val-hint" id="c-scale-val">0.85</span>
  </div>
  <button id="btn-validate" onclick="validate()">Valider Gate 2</button>
  <div id="val-msg"></div>
</div>
</main>
<script>
const SEGS={EJ};
const META={METAJ};
const TOTAL={TOTAL_FRAMES};
let curIdx=0, map=null, circleLayer=null, logoMarkers=[];

const TILES={{
  sat:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
  dark:'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
  light:'https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  topo:'https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png',
}};
let tileLayer=null;

function initMap(){{
  map=L.map('map-div',{{zoomControl:false,attributionControl:false}});
  tileLayer=L.tileLayer(TILES.sat,{{maxZoom:18}}).addTo(map);
  map.setView([20,0],2);
}}

function updateTiles(){{
  const s=document.getElementById('c-mapstyle').value;
  if(tileLayer) map.removeLayer(tileLayer);
  tileLayer=L.tileLayer(TILES[s]||TILES.sat,{{maxZoom:18,subdomains:'abcd'}}).addTo(map);
}}

function getFrameSize(){{
  const fmt=document.getElementById('c-format').value;
  const avH=window.innerHeight-160, avW=window.innerWidth-470;
  if(fmt==='short'){{
    const h=Math.min(avH,560); return [Math.round(h*9/16),h];
  }}else{{
    const w=Math.min(avW,760); return [w,Math.round(w*9/16)];
  }}
}}

function resizeFrame(){{
  const fw=document.getElementById('frame-wrap');
  const [w,h]=getFrameSize(); fw.style.width=w+'px'; fw.style.height=h+'px';
  if(map) map.invalidateSize();
}}

function getCountryColor(){{
  return document.getElementById('c-country-color').value||'#B30006';
}}

function refreshCountryHighlight(){{
  if(!map) return;
  const seg=SEGS[curIdx];
  if(circleLayer){{map.removeLayer(circleLayer);circleLayer=null;}}
  if(seg.lat||seg.lon){{
    circleLayer=L.circle([seg.lat,seg.lon],{{
      color:'#FFFFFF', weight:2,
      fillColor:getCountryColor(), fillOpacity:0.45,
      radius:200000
    }}).addTo(map);
  }}
}}

function clearLogoMarkers(){{
  logoMarkers.forEach(m=>map.removeLayer(m));
  logoMarkers=[];
}}

function addLogoMarkers(seg, currentFrame){{
  clearLogoMarkers();
  if(!seg.lat && !seg.lon) return;
  const brands=(seg.brands||[]).filter(b=> currentFrame===undefined || b.word_frame<=currentFrame);
  const n=brands.length;
  if(n===0) return;
  const factor=Math.pow(2,4-Math.min(seg.zoom||4,6))*0.12;
  const r=factor*800000/111000;
  brands.forEach((b,i)=>{{
    const angle=(n===1)?Math.PI/2:(i*2*Math.PI/n - Math.PI/2);
    const dlat=r*Math.sin(angle);
    const dlon=r*Math.cos(angle);
    const initials=b.name.split(/\s+/).map(w=>w[0]).join('').toUpperCase().slice(0,2);
    const icon=L.divIcon({{
      className:'',
      html:`<div style="background:#fff;border-radius:8px;padding:3px;width:54px;height:54px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,.7);border:2px solid #ffffff;transition:all .3s">
        <img src="${{b.logo}}" style="max-width:46px;max-height:46px;object-fit:contain"
          onerror="this.outerHTML='<div style=width:50px;height:50px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:bold;font-size:14px>${{initials}}</div>'">
      </div>`,
      iconSize:[54,54], iconAnchor:[27,27]
    }});
    const m=L.marker([seg.lat+dlat,seg.lon+dlon],{{icon,zIndexOffset:1000}}).addTo(map);
    m.bindTooltip(b.name,{{direction:'top',offset:[0,-30],permanent:false}});
    logoMarkers.push(m);
  }});
}}

function applySubtitleStyle(){{
  const txt=document.getElementById('subtitle-text');
  const bar=document.getElementById('subtitle-bar');
  const pos=document.getElementById('c-pos').value;
  txt.style.fontFamily=document.getElementById('c-font').value;
  txt.style.color=document.getElementById('c-color').value;
  txt.style.fontSize=document.getElementById('c-size').value+'px';
  bar.style.bottom=pos==='bottom'?'0':'auto';
  bar.style.top=pos==='top'?'0':pos==='center'?'40%':'auto';
  bar.style.transform=pos==='center'?'translateY(-50%)':'none';
}}

function loadSegment(idx){{
  if(idx<0||idx>=SEGS.length) return;
  curIdx=idx;
  document.querySelectorAll('.si').forEach((e,i)=>e.classList.toggle('act',i===idx));
  document.getElementById('seg-info').textContent=(idx+1)+' / '+SEGS.length+' segments';
  const seg=SEGS[idx];
  if(seg.lat||seg.lon) map.setView([seg.lat,seg.lon],seg.zoom||5,{{animate:true,duration:.5}});
  refreshCountryHighlight();
  addLogoMarkers(seg, seg.end_frame||(Math.round(seg.end*30)));
  document.getElementById('subtitle-text').textContent=seg.text;
  applySubtitleStyle();
  const lbl=document.getElementById('country-label');
  lbl.textContent=seg.iso?seg.iso+' — '+(seg.country||'').toUpperCase():'';
  const brands=(seg.brands||[]).map(b=>b.name).join(', ');
  document.getElementById('seg-detail').textContent=
    seg.start.toFixed(2)+'s → '+seg.end.toFixed(2)+'s'+(brands?' | '+brands:'');
  // Sync timeline
  const f=seg.start_frame||Math.round(seg.start*30);
  document.getElementById('timeline-bar').value=f;
  updateTimelineInfo(f,idx);
}}

function updateTimelineInfo(frame,segIdx){{
  document.getElementById('tl-frame').textContent='frame '+frame;
  document.getElementById('tl-seg').textContent='seg '+(segIdx+1);
  document.getElementById('tl-time').textContent=(frame/30).toFixed(2)+'s';
}}

function scrubTimeline(val){{
  const frame=parseInt(val);
  const fps=META.fps||30;
  const t=frame/fps;
  // Find which segment contains this frame
  let found=curIdx;
  for(let i=0;i<SEGS.length;i++){{
    if(t>=SEGS[i].start && t<SEGS[i].end){{found=i;break;}}
    if(t>=SEGS[i].end && i===SEGS.length-1) found=i;
  }}
  if(found!==curIdx){{
    loadSegment(found);
    addLogoMarkers(SEGS[found], frame);
  }} else {{
    addLogoMarkers(SEGS[curIdx], frame);
    updateTimelineInfo(frame,curIdx);
  }}
}}

function buildList(){{
  const list=document.getElementById('seg-list');
  list.innerHTML='';
  SEGS.forEach((s,i)=>{{
    const d=document.createElement('div');
    d.className='si'+(i===0?' act':'');
    const brands=(s.brands||[]).map(b=>b.name).slice(0,2).join(', ');
    d.innerHTML=`<div style="display:flex;justify-content:space-between"><b>${{s.iso||'?'}}</b><span class="st">${{s.start.toFixed(1)}}s</span></div>
      <div class="sc">${{brands||s.text.slice(0,35)}}</div>`;
    d.onclick=()=>loadSegment(i);
    list.appendChild(d);
  }});
}}

function validate(){{
  const payload={{
    format:document.getElementById('c-format').value,
    map_style:document.getElementById('c-mapstyle').value,
    country_color:document.getElementById('c-country-color').value,
    font:document.getElementById('c-font').value,
    font_color:document.getElementById('c-color').value,
    font_size:parseInt(document.getElementById('c-size').value),
    position:document.getElementById('c-pos').value,
    animation:document.getElementById('c-anim').value,
    visual_scale:parseFloat(document.getElementById('c-scale').value),
  }};
  fetch('/api/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}})
    .then(r=>r.json()).then(d=>{{
      document.getElementById('val-msg').textContent=d.ok?'render_spec.json ✓ Gate 3 prête':'Erreur: '+d.error;
    }}).catch(e=>document.getElementById('val-msg').textContent='OK — serveur arrêté');
}}

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

        render_spec = {
            "meta": {**META, "run_id": CFG.get("run_id", ""),
                     "format": body.get("format", FMT),
                     "map_style": body.get("map_style", "sat"),
                     "total_segments": len(SEGS)},
            "segments": SEGS,
            "display": {
                "font": body.get("font", "Cinzel"),
                "font_color": body.get("font_color", "#FFFFFF"),
                "font_size": int(body.get("font_size", 38)),
                "position": body.get("position", "bottom"),
                "animation": body.get("animation", "ltr"),
                "visual_scale": float(body.get("visual_scale", 0.85)),
            },
            "map_config": {
                "style": body.get("map_style", "sat"),
                "country_fill": body.get("country_color", "#B30006"),
                "country_opacity": 0.45,
                "border_color": "#FFFFFF",
                "border_width": 2,
            },
        }
        (out_dir / "render_spec.json").write_text(json.dumps(render_spec, indent=2, ensure_ascii=False))
        (out_dir / "config_final.json").write_text(json.dumps(body, indent=2, ensure_ascii=False))

        import shutil
        src_timing = ROOT / "F01_LION/OUT/timing.json"
        if src_timing.exists():
            shutil.copy(src_timing, out_dir / "timing.json")

        resp = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resp)

        def stop():
            import time; time.sleep(0.5); server.shutdown()
        threading.Thread(target=stop, daemon=True).start()


port = int(sys.argv[sys.argv.index("--port")+1]) if "--port" in sys.argv else 8080
server = HTTPServer(("0.0.0.0", port), Handler)
print(f"[CALIBAN] Gate 2 → http://localhost:{port}")
server.serve_forever()
