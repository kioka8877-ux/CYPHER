#!/usr/bin/env python3
"""CypherScene v5 — Manim 9:16 avec camera zoom, sync word_frame, ISO 2->3."""
import json, tempfile, os
from pathlib import Path

try:
    from manim import config
    config.pixel_width = 1080
    config.pixel_height = 1920
    config.frame_height = 8.0
    config.frame_width = config.frame_height * 1080 / 1920
    from manim import *
except ImportError:
    raise RuntimeError("manim non installe")

# ISO alpha-2 -> alpha-3 mapping (pays du render_spec)
ISO2TO3 = {
    "US":"USA","DE":"DEU","KR":"KOR","FR":"FRA","IT":"ITA","SE":"SWE",
    "CN":"CHN","CA":"CAN","GB":"GBR","AE":"ARE","TW":"TWN","CH":"CHE",
    "NL":"NLD","ES":"ESP","IN":"IND","AU":"AUS","SG":"SGP","FI":"FIN",
    "DK":"DNK","BR":"BRA","JP":"JPN","NO":"NOR","IE":"IRL","IL":"ISR",
    "ZA":"ZAF","MX":"MEX","TH":"THA","MY":"MYS","PH":"PHL","ID":"IDN",
    "SA":"SAU","QA":"QAT","NZ":"NZL","CL":"CHL","AR":"ARG","CO":"COL",
    "EG":"EGY","NG":"NGA","KE":"KEN","PL":"POL","CZ":"CZE","AT":"AUT",
    "BE":"BEL","PT":"PRT","RO":"ROU","HU":"HUN","GR":"GRC","TR":"TUR",
}

def load_spec() -> dict:
    for p in [Path("render_spec.json"), Path("../render_spec.json"),
              Path("render_workspace/render_spec.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("render_spec.json introuvable")


def generate_map(lat, lon, iso2, country_color, opacity, border_color, border_w, out_path, w=810, h=1080):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import geopandas as gpd

        try:
            world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        except Exception:
            world = gpd.read_file("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")

        # Detecter la colonne ISO
        iso_col = None
        for col in ["iso_a3", "ISO_A3", "ADM0_A3", "ISO_A3_EH", "SOV_A3"]:
            if col in world.columns:
                iso_col = col; break

        fig, ax = plt.subplots(figsize=(w/100, h/100), dpi=100)
        fig.patch.set_facecolor("#050B08")
        ax.set_facecolor("#050B08")
        world.plot(ax=ax, color="#1A2E25", edgecolor="#3A5A4A", linewidth=0.3)

        # Convertir ISO 2 -> 3
        iso3 = ISO2TO3.get(iso2.upper(), iso2.upper()) if iso2 else ""
        highlighted = False

        if iso3 and iso_col:
            hi = world[world[iso_col] == iso3]
            if hi.empty and len(iso3) == 2:
                # Essai direct si 2 lettres
                hi = world[world[iso_col].str[:2] == iso3]
            if not hi.empty:
                from matplotlib.colors import to_rgba
                rgba = to_rgba(country_color, alpha=opacity)
                hi.plot(ax=ax, color=rgba, edgecolor=border_color, linewidth=border_w)
                highlighted = True
                b = hi.total_bounds
                cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
                sx = max((b[2]-b[0])*2.2, 50)
                sy = max((b[3]-b[1])*2.2, 35)
                ax.set_xlim(cx-sx/2, cx+sx/2)
                ax.set_ylim(cy-sy/2, cy+sy/2)

        if not highlighted:
            ax.set_xlim(lon-35, lon+35); ax.set_ylim(lat-25, lat+25)

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
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        Path(path).write_bytes(data)
        return len(data) > 800
    except Exception as e:
        print(f"[LOGO] {e}"); return False


def safe_text(txt, sz, col, font):
    for f in [font, "Impact", "DejaVu Sans"]:
        if not f or "," in f: continue
        try:
            return Text(txt, font_size=sz, color=col, font=f)
        except Exception:
            continue
    return Text(txt, font_size=sz, color=col)


class CypherScene(MovingCameraScene):
    def construct(self):
        spec      = load_spec()
        meta      = spec.get("meta", {})
        segments  = spec.get("segments", [])
        display   = spec.get("display", {})
        map_conf  = spec.get("map_config", {})

        raw_font = display.get("font", "DejaVu Sans")
        font     = raw_font.split(",")[0].strip().strip("'").strip('"')
        fcolor   = display.get("font_color", "#FFFFFF")
        fsize    = int(display.get("font_size", 38))
        pos      = display.get("position", "bottom")
        vs       = float(display.get("visual_scale", 0.85))
        anim     = display.get("animation", "ltr")
        spd      = 0.3

        cfill    = map_conf.get("country_fill", "#B30006")
        copacity = float(map_conf.get("country_opacity", 0.45))
        cborder  = map_conf.get("border_color", "#FFFFFF")
        cborderw = float(map_conf.get("border_width", 2))
        fps      = int(meta.get("fps", 30))
        fw       = config.frame_width
        fh       = config.frame_height
        sub_y    = -fh * 0.40 if pos == "bottom" else (fh * 0.40 if pos == "top" else 0.0)

        self.camera.background_color = "#050B08"
        tmp = Path(tempfile.mkdtemp())

        for i, seg in enumerate(segments):
            seg_start = float(seg.get("start", 0))
            seg_end   = float(seg.get("end", seg_start + 3))
            seg_dur   = max(seg_end - seg_start, 0.5)
            zoom_lvl  = float(seg.get("zoom", 5))

            text    = seg.get("text", "")
            lat     = float(seg.get("lat", 0))
            lon     = float(seg.get("lon", 0))
            iso     = seg.get("iso", "")
            brands  = seg.get("brands", [])

            # Sync au temps absolu
            current_time = self.renderer.time
            if seg_start > current_time + 0.05:
                self.wait(seg_start - current_time)

            # -- carte avec highlight pays (ISO 2->3 + couleur render_spec) --
            mp = str(tmp / f"map_{i:02d}.png")
            if generate_map(lat, lon, iso, cfill, copacity, cborder, cborderw, mp):
                map_mob = ImageMobject(mp)
                map_mob.scale_to_fit_width(fw * 0.92)
                if map_mob.height > fh * 0.55:
                    map_mob.scale_to_fit_height(fh * 0.55)
            else:
                map_mob = Rectangle(
                    width=fw*0.9, height=fh*0.5,
                    fill_color="#1A2E25", fill_opacity=0.9,
                    stroke_color=cfill, stroke_width=2)
            map_mob.move_to(UP * fh * 0.05)

            # -- sous-titre --
            sub = safe_text(text, fsize, fcolor, font)
            sub.move_to([0, sub_y, 0])
            if sub.width > fw * 0.92:
                sub.scale(fw * 0.92 / sub.width)

            # -- IN: carte + sous-titre avec animation directionnelle --
            if anim == "ltr":
                map_mob.shift(LEFT * fw)
                sub.shift(LEFT * fw)
                self.play(
                    map_mob.animate.shift(RIGHT * fw),
                    sub.animate.shift(RIGHT * fw),
                    run_time=spd * 1.5
                )
            else:
                self.play(FadeIn(map_mob, run_time=spd), FadeIn(sub, run_time=spd))

            # -- ZOOM camera (zoom_lvl: 4=wide, 7=close) --
            # Normaliser zoom: 4 -> scale 1.0, 7 -> scale 1.4
            cam_scale = 1.0 + (zoom_lvl - 4) * 0.13
            if abs(cam_scale - 1.0) > 0.05:
                self.play(
                    self.camera.frame.animate.scale(1.0 / cam_scale),
                    run_time=seg_dur * 0.3
                )

            # -- LOGOS synchronises au word_frame --
            logo_mobs = []
            for bi, brand in enumerate(brands):
                wf = int(brand.get("word_frame", 0))
                logo_time = wf / fps  # temps absolu
                # Attendre le bon moment
                ct = self.renderer.time
                if logo_time > ct + 0.1:
                    self.wait(logo_time - ct)
                elif logo_time < ct - 2:
                    # Ne pas attendre un temps deja passe
                    pass

                # Creer logo mob
                logo_mob = None
                logo_height = fw * 0.10 * vs
                lp = str(tmp / f"logo_{i:02d}_{bi:02d}.png")
                lurl = brand.get("logo", "")
                if lurl and dl_logo(lurl, lp):
                    try:
                        li = ImageMobject(lp)
                        li.scale_to_fit_height(logo_height)
                        bg = RoundedRectangle(
                            corner_radius=0.08,
                            width=li.width + 0.15, height=li.height + 0.1,
                            fill_color="#FFFFFF", fill_opacity=1.0, stroke_width=0)
                        # Positionner: centrer en haut, decaler pour chaque logo
                        x_pos = (bi - len(brands)/2 + 0.5) * (logo_height + 0.25)
                        bg.move_to([x_pos, fh * 0.34, 0])
                        li.move_to(bg.get_center())
                        logo_mob = VGroup(bg, li)
                    except Exception:
                        logo_mob = None
                if logo_mob is None:
                    bname = brand.get("name", "").upper()[:10]
                    txt_sz = max(int(12 * vs), 8)
                    bw = logo_height * 2.5
                    bb = RoundedRectangle(corner_radius=0.06, width=bw, height=logo_height + 0.12,
                                           fill_color="#FFFFFF", fill_opacity=1.0, stroke_width=0)
                    x_pos = (bi - len(brands)/2 + 0.5) * (bw + 0.1)
                    bb.move_to([x_pos, fh * 0.34, 0])
                    bt = safe_text(bname, txt_sz, "#050B08", font)
                    bt.move_to(bb.get_center())
                    logo_mob = VGroup(bb, bt)

                self.play(FadeIn(logo_mob, shift=UP * 0.15, run_time=0.2))
                logo_mobs.append(logo_mob)

            # Attendre la fin du segment
            ct = self.renderer.time
            remaining = seg_end - ct
            if remaining > 0.1:
                self.wait(remaining * 0.7)

            # -- OUT: tout disparait + reset camera --
            outs = [FadeOut(map_mob, run_time=spd*0.5), FadeOut(sub, run_time=spd*0.5)]
            for lm in logo_mobs:
                outs.append(FadeOut(lm, run_time=spd*0.5))
            if abs(cam_scale - 1.0) > 0.05:
                outs.append(self.camera.frame.animate.scale(cam_scale).set_run_time(spd*0.5))
            self.play(*outs)
