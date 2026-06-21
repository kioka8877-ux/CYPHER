"""
F02 CALIBAN — Traducteur dict→acier ManimCE + preview HTML
Lit lion_output.json, génère acier.py (code ManimCE exécutable) et preview.html
"""
import argparse
import json
import os
import sys
import datetime
import http.server
import threading
import webbrowser
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
LEDGER_PATH = BASE / "cypher_ledger.json"
STYLE_PATH = BASE / "STYLE" / "CYPHER_STYLE.py"


def load_ledger():
    with open(LEDGER_PATH) as f:
        return json.load(f)


def save_ledger(data):
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# ACIER GENERATOR
# ---------------------------------------------------------------------------

ACIER_HEADER = '''\
"""
CYPHER Acier — généré automatiquement par CALIBAN
Run : python -m manim acier.py CypherScene -o output.mp4 --fps 30
"""
from manim import *
import json
from pathlib import Path

try:
    from atlas.primitives.geo import GeoScene
    from atlas.primitives.overlay import TextOverlay
    from atlas.clock.temporal import TemporalClock
    ATLAS_OK = True
except ImportError:
    ATLAS_OK = False

STYLE = {
    "bg": "#050B08",
    "alert": "#B30006",
    "neutral": "#1A2E25",
    "text": "#E8E0D0",
    "grid": "#0F2018",
}

EVENTS = {events_json}

SCRIPT = {script_json}

'''

ACIER_SCENE = '''\
class CypherScene(Scene):
    def construct(self):
        self.camera.background_color = STYLE["bg"]

        if ATLAS_OK:
            self._construct_atlas()
        else:
            self._construct_fallback()

    def _construct_atlas(self):
        """Rendu complet via ATLAS (ManimCE + géo)."""
        for i, ev in enumerate(EVENTS):
            gf = ev["geo_focus"]
            scene = GeoScene(
                lat=gf["lat"], lon=gf["lon"], zoom=gf.get("zoom", 4),
                width=14, height=8
            )
            # Highlights
            for h in ev.get("highlights", []):
                scene.highlight(h["iso"], color=h.get("color", STYLE["alert"]),
                                opacity=h.get("opacity", 0.6))

            duration = ev["t_end"] - ev["t_start"]
            sub = self._get_subtitle(ev["t_start"], ev["t_end"])

            if i == 0:
                self.play(FadeIn(scene), run_time=0.5)
            else:
                self.play(FadeTransform(prev_scene, scene), run_time=0.8)

            if sub:
                txt = Text(sub, font_size=24, color=STYLE["text"]).to_edge(DOWN).shift(UP * 0.3)
                self.play(FadeIn(txt), run_time=0.3)
                self.wait(max(0.5, duration - 1.2))
                self.play(FadeOut(txt), run_time=0.3)
            else:
                self.wait(max(0.2, duration - 0.8))

            prev_scene = scene

        self.play(FadeOut(prev_scene), run_time=0.5)

    def _construct_fallback(self):
        """Rendu simplifié sans ATLAS (rectangles colorés)."""
        for i, ev in enumerate(EVENTS):
            gf = ev["geo_focus"]
            duration = ev["t_end"] - ev["t_start"]
            sub = self._get_subtitle(ev["t_start"], ev["t_end"])

            bg = Rectangle(width=14, height=8, fill_color=STYLE["neutral"],
                            fill_opacity=1, stroke_width=0)
            coords = Text(
                f"lat={gf['lat']:.1f}  lon={gf['lon']:.1f}  zoom={gf.get('zoom',4)}",
                font_size=18, color=STYLE["alert"]
            ).to_edge(UP).shift(DOWN * 0.3)

            highlights = ev.get("highlights", [])
            bars = VGroup()
            for j, h in enumerate(highlights[:5]):
                r = Rectangle(width=1.2, height=0.5,
                               fill_color=h.get("color", STYLE["alert"]),
                               fill_opacity=0.8, stroke_width=0)
                label = Text(h["iso"], font_size=16, color=WHITE)
                group = VGroup(r, label).arrange(DOWN, buff=0.05)
                group.shift(RIGHT * (j * 1.5 - 3))
                bars.add(group)
            bars.next_to(coords, DOWN)

            group = VGroup(bg, coords, bars)
            if sub:
                txt = Text(sub[:120], font_size=22, color=STYLE["text"]).to_edge(DOWN).shift(UP * 0.3)
                group.add(txt)

            if i == 0:
                self.play(FadeIn(group), run_time=0.5)
                self.wait(max(0.2, duration - 0.8))
            else:
                self.play(FadeTransform(prev_group, group), run_time=0.5)
                self.wait(max(0.2, duration - 0.8))
            prev_group = group

        self.play(FadeOut(prev_group), run_time=0.5)

    def _get_subtitle(self, t_start: float, t_end: float) -> str:
        """Découpe le script selon les timestamps d'événement."""
        total_dur = EVENTS[-1]["t_end"] if EVENTS else 1
        words = SCRIPT.split()
        if not words or total_dur == 0:
            return ""
        start_ratio = t_start / total_dur
        end_ratio = t_end / total_dur
        start_i = int(start_ratio * len(words))
        end_i = int(end_ratio * len(words))
        return " ".join(words[start_i:end_i])
'''


def build_acier(events: list, script: str) -> str:
    events_json = json.dumps(events, indent=2, ensure_ascii=False)
    script_json = json.dumps(script, ensure_ascii=False)
    return (ACIER_HEADER.replace("{events_json}", events_json)
                        .replace("{script_json}", script_json)) + ACIER_SCENE


# ---------------------------------------------------------------------------
# PREVIEW HTML GENERATOR
# ---------------------------------------------------------------------------

def lat_lon_to_pct(lat: float, lon: float):
    """Projection équirectangulaire → pourcentage sur SVG 360×180."""
    x = (lon + 180) / 360 * 100
    y = (90 - lat) / 180 * 100
    return round(x, 2), round(y, 2)


def build_preview_html(events: list, script: str, subject: str, run_id: str) -> str:
    words = script.split()
    total_dur = events[-1]["t_end"] if events else 1

    segments_html = ""
    for i, ev in enumerate(events):
        gf = ev.get("geo_focus", {})
        lat = gf.get("lat", 0)
        lon = gf.get("lon", 0)
        zoom = gf.get("zoom", 4)
        t0 = ev.get("t_start", 0)
        t1 = ev.get("t_end", 0)
        dur = t1 - t0

        # Sous-titre extrait
        start_ratio = t0 / total_dur
        end_ratio = t1 / total_dur
        si = int(start_ratio * len(words))
        ei = int(end_ratio * len(words))
        sub = " ".join(words[si:ei]) if words else ""

        # Highlights pills
        pills = ""
        for h in ev.get("highlights", []):
            iso = h.get("iso", "?")
            color = h.get("color", "#B30006")
            pills += f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;margin:2px;font-size:12px">{iso}</span>'

        # Dot sur mini-map
        px, py = lat_lon_to_pct(lat, lon)
        dot_size = max(6, min(20, int(40 / zoom)))

        segments_html += f"""
        <div class="seg-card" id="seg-{i}">
          <div class="seg-header">
            <span class="seg-index">SEG {i:02d}</span>
            <span class="seg-time">{t0:.1f}s → {t1:.1f}s ({dur:.1f}s)</span>
            <span class="seg-coords">lat={lat:.2f} lon={lon:.2f} zoom={zoom}</span>
          </div>
          <div class="seg-body">
            <div class="minimap-wrap">
              <div class="minimap">
                <div class="dot" style="left:{px}%;top:{py}%;width:{dot_size}px;height:{dot_size}px"></div>
              </div>
              <div class="highlights">{pills}</div>
            </div>
            <div class="sub-text">{sub}</div>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>CALIBAN Preview — {subject}</title>
<style>
  :root{{--bg:#050B08;--bg2:#0F1A12;--bg3:#1A2E25;--alert:#B30006;--text:#E8E0D0;--muted:#6B8F71}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:monospace;padding:20px}}
  header{{border-bottom:1px solid var(--alert);padding-bottom:12px;margin-bottom:20px}}
  h1{{font-size:22px;color:var(--alert);letter-spacing:2px}}
  .meta{{color:var(--muted);font-size:12px;margin-top:4px}}
  .script-box{{background:var(--bg2);border-left:3px solid var(--alert);padding:12px;
    margin-bottom:24px;font-size:13px;line-height:1.7;max-height:140px;overflow:auto}}
  .seg-card{{background:var(--bg2);border:1px solid var(--bg3);border-radius:4px;
    margin-bottom:12px;overflow:hidden}}
  .seg-header{{background:var(--bg3);padding:8px 12px;display:flex;gap:16px;align-items:center}}
  .seg-index{{color:var(--alert);font-weight:bold;min-width:50px}}
  .seg-time{{color:var(--muted);font-size:12px}}
  .seg-coords{{color:var(--text);font-size:11px;margin-left:auto}}
  .seg-body{{padding:10px 12px;display:flex;gap:12px;align-items:flex-start}}
  .minimap-wrap{{min-width:160px}}
  .minimap{{position:relative;width:160px;height:80px;background:#0a1f10;
    border:1px solid var(--bg3);border-radius:2px;overflow:hidden}}
  .minimap::before{{content:'';position:absolute;inset:0;
    background:repeating-linear-gradient(0deg,transparent,transparent 19px,#1a2e2550 19px,#1a2e2550 20px),
    repeating-linear-gradient(90deg,transparent,transparent 19px,#1a2e2550 19px,#1a2e2550 20px)}}
  .dot{{position:absolute;background:var(--alert);border-radius:50%;transform:translate(-50%,-50%);
    box-shadow:0 0 6px var(--alert)}}
  .highlights{{margin-top:6px;display:flex;flex-wrap:wrap;gap:2px}}
  .sub-text{{flex:1;font-size:13px;line-height:1.6;color:var(--text);padding-top:4px;
    border-left:2px solid var(--bg3);padding-left:10px}}
  footer{{margin-top:24px;color:var(--muted);font-size:11px;border-top:1px solid var(--bg3);padding-top:8px}}
</style>
</head>
<body>
<header>
  <h1>CALIBAN PREVIEW</h1>
  <div class="meta">run_id: {run_id} | sujet: {subject} | {len(events)} événements | généré: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</header>
<div class="script-box">{script}</div>
{segments_html}
<footer>CYPHER · CALIBAN F02 · Validé ici → DEATHWING se déclenche (gate3)</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CYPHER F02 CALIBAN")
    parser.add_argument("--input", default=None, help="Chemin lion_output.json (défaut: F01_LION/OUT/lion_output.json)")
    parser.add_argument("--serve", action="store_true", help="Servir le preview sur http://localhost:8090")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()

    # Localiser lion_output.json
    if args.input:
        lion_path = Path(args.input)
    else:
        lion_path = BASE / "F01_LION" / "OUT" / "lion_output.json"

    if not lion_path.exists():
        sys.exit(f"[CALIBAN] lion_output.json introuvable : {lion_path}")

    with open(lion_path) as f:
        lion_data = json.load(f)

    events = lion_data.get("spatial_events", [])
    script = lion_data.get("script", "")

    if not events:
        sys.exit("[CALIBAN] Aucun spatial_event dans lion_output.json")

    ledger = load_ledger()
    subject = ledger.get("narrative", {}).get("subject", "CYPHER")
    run_id = ledger.get("run_id", "?")

    print(f"[CALIBAN] {len(events)} événements | run_id: {run_id}")

    # Générer acier.py
    acier_code = build_acier(events, script)
    out_dir = BASE / "F02_CALIBAN" / "OUT"
    out_dir.mkdir(exist_ok=True)
    acier_path = out_dir / "acier.py"
    with open(acier_path, "w") as f:
        f.write(acier_code)
    print(f"[CALIBAN] acier.py → {acier_path}")

    # Générer preview.html
    preview_html = build_preview_html(events, script, subject, run_id)
    preview_path = out_dir / "preview.html"
    with open(preview_path, "w") as f:
        f.write(preview_html)
    print(f"[CALIBAN] preview.html → {preview_path}")

    # Mettre à jour le ledger
    ledger["assets"]["acier_path"] = str(acier_path)
    ledger["assets"]["preview_html"] = str(preview_path)
    ledger["status"] = "caliban_done"
    save_ledger(ledger)

    print(f"\n[CALIBAN] STATUS: caliban_done")
    print(f"[CALIBAN] Preview : {preview_path}")

    if args.serve:
        # Serveur HTTP minimaliste pour le preview
        import http.server
        import socketserver

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=str(out_dir), **kw)
            def log_message(self, *a):
                pass

        port = args.port
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"[CALIBAN] Preview disponible → http://localhost:{port}/preview.html")
            print(f"[CALIBAN] Ctrl+C pour arrêter")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[CALIBAN] Serveur arrêté")


if __name__ == "__main__":
    main()
