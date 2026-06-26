#!/usr/bin/env python3
"""CypherScene v3 — Template Manim. Lit render_spec.json, forge video 9:16."""
import json, tempfile
from pathlib import Path

try:
    from manim import config
    config.pixel_width = 1080
    config.pixel_height = 1920
    config.frame_height = 8.0
    config.frame_width = config.frame_height * 1080 / 1920  # = 4.5 (portrait)
    from manim import *
except ImportError:
    raise RuntimeError("manim non installe")


def load_spec() -> dict:
    for p in [Path("render_spec.json"), Path("../render_spec.json"),
              Path("render_workspace/render_spec.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("render_spec.json introuvable")


def generate_map(lat, lon, iso, country_color, out_path, w=810, h=1080):
    """FIX 1: shapefile via URL (geopandas.datasets deprecie/casse)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import geopandas as gpd

        # Tente le nouveau chemin, sinon telecharge NaturalEarth direct
        try:
            world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        except Exception:
            ne_url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
            world = gpd.read_file(ne_url)

        fig, ax = plt.subplots(figsize=(w/100, h/100), dpi=100)
        fig.patch.set_facecolor("#050B08")
        ax.set_facecolor("#050B08")
        world.plot(ax=ax, color="#1A2E25", edgecolor="#FFFFFF", linewidth=0.3)
        if iso:
            hi = world[world["iso_a3"] == iso.upper()]
            if not hi.empty:
                hi.plot(ax=ax, color=country_color, edgecolor="#FFFFFF", linewidth=1.5)
                b = hi.total_bounds
                cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
                sx = max((b[2]-b[0])*2.2, 60)
                sy = max((b[3]-b[1])*2.2, 40)
                ax.set_xlim(cx-sx/2, cx+sx/2)
                ax.set_ylim(cy-sy/2, cy+sy/2)
            else:
                ax.set_xlim(lon-35, lon+35); ax.set_ylim(lat-25, lat+25)
        else:
            ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
        ax.set_axis_off()
        plt.tight_layout(pad=0)
        plt.savefig(out_path, bbox_inches="tight", pad_inches=0, facecolor="#050B08", dpi=100)
        plt.close(fig)
        return Path(out_path).stat().st_size > 500
    except Exception as e:
        print(f"[MAP] {e}"); return False


def dl_logo(url, path):
    try:
        import urllib.request
        urllib.request.urlretrieve(url, path)
        return Path(path).stat().st_size > 800
    except Exception as e:
        print(f"[LOGO] {e}"); return False


def safe_text(txt, sz, col, font):
    f = font if font not in ("Arrila Black", "MedievalSharp") else "DejaVu Sans"
    try:
        return Text(txt, font_size=sz, color=col, font=f)
    except Exception:
        return Text(txt, font_size=sz, color=col)


class CypherScene(Scene):
    def construct(self):
        spec      = load_spec()
        meta      = spec.get("meta", {})
        segments  = spec.get("segments", [])
        display   = spec.get("display", {})
        map_conf  = spec.get("map_config", {})

        font    = display.get("font", "DejaVu Sans")
        fcolor  = display.get("font_color", "#FFFFFF")
        fsize   = int(display.get("font_size", 38))
        pos     = display.get("position", "bottom")
        vs      = float(display.get("visual_scale", 0.85))   # FIX 2: lire visual_scale
        spd     = 0.3

        cfill   = map_conf.get("country_fill", "#B30006")
        fps     = int(meta.get("fps", 30))
        fw      = config.frame_width
        fh      = config.frame_height
        sub_y   = -fh * 0.38 if pos == "bottom" else 0.0

        self.camera.background_color = "#050B08"
        tmp = Path(tempfile.mkdtemp())

        for i, seg in enumerate(segments):
            # FIX 3: sync au temps absolu (secondes) au lieu de frames sequentielles
            seg_start = float(seg.get("start", seg.get("start_frame", i * 90) / fps))
            seg_end   = float(seg.get("end", seg.get("end_frame", (i+1) * 90) / fps))
            seg_dur   = max(seg_end - seg_start, 0.5)
            hold      = max(seg_dur - spd * 2, 0.15)

            text    = seg.get("text", "")
            lat     = float(seg.get("lat", 0))
            lon     = float(seg.get("lon", 0))
            iso     = seg.get("iso", "")
            brands  = seg.get("brands", [])

            # FIX 3: attendre le bon moment absolu avant de jouer ce segment
            current_time = self.renderer.time
            if seg_start > current_time + 0.05:
                self.wait(seg_start - current_time)

            # -- carte --
            mp = str(tmp / f"map_{i:02d}.png")
            if generate_map(lat, lon, iso, cfill, mp):
                map_mob = ImageMobject(mp)
                map_mob.scale_to_fit_width(fw * 0.92)
                if map_mob.height > fh * 0.55:
                    map_mob.scale_to_fit_height(fh * 0.55)
            else:
                map_mob = Rectangle(
                    width=fw*0.9, height=fh*0.5,
                    fill_color="#1A2E25", fill_opacity=0.9,
                    stroke_color=cfill, stroke_width=2)
            map_mob.move_to(UP * fh * 0.1)

            # -- logo -- FIX 2: scale relatif a fw (pas fh) + visual_scale applique
            logo_mob = None
            logo_height = fw * 0.12 * vs   # relatif a la largeur portrait + visual_scale
            if brands:
                lp = str(tmp / f"logo_{i:02d}.png")
                lurl = brands[0].get("logo", "")
                if lurl and dl_logo(lurl, lp):
                    try:
                        li = ImageMobject(lp)
                        li.scale_to_fit_height(logo_height)
                        bg = RoundedRectangle(
                            corner_radius=0.08,
                            width=li.width + 0.2, height=li.height + 0.15,
                            fill_color="#FFFFFF", fill_opacity=1.0, stroke_width=0)
                        bg.move_to(UP * fh * 0.34)
                        li.move_to(bg.get_center())
                        logo_mob = VGroup(bg, li)
                    except Exception:
                        logo_mob = None
                if logo_mob is None:
                    bname = brands[0].get("name", "").upper()[:12]
                    txt_sz = max(int(14 * vs), 10)
                    bw = min(fw * 0.7, 3.0)
                    bb = RoundedRectangle(corner_radius=0.08, width=bw, height=logo_height + 0.2,
                                           fill_color="#FFFFFF", fill_opacity=1.0, stroke_width=0)
                    bb.move_to(UP * fh * 0.34)
                    bt = Text(bname, font_size=txt_sz, color="#050B08")
                    bt.move_to(bb.get_center())
                    logo_mob = VGroup(bb, bt)

            # -- sous-titre --
            sub = safe_text(text, fsize, fcolor, font)
            sub.move_to([0, sub_y, 0])
            if sub.width > fw * 0.9:
                sub.scale(fw * 0.9 / sub.width)

            # -- in --
            ins = [FadeIn(map_mob, run_time=spd), FadeIn(sub, run_time=spd)]
            if logo_mob: ins.append(FadeIn(logo_mob, run_time=spd))
            self.play(*ins)
            self.wait(hold)

            # -- out --
            outs = [FadeOut(map_mob, run_time=spd*0.7), FadeOut(sub, run_time=spd*0.7)]
            if logo_mob: outs.append(FadeOut(logo_mob, run_time=spd*0.7))
            self.play(*outs)
