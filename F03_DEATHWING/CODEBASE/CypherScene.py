#!/usr/bin/env python3
"""CypherScene v6 — Carte monde unique + camera mobile + logos geolocalises."""
import json, tempfile, math
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

# ── Projection constants ──
EXTENT = (-180, 180, -60, 85)  # lon_min, lon_max, lat_min, lat_max
MAP_W = 24.0                   # Manim units width for the full map
MAP_H = MAP_W * (EXTENT[3] - EXTENT[2]) / (EXTENT[1] - EXTENT[0])  # ~14.5

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


def geo_to_manim(lon, lat):
    """Convert lon/lat to Manim coordinates on the map."""
    x = (lon - EXTENT[0]) / (EXTENT[1] - EXTENT[0]) * MAP_W - MAP_W / 2
    y = (lat - EXTENT[2]) / (EXTENT[3] - EXTENT[2]) * MAP_H - MAP_H / 2
    return x, y


def load_spec() -> dict:
    for p in [Path("render_spec.json"), Path("../render_spec.json"),
              Path("render_workspace/render_spec.json")]:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("render_spec.json introuvable")


def _get_world():
    import geopandas as gpd
    try:
        return gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    except Exception:
        return gpd.read_file("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")


def _iso_col(world):
    for c in ["iso_a3", "ISO_A3", "ADM0_A3", "ISO_A3_EH"]:
        if c in world.columns:
            return c
    return None


def generate_base_map(out_path, w=4000, h=2400):
    """Render one full world map — cinematic dark ocean + green land."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        world = _get_world()
        fig, ax = plt.subplots(figsize=(w/100, h/100), dpi=100)
        fig.patch.set_facecolor("#0a1628")
        ax.set_facecolor("#0a1628")
        # Land
        world.plot(ax=ax, color="#1a3a2a", edgecolor="#2a5a3a", linewidth=0.4)
        ax.set_xlim(EXTENT[0], EXTENT[1])
        ax.set_ylim(EXTENT[2], EXTENT[3])
        ax.set_axis_off()
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.savefig(out_path, bbox_inches="tight", pad_inches=0, facecolor="#0a1628", dpi=100)
        plt.close(fig)
        return True
    except Exception as e:
        print(f"[MAP-BASE] {e}"); return False


def generate_highlight(iso2, color, opacity, out_path, w=4000, h=2400):
    """Render transparent overlay with just the highlighted country."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import to_rgba
        world = _get_world()
        ic = _iso_col(world)
        iso3 = ISO2TO3.get(iso2.upper(), iso2.upper()) if iso2 else ""
        if not iso3 or not ic:
            return False
        hi = world[world[ic] == iso3]
        if hi.empty:
            return False
        fig, ax = plt.subplots(figsize=(w/100, h/100), dpi=100)
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        rgba = to_rgba(color, alpha=opacity)
        hi.plot(ax=ax, color=rgba, edgecolor="#FFFFFF", linewidth=1.5)
        ax.set_xlim(EXTENT[0], EXTENT[1])
        ax.set_ylim(EXTENT[2], EXTENT[3])
        ax.set_axis_off()
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.savefig(out_path, bbox_inches="tight", pad_inches=0, transparent=True, dpi=100)
        plt.close(fig)
        return Path(out_path).stat().st_size > 500
    except Exception as e:
        print(f"[MAP-HI] {e}"); return False


def get_country_bounds(iso2):
    """Return (min_lon, min_lat, max_lon, max_lat) for scattering logos inside."""
    try:
        world = _get_world()
        ic = _iso_col(world)
        iso3 = ISO2TO3.get(iso2.upper(), iso2.upper())
        hi = world[world[ic] == iso3]
        if not hi.empty:
            return hi.total_bounds  # (minx, miny, maxx, maxy)
    except Exception:
        pass
    return None


def dl_logo(url, path):
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            Path(path).write_bytes(resp.read())
        return Path(path).stat().st_size > 800
    except Exception as e:
        print(f"[LOGO] {e}"); return False


def safe_text(txt, sz, col, font):
    for f in [font, "Impact", "DejaVu Sans"]:
        if not f or "," in f:
            continue
        try:
            return Text(txt, font_size=sz, color=col, font=f)
        except Exception:
            continue
    return Text(txt, font_size=sz, color=col)


def scatter_positions(cx, cy, bounds, n):
    """Generate n positions scattered within country bounds around centroid."""
    if bounds is None or n == 0:
        return [(cx, cy)] * n
    minx, miny, maxx, maxy = bounds
    # Convert bounds to manim
    bx0, by0 = geo_to_manim(minx, miny)
    bx1, by1 = geo_to_manim(maxx, maxy)
    dx = (bx1 - bx0) * 0.3
    dy = (by1 - by0) * 0.3
    positions = []
    # Spiral-ish scatter
    angles = [i * 2.3998 for i in range(n)]  # golden angle
    for i, a in enumerate(angles):
        r = 0.3 + 0.15 * i
        px = cx + math.cos(a) * min(dx, r)
        py = cy + math.sin(a) * min(dy, r)
        # Clamp within bounds
        px = max(bx0 + 0.1, min(bx1 - 0.1, px))
        py = max(by0 + 0.1, min(by1 - 0.1, py))
        positions.append((px, py))
    return positions


class CypherScene(MovingCameraScene):
    def construct(self):
        spec     = load_spec()
        meta     = spec.get("meta", {})
        segments = spec.get("segments", [])
        display  = spec.get("display", {})
        map_conf = spec.get("map_config", {})

        raw_font = display.get("font", "DejaVu Sans")
        font     = raw_font.split(",")[0].strip().strip("'").strip('"')
        fcolor   = display.get("font_color", "#FFFFFF")
        fsize    = max(int(display.get("font_size", 38)), 36)  # floor 36
        pos      = display.get("position", "bottom")
        vs       = float(display.get("visual_scale", 0.85))

        cfill    = map_conf.get("country_fill", "#B30006")
        copacity = float(map_conf.get("country_opacity", 0.45))
        fps      = int(meta.get("fps", 30))

        tmp = Path(tempfile.mkdtemp())

        # ══════════════════════════════════════════════
        # PHASE 1: Pre-render all images
        # ══════════════════════════════════════════════
        print("[CYPHER] Generating base world map...")
        base_path = str(tmp / "base_map.png")
        generate_base_map(base_path)

        print("[CYPHER] Generating country highlights...")
        highlight_paths = {}
        for seg in segments:
            iso = seg.get("iso", "")
            if iso and iso not in highlight_paths:
                hp = str(tmp / f"hi_{iso}.png")
                if generate_highlight(iso, cfill, copacity, hp):
                    highlight_paths[iso] = hp

        # ══════════════════════════════════════════════
        # PHASE 2: Build Manim scene
        # ══════════════════════════════════════════════
        print("[CYPHER] Building scene...")

        # Base map (always visible)
        base_mob = ImageMobject(base_path)
        base_mob.set_width(MAP_W)
        base_mob.move_to(ORIGIN)
        self.add(base_mob)

        # Camera starts showing full world
        self.camera.frame.set_width(MAP_W * 1.05)
        self.camera.frame.move_to(ORIGIN)

        # Intro: hold full map view 1s
        self.wait(0.5)

        for i, seg in enumerate(segments):
            seg_start = float(seg.get("start", 0))
            seg_end   = float(seg.get("end", seg_start + 3))
            zoom_lvl  = float(seg.get("zoom", 5))
            text      = seg.get("text", "")
            lat       = float(seg.get("lat", 0))
            lon       = float(seg.get("lon", 0))
            iso       = seg.get("iso", "")
            brands    = seg.get("brands", [])

            # Sync to absolute time
            ct = self.renderer.time
            if seg_start > ct + 0.05:
                self.wait(seg_start - ct)

            # Target position in Manim coords
            cx, cy = geo_to_manim(lon, lat)

            # Zoom width: zoom 4=wide(8), 5=medium(6), 6=close(4.5), 7=tight(3.5)
            zoom_width = max(10.0 - zoom_lvl * 1.0, 3.0)

            # ── Camera travel to country ──
            self.play(
                self.camera.frame.animate.move_to([cx, cy, 0]).set(width=zoom_width),
                run_time=0.8, rate_func=smooth
            )

            # ── Country highlight (illuminate) ──
            hi_mob = None
            if iso in highlight_paths:
                hi_mob = ImageMobject(highlight_paths[iso])
                hi_mob.set_width(MAP_W)  # same scale as base
                hi_mob.move_to(ORIGIN)   # same position as base
                self.play(FadeIn(hi_mob, run_time=0.3))

            # ── Subtitle (anchored to camera viewport bottom) ──
            sub = safe_text(text, fsize, fcolor, font)
            cam_center = self.camera.frame.get_center()
            cam_h = self.camera.frame.height
            sub_pos = cam_center + DOWN * cam_h * 0.42
            sub.move_to(sub_pos)
            # Scale subtitle to fit camera viewport width
            cam_w = self.camera.frame.width
            if sub.width > cam_w * 0.92:
                sub.scale(cam_w * 0.92 / sub.width)
            self.play(FadeIn(sub, run_time=0.25))

            # ── Logos: one by one at word_frame, inside country ──
            bounds = get_country_bounds(iso) if iso else None
            positions = scatter_positions(cx, cy, bounds, len(brands))
            logo_mobs = []

            for bi, brand in enumerate(brands):
                wf = int(brand.get("word_frame", 0))
                logo_time = wf / fps
                # Wait for word_frame
                ct2 = self.renderer.time
                if logo_time > ct2 + 0.08:
                    self.wait(logo_time - ct2)

                # Build logo (SQUARE)
                logo_mob = None
                logo_sz = zoom_width * 0.08 * vs  # relative to current zoom
                lp = str(tmp / f"logo_{i:02d}_{bi:02d}.png")
                lurl = brand.get("logo", "")
                if lurl and dl_logo(lurl, lp):
                    try:
                        li = ImageMobject(lp)
                        li.scale_to_fit_height(logo_sz)
                        if li.width > logo_sz:
                            li.scale_to_fit_width(logo_sz)
                        # Square white background
                        side = max(li.width, li.height) + logo_sz * 0.15
                        bg = Square(side_length=side,
                                    fill_color="#FFFFFF", fill_opacity=1.0,
                                    stroke_width=0)
                        bg.round_corners(radius=side * 0.1)
                        px, py = positions[bi]
                        bg.move_to([px, py, 0])
                        li.move_to(bg.get_center())
                        logo_mob = VGroup(bg, li)
                    except Exception:
                        logo_mob = None

                if logo_mob is None:
                    bname = brand.get("name", "").upper()[:10]
                    side = logo_sz * 1.2
                    bg = Square(side_length=side,
                                fill_color="#FFFFFF", fill_opacity=1.0,
                                stroke_width=0)
                    bg.round_corners(radius=side * 0.1)
                    px, py = positions[bi]
                    bg.move_to([px, py, 0])
                    bt = safe_text(bname, max(int(10 * vs), 7), "#050B08", font)
                    bt.move_to(bg.get_center())
                    if bt.width > side * 0.85:
                        bt.scale(side * 0.85 / bt.width)
                    logo_mob = VGroup(bg, bt)

                # Camera follows logo slightly
                px, py = positions[bi]
                self.play(
                    FadeIn(logo_mob, shift=UP * 0.08, run_time=0.2),
                    self.camera.frame.animate.move_to([px, py, 0]),
                    run_time=0.25
                )
                # Update subtitle position (follows camera)
                new_sub_pos = self.camera.frame.get_center() + DOWN * cam_h * 0.42
                sub.move_to(new_sub_pos)
                logo_mobs.append(logo_mob)

            # ── Hold remaining time ──
            ct3 = self.renderer.time
            remaining = seg_end - ct3
            if remaining > 0.2:
                self.wait(remaining * 0.6)

            # ── Cleanup: fade out highlight + logos + subtitle ──
            fade_outs = [FadeOut(sub, run_time=0.3)]
            if hi_mob:
                fade_outs.append(FadeOut(hi_mob, run_time=0.3))
            for lm in logo_mobs:
                fade_outs.append(FadeOut(lm, run_time=0.3))
            self.play(*fade_outs)
