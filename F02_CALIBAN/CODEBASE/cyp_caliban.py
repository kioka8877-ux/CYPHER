#!/usr/bin/env python3
"""F02 CALIBAN v5 — Preview visuel Gate 2 CYPHER"""

import json, sys, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
SAVED = threading.Event()

def find(names):
    for n in names:
        for d in [BASE/"IN", ROOT/"F01_LION/OUT"]:
            p = d/n
            if p.exists(): return p
    return None

lp = find(["lion_output.json"])
cp = find(["config.json"])
if not lp or not cp:
    print("[CALIBAN] lion_output.json / config.json introuvables"); sys.exit(1)

LION   = json.loads(lp.read_text())
CFG    = json.loads(cp.read_text())
EVENTS = LION.get("spatial_events", [])
FMT    = CFG.get("format", "short")
DISP   = CFG.get("display", {})
EJ     = json.dumps(EVENTS, ensure_ascii=False)
CJ     = json.dumps(CFG,    ensure_ascii=False)

HTML = ("""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>CYPHER F02 CALIBAN — Gate 2</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#050B08;color:#e0e0e0;font-family:'Cinzel',serif;display:flex;flex-direction:column;height:100vh;overflow:hidden}
header{background:#0a1a12;border-bottom:1px solid #1a3a22;padding:7px 16px;font-size:12px;color:#4a9a6a;letter-spacing:2px;flex-shrink:0}
main{display:flex;flex:1;overflow:hidden}
#left{width:270px;flex-shrink:0;background:#061009;border-right:1px solid #1a3a22;display:flex;flex-direction:column;overflow:hidden}
#seg-list{flex:1;overflow-y:auto;padding:6px}
.si{padding:7px 9px;border:1px solid #1a3a22;border-radius:4px;margin-bottom:5px;cursor:pointer;transition:.15s;font-size:11px}
.si:hover,.si.act{background:#0f2a18;border-color:#4a9a6a;color:#fff}
.st{color:#4a9a6a;font-size:10px;font-family:monospace}
.siso{color:#dc143c;font-weight:bold;font-size:10px}
#ctrl{padding:8px 10px;border-top:1px solid #1a3a22;background:#050B08;font-size:11px}
.cr{display:flex;align-items:center;gap:6px;margin-bottom:5px}
.cr label{width:88px;color:#6a9a7a;font-size:10px;flex-shrink:0}
.cr select,.cr input[type=text]{flex:1;background:#0f2a18;border:1px solid #2a5a3a;color:#e0e0e0;padding:3px 5px;border-radius:3px;font-size:11px}
.cr input[type=range]{flex:1;accent-color:#4a9a6a}
.cr input[type=color]{width:34px;height:22px;border:none;background:none;cursor:pointer;padding:0}
.vv{width:26px;text-align:right;font-size:10px;color:#4a9a6a}
#sfx{border-top:1px solid #1a3a22;padding:6px 10px;max-height:120px;overflow-y:auto}
#sfx h4{color:#dc143c;margin-bottom:4px;font-size:10px;letter-spacing:1px}
.sfxr{display:flex;align-items:center;gap:5px;margin-bottom:2px}
.sfxr span{flex:1;font-size:10px;color:#8a9a8a;font-family:monospace}
.sfxb{padding:1px 7px;border-radius:3px;border:1px solid #2a5a3a;background:#0f2a18;color:#e0e0e0;cursor:pointer;font-size:10px}
.sfxb.on{background:#dc143c;border-color:#dc143c;color:#fff}
#vbtn{margin:8px 10px;padding:9px;background:#dc143c;color:#fff;border:none;border-radius:4px;font-family:'Cinzel',serif;font-size:12px;letter-spacing:2px;cursor:pointer;text-transform:uppercase}
#vbtn:hover{background:#b00010}
#right{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#030805;padding:12px;overflow:hidden;gap:8px}
#fw{position:relative;background:#000;box-shadow:0 0 40px rgba(220,20,60,.3);overflow:hidden}
#map{position:absolute;top:0;left:0;width:100%;height:100%}
#sov{position:absolute;left:0;right:0;display:flex;justify-content:center;pointer-events:none;z-index:1000}
#stxt{display:inline-block;text-align:center;text-shadow:2px 2px 4px #000;background:rgba(0,0,0,.4);padding:4px 10px;border-radius:4px;max-width:90%}
#fi{position:absolute;top:7px;right:7px;background:rgba(0,0,0,.75);color:#4a9a6a;font-size:9px;padding:2px 7px;border-radius:3px;z-index:1000;font-family:monospace}
#si{position:absolute;top:7px;left:7px;background:rgba(220,20,60,.85);color:#fff;font-size:9px;padding:2px 7px;border-radius:3px;z-index:1000;font-family:monospace}
#fb{color:#4a9a6a;font-size:10px;letter-spacing:2px;font-family:monospace}
.leaflet-container{background:#000!important}
</style>
</head>
<body>
<header>&#9670; CYPHER — F02 CALIBAN — Preview Gate 2 &#9670;</header>
<main>
<div id="left">
  <div id="seg-list"></div>
  <div id="ctrl">
    <div class="cr"><label>Format</label>
      <select id="cf"><option value="short">short (9:16)</option><option value="long">long (16:9)</option></select></div>
    <div class="cr"><label>Fond carte</label>
      <select id="cm"><option value="sat">Satellite ESRI</option><option value="ter">Terrain ESRI</option><option value="cdb">CartoDB Dark</option><option value="osm">OSM</option></select></div>
    <div class="cr"><label>Police</label>
      <select id="cfo"><option>Cinzel</option><option>Arial Black</option><option>Georgia</option><option>Impact</option><option>Times New Roman</option></select></div>
    <div class="cr"><label>Couleur</label><input type="color" id="cc" value="#ffffff"></div>
    <div class="cr"><label>Taille</label><input type="range" id="cs" min="18" max="72" value="52"><span class="vv" id="csv">52</span></div>
    <div class="cr"><label>Position</label>
      <select id="cp"><option value="bottom">Bas</option><option value="center">Centre</option><option value="top">Haut</option></select></div>
    <div class="cr"><label>Animation</label>
      <select id="ca"><option value="ltr">G → D</option><option value="none">Aucune</option><option value="fade">Fondu</option></select></div>
    <div class="cr"><label>Scale vis.</label><input type="range" id="csc" min="40" max="120" value="85"><span class="vv" id="cscv">0.85</span></div>
  </div>
  <div id="sfx"><h4>&#9836; SFX</h4><div id="sfxl"></div></div>
  <button id="vbtn" onclick="doValidate()">&#9654; VALIDER GATE 2</button>
</div>
<div id="right">
  <div id="fw">
    <div id="map"></div>
    <div id="si">SEG 0</div>
    <div id="fi">9:16 | satellite</div>
    <div id="sov"><span id="stxt">—</span></div>
  </div>
  <div id="fb">&#9670; 9:16 SHORT</div>
</div>
</main>
<script>
const EV="""
+ EJ
+ """;
const CFG="""
+ CJ
+ """;
const D=CFG.display||{};
const ISO2N={AF:4,AL:8,DZ:12,AR:32,AM:51,AU:36,AT:40,AZ:31,BY:112,BE:56,BR:76,BG:100,CA:124,CL:152,CN:156,CO:170,HR:191,CU:192,CY:196,CZ:203,DK:208,EG:818,EE:233,ET:231,FI:246,FR:250,GE:268,DE:276,GH:288,GR:300,HU:348,IN:356,ID:360,IR:364,IQ:368,IE:372,IL:376,IT:380,JP:392,JO:400,KZ:398,KE:404,LB:422,LY:434,LT:440,MY:458,MX:484,MD:498,MN:496,MA:504,NL:528,NZ:554,NG:566,NO:578,PK:586,PL:616,PT:620,QA:634,RO:642,RU:643,SA:682,RS:688,SG:702,ZA:710,KR:410,ES:724,SD:729,SE:752,CH:756,SY:760,TW:158,TH:764,TN:788,TR:792,UA:804,AE:784,GB:826,US:840,UY:858,UZ:860,VE:862,VN:704,YE:887};
let map,topo=null,hl=null,cur=0;const sfx={};
const TL={sat:['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}','Esri'],ter:['https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}','Esri'],cdb:['https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png','CARTO'],osm:['https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png','OSM']};
function initMap(){map=L.map('map',{zoomControl:false,attributionControl:false});setTile('sat');map.setView([20,20],2);}
function setTile(k){if(window._tl)map.removeLayer(window._tl);const[u]=TL[k]||TL.sat;window._tl=L.tileLayer(u,{subdomains:'abcd'}).addTo(map);}
function sizeFrame(f){
  const rw=document.getElementById('right');
  const ah=rw.clientHeight-50,aw=rw.clientWidth-30;
  let w,h;
  if(f==='short'){h=ah;w=h*9/16;if(w>aw){w=aw;h=w*16/9;}}
  else{w=aw;h=w*9/16;if(h>ah){h=ah;w=h*16/9;}}
  const fw=document.getElementById('fw');
  fw.style.width=Math.round(w)+'px';fw.style.height=Math.round(h)+'px';
  document.getElementById('fb').textContent=f==='short'?'&#9670; 9:16 SHORT':'&#9670; 16:9 LONG';
  document.getElementById('fi').textContent=(f==='short'?'9:16':'16:9')+' | '+document.getElementById('cm').value;
  setTimeout(()=>{if(map)map.invalidateSize();},60);
}
function loadTopo(){fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json').then(r=>r.json()).then(t=>{topo=t;applyS(cur);}).catch(()=>{});}
function hlISOs(hls){
  if(hl){map.removeLayer(hl);hl=null;}
  if(!hls||!hls.length)return;
  if(topo){
    const feats=topojson.feature(topo,topo.objects.countries).features;
    const layers=[];
    hls.forEach(h=>{const n=ISO2N[h.iso];if(!n)return;const f=feats.find(x=>+x.id===n);if(!f)return;
      layers.push(L.geoJSON(f,{style:{fillColor:h.color||'#DC143C',fillOpacity:h.opacity||0.65,color:'#FFFFFF',weight:3,opacity:1}}));});
    if(layers.length){hl=L.layerGroup(layers).addTo(map);}
  } else {
    const ev=EV[cur];if(!ev)return;
    const g=ev.geo_focus||{};
    hl=L.circle([g.lat||20,g.lon||20],{radius:500000,color:hls[0]?.color||'#DC143C',fillColor:hls[0]?.color||'#DC143C',fillOpacity:.4,weight:3}).addTo(map);
  }
}
function applyS(i){
  const ev=EV[i];if(!ev)return;
  document.getElementById('si').textContent='SEG '+i;
  const g=ev.geo_focus||{};if(map&&g.lat!=null)map.setView([g.lat,g.lon],g.zoom||5,{animate:true});
  hlISOs(ev.highlights);
  const ov=(ev.overlays||[]).find(o=>o.type==='text');
  const txt=ov?ov.content:(ev.highlights||[]).map(h=>h.iso).join(' / ')||'—';
  updateSub(txt);
}
function updateSub(t){
  const el=document.getElementById('stxt'),ov=document.getElementById('sov');
  el.style.fontSize=document.getElementById('cs').value+'px';
  el.style.color=document.getElementById('cc').value;
  el.style.fontFamily=document.getElementById('cfo').value+',serif';
  el.textContent=t;
  const pos=document.getElementById('cp').value;
  ov.style.bottom=pos==='bottom'?'6%':pos==='top'?'auto':'45%';
  ov.style.top=pos==='top'?'8%':'auto';
}
function buildSegs(){
  const sl=document.getElementById('seg-list');sl.innerHTML='';
  EV.forEach((ev,i)=>{
    const isos=(ev.highlights||[]).map(h=>h.iso).join(',');
    const d=document.createElement('div');d.className='si'+(i===0?' act':'');d.id='s'+i;
    d.innerHTML=`<div class="st">${ev.t_start.toFixed(1)}s → ${ev.t_end.toFixed(1)}s</div><div class="siso">&#9670; ${isos||'—'}</div>`;
    d.onclick=()=>selSeg(i);sl.appendChild(d);
  });
}
function buildSfx(){
  const sl=document.getElementById('sfxl');sl.innerHTML='';
  EV.forEach((ev,i)=>{sfx[i]=false;const r=document.createElement('div');r.className='sfxr';
    r.innerHTML=`<span>Seg ${i} (${ev.t_start.toFixed(1)}s)</span><button class="sfxb" id="sfxb${i}" onclick="toggleSfx(${i})">&#9675; OFF</button>`;
    sl.appendChild(r);});
}
function toggleSfx(i){sfx[i]=!sfx[i];const b=document.getElementById('sfxb'+i);b.className='sfxb'+(sfx[i]?' on':'');b.innerHTML=sfx[i]?'&#9679; ON':'&#9675; OFF';}
function selSeg(i){document.querySelectorAll('.si').forEach(e=>e.classList.remove('act'));document.getElementById('s'+i).classList.add('act');cur=i;applyS(i);}
function wireCtrl(){
  document.getElementById('cf').value=CFG.format||'short';
  document.getElementById('cfo').value=D.font||'Cinzel';
  document.getElementById('cc').value=D.font_color||'#ffffff';
  document.getElementById('cs').value=D.font_size||52;
  document.getElementById('csv').textContent=D.font_size||52;
  document.getElementById('cp').value=D.position||'bottom';
  document.getElementById('ca').value=D.animation||'ltr';
  document.getElementById('csc').value=Math.round((D.visual_scale||0.85)*100);
  document.getElementById('cscv').textContent=(D.visual_scale||0.85).toFixed(2);
  document.getElementById('cf').onchange=()=>sizeFrame(document.getElementById('cf').value);
  document.getElementById('cm').onchange=()=>{setTile(document.getElementById('cm').value);sizeFrame(document.getElementById('cf').value);};
  document.getElementById('cs').oninput=()=>{document.getElementById('csv').textContent=document.getElementById('cs').value;applyS(cur);};
  document.getElementById('cc').oninput=()=>applyS(cur);
  document.getElementById('cfo').onchange=()=>applyS(cur);
  document.getElementById('cp').onchange=()=>applyS(cur);
  document.getElementById('csc').oninput=()=>{document.getElementById('cscv').textContent=(document.getElementById('csc').value/100).toFixed(2);};
}
function doValidate(){
  const b={format:document.getElementById('cf').value,map_style:document.getElementById('cm').value,font:document.getElementById('cfo').value,font_color:document.getElementById('cc').value,font_size:+document.getElementById('cs').value,position:document.getElementById('cp').value,animation:document.getElementById('ca').value,visual_scale:+document.getElementById('csc').value/100,sfx_triggers:sfx};
  fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.json()).then(d=>{if(d.ok){const btn=document.getElementById('vbtn');btn.textContent='&#10003; GATE 2 VALIDÉ';btn.style.background='#1a5a2a';}});
}
window.onload=()=>{initMap();buildSegs();buildSfx();wireCtrl();sizeFrame(CFG.format||'short');loadTopo();setTimeout(()=>selSeg(0),350);};
window.onresize=()=>sizeFrame(document.getElementById('cf').value);
</script></body></html>""")

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path in ('/','/index.html'):
            body=HTML.encode('utf-8')
            self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Content-Length',len(body));self.end_headers();self.wfile.write(body)
        else:
            self.send_response(404);self.end_headers()
    def do_POST(self):
        if self.path=='/api/save':
            n=int(self.headers.get('Content-Length',0))
            body=json.loads(self.rfile.read(n))
            spec={'meta':{'run_id':CFG.get('run_id',''),'format':body.get('format',FMT),'map_style':body.get('map_style','sat'),'total_segments':len(EVENTS)},'spatial_events':EVENTS,'display':{'font':body.get('font','Cinzel'),'font_color':body.get('font_color','#FFFFFF'),'font_size':int(body.get('font_size',52)),'position':body.get('position','bottom'),'animation':body.get('animation','ltr'),'visual_scale':float(body.get('visual_scale',0.85))},'sfx_triggers':body.get('sfx_triggers',{}),'visuals':CFG.get('visuals',{}),'map_config':CFG.get('map_config',{})}
            out=BASE/'OUT'/'render_spec.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(spec,indent=2,ensure_ascii=False))
            resp=json.dumps({'ok':True}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',len(resp));self.end_headers();self.wfile.write(resp)
            SAVED.set()
        else:
            self.send_response(404);self.end_headers()

def run():
    srv=HTTPServer(('0.0.0.0',PORT),Handler)
    print(f'[CALIBAN] http://localhost:{PORT}',flush=True)
    t=threading.Thread(target=srv.serve_forever,daemon=True);t.start()
    SAVED.wait();print('[CALIBAN] render_spec.json OK',flush=True);srv.shutdown()

if __name__=='__main__':run()
