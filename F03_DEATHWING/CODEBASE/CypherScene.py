#!/usr/bin/env python3
"""CypherScene v7.1 — Carte satellite + camera fluide + gros logos dans le pays."""
import json, tempfile, math, os, time
from pathlib import Path

try:
    from manim import config
    config.pixel_width = 1080
    config.pixel_height = 1920
    config.frame_height = 8.0
    config.frame_width = 4.5
    config.background_color = "#0a0a12"
except Exception:
    pass

from manim import (
    Scene, MovingCameraScene, ImageMobject, Text, Square, Group,
    FadeIn, FadeOut, ORIGIN, UP, DOWN, LEFT, RIGHT,
    rate_functions, AnimationGroup
)

# ═══════════════════════════════════════════
# GLOBALS — must match camera_plan generator
# ═══════════════════════════════════════════
EXTENT = (-180, 180, -60, 85)
MAP_W = 24.0
MAP_H = MAP_W * (EXTENT[3] - EXTENT[2]) / (EXTENT[1] - EXTENT[0]) * 1.2

ISO2TO3 = {
    "US":"USA","DE":"DEU","JP":"JPN","KR":"KOR","FR":"FRA","IT":"ITA",
    "SE":"SWE","CN":"CHN","CA":"CAN","GB":"GBR","AE":"ARE","TW":"TWN",
    "CH":"CHE","NL":"NLD","ES":"ESP","IN":"IND","AU":"AUS","SG":"SGP",
    "FI":"FIN","DK":"DNK","BR":"BRA","MX":"MEX","SA":"SAU","NO":"NOR",
    "TH":"THA","ID":"IDN","MY":"MYS","PH":"PHL","VN":"VNM","ZA":"ZAF",
    "NG":"NGA","EG":"EGY","IL":"ISR","TR":"TUR",
}


def geo_to_manim(lon, lat):
    """Convert lon/lat to Manim coordinates on the map."""
    x = (lon - EXTENT[0]) / (EXTENT[1] - EXTENT[0]) * MAP_W - MAP_W / 2
    y = (lat - EXTENT[2]) / (EXTENT[3] - EXTENT[2]) * MAP_H - MAP_H / 2
    return x, y


def dl_logo(url, dest, retries=3):
    """Download a logo with retries. Returns True on success."""
    import requests
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=12)
            if r.status_code == 200 and len(r.content) > 500:
                Path(dest).write_bytes(r.content)
                return True
        except Exception as e:
            print(f"[LOGO] attempt {attempt+1}/{retries} failed for {url}: {e}")
            time.sleep(1)
    return False


def get_country_bounds(iso):
    """Get country bounds from shapefile (minx,miny,maxx,maxy) in manim coords."""
    try:
        import geopandas as gpd
        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        iso2 = iso.upper()
        iso3 = ISO2TO3.get(iso2, iso2)
        # Try iso_a3 first, then name matching
        for col in ["iso_a3", "iso_a2"]:
            if col in world.columns:
                hi = world[world[col] == (iso3 if col == "iso_a3" else iso2)]
                if not hi.empty:
                    b = hi.total_bounds  # minx, miny, maxx, maxy
                    x1, y1 = geo_to_manim(b[0], b[1])
                    x2, y2 = geo_to_manim(b[2], b[3])
                    return (x1, y1, x2, y2)
    except Exception as e:
        print(f"[BOUNDS] failed for {iso}: {e}")
    return None


def generate_base_map(out_path):
    """Generate satellite world map using contextily Esri tiles."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import geopandas as gpd
    import contextily as ctx

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    world = world.to_crs(epsg=4326)

    fig, ax = plt.subplots(1, 1, figsize=(24, 14), dpi=150)
    ax.set_xlim(EXTENT[0], EXTENT[1])
    ax.set_ylim(EXTENT[2], EXTENT[3])

    # Satellite basemap — Esri World Imagery
    try:
        ctx.add_basemap(ax, crs="EPSG:4326",
                        source=ctx.providers.Esri.WorldImagery,
                        zoom=3, attribution="")
    except Exception as e:
        print(f"[MAP] Esri tiles failed, fallback to CartoDB: {e}")
        try:
            ctx.add_basemap(ax, crs="EPSG:4326",
                            source=ctx.providers.CartoDB.DarkMatter,
                            zoom=3, attribution="")
        except:
            world.plot(ax=ax, color="#1a1a2e", edgecolor="#333", linewidth=0.3)

    ax.set_axis_off()
    fig.patch.set_facecolor("#0a0a12")
    ax.patch.set_facecolor("#0a0a12")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0,
                facecolor="#0a0a12")
    plt.close(fig)
    print(f"[CYPHER] Base map saved: {out_path}")


def generate_highlight(iso, out_path, fill_color="#baa0da", opacity=0.55):
    """Generate a country highlight overlay as transparent PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import geopandas as gpd
    from matplotlib.colors import to_rgba

    world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    iso3 = ISO2TO3.get(iso.upper(), iso.upper())

    hi = None
    for col in ["iso_a3"]:
        if col in world.columns:
            hi = world[world[col] == iso3]
            if not hi.empty:
                break
    if hi is None or hi.empty:
        print(f"[HIGHLIGHT] no shape for {iso}")
        return False

    fig, ax = plt.subplots(1, 1, figsize=(24, 14), dpi=150)
    ax.set_xlim(EXTENT[0], EXTENT[1])
    ax.set_ylim(EXTENT[2], EXTENT[3])

    rgba = to_rgba(fill_color, alpha=opacity)
    hi.plot(ax=ax, color=rgba, edgecolor="#FFFFFF", linewidth=1.5)

    ax.set_axis_off()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0,
                transparent=True)
    plt.close(fig)
    return True


def load_spec():
    """Load render_spec — prefer v2 (split) if present."""
    for name in ["render_spec_v2.json", "render_spec.json"]:
        p = Path(name)
        if p.exists():
            print(f"[CYPHER] Using {name}")
            return json.loads(p.read_text())
    raise FileNotFoundError("No render_spec found")


class CypherScene(MovingCameraScene):
    def construct(self):
        spec     = load_spec()
        meta     = spec.get("meta", {})
        segments = spec.get("segments", [])
        display  = spec.get("display", {})
        map_conf = spec.get("map_config", {})

        raw_font = display.get("font", "DejaVu Sans")
        font     = raw_font if raw_font else "DejaVu Sans"
        sub_size = max(int(display.get("subtitle_size", 42)), 36)
        vs       = float(display.get("visual_scale", 0.85))

        cfill    = map_conf.get("country_fill", "#baa0da")
        copacity = float(map_conf.get("country_opacity", 0.55))
        fps      = int(meta.get("fps", 30))

        # ── v7.1 chunked rendering: segment range + camera plan ──
        _last    = len(segments) - 1
        SEG_FROM = max(0, min(int(os.environ.get("CYP_SEG_FROM", "0")), max(_last, 0)))
        SEG_TO   = max(SEG_FROM, min(int(os.environ.get("CYP_SEG_TO", str(_last))), max(_last, 0)))
        _all_seg = segments
        T0       = float(_all_seg[SEG_FROM].get("start", 0)) if _all_seg else 0.0
        segments = _all_seg[SEG_FROM:SEG_TO + 1]
        _cam_entry = None
        if SEG_FROM > 0 and Path("camera_plan.json").exists():
            _plan = json.loads(Path("camera_plan.json").read_text())
            if SEG_FROM < len(_plan):
                _cam_entry = _plan[SEG_FROM]
        print(f"[CYPHER v7.1] segments {SEG_FROM}..{SEG_TO} T0={T0:.2f}s")

        tmp = Path(tempfile.mkdtemp())

        # ══════════════════════════════════════════════
        # PHASE 1: Pre-render images
        # ══════════════════════════════════════════════
        print("[CYPHER] Generating satellite world map (Esri)...")
        base_path = str(tmp / "base_map.png")
        generate_base_map(base_path)

        highlight_paths = {}
        for seg in _all_seg:
            iso = seg.get("iso", "")
            if iso and iso not in highlight_paths:
                hp = str(tmp / f"hi_{iso}.png")
                if generate_highlight(iso, hp, cfill, copacity):
                    highlight_paths[iso] = hp

        # Pre-download ALL logos
        logo_cache = {}
        for seg in segments:
            for bi, brand in enumerate(seg.get("brands", [])):
                lurl = brand.get("logo", "")
                lp = str(tmp / f"logo_{seg.get('id',0):02d}_{bi:02d}.png")
                if lurl and dl_logo(lurl, lp):
                    logo_cache[(seg.get("id",0), bi)] = lp
                    print(f"[LOGO] ✅ {brand.get('name','?')}")
                else:
                    print(f"[LOGO] ❌ {brand.get('name','?')} — will use text fallback")

        # ══════════════════════════════════════════════
        # PHASE 2: Build scene
        # ══════════════════════════════════════════════
        base_mob = ImageMobject(base_path)
        base_mob.set_width(MAP_W)
        base_mob.move_to(ORIGIN)
        self.add(base_mob)

        # Camera start: world view (first chunk) OR resume (camera plan)
        if _cam_entry is not None:
            self.camera.frame.set_width(float(_cam_entry.get("width", MAP_W * 1.05)))
            _c = _cam_entry.get("center", [0, 0])
            self.camera.frame.move_to([float(_c[0]), float(_c[1]), 0])
        else:
            self.camera.frame.set_width(MAP_W * 1.05)
            self.camera.frame.move_to(ORIGIN)
            self.wait(0.8)  # intro: hold full map view

        for i, seg in enumerate(segments):
            seg_start = float(seg.get("start", 0)) - T0
            seg_end   = float(seg.get("end", seg_start + 3)) - T0
            zoom_lvl  = float(seg.get("zoom", 5))
            text      = seg.get("text", "")
            lat       = float(seg.get("lat", 0))
            lon       = float(seg.get("lon", 0))
            iso       = seg.get("iso", "")
            brands    = seg.get("brands", [])

            cx, cy = geo_to_manim(lon, lat)

            # ── Sync to audio timeline ──
            ct = self.renderer.time
            wait_t = seg_start - ct
            if wait_t > 0.05:
                self.wait(wait_t)

            # ══════════════════════════════════════════
            # CAMERA TRAVEL — fluid "human-like" movement
            # ══════════════════════════════════════════
            zoom_width = max(10.0 - zoom_lvl * 1.0, 3.0)

            self.play(
                self.camera.frame.animate.move_to([cx, cy, 0]).set(width=zoom_width),
                run_time=1.4 if i > 0 else 1.8,
                rate_func=rate_functions.ease_in_out_cubic
            )
            # Micro-settle: tiny overshoot correction for natural feel
            self.play(
                self.camera.frame.animate.set(width=zoom_width * 0.98),
                run_time=0.15,
                rate_func=rate_functions.ease_out_sine
            )
            self.play(
                self.camera.frame.animate.set(width=zoom_width),
                run_time=0.1,
                rate_func=rate_functions.ease_in_sine
            )

            # ── Country highlight (illuminate ~0.3s) ──
            hi_mob = None
            if iso in highlight_paths:
                hi_mob = ImageMobject(highlight_paths[iso])
                hi_mob.set_width(MAP_W)
                hi_mob.move_to(ORIGIN)
                self.play(FadeIn(hi_mob, run_time=0.3))

            # ── Subtitle ──
            cam_center = self.camera.frame.get_center()
            cam_h = self.camera.frame.height
            sub = Text(text, font=font, font_size=sub_size,
                       color="#FFFFFF", weight="BOLD")
            sub.set_max_width(self.camera.frame.width * 0.88)
            sub.move_to(cam_center + DOWN * cam_h * 0.42)
            self.play(FadeIn(sub, run_time=0.25))

            # ══════════════════════════════════════════
            # LOGOS — big, inside country, camera follows
            # ══════════════════════════════════════════
            logo_mobs = []

            # Get country bounds for placement
            bounds = get_country_bounds(iso) if iso else None
            n_brands = len(brands)

            for bi, brand in enumerate(brands):
                bname = brand.get("name", "").upper()[:12]
                wf = brand.get("word_frame", 0)
                logo_time = wf / fps - T0

                # Wait for logo timing
                ct2 = self.renderer.time
                logo_wait = logo_time - ct2
                if logo_wait > 0.1:
                    self.wait(min(logo_wait, 2.0))

                # Logo size: BIG relative to zoom (like target screenshot)
                logo_sz = zoom_width * 0.30

                # Position: scatter inside country bounds around center
                if bounds and n_brands > 0:
                    bx1, by1, bx2, by2 = bounds
                    bcx = (bx1 + bx2) / 2
                    bcy = (by1 + by2) / 2
                    bw = abs(bx2 - bx1) * 0.35
                    bh = abs(by2 - by1) * 0.35
                    # Distribute brands evenly within bounds
                    if n_brands == 1:
                        px, py = bcx, bcy
                    elif n_brands == 2:
                        off = [-0.3, 0.3]
                        px = bcx + bw * off[bi % 2]
                        py = bcy + bh * off[(bi + 1) % 2]
                    else:
                        angle = (2 * math.pi * bi) / n_brands - math.pi / 2
                        radius = min(bw, bh) * 0.5
                        px = bcx + math.cos(angle) * radius
                        py = bcy + math.sin(angle) * radius
                else:
                    px, py = cx, cy

                # Try to use downloaded logo image
                logo_key = (seg.get("id", 0), bi)
                logo_mob = None

                if logo_key in logo_cache:
                    try:
                        li = ImageMobject(logo_cache[logo_key])
                        li.set_height(logo_sz)
                        # White background card
                        side = max(li.width, li.height) * 1.2
                        bg = Square(side_length=side,
                                    fill_color="#FFFFFF", fill_opacity=0.95,
                                    stroke_width=0)
                        bg.move_to([px, py, 0])
                        li.move_to(bg.get_center())
                        logo_mob = Group(bg, li)
                    except Exception as e:
                        print(f"[LOGO] render failed {bname}: {e}")

                # Fallback: big text label
                if logo_mob is None:
                    txt = Text(bname, font=font, font_size=52,
                               color="#FFFFFF", weight="BOLD")
                    txt.set_max_width(zoom_width * 0.6)
                    txt.move_to([px, py, 0])
                    logo_mob = txt

                # Animate: fade in logo
                self.play(FadeIn(logo_mob, run_time=0.35),
                          rate_func=rate_functions.ease_out_sine)
                logo_mobs.append(logo_mob)

                # Camera FOLLOWS the logo (zoom in slightly)
                self.play(
                    self.camera.frame.animate
                        .move_to([px, py, 0])
                        .set(width=zoom_width * 0.82),
                    run_time=0.45,
                    rate_func=rate_functions.ease_in_out_sine
                )

                # Update subtitle position to follow camera
                new_sub_pos = self.camera.frame.get_center() + DOWN * self.camera.frame.height * 0.42
                sub.move_to(new_sub_pos)

                # Brief hold on logo
                self.wait(0.25)

                # Camera pulls back slightly before next logo
                if bi < n_brands - 1:
                    self.play(
                        self.camera.frame.animate.set(width=zoom_width * 0.95),
                        run_time=0.2,
                        rate_func=rate_functions.ease_in_out_sine
                    )

            # ── Wait for segment end ──
            ct3 = self.renderer.time
            remaining = seg_end - ct3
            if remaining > 0.2:
                self.wait(remaining * 0.6)

            # ── Cleanup: fade out highlight + logos + sub ──
            fade_outs = [FadeOut(sub, run_time=0.3)]
            if hi_mob:
                fade_outs.append(FadeOut(hi_mob, run_time=0.3))
            for lm in logo_mobs:
                fade_outs.append(FadeOut(lm, run_time=0.3))
            self.play(*fade_outs)

            # Camera pulls back to mid-range before next country
            if i < len(segments) - 1:
                self.play(
                    self.camera.frame.animate.set(width=zoom_width * 1.3),
                    run_time=0.4,
                    rate_func=rate_functions.ease_in_out_sine
                )
