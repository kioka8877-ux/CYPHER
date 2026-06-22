#!/usr/bin/env python3
"""
F02 CALIBAN — Preview HTML Imperivm + contrôles éditables
Lit timing.json + config.json (F01), génère preview.html interactif.
L'opérateur modifie les paramètres visuels et valide → config_final.json.
"""

import json
import os
import sys
import http.server
import threading
from pathlib import Path

BASE        = Path(__file__).resolve().parents[3]
LION_OUT    = BASE / "F01_LION" / "OUT"
CALIBAN_OUT = BASE / "F02_CALIBAN" / "OUT"

TIMING_PATH   = LION_OUT / "timing.json"
CONFIG_PATH   = LION_OUT / "config.json"
PREVIEW_PATH  = CALIBAN_OUT / "preview.html"
CONFIG_FINAL  = CALIBAN_OUT / "config_final.json"
RENDER_SPEC   = CALIBAN_OUT / "render_spec.json"

FONTS = [
    "Arrila Black", "Cinzel", "Cinzel Decorative",
    "IM Fell English", "Crimson Text", "MedievalSharp",
    "Arial", "Impact",
]
SUBTITLE_ANIMATIONS = [
    ("fade", "Fondu"), ("left", "Gauche → Droite"),
    ("right", "Droite → Gauche"), ("up", "Bas → Haut"),
    ("typewriter", "Machine à écrire"), ("none", "Aucune"),
]
MAP_STYLES = [
    ("dark", "Sombre (Dark Angels)"), ("satellite", "Satellite"),
    ("relief", "Relief"), ("vintage", "Vintage / Vieux papier"),
    ("military", "Militaire (topo)"),
]


def build_preview(timing: dict, config: dict) -> str:
    segments  = timing.get("segments", [])
    words     = timing.get("words", [])
    meta      = timing.get("meta", {})
    vis_list  = config.get("visuals", [])
    cfg       = config.get("display", {})
    fmt       = config.get("format", "short")

    sub_font  = cfg.get("subtitle_font", "Cinzel")
    sub_color = cfg.get("subtitle_color", "#FFFFFF")
    sub_size  = cfg.get("subtitle_size", 36)
    sub_pos   = cfg.get("subtitle_position", "bottom")
    sub_anim  = cfg.get("subtitle_animation", "left")
    sub_speed = cfg.get("subtitle_speed", 1.0)
    v_scale   = cfg.get("visual_scale", 1.0)
    map_style = cfg.get("map_style", "dark")

    def opts(items, cur):
        return "".join(
            f'<option value="{v}"{" selected" if v == cur else ""}>{l}</option>'
            for v, l in items
        )

    fonts_opts = "".join(
        f'<option value="{f}"{" selected" if f == sub_font else ""}>{f}</option>'
        for f in FONTS
    )
    fmt_opts = opts([("short","Short"),("long","Long")], fmt)
    map_opts = opts(MAP_STYLES, map_style)
    anim_opts = opts(SUBTITLE_ANIMATIONS, sub_anim)
    pos_opts  = opts([("bottom","Bas"),("center","Centre"),("top","Haut")], sub_pos)

    seg_cards = ""
    for i, seg in enumerate(segments):
        vis = vis_list[i] if i < len(vis_list) else {}
        ev  = seg.get("event", {})
        geo = ev.get("geo_focus", {})
        hl  = ev.get("highlights", [])
        sfx = ev.get("sfx", False)
        hl_html = "".join(f'<span class="pill">{h}</span>' for h in hl) or '<span class="pill dim">—</span>'
        seg_cards += f"""
        <div class="seg-card" id="seg-{i}">
          <div class="seg-hdr">
            <span class="seg-num">#{i+1}</span>
            <span class="seg-t">{seg.get('start_clean',0):.1f}s–{seg.get('end_clean',0):.1f}s</span>
            <span class="sfx-btn {'sfx-on' if sfx else 'sfx-off'}" onclick="toggleSfx({i})">
              {'SFX ●' if sfx else 'SFX ○'}</span>
          </div>
          <div class="seg-txt">"{seg.get('text','')}"</div>
          <div class="seg-meta">🗺 {geo.get('country','—')} · {geo.get('lat','—')}/{geo.get('lon','—')}</div>
          <div class="seg-meta">🖼 {vis.get('file','—')} ({vis.get('type','image')})</div>
          <div class="seg-hl">{hl_html}</div>
        </div>"""

    word_chips = " ".join(
        f'<span class="wc" title="{w.get("start",0):.2f}s">{w.get("word","")}</span>'
        for w in words[:80]
    )
    if len(words) > 80:
        word_chips += f' <span class="wc dim">… +{len(words)-80}</span>'

    dur = meta.get("duration_seconds", 0)
    fps = meta.get("fps", 30)
    fr  = meta.get("total_frames", 0)

    return f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8">
<title>CYPHER — Gate 2</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Cinzel+Decorative:wght@400;700&family=Crimson+Text:ital,wght@0,400;1,400&display=swap');
:root{{--bg:#050B08;--panel:#0D1A14;--card:#111E17;--red:#B30006;--gold:#C9A84C;--txt:#D4C5A9;--dim:#506050;--grn:#1A5C32}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Crimson Text',serif;min-height:100vh}}
header{{background:linear-gradient(90deg,#000,#0a1a0e 50%,#000);border-bottom:2px solid var(--gold);padding:14px 28px;display:flex;align-items:center;justify-content:space-between}}
header h1{{font-family:'Cinzel Decorative',serif;font-size:1.5rem;color:var(--gold);letter-spacing:.15em}}
header .m{{font-size:.8rem;color:var(--dim)}}
.layout{{display:grid;grid-template-columns:320px 1fr;height:calc(100vh - 58px);overflow:hidden}}
.left{{background:var(--panel);border-right:1px solid #1a2e1a;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:14px}}
.sec{{font-family:'Cinzel',serif;font-size:.7rem;letter-spacing:.2em;color:var(--gold);text-transform:uppercase;padding-bottom:5px;border-bottom:1px solid #1a2e1a;margin-bottom:8px}}
label{{display:block;font-size:.8rem;color:var(--dim);margin-top:8px;margin-bottom:3px}}
select,input[type=color],input[type=text]{{width:100%;background:#0a1a0e;border:1px solid #1a2e1a;color:var(--txt);padding:6px 10px;border-radius:3px;font-family:inherit;font-size:.88rem}}
input[type=range]{{width:100%;accent-color:var(--gold);cursor:pointer}}
.rrow{{display:flex;gap:8px;align-items:center}}
.rrow span{{min-width:38px;text-align:right;color:var(--gold);font-size:.82rem}}
.btn-v{{width:100%;padding:13px;margin-top:6px;background:var(--red);color:#fff;border:none;cursor:pointer;font-family:'Cinzel',serif;font-size:.85rem;letter-spacing:.15em;text-transform:uppercase;border-radius:3px}}
.btn-v:hover{{background:#8a0004}}
.btn-e{{width:100%;padding:9px;margin-top:4px;background:#0d2b1a;color:var(--gold);border:1px solid var(--gold);cursor:pointer;font-family:'Cinzel',serif;font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;border-radius:3px}}
.subp{{background:#111;border:1px solid #1a2e1a;border-radius:4px;min-height:72px;display:flex;align-items:flex-end;justify-content:center;padding:10px;overflow:hidden}}
.subp.ctr{{align-items:center}}
.sub-demo{{font-size:36px;color:#fff;text-shadow:0 2px 8px #000;text-align:center;max-width:90%;transition:all .2s}}
.right{{overflow-y:auto;padding:22px;display:flex;flex-direction:column;gap:18px}}
.stat-bar{{display:flex;gap:20px;flex-wrap:wrap;background:var(--card);border:1px solid #1a2e1a;border-radius:4px;padding:12px 18px;font-size:.8rem}}
.stat{{display:flex;flex-direction:column}}.stat span{{color:var(--gold);font-family:'Cinzel',serif;font-size:.95rem}}
.wbox{{background:var(--card);border:1px solid #1a2e1a;border-radius:4px;padding:12px;line-height:2.2}}
.wc{{display:inline-block;background:#0d2b1a;color:var(--txt);padding:1px 5px;border-radius:2px;font-size:.8rem;cursor:default}}
.wc:hover{{background:var(--grn)}}.wc.dim{{color:var(--dim)}}
.sg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px}}
.seg-card{{background:var(--card);border:1px solid #1a2e1a;border-radius:4px;padding:12px;display:flex;flex-direction:column;gap:6px}}
.seg-hdr{{display:flex;align-items:center;gap:7px}}
.seg-num{{font-family:'Cinzel',serif;color:var(--gold);font-size:.78rem;min-width:26px}}
.seg-t{{font-size:.75rem;color:var(--dim)}}
.sfx-btn{{margin-left:auto;font-size:.72rem;cursor:pointer;padding:2px 7px;border-radius:2px}}
.sfx-on{{background:#1a3a1a;color:#4caf50}}.sfx-off{{background:#1a0f0f;color:var(--dim)}}
.seg-txt{{font-style:italic;font-size:.88rem;line-height:1.4}}
.seg-meta{{font-size:.74rem;color:var(--dim)}}
.seg-hl{{display:flex;flex-wrap:wrap;gap:3px}}
.pill{{background:#0d2b1a;color:var(--gold);padding:1px 7px;border-radius:10px;font-size:.72rem;font-family:'Cinzel',serif}}
.pill.dim{{background:#111;color:var(--dim)}}
.sec-lbl{{font-family:'Cinzel',serif;font-size:.7rem;letter-spacing:.15em;color:var(--gold);text-transform:uppercase;margin-bottom:8px}}
.toast{{position:fixed;bottom:28px;right:28px;background:#1a5c32;color:#fff;padding:11px 22px;border-radius:4px;font-family:'Cinzel',serif;font-size:.82rem;opacity:0;transition:opacity .3s;pointer-events:none;z-index:9999}}
.toast.show{{opacity:1}}
</style></head><body>
<header>
  <h1>⚔ CYPHER — Gate 2</h1>
  <span class="m">Format: {fmt.upper()} &nbsp;|&nbsp; {dur:.1f}s &nbsp;|&nbsp; {fr} frames @ {fps}fps &nbsp;|&nbsp; {len(segments)} segments</span>
</header>
<div class="layout">
<div class="left">
  <div>
    <div class="sec">Format & Carte</div>
    <label>Format vidéo</label><select id="ctl-fmt">{fmt_opts}</select>
    <label>Style de carte</label><select id="ctl-map">{map_opts}</select>
  </div>
  <div>
    <div class="sec">Sous-titres</div>
    <label>Police</label><select id="ctl-font">{fonts_opts}</select>
    <label>Couleur</label><input type="color" id="ctl-color" value="{sub_color}">
    <label>Taille (px)</label>
    <div class="rrow"><input type="range" id="ctl-size" min="18" max="72" value="{sub_size}"><span id="sz-v">{sub_size}</span></div>
    <label>Position</label><select id="ctl-pos">{pos_opts}</select>
    <label>Animation</label><select id="ctl-anim">{anim_opts}</select>
    <label>Vitesse</label>
    <div class="rrow"><input type="range" id="ctl-spd" min="0.5" max="3" step="0.1" value="{sub_speed}"><span id="spd-v">{sub_speed:.1f}x</span></div>
  </div>
  <div>
    <div class="sec">Visuels</div>
    <label>Échelle</label>
    <div class="rrow"><input type="range" id="ctl-scl" min="0.5" max="1.5" step="0.05" value="{v_scale}"><span id="scl-v">{v_scale:.2f}x</span></div>
  </div>
  <div>
    <div class="sec">Aperçu sous-titre</div>
    <div class="subp" id="subp"><div class="sub-demo" id="sdemo">La chute de Constantinople</div></div>
  </div>
  <div>
    <button class="btn-v" onclick="save()">✓ VALIDER — GATE 2</button>
    <button class="btn-e" onclick="exportCfg()">⬇ Exporter config_final.json</button>
  </div>
</div>
<div class="right">
  <div class="stat-bar">
    <div class="stat">Audio<span>{dur:.1f}s</span></div>
    <div class="stat">Frames<span>{fr}</span></div>
    <div class="stat">FPS<span>{fps}</span></div>
    <div class="stat">Segments<span>{len(segments)}</span></div>
    <div class="stat">Visuels<span>{len(vis_list)}</span></div>
  </div>
  <div>
    <div class="sec-lbl">Timeline mots</div>
    <div class="wbox">{word_chips}</div>
  </div>
  <div>
    <div class="sec-lbl">Segments ({len(segments)})</div>
    <div class="sg">{seg_cards}</div>
  </div>
</div>
</div>
<div class="toast" id="toast"></div>
<script>
const sfxState={{}};
function toggleSfx(i){{
  sfxState[i]=!sfxState[i];
  const el=document.getElementById('seg-'+i).querySelector('.sfx-btn');
  el.className='sfx-btn '+(sfxState[i]?'sfx-on':'sfx-off');
  el.textContent=sfxState[i]?'SFX ●':'SFX ○';
}}
function upPreview(){{
  const d=document.getElementById('sdemo');
  const p=document.getElementById('subp');
  const font=document.getElementById('ctl-font').value;
  const color=document.getElementById('ctl-color').value;
  const size=document.getElementById('ctl-size').value;
  const pos=document.getElementById('ctl-pos').value;
  d.style.fontFamily="'"+font+"',serif";
  d.style.color=color;
  d.style.fontSize=size+'px';
  p.className='subp'+(pos==='center'?' ctr':'');
  document.getElementById('sz-v').textContent=size;
}}
document.getElementById('ctl-font').addEventListener('change',upPreview);
document.getElementById('ctl-color').addEventListener('input',upPreview);
document.getElementById('ctl-size').addEventListener('input',upPreview);
document.getElementById('ctl-pos').addEventListener('change',upPreview);
document.getElementById('ctl-spd').addEventListener('input',()=>{{
  document.getElementById('spd-v').textContent=parseFloat(document.getElementById('ctl-spd').value).toFixed(1)+'x';
}});
document.getElementById('ctl-scl').addEventListener('input',()=>{{
  document.getElementById('scl-v').textContent=parseFloat(document.getElementById('ctl-scl').value).toFixed(2)+'x';
}});
function getCfg(){{
  return{{
    format:document.getElementById('ctl-fmt').value,
    display:{{
      map_style:document.getElementById('ctl-map').value,
      subtitle_font:document.getElementById('ctl-font').value,
      subtitle_color:document.getElementById('ctl-color').value,
      subtitle_size:parseInt(document.getElementById('ctl-size').value),
      subtitle_position:document.getElementById('ctl-pos').value,
      subtitle_animation:document.getElementById('ctl-anim').value,
      subtitle_speed:parseFloat(document.getElementById('ctl-spd').value),
      visual_scale:parseFloat(document.getElementById('ctl-scl').value),
    }},
    sfx_overrides:sfxState,
  }};
}}
function toast(msg){{
  const t=document.getElementById('toast');
  t.textContent=msg;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2500);
}}
function save(){{
  fetch('/api/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(getCfg())}})
  .then(r=>r.json()).then(d=>{{
    if(d.ok)toast('✓ Config sauvegardée — Gate 2 validée');
    else toast('Erreur : '+d.error);
  }}).catch(()=>toast('Erreur réseau'));
}}
function exportCfg(){{
  const b=new Blob([JSON.stringify(getCfg(),null,2)],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='config_final.json';a.click();
}}
upPreview();
</script>
</body></html>"""


def _merge_segments(timing_segs: list, gate2_cfg: dict) -> list:
    """Fusionne les segments timing avec les overrides Gate 2 (sfx_triggers, visuels assignés)."""
    sfx_overrides  = gate2_cfg.get("sfx_triggers", {})   # {str(idx): bool}
    visuals_assign = gate2_cfg.get("visuals_assign", {})  # {str(idx): filename}
    media_types    = gate2_cfg.get("media_types", {})     # {str(idx): "image"|"video"|"gif"}
    merged = []
    for i, seg in enumerate(timing_segs):
        s = dict(seg)
        k = str(i)
        if k in sfx_overrides:
            s["sfx_trigger"] = sfx_overrides[k]
        if k in visuals_assign:
            s["visual_file"] = visuals_assign[k]
        if k in media_types:
            s["media_type"] = media_types[k]
        merged.append(s)
    return merged


class CalibanHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path in ("/", "/preview"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(PREVIEW_PATH.read_bytes())
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == "/api/save":
            n = int(self.headers.get("Content-Length", 0))
            gate2_cfg = json.loads(self.rfile.read(n))
            CALIBAN_OUT.mkdir(parents=True, exist_ok=True)

            # Sauvegarder config_final.json (Gate 2 brut)
            CONFIG_FINAL.write_text(json.dumps(gate2_cfg, indent=2, ensure_ascii=False))

            # Merger timing.json + config.json + Gate 2 → render_spec.json
            timing = json.loads(TIMING_PATH.read_text()) if TIMING_PATH.exists() else {}
            base_cfg = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}

            render_spec = {
                "meta":     timing.get("meta", {}),
                "words":    timing.get("words", []),
                "segments": _merge_segments(timing.get("segments", []), gate2_cfg),
                "display": {
                    "font":           gate2_cfg.get("font", base_cfg.get("subtitle_font", "Arrila Black")),
                    "font_color":     gate2_cfg.get("font_color", base_cfg.get("subtitle_color", "#FFFFFF")),
                    "font_size":      gate2_cfg.get("font_size", base_cfg.get("subtitle_size", 48)),
                    "position":       gate2_cfg.get("subtitle_position", base_cfg.get("subtitle_position", "bottom")),
                    "animation":      gate2_cfg.get("subtitle_animation", base_cfg.get("subtitle_animation", "left")),
                    "animation_speed":gate2_cfg.get("animation_speed", base_cfg.get("animation_speed", 0.4)),
                    "visual_scale":   gate2_cfg.get("visual_scale", base_cfg.get("visual_scale", 1.0)),
                },
                "format":    base_cfg.get("format", "short"),
                "map_style": base_cfg.get("map_style", "dark"),
                "visuals":   base_cfg.get("visuals", []),
            }
            RENDER_SPEC.write_text(json.dumps(render_spec, indent=2, ensure_ascii=False))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_response(404); self.end_headers()


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8090)
    args = p.parse_args()

    for path, name in [(TIMING_PATH, "timing.json"), (CONFIG_PATH, "config.json")]:
        if not path.exists():
            print(f"[CALIBAN] ERREUR : {name} introuvable → {path}")
            sys.exit(1)

    timing = json.loads(TIMING_PATH.read_text())
    config = json.loads(CONFIG_PATH.read_text())

    print("═" * 52)
    print("  F02 CALIBAN — Preview Gate 2 (thème Imperivm)")
    print("═" * 52)

    CALIBAN_OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.write_text(build_preview(timing, config), encoding="utf-8")
    print(f"[CALIBAN] Preview → {PREVIEW_PATH}")

    server = http.server.HTTPServer(("0.0.0.0", args.port), CalibanHandler)
    print(f"[CALIBAN] Port {args.port} — serveur actif")
    print(f"[CALIBAN] Fermeture automatique après Gate 2 validée")
    print("─" * 52)
    server.serve_forever()

    if RENDER_SPEC.exists():
        print(f"[CALIBAN] render_spec.json → {RENDER_SPEC}")
        print("[CALIBAN] Gate 2 ✓ — prêt pour Gate 3 DEATHWING")


if __name__ == "__main__":
    main()
