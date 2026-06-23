#!/usr/bin/env python3
"""F02 CALIBAN v4 — Preview visuel interactif CYPHER"""
import json, os, sys, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).parent.parent
IN   = BASE / "IN"
OUT  = BASE / "OUT"
OUT.mkdir(exist_ok=True)

COUNTRY_COORDS = {
    "united states":{"lat":38,"lon":-97,"zoom":4,"iso":"US","flag":"🇺🇸"},
    "usa":{"lat":38,"lon":-97,"zoom":4,"iso":"US","flag":"🇺🇸"},
    "germany":{"lat":51.2,"lon":10.5,"zoom":5,"iso":"DE","flag":"🇩🇪"},
    "japan":{"lat":36.2,"lon":138.3,"zoom":5,"iso":"JP","flag":"🇯🇵"},
    "south korea":{"lat":35.9,"lon":127.8,"zoom":6,"iso":"KR","flag":"🇰🇷"},
    "korea":{"lat":35.9,"lon":127.8,"zoom":6,"iso":"KR","flag":"🇰🇷"},
    "france":{"lat":46.2,"lon":2.2,"zoom":5,"iso":"FR","flag":"🇫🇷"},
    "italy":{"lat":41.9,"lon":12.6,"zoom":5,"iso":"IT","flag":"🇮🇹"},
    "sweden":{"lat":60.1,"lon":18.6,"zoom":5,"iso":"SE","flag":"🇸🇪"},
    "china":{"lat":35.9,"lon":104.2,"zoom":4,"iso":"CN","flag":"🇨🇳"},
    "canada":{"lat":56.1,"lon":-106.3,"zoom":4,"iso":"CA","flag":"🇨🇦"},
    "united kingdom":{"lat":55.4,"lon":-3.4,"zoom":5,"iso":"GB","flag":"🇬🇧"},
    "uk":{"lat":55.4,"lon":-3.4,"zoom":5,"iso":"GB","flag":"🇬🇧"},
    "united arab emirates":{"lat":23.4,"lon":53.8,"zoom":6,"iso":"AE","flag":"🇦🇪"},
    "uae":{"lat":23.4,"lon":53.8,"zoom":6,"iso":"AE","flag":"🇦🇪"},
    "taiwan":{"lat":23.7,"lon":121.0,"zoom":7,"iso":"TW","flag":"🇹🇼"},
    "switzerland":{"lat":46.8,"lon":8.2,"zoom":7,"iso":"CH","flag":"🇨🇭"},
    "netherlands":{"lat":52.1,"lon":5.3,"zoom":7,"iso":"NL","flag":"🇳🇱"},
    "spain":{"lat":40.4,"lon":-3.7,"zoom":5,"iso":"ES","flag":"🇪🇸"},
    "india":{"lat":20.6,"lon":78.9,"zoom":4,"iso":"IN","flag":"🇮🇳"},
    "australia":{"lat":-25.3,"lon":133.8,"zoom":4,"iso":"AU","flag":"🇦🇺"},
    "singapore":{"lat":1.3,"lon":103.8,"zoom":10,"iso":"SG","flag":"🇸🇬"},
    "finland":{"lat":61.9,"lon":25.7,"zoom":5,"iso":"FI","flag":"🇫🇮"},
    "denmark":{"lat":56.3,"lon":9.5,"zoom":6,"iso":"DK","flag":"🇩🇰"},
    "brazil":{"lat":-14.2,"lon":-51.9,"zoom":4,"iso":"BR","flag":"🇧🇷"},
}
BRAND_DOMAINS = {
    "apple":"apple.com","nike":"nike.com","coca-cola":"coca-cola.com",
    "mcdonald's":"mcdonalds.com","tesla":"tesla.com","bmw":"bmw.com",
    "mercedes-benz":"mercedes-benz.com","mercedes":"mercedes-benz.com",
    "adidas":"adidas.com","toyota":"toyota.com","sony":"sony.com",
    "nintendo":"nintendo.com","samsung":"samsung.com","hyundai":"hyundai.com",
    "lg":"lg.com","airbus":"airbus.com","louis vuitton":"louisvuitton.com",
    "ferrari":"ferrari.com","gucci":"gucci.com","lamborghini":"lamborghini.com",
    "ikea":"ikea.com","volvo":"volvo.com","spotify":"spotify.com",
    "tiktok":"tiktok.com","huawei":"huawei.com","dji":"dji.com",
    "shopify":"shopify.com","bombardier":"bombardier.com",
    "rolls-royce":"rolls-royce.com","burberry":"burberry.com",
    "british airways":"britishairways.com","emirates":"emirates.com",
    "tsmc":"tsmc.com","acer":"acer.com","nestle":"nestle.com",
    "rolex":"rolex.com","ubs":"ubs.com","philips":"philips.com",
    "heineken":"heineken.com","asml":"asml.com","zara":"zara.com",
    "santander":"santander.com","reliance":"relianceindustries.com",
    "qantas":"qantas.com","atlassian":"atlassian.com","canva":"canva.com",
    "grab":"grab.com","singapore airlines":"singaporeair.com",
    "nokia":"nokia.com","kone":"kone.com","lego":"lego.com",
    "maersk":"maersk.com","embraer":"embraer.com",
}

def extract(text):
    t=text.lower()
    countries=[{"name":n.title(),**d} for n,d in COUNTRY_COORDS.items() if n in t]
    brands=[{"name":b.title(),"domain":dm,"logo":f"https://logo.clearbit.com/{dm}"}
            for b,dm in BRAND_DOMAINS.items() if b in t]
    return countries,brands

def build_segs(timing):
    out=[]
    for i,s in enumerate(timing.get("segments",[])):
        text=s.get("text","")
        countries,brands=extract(text)
        primary=countries[0] if countries else {"lat":20,"lon":0,"zoom":2,"iso":"XX","flag":"🌍","name":"World"}
        out.append({"id":i,"start":s.get("start",0),"end":s.get("end",0),"text":text.strip(),
                    "countries":countries,"brands":brands,"primary":primary,"sfx":False,"visual_override":None})
    return out

HTML=r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>CYPHER Gate 2</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#050B08;color:#e8e4d0;font-family:'Segoe UI',sans-serif;display:flex;height:100vh;overflow:hidden}
#sb{width:290px;flex-shrink:0;background:#08120a;border-right:1px solid #162018;display:flex;flex-direction:column}
#ctrl{padding:10px;border-bottom:1px solid #162018}
#ctrl h3{color:#b30006;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px}
.cr{display:flex;align-items:center;gap:5px;margin-bottom:5px;font-size:11px}
.cr label{width:80px;color:#556;flex-shrink:0}
.cr select,.cr input{flex:1;background:#0d1e10;border:1px solid #1c2e1e;color:#e8e4d0;padding:3px 5px;border-radius:2px;font-size:11px}
.cr input[type=range]{padding:0}
.cr span{font-size:10px;color:#667;width:32px}
#vbtn{width:100%;padding:10px;background:#b30006;color:#fff;border:none;cursor:pointer;font-size:12px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;margin-top:7px}
#vbtn:hover{background:#d40008}
#slist{flex:1;overflow-y:auto}
.si{padding:7px 11px;border-bottom:1px solid #0d1a0e;cursor:pointer}
.si:hover,.si.active{background:#0d2014}
.si.active{border-left:3px solid #b30006}
.st{font-size:10px;color:#334}
.sx{font-size:11px;color:#889;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
.sf{font-size:12px;margin-top:2px}
.sfb{padding:2px 6px;font-size:10px;border:1px solid #1c2e1e;background:transparent;color:#445;cursor:pointer;border-radius:2px;margin-top:3px}
.sfb.on{border-color:#b30006;color:#b30006}
#main{flex:1;display:flex;flex-direction:column}
#map{flex:1}
#fr{height:105px;background:#050B08;border-top:1px solid #162018;display:flex;align-items:center;gap:10px;padding:8px 13px}
#lg{display:flex;gap:5px;align-items:center;flex-wrap:wrap;min-width:90px}
#lg img{height:30px;background:#fff;border-radius:3px;padding:2px}
#sw{flex:1;height:85px;display:flex;align-items:flex-end;justify-content:center;padding-bottom:5px}
#st{font-size:16px;color:#fff;text-shadow:0 2px 5px #000;padding:3px 8px;background:rgba(0,0,0,.5);border-radius:3px}
#inf{font-size:10px;color:#334;white-space:nowrap}
#fb{background:#b30006;color:#fff;padding:1px 6px;border-radius:2px;font-size:10px;margin-left:5px}
</style></head><body>
<div id="sb">
  <div id="ctrl">
    <h3>Imperivm <span id="fb">SHORT</span></h3>
    <div class="cr"><label>Format</label>
      <select id="cf" onchange="document.getElementById('fb').textContent=this.value.toUpperCase()">
        <option value="short">Short 9:16</option><option value="long">Long 16:9</option></select></div>
    <div class="cr"><label>Police</label>
      <select id="cfont" onchange="us()">
        <option value="Cinzel">Cinzel</option><option value="Arial Black">Arrila Black</option>
        <option value="Times New Roman">Times New Roman</option><option value="Georgia">Georgia</option></select></div>
    <div class="cr"><label>Couleur</label><input type="color" id="ccol" value="#ffffff" oninput="us()"></div>
    <div class="cr"><label>Taille</label><input type="range" id="csz" min="14" max="68" value="52" oninput="document.getElementById('szv').textContent=this.value+'px';us()"><span id="szv">52px</span></div>
    <div class="cr"><label>Position</label>
      <select id="cpos" onchange="up()"><option value="bottom">Bas</option><option value="center">Centre</option><option value="top">Haut</option></select></div>
    <div class="cr"><label>Animation</label>
      <select id="canim"><option value="ltr">Gauche→Droite</option><option value="fade">Fondu</option><option value="none">Aucune</option></select></div>
    <div class="cr"><label>Scale</label><input type="range" id="csc" min="30" max="150" value="85" oninput="document.getElementById('scv').textContent=this.value+'%'"><span id="scv">85%</span></div>
    <div class="cr"><label>Carte</label>
      <select id="cmap" onchange="setT(this.value)">
        <option value="satellite">Satellite ESRI</option><option value="dark">Dark</option><option value="terrain">Terrain</option></select></div>
    <button id="vbtn" onclick="save()">✓ VALIDER GATE 2</button>
  </div>
  <div id="slist"></div>
</div>
<div id="main"><div id="map"></div>
  <div id="fr">
    <div id="lg"></div>
    <div id="sw"><div id="st">Sous-titre preview</div></div>
    <div id="inf">SEG 0</div>
  </div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const S=__SEGS__;const C=__CFG__;let cur=0,tl,hl;
const map=L.map('map',{zoomControl:true,attributionControl:false});
function setT(s){if(tl)map.removeLayer(tl);
  const m={satellite:'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    dark:'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    terrain:'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'};
  tl=L.tileLayer(m[s]).addTo(map);}
setT('satellite');
function show(i){cur=i;const s=S[i],p=s.primary;
  map.flyTo([p.lat,p.lon],p.zoom,{duration:1});
  if(hl)map.removeLayer(hl);
  hl=L.circle([p.lat,p.lon],{radius:Math.max(40000,600000/Math.pow(2,p.zoom-3)),
    color:'#fff',weight:3,fillColor:'#b30006',fillOpacity:.25}).addTo(map);
  document.getElementById('lg').innerHTML=s.brands.slice(0,5).map(b=>
    `<img src="${b.logo}" title="${b.name}" onerror="this.style.display='none'">`).join('');
  document.getElementById('st').textContent=s.text.length>70?s.text.slice(0,70)+'…':s.text;
  document.getElementById('inf').textContent=`SEG ${i} | ${s.start.toFixed(1)}→${s.end.toFixed(1)}s`;
  us();document.querySelectorAll('.si').forEach((el,j)=>el.classList.toggle('active',j===i));}
function us(){const el=document.getElementById('st');
  el.style.fontFamily=document.getElementById('cfont').value;
  el.style.color=document.getElementById('ccol').value;
  el.style.fontSize=document.getElementById('csz').value+'px';}
function up(){const p=document.getElementById('cpos').value,w=document.getElementById('sw');
  w.style.alignItems=p==='top'?'flex-start':p==='center'?'center':'flex-end';}
const sl=document.getElementById('slist');
S.forEach((s,i)=>{const d=document.createElement('div');d.className='si'+(i===0?' active':'');
  d.innerHTML=`<div class="st">${s.start.toFixed(1)}–${s.end.toFixed(1)}s</div>
    <div class="sx">${s.text.slice(0,55)}</div><div class="sf">${s.countries.map(c=>c.flag||'').join(' ')}</div>
    <button class="sfb ${s.sfx?'on':''}" onclick="tsf(event,${i})">${s.sfx?'SFX ●':'SFX ○'}</button>`;
  d.addEventListener('click',e=>{if(e.target.classList.contains('sfb'))return;show(i);});sl.appendChild(d);});
function tsf(e,i){e.stopPropagation();S[i].sfx=!S[i].sfx;const b=e.target;
  b.className='sfb'+(S[i].sfx?' on':'');b.textContent=S[i].sfx?'SFX ●':'SFX ○';}
function save(){
  const cfg={format:document.getElementById('cf').value,map_style:document.getElementById('cmap').value,
    display:{font:document.getElementById('cfont').value,font_color:document.getElementById('ccol').value,
      font_size:parseInt(document.getElementById('csz').value),position:document.getElementById('cpos').value,
      animation:document.getElementById('canim').value,visual_scale:parseInt(document.getElementById('csc').value)/100}};
  fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({segments:S,config:cfg})})
  .then(r=>r.json()).then(d=>{const b=document.getElementById('vbtn');b.textContent='✓ VALIDÉ';b.style.background='#1a6e2a';});}
show(0);
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    segs=[];timing={};config={}
    def log_message(self,*a):pass
    def do_GET(self):
        if urlparse(self.path).path=='/':
            h=HTML.replace('__SEGS__',json.dumps(self.segs,ensure_ascii=False)).replace('__CFG__',json.dumps(self.config,ensure_ascii=False))
            self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.end_headers();self.wfile.write(h.encode())
        else:self.send_response(404);self.end_headers()
    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))
        segs=data.get('segments',[]);cfg=data.get('config',{})
        spec={"run_id":self.config.get('run_id',''),"meta":self.timing.get('meta',{}),"words":self.timing.get('words',[]),
              "segments":[{"id":s['id'],"start":s['start'],"end":s['end'],"text":s['text'],"countries":s.get('countries',[]),
              "brands":s.get('brands',[]),"primary":s.get('primary',{}),"sfx_trigger":s.get('sfx',False),
              "media_type":"image","visual_file":s.get('visual_override','')} for s in segs],
              "display":cfg.get('display',{}),"format":cfg.get('format','short'),
              "map_style":cfg.get('map_style','satellite'),"map_config":self.config.get('map_config',{})}
        (OUT/'render_spec.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False))
        (OUT/'config_final.json').write_text(json.dumps(cfg,indent=2))
        resp=json.dumps({"ok":True,"path":str(OUT/'render_spec.json')}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(resp)
        threading.Timer(1.5,lambda:os._exit(0)).start()

def main(port=8080):
    tp=IN/'timing.json';cp=IN/'config.json'
    if not tp.exists():sys.exit(f"[CALIBAN] Manque {tp}")
    t=json.loads(tp.read_text());c=json.loads(cp.read_text()) if cp.exists() else {}
    Handler.timing=t;Handler.config=c;Handler.segs=build_segs(t)
    print(f"[CALIBAN] {len(Handler.segs)} segments | http://localhost:{port}")
    HTTPServer(('0.0.0.0',port),Handler).serve_forever()

if __name__=='__main__':
    main(int(sys.argv[1]) if len(sys.argv)>1 else 8080)
