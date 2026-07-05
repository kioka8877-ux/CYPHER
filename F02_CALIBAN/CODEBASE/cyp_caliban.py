#!/usr/bin/env python3
"""F02 CALIBAN v8 — Hybrid Preview (CYPHER × GAMMA)

Fusion de CYPHER (carte, travel, états) + Castellan (capsule, sinusoïdal,
background textures, titres, mots forts, grain, vignette) + génération
hybrid_spec.json pour le pipeline hybride complet.
"""
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

US_STATES_MAP = {
    "maryland": ("MD", 39.05, -76.64, 7),
    "georgia": ("GA", 32.68, -83.64, 6.5),
    "virginia": ("VA", 37.77, -78.17, 6.5),
    "florida": ("FL", 28.68, -81.76, 6),
    "california": ("CA", 36.78, -119.42, 6),
    "texas": ("TX", 31.97, -99.90, 6),
    "new york": ("NY", 43.0, -75.5, 6),
    "pennsylvania": ("PA", 41.2, -77.4, 6),
    "ohio": ("OH", 40.4, -82.9, 6),
    "michigan": ("MI", 44.3, -85.4, 6),
    "illinois": ("IL", 40.0, -89.0, 6),
    "north carolina": ("NC", 35.6, -79.0, 6),
    "arizona": ("AZ", 34.3, -111.6, 6),
    "washington": ("WA", 47.4, -121.0, 6),
}

USA_CENTER = ("US", 39.8, -98.5, 3)

BRAND_DOMAINS = {
    "apple": "apple.com", "nike": "nike.com", "coca-cola": "coca-cola.com",
    "mcdonald\'s": "mcdonalds.com", "tesla": "tesla.com", "bmw": "bmw.com",
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
    # Check US states first (priority)
    for name, (c, la, lo, z) in US_STATES_MAP.items():
        if name in text:
            country, iso, lat, lon, zoom = name, c, la, lo, z; break
    # Then countries
    if not country:
        for name, (c, la, lo, z) in COUNTRY_MAP.items():
            if name in text:
                country, iso, lat, lon, zoom = name, c, la, lo, z; break
    fps = 30
    brands = []
    for brand, domain in BRAND_DOMAINS.items():
        if brand in text:
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


def detect_states(segs):
    """Detect US states mentioned in segments, in order of appearance."""
    found = []
    for seg in segs:
        text = seg["text"].lower()
        for name, (iso, lat, lon, zoom) in US_STATES_MAP.items():
            if name in text and name not in [s["name"] for s in found]:
                found.append({"name": name, "iso": iso, "lat": lat, "lon": lon, "zoom": zoom})
    return found


def build_hybrid_chunks(segs, states, fps=30):
    """Build interleaved gamma/cypher chunks from parsed segments + detected states."""
    chunks = []
    cid = 0

    if not states:
        # No states → single gamma chunk
        chunks.append({
            "id": cid, "engine": "gamma",
            "start": segs[0]["start"], "end": segs[-1]["end"],
            "image_file": "intro.png", "media_type": "image",
            "overlay_type": "defaut",
            "text_subtitles": " ".join(s["text"] for s in segs),
            "state_name": "Introduction"
        })
        return chunks

    # Find first segment that mentions a state
    first_state_seg_idx = None
    for i, seg in enumerate(segs):
        text = seg["text"].lower()
        for s in states:
            if s["name"] in text:
                first_state_seg_idx = i
                break
        if first_state_seg_idx is not None:
            break

    # Phase 1: Intro gamma chunk (before first state)
    if first_state_seg_idx and first_state_seg_idx > 0:
        intro_end = segs[first_state_seg_idx]["start"]
        intro_text = " ".join(s["text"] for s in segs[:first_state_seg_idx])
        chunks.append({
            "id": cid, "engine": "gamma",
            "start": segs[0]["start"], "end": intro_end,
            "image_file": "intro_student_debt.png",
            "media_type": "image", "overlay_type": "defaut",
            "text_subtitles": intro_text,
            "state_name": "Introduction"
        })
        cid += 1

    # Phase 2: For each state, create cypher travel + gamma story
    prev_state = None
    for state in states:
        sn = state["name"]
        si = state["iso"]
        slat = state["lat"]
        slon = state["lon"]
        szoom = state["zoom"]

        # Find segments for this state
        state_segs = [s for s in segs if sn in s["text"].lower()]
        if not state_segs:
            continue

        state_start = state_segs[0]["start"]
        state_end = state_segs[-1]["end"]

        # Cypher travel chunk — ALWAYS create one before each state (even first)
        travel_start = chunks[-1]["end"] if chunks else 0.0
        travel_end = state_start
        # Ensure minimum 2s travel time for first state (USA → state)
        if prev_state is None and travel_end - travel_start < 2.0:
            travel_end = travel_start + 2.0
            # Adjust state_start to match
            state_start = travel_end
        if travel_end > travel_start:
            from_coords = {"lon": prev_state["lon"], "lat": prev_state["lat"], "zoom": prev_state["zoom"]} if prev_state \
                else {"lon": USA_CENTER[2], "lat": USA_CENTER[1], "zoom": USA_CENTER[3]}
            chunks.append({
                "id": cid, "engine": "cypher",
                "start": travel_start, "end": travel_end,
                "action": "travel",
                "from": from_coords,
                "to": {"lon": slon, "lat": slat, "zoom": szoom},
                "state_name": sn.title(),
                "state_iso": si
            })
            cid += 1

        # Gamma story chunk
        story_text = " ".join(s["text"] for s in state_segs)
        image_file = f"{sn.replace(' ', '_')}_debt.png"
        chunks.append({
            "id": cid, "engine": "gamma",
            "start": state_start, "end": state_end,
            "image_file": image_file,
            "media_type": "image", "overlay_type": "defaut",
            "text_subtitles": story_text,
            "state_name": sn.title()
        })
        cid += 1

        prev_state = state

    # Phase 3: Travel out (back to USA)
    if prev_state and chunks:
        travel_out_start = chunks[-1]["end"]
        travel_out_end = segs[-1]["end"]
        if travel_out_end > travel_out_start:
            chunks.append({
                "id": cid, "engine": "cypher",
                "start": travel_out_start, "end": travel_out_end,
                "action": "travel_out",
                "from": {"lon": prev_state["lon"], "lat": prev_state["lat"], "zoom": prev_state["zoom"]},
                "to": {"lon": USA_CENTER[2], "lat": USA_CENTER[1], "zoom": USA_CENTER[3]},
                "state_name": "USA",
                "state_iso": "US"
            })

    return chunks


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
STATES = detect_states(SEGS)
HYBRID_CHUNKS = build_hybrid_chunks(SEGS, STATES)


EJ = json.dumps(SEGS, ensure_ascii=False)
METAJ = json.dumps(META, ensure_ascii=False)
STATESJ = json.dumps(STATES, ensure_ascii=False)
CHUNKSJ = json.dumps(HYBRID_CHUNKS, ensure_ascii=False)
TOTAL_FRAMES = META.get("total_frames", 1800)

HTML = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>CYPHER F02 CALIBAN — Hybrid Gate 2</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Playfair+Display:wght@400;700&family=Oswald:wght@400;700&family=Bebas+Neue&family=Montserrat:wght@400;700&family=Inter:wght@400;700;900&family=Lato:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0A0A0A;color:#E8DCC8;font-family:'Courier Prime','Courier New',monospace;font-size:12px;display:flex;flex-direction:column;height:100vh;overflow:hidden}
header{background:#0D0D0D;border-bottom:2px solid #C5A44E;padding:8px 16px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
header .title{font-family:'Cinzel',serif;font-size:14px;font-weight:700;color:#C5A44E;letter-spacing:3px}
header .sub{font-size:10px;color:#666;letter-spacing:1px}
main{display:flex;flex:1;overflow:hidden}
/* Left: Config panel */
#left{width:260px;min-width:260px;background:#0D0D0D;border-right:1px solid #1A1A1A;overflow-y:auto;padding:10px;flex-shrink:0}
#left::-webkit-scrollbar{width:4px}#left::-webkit-scrollbar-thumb{background:rgba(197,164,78,0.25);border-radius:2px}
.section-title{font-family:'Cinzel',serif;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#C5A44E;margin-top:12px;margin-bottom:5px;padding-bottom:3px;border-bottom:1px solid rgba(197,164,78,0.25)}
.section-title:first-child{margin-top:0}
.ctrl-row{margin-bottom:7px}
.ctrl-row label{font-size:11px;color:#999;display:flex;justify-content:space-between;align-items:center}
.ctrl-row .val{font-family:monospace;color:#C5A44E;font-size:10px}
.ctrl-row input[type=range]{width:100%;margin-top:2px;accent-color:#C5A44E}
.ctrl-row select{width:100%;margin-top:2px;background:#1A1A1A;border:1px solid rgba(197,164,78,0.25);border-radius:4px;padding:3px 6px;font-size:11px;color:#E8DCC8;font-family:inherit}
.ctrl-row input[type=color]{width:28px;height:28px;border-radius:4px;border:1px solid rgba(197,164,78,0.25);cursor:pointer;background:transparent;padding:1px}
.ctrl-row input[type=checkbox]{accent-color:#C5A44E;width:15px;height:15px;cursor:pointer}
.ctrl-row input[type=text]{width:100%;margin-top:2px;background:#1A1A1A;border:1px solid rgba(197,164,78,0.25);border-radius:4px;padding:3px 6px;font-size:11px;color:#E8DCC8;font-family:inherit}
/* Center: Preview */
#center{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:10px;overflow:hidden;gap:8px}
#frame-wrap{position:relative;background:#000;border:1px solid rgba(197,164,78,0.25);border-radius:8px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.6)}
#map-div{width:100%;height:100%;position:absolute;top:0;left:0}
#subtitle-bar{position:absolute;left:0;right:0;padding:10px;text-align:center;z-index:1000;pointer-events:none}
#subtitle-text{display:inline-block;padding:4px 12px;border-radius:3px;text-shadow:1px 1px 3px #000}
#state-label{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:1001;background:rgba(0,0,0,0.65);padding:3px 10px;border-radius:3px;font-size:11px;color:#fff;letter-spacing:2px;pointer-events:none}
#timeline-wrap{width:100%;max-width:600px;display:flex;flex-direction:column;gap:4px}
#timeline-bar{width:100%;accent-color:#C5A44E;height:18px}
#timeline-info{display:flex;justify-content:space-between;font-size:9px;color:#C5A44E;font-family:monospace}
/* Right: Segments + chunks */
#right{width:240px;min-width:240px;background:#0D0D0D;border-left:1px solid #1A1A1A;overflow-y:auto;padding:8px;flex-shrink:0}
#right::-webkit-scrollbar{width:4px}#right::-webkit-scrollbar-thumb{background:rgba(197,164,78,0.25);border-radius:2px}
.si{padding:5px 8px;border:1px solid #1A1A1A;border-radius:4px;margin-bottom:3px;cursor:pointer;font-size:10px;transition:.15s}
.si:hover,.si.act{background:rgba(197,164,78,0.08);border-color:#C5A44E;color:#fff}
.st{color:#C5A44E;font-size:9px;font-family:monospace}
.sc{color:#aaa;font-size:9px;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chunk-item{padding:4px 8px;border:1px solid #1A1A1A;border-radius:4px;margin-bottom:3px;font-size:10px}
.chunk-item .engine{font-weight:bold;color:#C5A44E}
.chunk-item .engine.gamma{color:#4a9a6a}
.chunk-item .engine.cypher{color:#4a8aca}
#btn-validate{width:100%;background:#8B0000;color:#E8DCC8;border:none;padding:9px;cursor:pointer;border-radius:4px;font-family:'Cinzel',serif;font-size:12px;letter-spacing:2px;margin-top:8px;text-transform:uppercase;font-weight:700}
#btn-validate:hover{background:#A30000}
#val-msg{font-size:13px;font-weight:bold;color:#4aff8a;margin-top:8px;text-align:center;min-height:20px;background:#0a2a18;border:1px solid #4aff8a;border-radius:4px;padding:6px;display:none}
.leaflet-marker-icon{transition:transform .2s}
</style>
</head>
<body>
<header>
  <div><span class="title">CYPHER</span> <span class="sub">// F02 CALIBAN // HYBRID GATE 2</span></div>
  <div id="seg-info">— / __NUM_SEGS__ segments · __TOTAL_FRAMES__ frames</div>
</header>
<main>
<div id="left">
  <div id="controls"></div>
  <button id="btn-validate" onclick="validate()">Valider Gate 2</button>
  <div id="val-msg"></div>
</div>
<div id="center">
  <div id="frame-wrap">
    <div id="map-div"></div>
    <div id="state-label"></div>
    <div id="subtitle-bar"><span id="subtitle-text">—</span></div>
  </div>
  <div id="timeline-wrap">
    <input type="range" id="timeline-bar" min="0" max="__TOTAL_FRAMES__" value="0" oninput="scrubTimeline(this.value)">
    <div id="timeline-info">
      <span id="tl-frame">frame 0</span>
      <span id="tl-seg">seg —</span>
      <span id="tl-time">0.00s</span>
    </div>
  </div>
</div>
<div id="right">
  <div class="section-title" style="margin-top:0">📋 Segments</div>
  <div id="seg-list"></div>
  <div class="section-title">🔀 Hybrid Chunks</div>
  <div id="chunk-list"></div>
</div>
</main>
<script>
const SEGS=__SEGS_JSON__;
const META=__META_JSON__;
const STATES=__STATES_JSON__;
const CHUNKS=__CHUNKS_JSON__;
const TOTAL=__TOTAL_FRAMES__;
let curIdx=0, map=null, circleLayer=null, logoMarkers=[];
let styleOverrides = {};

const FONTS = ["Cinzel","Playfair Display","Oswald","Bebas Neue","Montserrat","Inter","Lato","Roboto Slab","Arial Black","Impact","Georgia","Courier Prime"];
const FONT_LABELS = ["Cinzel — Serif élégant","Playfair Display — Serif","Oswald — Sans condensé","Bebas Neue — Display","Montserrat — Sans moderne","Inter — Sans tech","Lato — Sans lisible","Roboto Slab — Serif moderne","Arial Black — Display bold","Impact — Impact","Georgia — Serif classique","Courier Prime — Mono"];

const BG_OPTIONS = [
  {label:"Couleur unie", value:"solid"},
  {label:"Papier neuf", value:"paper_new"},
  {label:"Papier froissé", value:"paper_crumpled"},
  {label:"Papyrus ancien", value:"papyrus_old"},
  {label:"Quadrillé bleu", value:"grid_dark"},
];

const BG_IMAGE_URLS = {
  paper_new: "https://raw.githubusercontent.com/kioka8877-ux/CRUSADER/main/gamma/F02_PREVIEW/dist/bg_paper_new.png",
  paper_crumpled: "https://raw.githubusercontent.com/kioka8877-ux/CRUSADER/main/gamma/F02_PREVIEW/dist/bg_paper_crumpled.png",
  papyrus_old: "https://raw.githubusercontent.com/kioka8877-ux/CRUSADER/main/gamma/F02_PREVIEW/dist/bg_papyrus_old.png",
  grid_dark: "https://raw.githubusercontent.com/kioka8877-ux/CRUSADER/main/gamma/F02_PREVIEW/dist/bg_grid_dark.png",
};

const defaults = {
  format: "long",
  width: 854, height: 480,
  // Capsules
  world_scale: 0.85, world_next_scale: 0.35,
  world_opacity: 1.0, world_next_opacity: 0.3,
  // Camera sinusoidal
  camera_amplitude: 200, camera_spacing: 1500,
  // Background
  background_type: "solid", background_color: "#0D0D1A", background_scale: 1.0,
  // Titles
  world_title_visible: true, world_title_font: "Arial Black",
  world_title_size: 32, world_title_color: "#FFFFFF",
  world_title_speed: 12, world_title_gap: 20,
  // Subtitles
  font_primary: "Arial Black", font_accent: "Playfair Display",
  subtitle_size: 36, subtitle_color: "#000000",
  subtitle_position: "bottom", subtitle_align: "center",
  subtitle_anim_enabled: true, subtitle_anim_speed: 5, subtitle_word_fade: 3,
  // Accent / strong words
  accent_color: "#FFD700", accent_size: 42, accent_font: "Playfair Display",
  // Effects
  grain_intensity: 0.08, vignette: true,
  // Highlight (CYPHER)
  highlight_color: "#B30006", highlight_opacity: 0.55,
};

function getS(key) { return styleOverrides[key] ?? defaults[key]; }
function setS(key, val) { styleOverrides[key] = val; }

// ── Map init ──
const TILES = {
  sat:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  dark:'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  light:'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
};
let tileLayer=null;

function initMap() {
  map=L.map('map-div',{zoomControl:false,attributionControl:false});
  tileLayer=L.tileLayer(TILES.sat,{maxZoom:18}).addTo(map);
  map.setView([20,0],2);
}

function getFrameSize() {
  const fmt=getS('format');
  const avH=window.innerHeight-160, avW=window.innerWidth-520;
  if(fmt==='short'){
    const h=Math.min(avH,480); return [Math.round(h*9/16),h];
  }else{
    const w=Math.min(avW,854); return [w,Math.round(w*9/16)];
  }
}

function resizeFrame() {
  const fw=document.getElementById('frame-wrap');
  const [w,h]=getFrameSize(); fw.style.width=w+'px'; fw.style.height=h+'px';
  if(map) map.invalidateSize();
}

function getHighlightColor(){return getS('highlight_color');}

function refreshCountryHighlight(){
  if(!map) return;
  const seg=SEGS[curIdx];
  if(circleLayer){map.removeLayer(circleLayer);circleLayer=null;}
  if(seg.lat||seg.lon){
    circleLayer=L.circle([seg.lat,seg.lon],{
      color:'#FFFFFF',weight:2,
      fillColor:getHighlightColor(),fillOpacity:getS('highlight_opacity'),
      radius:200000
    }).addTo(map);
  }
}

function clearLogoMarkers(){logoMarkers.forEach(m=>map.removeLayer(m));logoMarkers=[];}

function addLogoMarkers(seg,currentFrame){
  clearLogoMarkers();
  if(!seg.lat&&!seg.lon) return;
  const brands=(seg.brands||[]).filter(b=>currentFrame===undefined||b.word_frame<=currentFrame);
  const n=brands.length; if(n===0) return;
  const factor=Math.pow(2,4-Math.min(seg.zoom||4,6))*0.12;
  const r=factor*800000/111000;
  brands.forEach((b,i)=>{
    const angle=(n===1)?Math.PI/2:(i*2*Math.PI/n-Math.PI/2);
    const dlat=r*Math.sin(angle), dlon=r*Math.cos(angle);
    const initials=b.name.split(/\s+/).map(w=>w[0]).join('').toUpperCase().slice(0,2);
    const icon=L.divIcon({
      className:'',
      html:'<div style="background:#fff;border-radius:8px;padding:3px;width:54px;height:54px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,.7);border:2px solid #ffffff"><img src="'+b.logo+'" style="max-width:46px;max-height:46px;object-fit:contain" onerror="this.outerHTML='<div style=width:50px;height:50px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:bold;font-size:14px>'+initials+'</div>'"></div>',
      iconSize:[54,54],iconAnchor:[27,27]
    });
    const m=L.marker([seg.lat+dlat,seg.lon+dlon],{icon,zIndexOffset:1000}).addTo(map);
    m.bindTooltip(b.name,{direction:'top',offset:[0,-30],permanent:false});
    logoMarkers.push(m);
  });
}

function applySubtitleStyle(){
  const txt=document.getElementById('subtitle-text');
  const bar=document.getElementById('subtitle-bar');
  const pos=getS('subtitle_position');
  txt.style.fontFamily="'"+getS('font_primary')+"',Georgia,serif";
  txt.style.color=getS('subtitle_color');
  txt.style.fontSize=getS('subtitle_size')+'px';
  bar.style.bottom=pos==='bottom'?'0':'auto';
  bar.style.top=pos==='top'?'0':pos==='center'?'40%':'auto';
  bar.style.transform=pos==='center'?'translateY(-50%)':'none';
}

function loadSegment(idx){
  if(idx<0||idx>=SEGS.length) return;
  curIdx=idx;
  document.querySelectorAll('.si').forEach((e,i)=>e.classList.toggle('act',i===idx));
  document.getElementById('seg-info').textContent=(idx+1)+' / '+SEGS.length+' segments';
  const seg=SEGS[idx];
  if(seg.lat||seg.lon) map.setView([seg.lat,seg.lon],seg.zoom||5,{animate:true,duration:.5});
  refreshCountryHighlight();
  addLogoMarkers(seg,seg.end_frame||(Math.round(seg.end*30)));
  document.getElementById('subtitle-text').textContent=seg.text;
  applySubtitleStyle();
  const lbl=document.getElementById('state-label');
  lbl.textContent=seg.iso?seg.iso+' — '+(seg.country||'').toUpperCase():'';
  const brands=(seg.brands||[]).map(b=>b.name).join(', ');
  document.getElementById('tl-seg').textContent='seg '+(idx+1);
  const f=seg.start_frame||Math.round(seg.start*30);
  document.getElementById('timeline-bar').value=f;
  updateTimelineInfo(f,idx);
}

function updateTimelineInfo(frame,segIdx){
  document.getElementById('tl-frame').textContent='frame '+frame;
  document.getElementById('tl-time').textContent=(frame/30).toFixed(2)+'s';
}

function scrubTimeline(val){
  const frame=parseInt(val);
  const fps=META.fps||30;
  const t=frame/fps;
  let found=curIdx;
  for(let i=0;i<SEGS.length;i++){
    if(t>=SEGS[i].start&&t<SEGS[i].end){found=i;break;}
    if(t>=SEGS[i].end&&i===SEGS.length-1) found=i;
  }
  if(found!==curIdx){
    loadSegment(found);
    addLogoMarkers(SEGS[found],frame);
  } else {
    addLogoMarkers(SEGS[curIdx],frame);
    updateTimelineInfo(frame,curIdx);
  }
}

function buildList(){
  const list=document.getElementById('seg-list');
  list.innerHTML='';
  SEGS.forEach((s,i)=>{
    const d=document.createElement('div');
    d.className='si'+(i===0?' act':'');
    const brands=(s.brands||[]).map(b=>b.name).slice(0,2).join(', ');
    d.innerHTML='<div style="display:flex;justify-content:space-between"><b>'+(s.iso||'?')+'</b><span class="st">'+s.start.toFixed(1)+'s</span></div><div class="sc">'+(brands||s.text.slice(0,35))+'</div>';
    d.onclick=()=>loadSegment(i);
    list.appendChild(d);
  });
}

function buildChunkList(){
  const list=document.getElementById('chunk-list');
  list.innerHTML='';
  CHUNKS.forEach(c=>{
    const d=document.createElement('div');
    d.className='chunk-item';
    const engineClass=c.engine;
    const detail=c.engine==='cypher'?(c.action+' → '+c.state_name):c.state_name;
    d.innerHTML='<span class="engine '+engineClass+'">'+c.engine.toUpperCase()+'</span> #'+c.id+' <span class="st">'+c.start.toFixed(1)+'s→'+c.end.toFixed(1)+'s</span><div class="sc">'+detail+'</div>';
    list.appendChild(d);
  });
}

// ── Control builders ──
function section(t){return '<div class="section-title">'+t+'</div>';}
function slider(key,label,min,max,step){
  const v=getS(key);
  return '<div class="ctrl-row"><label><span>'+label+'</span><span class="val">'+v+'</span></label><input type="range" data-key="'+key+'" min="'+min+'" max="'+max+'" step="'+step+'" value="'+v+'"></div>';
}
function selectCtrl(key,label,values,labels){
  const v=getS(key);
  const opts=values.map((val,i)=>'<option value="'+val+'" '+(String(val)===String(v)?'selected':'')+'>'+labels[i]+'</option>').join('');
  return '<div class="ctrl-row"><label>'+label+'</label><select data-key="'+key+'">'+opts+'</select></div>';
}
function fontSelect(key,label){
  const v=getS(key);
  const opts=FONTS.map((f,i)=>'<option value="'+f+'" '+(f===v?'selected':'')+'>'+FONT_LABELS[i]+'</option>').join('');
  return '<div class="ctrl-row"><label>'+label+'</label><select data-key="'+key+'">'+opts+'</select></div>';
}
function colorCtrl(key,label){
  const v=getS(key);
  return '<div class="ctrl-row" style="display:flex;align-items:center;gap:8px"><input type="color" data-key="'+key+'" value="'+v+'"><label style="flex:1">'+label+'</label><span class="val" style="font-size:10px">'+v+'</span></div>';
}
function checkbox(key,label){
  const v=getS(key);
  return '<div class="ctrl-row"><label style="gap:8px;cursor:pointer;display:flex;align-items:center"><input type="checkbox" data-key="'+key+'" '+(v?'checked':'')+'> '+label+'</label></div>';
}
function radioGroup(key,options){
  const v=getS(key);
  return '<div class="ctrl-row" style="display:flex;gap:6px">'+options.map(o=>'<label style="flex:1;display:flex;align-items:center;gap:4px;padding:6px 8px;background:'+(o.value===v?'rgba(197,164,78,0.08)':'#1A1A1A')+';border:1px solid '+(o.value===v?'rgba(197,164,78,0.25)':'#1A1A1A')+';border-radius:4px;cursor:pointer;font-size:10px;color:'+(o.value===v?'#C5A44E':'#E8DCC8')+'"><input type="radio" name="'+key+'" value="'+o.value+'" '+(o.value===v?'checked':'')+' style="accent-color:#C5A44E"> '+o.label+'</label>').join('')+'</div>';
}

function buildControls(){
  const c=document.getElementById('controls');
  c.innerHTML =
    section("📐 Format (480p)")+
    radioGroup("format",[{value:"long",label:"16:9 (854×480)"},{value:"short",label:"9:16 (480×854)"}])+

    section("🖼️ Capsules")+
    slider("world_scale","Taille visuel actif",0.2,1,0.05)+
    slider("world_next_scale","Taille visuel N+1",0.1,1,0.05)+
    slider("world_opacity","Opacité visuel actif",0,1,0.05)+
    slider("world_next_opacity","Opacité visuel N+1",0,1,0.01)+

    section("🎥 Caméra sinusoïdale")+
    slider("camera_amplitude","Amplitude (px)",0,500,10)+
    slider("camera_spacing","Espacement (px)",500,3000,50)+

    section("🖼️ Background")+
    selectCtrl("background_type","Type de fond",BG_OPTIONS.map(o=>o.value),BG_OPTIONS.map(o=>o.label))+
    colorCtrl("background_color","Couleur fond")+
    slider("background_scale","Scale fond",0.5,2,0.05)+

    section("📝 Typographie")+
    fontSelect("font_primary","Police principale")+
    fontSelect("font_accent","Police accent")+
    slider("subtitle_size","Taille sous-titres (px)",16,120,2)+
    selectCtrl("subtitle_position","Position",["top","center","bottom"],["Haut","Centre","Bas"])+

    section("🎨 Couleurs")+
    colorCtrl("subtitle_color","Couleur sous-titres")+
    colorCtrl("accent_color","Couleur accent")+

    section("💪 Mots forts (**mot**)")+
    fontSelect("accent_font","Police mots forts")+
    slider("accent_size","Taille mots forts (px)",16,120,2)+
    colorCtrl("accent_color","Couleur mots forts")+

    section("🏷️ Titres (scène)")+
    checkbox("world_title_visible","Afficher les titres")+
    fontSelect("world_title_font","Police titre")+
    slider("world_title_size","Taille titre",14,60,2)+
    colorCtrl("world_title_color","Couleur titre")+
    slider("world_title_speed","Vitesse anim (frames)",4,30,1)+
    slider("world_title_gap","Espace titre↔visuel (px)",0,80,2)+

    section("🎬 Animation sous-titres")+
    checkbox("subtitle_anim_enabled","Animation activée")+
    slider("subtitle_anim_speed","Vitesse (frames)",1,15,1)+
    slider("subtitle_word_fade","Fondu mot (frames)",1,12,1)+

    section("✨ Effets")+
    slider("grain_intensity","Grain",0,1,0.01)+
    checkbox("vignette","Vignetage activé")+

    section("🗺️ Highlight état (CYPHER)")+
    colorCtrl("highlight_color","Couleur highlight")+
    slider("highlight_opacity","Opacité highlight",0,1,0.05);
  bindControlEvents();
}

function bindControlEvents(){
  const c=document.getElementById('controls');
  c.querySelectorAll('input[type=range]').forEach(el=>{
    el.addEventListener('input',()=>{
      const v=parseFloat(el.value);
      setS(el.dataset.key,v);
      const valEl=el.closest('.ctrl-row').querySelector('.val');
      if(valEl) valEl.textContent=v;
    });
  });
  c.querySelectorAll('select').forEach(el=>{
    el.addEventListener('change',()=>{setS(el.dataset.key,el.value);});
  });
  c.querySelectorAll('input[type=checkbox]').forEach(el=>{
    el.addEventListener('change',()=>setS(el.dataset.key,el.checked));
  });
  c.querySelectorAll('input[type=color]').forEach(el=>{
    el.addEventListener('input',()=>{
      setS(el.dataset.key,el.value);
      const valEl=el.closest('.ctrl-row').querySelector('.val');
      if(valEl) valEl.textContent=el.value;
    });
  });
  c.querySelectorAll('input[name=format]').forEach(el=>{
    el.addEventListener('change',()=>{
      setS('format',el.value);
      setS('width',el.value==='short'?480:854);
      setS('height',el.value==='short'?854:480);
      resizeFrame();
    });
  });
}

function validate(){
  const fmt=getS('format');
  const w=fmt==='short'?480:854;
  const h=fmt==='short'?854:480;
  const payload={
    format:fmt, width:w, height:h,
    // Capsules
    world_scale:getS('world_scale'), world_next_scale:getS('world_next_scale'),
    world_opacity:getS('world_opacity'), world_next_opacity:getS('world_next_opacity'),
    // Camera
    camera_amplitude:getS('camera_amplitude'), camera_spacing:getS('camera_spacing'),
    // Background
    background_type:getS('background_type'), background_color:getS('background_color'),
    background_scale:getS('background_scale'),
    // Titles
    world_title_visible:getS('world_title_visible'),
    world_title_font:getS('world_title_font'),
    world_title_size:getS('world_title_size'),
    world_title_color:getS('world_title_color'),
    world_title_speed:getS('world_title_speed'),
    world_title_gap:getS('world_title_gap'),
    // Subtitles
    font_primary:getS('font_primary'), font_accent:getS('font_accent'),
    subtitle_size:getS('subtitle_size'), subtitle_color:getS('subtitle_color'),
    subtitle_position:getS('subtitle_position'), subtitle_align:getS('subtitle_align'),
    subtitle_anim_enabled:getS('subtitle_anim_enabled'),
    subtitle_anim_speed:getS('subtitle_anim_speed'),
    subtitle_word_fade:getS('subtitle_word_fade'),
    // Accent
    accent_color:getS('accent_color'), accent_size:getS('accent_size'),
    accent_font:getS('accent_font'),
    // Effects
    grain_intensity:getS('grain_intensity'), vignette:getS('vignette'),
    // Highlight
    highlight_color:getS('highlight_color'), highlight_opacity:getS('highlight_opacity'),
  };
  fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    .then(r=>r.json()).then(d=>{
      var el=document.getElementById('val-msg');
      el.style.display='block';
      el.textContent=d.ok?'✓ hybrid_spec.json + render_spec.json générés — Gate 3 débloquée':'Erreur: '+d.error;
      if(d.ok){el.style.color='#4aff8a';el.style.borderColor='#4aff8a';}
    }).catch(e=>{
      var el=document.getElementById('val-msg');
      el.style.display='block';
      el.style.color='#4aff8a';
      el.textContent='✓ Validé — serveur arrêté (normal)';
    });
}

window.onresize=resizeFrame;
initMap();
buildControls();
buildList();
buildChunkList();
resizeFrame();
loadSegment(0);
</script>
</body>
</html>
"""

HTML = HTML.replace("__NUM_SEGS__", str(len(SEGS)))
HTML = HTML.replace("__TOTAL_FRAMES__", str(TOTAL_FRAMES))
HTML = HTML.replace("__SEGS_JSON__", EJ)
HTML = HTML.replace("__META_JSON__", METAJ)
HTML = HTML.replace("__STATES_JSON__", STATESJ)
HTML = HTML.replace("__CHUNKS_JSON__", CHUNKSJ)


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

        out_dir = ROOT / "F02_CALIBAN" / "OUT"
        out_dir.mkdir(parents=True, exist_ok=True)
        shared_dir = ROOT / "SHARED"
        shared_dir.mkdir(parents=True, exist_ok=True)

        fps = META.get("fps", 30)
        fmt = body.get("format", "long")
        width = body.get("width", 854)
        height = body.get("height", 480)

        # ── gamma_config ──
        gamma_config = {
            "font_primary": body.get("font_primary", "Arial Black"),
            "font_accent": body.get("font_accent", "Playfair Display"),
            "subtitle_size": int(body.get("subtitle_size", 36)),
            "subtitle_color": body.get("subtitle_color", "#000000"),
            "subtitle_position": body.get("subtitle_position", "bottom"),
            "subtitle_align": body.get("subtitle_align", "center"),
            "subtitle_anim_enabled": body.get("subtitle_anim_enabled", True),
            "subtitle_anim_speed": int(body.get("subtitle_anim_speed", 5)),
            "subtitle_word_fade": int(body.get("subtitle_word_fade", 3)),
            "accent_color": body.get("accent_color", "#FFD700"),
            "accent_size": int(body.get("accent_size", 42)),
            "accent_font": body.get("accent_font", "Playfair Display"),
            "background_type": body.get("background_type", "solid"),
            "background_color": body.get("background_color", "#0D0D1A"),
            "background_scale": float(body.get("background_scale", 1.0)),
            "grain_intensity": float(body.get("grain_intensity", 0.08)),
            "vignette": body.get("vignette", True),
            # Capsule
            "world_scale": float(body.get("world_scale", 0.85)),
            "world_next_scale": float(body.get("world_next_scale", 0.35)),
            "world_opacity": float(body.get("world_opacity", 1.0)),
            "world_next_opacity": float(body.get("world_next_opacity", 0.3)),
            # Sinusoidal
            "camera_amplitude": int(body.get("camera_amplitude", 200)),
            "camera_spacing": int(body.get("camera_spacing", 1500)),
            # Titles
            "world_title_visible": body.get("world_title_visible", True),
            "world_title_font": body.get("world_title_font", "Arial Black"),
            "world_title_size": int(body.get("world_title_size", 32)),
            "world_title_color": body.get("world_title_color", "#FFFFFF"),
            "world_title_speed": int(body.get("world_title_speed", 12)),
            "world_title_gap": int(body.get("world_title_gap", 20)),
        }

        # ── cypher_config ──
        cypher_config = {
            "highlight_color": body.get("highlight_color", "#B30006"),
            "highlight_opacity": float(body.get("highlight_opacity", 0.55)),
        }

        # ── hybrid_spec.json ──
        hybrid_spec = {
            "meta": {
                **META,
                "format": "horizontal" if fmt == "long" else "vertical",
                "width": width,
                "height": height,
                "audio": META.get("audio", "audio_clean.mp3"),
                "version": "2.0",
                "engines": ["cypher", "gamma"],
            },
            "gamma_config": gamma_config,
            "cypher_config": cypher_config,
            "chunks": HYBRID_CHUNKS,
        }

        hybrid_path = shared_dir / "hybrid_spec.json"
        hybrid_path.write_text(json.dumps(hybrid_spec, indent=2, ensure_ascii=False))

        # ── render_spec.json (backward compat) ──
        render_spec = {
            "meta": {**META, "run_id": CFG.get("run_id", ""),
                     "format": fmt, "map_style": "sat",
                     "total_segments": len(SEGS)},
            "segments": SEGS,
            "display": {
                "font": body.get("font_primary", "Arial Black"),
                "font_color": body.get("subtitle_color", "#000000"),
                "font_size": int(body.get("subtitle_size", 36)),
                "position": body.get("subtitle_position", "bottom"),
                "animation": "ltr" if body.get("subtitle_anim_enabled") else "none",
                "visual_scale": float(body.get("world_scale", 0.85)),
            },
            "map_config": {
                "style": "sat",
                "country_fill": body.get("highlight_color", "#B30006"),
                "country_opacity": float(body.get("highlight_opacity", 0.55)),
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
            import time; time.sleep(2.0); server.shutdown()
        threading.Thread(target=stop, daemon=True).start()


port = int(sys.argv[sys.argv.index("--port")+1]) if "--port" in sys.argv else 8080
server = HTTPServer(("0.0.0.0", port), Handler)
print(f"[CALIBAN] Gate 2 → http://localhost:{port}")
server.serve_forever()
