#!/usr/bin/env python3
"""
CypherScene — Template Manim fixe.
Lit render_spec.json dans le répertoire courant et forge la vidéo.
"""
import json
from pathlib import Path

try:
    from manim import *
except ImportError:
    raise RuntimeError("manim non installé")

try:
    from atlas.primitives.geo import GeoScene as ATLASGeo
    from atlas.primitives.overlay import TextOverlay
    ATLAS_OK = True
except Exception:
    ATLAS_OK = False


# ── helpers ──────────────────────────────────────────────────────────────────

def load_spec() -> dict:
    for p in [Path("render_spec.json"), Path("../render_spec.json"),
              Path("render_workspace/render_spec.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("render_spec.json introuvable")


def safe_text(content: str, font_size: int, color: str, font: str) -> Text:
    # Arrila Black n'est pas disponible dans l'image Docker → fallback Dejavu
    safe_font = font if font not in ("Arrila Black", "MedievalSharp") else "DejaVu Sans"
    try:
        return Text(content, font_size=font_size, color=color, font=safe_font)
    except Exception:
        return Text(content, font_size=font_size, color=color)


def build_visual(seg: dict, visuals_dir: Path, frame_w: float, frame_h: float):
    """Retourne un Mobject visuel pour le segment."""
    vfile = seg.get("visual_file", "")
    if vfile:
        for d in [visuals_dir, Path("visuals"), Path(".")]:
            p = d / vfile
            if p.exists():
                try:
                    img = ImageMobject(str(p))
                    img.scale_to_fit_width(frame_w * 0.85)
                    if img.height > frame_h * 0.75:
                        img.scale_to_fit_height(frame_h * 0.75)
                    img.move_to(ORIGIN)
                    return img
                except Exception:
                    pass

    # Fallback : rectangle coloré avec coordonnées géo si disponibles
    geo_focus = seg.get("geo_focus", {})
    label = ""
    if geo_focus:
        lat = geo_focus.get("lat", 0)
        lon = geo_focus.get("lon", 0)
        label = f"{lat:.1f}°N {lon:.1f}°E"

    rect = Rectangle(
        width=frame_w * 0.85, height=frame_h * 0.6,
        fill_color="#1A2E25", fill_opacity=0.8,
        stroke_color="#B30006", stroke_width=2,
    )
    rect.move_to(ORIGIN)
    if label:
        coord_text = Text(label, font_size=20, color="#B30006")
        coord_text.move_to(rect.get_center())
        return VGroup(rect, coord_text)
    return rect


# ── scène principale ──────────────────────────────────────────────────────────

class CypherScene(Scene):
    def construct(self):
        spec       = load_spec()
        meta       = spec.get("meta", {})
        segments   = spec.get("segments", [])
        display    = spec.get("display", {})
        map_style  = spec.get("map_style", "dark")

        # Config display
        font       = display.get("font", "DejaVu Sans")
        fcolor     = display.get("font_color", "#FFFFFF")
        fsize      = int(display.get("font_size", 42))
        position   = display.get("position", "bottom")
        anim_type  = display.get("animation", "fade")
        anim_spd   = float(display.get("animation_speed", 0.35))

        fps         = int(meta.get("fps", 30))
        fw          = config.frame_width
        fh          = config.frame_height

        self.camera.background_color = "#050B08" if map_style == "dark" else "#1a1a2e"

        visuals_dir = Path("visuals")
        sub_y = -fh * 0.38 if position == "bottom" else 0.0

        for i, seg in enumerate(segments):
            start_f = seg.get("start_frame", i * 90)
            end_f   = seg.get("end_frame", (i + 1) * 90)
            hold    = max((end_f - start_f) / fps - anim_spd * 2, 0.05)
            text    = seg.get("text", "")

            visual  = build_visual(seg, visuals_dir, fw, fh)

            # Subtitle
            sub = safe_text(text, fsize, fcolor, font)
            sub.move_to([0, sub_y, 0])
            # Wrap long lines
            if sub.width > fw * 0.9:
                sub.scale(fw * 0.9 / sub.width)

            # Animate in
            if anim_type == "left":
                sub.shift(LEFT * fw * 0.15)
                sub.set_opacity(0)
                self.play(
                    FadeIn(visual, run_time=anim_spd),
                    sub.animate.shift(RIGHT * fw * 0.15).set_opacity(1),
                    run_time=anim_spd,
                )
            else:
                self.play(
                    FadeIn(visual, run_time=anim_spd),
                    FadeIn(sub, run_time=anim_spd),
                )

            self.wait(hold)

            # Animate out — dernier segment : fondu propre
            if i == len(segments) - 1:
                self.play(
                    FadeOut(visual, run_time=anim_spd),
                    FadeOut(sub, run_time=anim_spd),
                )
            else:
                self.play(
                    FadeOut(visual, run_time=anim_spd * 0.7),
                    FadeOut(sub, run_time=anim_spd * 0.7),
                )
