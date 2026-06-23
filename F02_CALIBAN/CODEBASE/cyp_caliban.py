"""
cyp_caliban.py — F02 CALIBAN — CYPHER
======================================
Preview visuel : Leaflet satellite + logos brands + sous-titres.
Inspiré architecture DORN F02 CASTELLAN.
Stack : http.server + Leaflet.js + base64 data injection.

Usage : python cyp_caliban.py [--port 8080]
Entrées  : F01_LION/OUT/timing.json + config.json
Sorties  : F02_CALIBAN/OUT/render_spec.json
"""
import argparse, base64, http.server, json, os, sys, threading

def find_root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "cypher_ledger.json")):
            return d
        d = os.path.dirname(d)
    return os.getcwd()

ROOT   = find_root()
F01OUT = os.path.join(ROOT, "F01_LION", "OUT")
F02IN  = os.path.join(ROOT, "F02_CALIBAN", "IN")
F02OUT = os.path.join(ROOT, "F02_CALIBAN", "OUT")

COUNTRY_DB = {
    "united states":{"iso":"US","lat":37.09,"lon":-95.71,"zoom":4,"flag":"🇺🇸","name":"United States"},
    "usa":          {"iso":"US","lat":37.09,"lon":-95.71,"zoom":4,"flag":"🇺🇸","name":"United States"},
    "germany":      {"iso":"DE","lat":51.16,"lon":10.45, "zoom":5,"flag":"🇩🇪","name":"Germany"},
    "japan":        {"iso":"JP","lat":36.2, "lon":138.25,"zoom":5,"flag":"🇯🇵","name":"Japan"},
    "south korea":  {"iso":"KR","lat":35.91,"lon":127.77,"zoom":6,"flag":"🇰🇷","name":"South Korea"},
    "korea":        {"iso":"KR","lat":35.91,"lon":127.77,"zoom":6,"flag":"🇰🇷","name":"South Korea"},
    "france":       {"iso":"FR","lat":46.23,"lon":2.21,  "zoom":5,"flag":"🇫🇷","name":"France"},
    "italy":        {"iso":"IT","lat":41.87,"lon":12.57, "zoom":5,"flag":"🇮🇹","name":"Italy"},
    "sweden":       {"iso":"SE","lat":60.13,"lon":18.64, "zoom":5,"flag":"🇸🇪","name":"Sweden"},
    "china":        {"iso":"CN","lat":35.86,"lon":104.19,"zoom":4,"flag":"🇨🇳","name":"China"},
    "canada":       {"iso":"CA","lat":56.13,"lon":-106.35,"zoom":4,"flag":"🇨🇦","name":"Canada"},
    "uk":           {"iso":"GB","lat":55.38,"lon":-3.44, "zoom":5,"flag":"🇬🇧","name":"United Kingdom"},
    "united kingdom":{"iso":"GB","lat":55.38,"lon":-3.44,"zoom":5,"flag":"🇬🇧","name":"United Kingdom"},
    "uae":          {"iso":"AE","lat":23.42,"lon":53.85, "zoom":6,"flag":"🇦🇪","name":"UAE"},
    "taiwan":       {"iso":"TW","lat":23.69,"lon":120.96,"zoom":7,"flag":"🇹🇼","name":"Taiwan"},
    "switzerland":  {"iso":"CH","lat":46.82,"lon":8.23,  "zoom":6,"flag":"🇨🇭","name":"Switzerland"},
    "netherlands":  {"iso":"NL","lat":52.13,"lon":5.29,  "zoom":7,"flag":"🇳🇱","name":"Netherlands"},
    "spain":        {"iso":"ES","lat":40.46,"lon":-3.75, "zoom":6,"flag":"🇪🇸","name":"Spain"},
    "india":        {"iso":"IN","lat":20.59,"lon":78.96, "zoom":5,"flag":"🇮🇳","name":"India"},
    "australia":    {"iso":"AU","lat":-25.27,"lon":133.77,"zoom":4,"flag":"🇦🇺","name":"Australia"},
    "singapore":    {"iso":"SG","lat":1.35, "lon":103.82,"zoom":11,"flag":"🇸🇬","name":"Singapore"},
    "finland":      {"iso":"FI","lat":61.92,"lon":25.75, "zoom":6,"flag":"🇫🇮","name":"Finland"},
    "denmark":      {"iso":"DK","lat":56.26,"lon":9.50,  "zoom":6,"flag":"🇩🇰","name":"Denmark"},
    "brazil":       {"iso":"BR","lat":-14.24,"lon":-51.93,"zoom":4,"flag":"🇧🇷","name":"Brazil"},
    "turkey":       {"iso":"TR","lat":38.96,"lon":35.24, "zoom":5,"flag":"🇹🇷","name":"Turkey"},
    "ottoman":      {"iso":"TR","lat":41.01,"lon":28.98, "zoom":7,"flag":"🌙","name":"Ottoman Empire"},
    "byzantine":    {"iso":"GR","lat":41.01,"lon":28.98, "zoom":8,"flag":"🏛️","name":"Byzantine Empire"},
    "constantinople":{"iso":"TR","lat":41.01,"lon":28.98,"zoom":9,"flag":"🏙️","name":"Constantinople"},
    "istanbul":     {"iso":"TR","lat":41.01,"lon":28.98, "zoom":9,"flag":"🕌","name":"Istanbul"},
    "russia":       {"iso":"RU","lat":61.52,"lon":105.32,"zoom":3,"flag":"🇷🇺","name":"Russia"},
    "mexico":       {"iso":"MX","lat":23.63,"lon":-102.55,"zoom":5,"flag":"🇲🇽","name":"Mexico"},
    "indonesia":    {"iso":"ID","lat":-0.79,"lon":113.92, "zoom":4,"flag":"🇮🇩","name":"Indonesia"},
    "saudi arabia": {"iso":"SA","lat":23.89,"lon":45.08,  "zoom":5,"flag":"🇸🇦","name":"Saudi Arabia"},
    "south africa": {"iso":"ZA","lat":-30.56,"lon":22.94, "zoom":5,"flag":"🇿🇦","name":"South Africa"},
    "argentina":    {"iso":"AR","lat":-38.42,"lon":-63.62,"zoom":4,"flag":"🇦🇷","name":"Argentina"},
    "poland":       {"iso":"PL","lat":51.92,"lon":19.15,  "zoom":6,"flag":"🇵🇱","name":"Poland"},
}

BRAND_DOMAINS = {
    "apple":"apple.com","nike":"nike.com","coca-cola":"coca-cola.com",
    "mcdonald":"mcdonalds.com","tesla":"tesla.com","bmw":"bmw.com",
    "mercedes":"mercedes-benz.com","adidas":"adidas.com","toyota":"toyota.com",
    "sony":"sony.com","nintendo":"nintendo.com","samsung":"samsung.com",
    "hyundai":"hyundai.com","lg":"lg.com","airbus":"airbus.com",
    "louis vuitton":"louisvuitton.com","ferrari":"ferrari.com","gucci":"gucci.com",
    "lamborghini":"lamborghini.com","ikea":"ikea.com","volvo":"volvo.com",
    "spotify":"spotify.com","tiktok":"tiktok.com","huawei":"huawei.com",
    "dji":"dji.com","shopify":"shopify.com","rolls-royce":"rolls-royce.com",
    "burberry":"burberry.com","emirates":"emirates.com","tsmc":"tsmc.com",
    "acer":"acer.com","nestle":"nestle.com","rolex":"rolex.com","ubs":"ubs.com",
    "philips":"philips.com","heineken":"heineken.com","asml":"asml.com",
    "zara":"zara.com","tata":"tata.com","qantas":"qantas.com",
    "atlassian":"atlassian.com","canva":"canva.com","grab":"grab.com",
    "nokia":"nokia.com","lego":"lego.com","maersk":"maersk.com",
    "embraer":"embraer.com","amazon":"amazon.com","google":"google.com",
    "microsoft":"microsoft.com","netflix":"netflix.com",
}

def extract_country(text):
    t = text.lower()
    for key in sorted(COUNTRY_DB.keys(), key=len, reverse=True):
        if key in t:
            return COUNTRY_DB[key]
    return {"iso":"WW","lat":20.0,"lon":0.0,"zoom":2,"flag":"🌍","name":"World"}

def extract_brands(text):
    t = text.lower()
    found = []
    for brand, domain in sorted(BRAND_DOMAINS.items(), key=lambda x:len(x[0]), reverse=True):
        if brand in t and domain not in [b["domain"] for b in found]:
            found.append({"name":brand.title(),"domain":domain,
                          "logo":f"https://logo.clearbit.com/{domain}"})
        if len(found) >= 4:
            break
    return found

def build_segments(timing, config):
    return [{
        "id": s["id"], "text": s["text"],
        "start": s["start"], "end": s["end"],
        "start_frame": s["start_frame"], "end_frame": s["end_frame"],
        "country":  extract_country(s["text"]),
        "brands":   extract_brands(s["text"]),
        "sfx_trigger": False, "media_type": "image",
    } for s in timing.get("segments", [])]

def build_html(segments, config):
    font_opts = "".join(
        f'<option value="{f}">{f}</option>'
        for f in ["Cinzel","Arial","Arial Black","Georgia","Impact","Verdana","Courier New"]
    )
    payload_b64 = base64.b64encode(
        json.dumps({"segments":segments,"config":config}, ensure_ascii=False).encode()
    ).decode("ascii")
    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CYPHER F02 CALIBAN</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#050B08;color:#c8c8c8;font-family:monospace;font-size:12px;height:100vh;display:flex;flex-direction:column;overflow:hidden}}
#hdr{{background:#0a120e;border-bottom:1px solid #1a3020;padding:7px 16px;display:flex;justify-content:space-between;align-items:center}}
#hdr h1{{font-size:13px;letter-spacing:3px;color:#00FFD1}}
#hdr span{{font-size:10px;color:#446644}}
#main{{display:flex;flex:1;overflow:hidden}}
#left{{width:255px;min-width:255px;background:#060d09;border-right:1px solid #1a3020;display:flex;flex-direction:column;overflow:hidden}}
#segs{{flex:1;overflow-y:auto;padding:6px}}
.si{{padding:5px 8px;margin:2px 0;cursor:pointer;border-left:2px solid #1a3020;border-radius:2px}}
.si:hover,.si.on{{background:#0d1e12;border-left-color:#00FFD1}}
.si-hd{{display:flex;justify-content:space-between;align-items:center}}
.si-co{{font-size:11px;color:#88cc88}}
.si-t{{font-size:10px;color:#446644}}
.si-tx{{font-size:10px;color:#556655;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:210px}}
.sfxb{{font-size:9px;padding:1px 5px;background:#1a0a0a;border:1px solid #330000;color:#884444;cursor:pointer;border-radius:2px}}
.sfxb.on{{background:#330000;border-color:#B30006;color:#ff7070}}
#ctrl{{padding:10px;border-top:1px solid #1a3020}}
.cr{{display:flex;align-items:center;margin:3px 0;gap:5px}}
.cl{{width:80px;color:#556655;font-size:11px;flex-shrink:0}}
.cr select,.cr input[type=text]{{flex:1;background:#0a1a0e;border:1px solid #1a3020;color:#c8c8c8;padding:3px 5px;font-family:monospace;font-size:11px}}
.cr input[type=range]{{flex:1;accent-color:#00FFD1}}
.cr input[type=color]{{width:28px;height:22px;border:1px solid #1a3020;cursor:pointer}}
.vv{{width:34px;font-size:10px;color:#88cc88}}
#vbtn{{width:100%;margin-top:8px;padding:8px;background:#002b1a;border:1px solid #00FFD1;color:#00FFD1;font-family:monospace;font-size:11px;letter-spacing:2px;cursor:pointer}}
#vbtn:hover{{background:#00FFD1;color:#050B08}}
#smsg{{margin-top:6px;padding:5px 8px;border-radius:3px;display:none;font-size:10px}}
#smsg.ok{{background:#002b1a;border:1px solid #00FFD1;color:#00FFD1;display:block}}
#smsg.er{{background:#2b0000;border:1px solid #B30006;color:#ff7070;display:block}}
#right{{flex:1;display:flex;align-items:center;justify-content:center;background:#030805;position:relative}}
#fw{{position:relative;border:1px solid #1a3020;box-shadow:0 0 30px rgba(0,255,200,.06)}}
#map{{width:100%;height:100%}}
#logos{{position:absolute;top:50%;left:50%;transform:translate(-50%,-60%);display:flex;gap:10px;align-items:center;justify-content:center;pointer-events:none;z-index:400}}
.lg{{height:52px;width:auto;object-fit:contain;background:rgba(0,0,0,.6);border-radius:5px;padding:4px 8px;border:1px solid rgba(255,255,255,.12)}}
.lg-txt{{background:rgba(0,0,0,.6);border:1px solid #446644;padding:4px 8px;border-radius:4px;font-size:11px;color:#88cc88}}
#sub{{position:absolute;left:0;right:0;padding:10px 14px;background:linear-gradient(transparent,rgba(0,0,0,.8));z-index:500;text-align:center;pointer-events:none}}
#stxt{{display:inline-block;text-shadow:2px 2px 4px #000,0 0 6px #000}}
#cbadge{{position:absolute;top:10px;left:10px;background:rgba(5,11,8,.88);border:1px solid #1a3020;border-radius:3px;padding:4px 9px;z-index:500;font-size:12px}}
#fbadge{{position:absolute;top:10px;right:10px;background:rgba(0,43,26,.88);border:1px solid #00FFD1;border-radius:3px;padding:3px 7px;z-index:500;font-size:9px;color:#00FFD1;letter-spacing:1px}}
</style></head><body>
<meta id="pl" data-b="{payload_b64}">
<div id="hdr"><h1>⬡ CYPHER F02 — CALIBAN</h1><span id="fi">—</span></div>
<div id="main">
  <div id="left">
    <div id="segs"></div>
    <div id="ctrl">
      <div style="color:#00FFD1;font-size:10px;letter-spacing:2px;margin-bottom:5px">PARAMÈTRES</div>
      <div class="cr"><span class="cl">Format</span>
        <select id="cf" onchange="applyCtrl()"><option value="short">SHORT 9:16</option><option value="long">LONG 16:9</option></select></div>
      <div class="cr"><span class="cl">Police</span>
        <select id="cfont" onchange="applyCtrl()">{font_opts}</select></div>
      <div class="cr"><span class="cl">Taille</span>
        <input type="range" id="csize" min="18" max="72" value="52" oninput="applyCtrl()">
        <span class="vv" id="csizev">52</span></div>
      <div class="cr"><span class="cl">Couleur</span>
        <input type="color" id="ccol" value="#FFFFFF" oninput="syncCol(this.value)">
        <input type="text" id="ccolh" value="#FFFFFF" maxlength="7" style="width:64px" oninput="syncHex(this.value)"></div>
      <div class="cr"><span class="cl">Position</span>
        <select id="cpos" onchange="applyCtrl()">
          <option value="bottom">Bas</option><option value="center">Centre</option><option value="top">Haut</option></select></div>
      <div class="cr"><span class="cl">Animation</span>
        <select id="canim" onchange="applyCtrl()">
          <option value="ltr">Gauche→Droite</option><option value="fade">Fondu</option><option value="none">Aucune</option></select></div>
      <div class="cr"><span class="cl">Logos scale</span>
        <input type="range" id="cscale" min="0.3" max="2.0" step="0.05" value="0.85" oninput="applyCtrl()">
        <span class="vv" id="cscalev">0.85</span></div>
      <button id="vbtn" onclick="doValidate()">▶ VALIDER GATE 2</button>
      <div id="smsg"></div>
    </div>
  </div>
  <div id="right">
    <div id="fw">
      <div id="map"></div>
      <div id="logos"></div>
      <div id="sub"><span id="stxt"></span></div>
      <div id="cbadge">—</div>
      <div id="fbadge">SHORT 9:16</div>
    </div>
  </div>
</div>
<script>
const DATA = JSON.parse(atob(document.getElementById('pl').dataset.b));
const SEGS = DATA.segments, CFG = DATA.config;
let map, cur=0, sfx={{}};

function frameSize(f){{ return f==='long'?[640,360]:[324,576]; }}

function applyFormat(f){{
  const [w,h]=frameSize(f), fw=document.getElementById('fw');
  fw.style.width=w+'px'; fw.style.height=h+'px';
  document.getElementById('fbadge').textContent=f==='long'?'LONG 16:9':'SHORT 9:16';
  if(map)map.invalidateSize();
}}

function initMap(){{
  map=L.map('map',{{zoomControl:false,attributionControl:false}});
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',{{maxZoom:18}}).addTo(map);
  loadSeg(0);
}}

function loadSeg(i){{
  cur=i; const s=SEGS[i], c=s.country;
  map.flyTo([c.lat,c.lon],c.zoom,{{animate:true,duration:0.7}});
  document.getElementById('cbadge').textContent=c.flag+' '+c.name;
  const ll=document.getElementById('logos'); ll.innerHTML='';
  const sc=parseFloat(document.getElementById('cscale').value);
  s.brands.slice(0,3).forEach(b=>{{
    const img=document.createElement('img');
    img.className='lg'; img.style.height=Math.round(52*sc)+'px';
    img.src=b.logo;
    img.onerror=()=>{{
      img.remove();
      const t=document.createElement('div');
      t.className='lg-txt'; t.textContent=b.name; ll.appendChild(t);
    }};
    ll.appendChild(img);
  }});
  applyCtrl();
  document.querySelectorAll('.si').forEach((el,j)=>el.classList.toggle('on',j===i));
  document.getElementById('fi').textContent=
    `SEG ${{i+1}}/${{SEGS.length}} · ${{s.start.toFixed(2)}}s→${{s.end.toFixed(2)}}s · f${{s.start_frame}}–${{s.end_frame}}`;
}}

function applyCtrl(){{
  const s=SEGS[cur];
  const font=document.getElementById('cfont').value;
  const size=document.getElementById('csize').value;
  const col=document.getElementById('ccol').value;
  const pos=document.getElementById('cpos').value;
  const sc=document.getElementById('cscale').value;
  const fmt=document.getElementById('cf').value;
  document.getElementById('csizev').textContent=size;
  document.getElementById('cscalev').textContent=parseFloat(sc).toFixed(2);
  const stxt=document.getElementById('stxt');
  stxt.textContent=s.text; stxt.style.fontFamily=font;
  stxt.style.fontSize=size+'px'; stxt.style.color=col;
  const sub=document.getElementById('sub');
  sub.style.bottom=pos==='bottom'?'0':'';
  sub.style.top=pos==='top'?'0':pos==='center'?'50%':'';
  document.querySelectorAll('.lg').forEach(img=>img.style.height=Math.round(52*parseFloat(sc))+'px');
  applyFormat(fmt);
}}

function syncCol(v){{ document.getElementById('ccolh').value=v; applyCtrl(); }}
function syncHex(v){{ if(/^#[0-9A-Fa-f]{{6}}$/.test(v))document.getElementById('ccol').value=v; applyCtrl(); }}

function buildList(){{
  const el=document.getElementById('segs');
  SEGS.forEach((s,i)=>{{
    sfx[i]=false;
    const d=document.createElement('div'); d.className='si'+(i===0?' on':'');
    d.innerHTML=`<div class="si-hd">
      <span class="si-co">${{s.country.flag}} ${{s.country.name}}</span>
      <button class="sfxb" id="sx${{i}}" onclick="tsfx(${{i}},event)">SFX</button></div>
      <div class="si-t">${{s.start.toFixed(2)}}s – ${{s.end.toFixed(2)}}s</div>
      <div class="si-tx">${{s.text}}</div>`;
    d.addEventListener('click',e=>{{ if(e.target.classList.contains('sfxb'))return; loadSeg(i); }});
    el.appendChild(d);
  }});
}}

function tsfx(i,e){{
  e.stopPropagation(); sfx[i]=!sfx[i];
  const b=document.getElementById('sx'+i); b.classList.toggle('on',sfx[i]);
}}

function doValidate(){{
  const font=document.getElementById('cfont').value;
  const size=parseInt(document.getElementById('csize').value);
  const col=document.getElementById('ccol').value;
  const pos=document.getElementById('cpos').value;
  const anim=document.getElementById('canim').value;
  const sc=parseFloat(document.getElementById('cscale').value);
  const fmt=document.getElementById('cf').value;
  const spec={{
    meta:DATA.config,
    segments:SEGS.map((s,i)=>Object.assign({{...s}},{{sfx_trigger:sfx[i]||false}})),
    display:{{font,font_color:col,font_size:size,position:pos,animation:anim,visual_scale:sc}},
    format:fmt, map_style:CFG.map_style||'satellite',
    map_config:CFG.map_config||{{}},
    validated_at:new Date().toISOString(),
  }};
  fetch('/api/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(spec)}})
  .then(r=>r.json()).then(d=>{{
    const m=document.getElementById('smsg');
    if(d.ok){{ m.className='ok'; m.textContent='✓ render_spec.json → Gate 3 DEATHWING'; }}
    else{{ m.className='er'; m.textContent='✗ '+(d.error||'?'); }}
  }}).catch(e=>{{ const m=document.getElementById('smsg'); m.className='er'; m.textContent='✗ '+e; }});
}}

window.addEventListener('load',()=>{{
  const d=CFG.display||{{}};
  if(d.font) document.getElementById('cfont').value=d.font;
  if(d.font_size) document.getElementById('csize').value=d.font_size;
  if(d.font_color){{ document.getElementById('ccol').value=d.font_color; document.getElementById('ccolh').value=d.font_color; }}
  if(d.position) document.getElementById('cpos').value=d.position;
  if(d.animation) document.getElementById('canim').value=d.animation;
  if(d.visual_scale) document.getElementById('cscale').value=d.visual_scale;
  document.getElementById('cf').value=CFG.format||'short';
  buildList(); initMap();
}});
</script></body></html>'''

_timing = _config = _segments = None
_shutdown = threading.Event()

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        html = build_html(_segments, _config).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(html)
    def do_POST(self):
        if self.path != "/api/save":
            self.send_response(404); self.end_headers(); return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        body["words"] = _timing.get("words",[])
        os.makedirs(F02OUT, exist_ok=True)
        path = os.path.join(F02OUT,"render_spec.json")
        with open(path,"w",encoding="utf-8") as f: json.dump(body,f,indent=2,ensure_ascii=False)
        resp = json.dumps({"ok":True,"path":path}).encode()
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(resp)
        print(f"\n[CALIBAN] render_spec.json → {path}")
        print("[CALIBAN] Gate 2 validée → python CYPHER_EXECUTEUR.py gate3")
        _shutdown.set()

def main():
    global _timing, _config, _segments
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8080)
    args = parser.parse_args()

    for p in [os.path.join(F01OUT,"timing.json"), os.path.join(F02IN,"timing.json")]:
        if os.path.exists(p):
            with open(p) as f: _timing = json.load(f)
            print(f"[CALIBAN] timing: {p}"); break
    for p in [os.path.join(F01OUT,"config.json"), os.path.join(F02IN,"config.json")]:
        if os.path.exists(p):
            with open(p) as f: _config = json.load(f)
            print(f"[CALIBAN] config: {p}"); break
    if _timing is None:
        print("[CALIBAN] ERREUR: timing.json introuvable"); sys.exit(1)
    _config = _config or {}
    _segments = build_segments(_timing, _config)
    print(f"[CALIBAN] {len(_segments)} segments | preview → http://localhost:{args.port}")

    srv = http.server.HTTPServer(("0.0.0.0", args.port), H)
    def serve():
        while not _shutdown.is_set(): srv.handle_request()
    threading.Thread(target=serve, daemon=True).start()
    _shutdown.wait()
    print("[CALIBAN] Fermé.")

if __name__ == "__main__":
    main()
