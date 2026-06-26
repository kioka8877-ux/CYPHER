#!/usr/bin/env python3
"""CypherScene v7.2 — Satellite + logos from release + word-by-word subs + fluid camera."""
import json, tempfile, math, os, time, zipfile, io
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
    Rectangle, VGroup,
    FadeIn, FadeOut, ORIGIN, UP, DOWN, LEFT, RIGHT,
    rate_functions
)

# ═══════════════════════════════════════════
# GLOBALS
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

# ═══════════════════════════════════════════
# Natural Earth (GeoPandas 1.0+ compat)
# ═══════════════════════════════════════════
_NE_CACHE = None
def _get_world():
    global _NE_CACHE
    if _NE_CACHE is not None:
        return _NE_CACHE
    import geopandas as gpd
    cache_dir = Path(tempfile.gettempdir()) / "ne_lowres"
    shp = cache_dir / "ne_110m_admin_0_countries.shp"
    if not shp.exists():
        import requests
        cache_dir.mkdir(parents=True, exist_ok=True)
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        print("[CYPHER] Downloading Natural Earth shapefile...")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            zf.extractall(cache_dir)
    _NE_CACHE = gpd.read_file(shp)
    print(f"[CYPHER] NE columns: {list(_NE_CACHE.columns[:15])}")
    return _NE_CACHE


def geo_to_manim(lon, lat):
    x = (lon - EXTENT[0]) / (EXTENT[1] - EXTENT[0]) * MAP_W - MAP_W / 2
    y = (lat - EXTENT[2]) / (EXTENT[3] - EXTENT[2]) * MAP_H - MAP_H / 2
    return x, y


def _find_country(world, iso2):
    """Find country in shapefile trying multiple column names."""
    iso3 = ISO2TO3.get(iso2.upper(), iso2.upper())
    for col in ["ISO_A3", "iso_a3", "ADM0_A3", "ISO_A3_EH"]:
        if col in world.columns:
            hi = world[world[col] == iso3]
            if not hi.empty:
                return hi
    # Try ISO2
    for col in ["ISO_A2", "iso_a2"]:
        if col in world.columns:
            hi = world[world[col] == iso2.upper()]
            if not hi.empty:
                return hi
    return None


def get_country_bounds_manim(iso):
    """Get country bounds in manim coords: (x1,y1,x2,y2)."""
    try:
        world = _get_world()
        hi = _find_country(world, iso)
        if hi is not None:
            b = hi.total_bounds  # minx, miny, maxx, maxy (lon/lat)
            x1, y1 = geo_to_manim(b[0], b[1])
            x2, y2 = geo_to_manim(b[2], b[3])
            return (x1, y1, x2, y2)
    except Exception as e:
        print(f"[BOUNDS] {iso}: {e}")
    return None


def generate_base_map(out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import contextily as ctx

    fig, ax = plt.subplots(1, 1, figsize=(24, 14), dpi=150)
    ax.set_xlim(EXTENT[0], EXTENT[1])
    ax.set_ylim(EXTENT[2], EXTENT[3])
    try:
        ctx.add_basemap(ax, crs="EPSG:4326",
                        source="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                        zoom=3, attribution="")
    except Exception as e:
        print(f"[MAP] Esri fail: {e}, fallback dark")
        try:
            ctx.add_basemap(ax, crs="EPSG:4326",
                            source="https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
                            zoom=3, attribution="")
        except:
            world = _get_world()
            world.plot(ax=ax, color="#1a1a2e", edgecolor="#333", linewidth=0.3)
    ax.set_axis_off()
    fig.patch.set_facecolor("#0a0a12")
    ax.patch.set_facecolor("#0a0a12")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0, facecolor="#0a0a12")
    plt.close(fig)


def generate_highlight(iso, out_path, fill_color="#baa0da", opacity=0.55):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba

    world = _get_world()
    hi = _find_country(world, iso)
    if hi is None:
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
    fig.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close(fig)
    return True


def load_spec():
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

        raw_font = display.get("font", "DejaVu Sans") or "DejaVu Sans"
        vs       = float(display.get("visual_scale", 0.85))
        cfill    = map_conf.get("country_fill", "#baa0da")
        copacity = float(map_conf.get("country_opacity", 0.55))
        fps      = int(meta.get("fps", 30))

        # ── v7.2 chunk range ──
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
        print(f"[CYPHER v7.2] segs {SEG_FROM}..{SEG_TO} T0={T0:.2f}s")

        # ── Logo directory (pre-downloaded from release) ──
        logo_dir = Path("logos")
        print(f"[CYPHER] Logo dir exists: {logo_dir.exists()}, files: {list(logo_dir.glob('*.png')) if logo_dir.exists() else 'N/A'}")

        wrk = Path(tempfile.mkdtemp())

        # ══════════ PHASE 1: Pre-render maps ══════════
        print("[CYPHER] Generating satellite world map...")
        base_path = str(wrk / "base_map.png")
        generate_base_map(base_path)

        highlight_paths = {}
        for seg in _all_seg:
            iso = seg.get("iso", "")
            if iso and iso not in highlight_paths:
                hp = str(wrk / f"hi_{iso}.png")
                if generate_highlight(iso, hp, cfill, copacity):
                    highlight_paths[iso] = hp
                    print(f"[HIGHLIGHT] ✅ {iso}")
                else:
                    print(f"[HIGHLIGHT] ❌ {iso}")

        # ══════════ PHASE 2: Build scene ══════════
        base_mob = ImageMobject(base_path)
        base_mob.set_width(MAP_W)
        base_mob.move_to(ORIGIN)
        self.add(base_mob)

        # Camera start
        if _cam_entry is not None:
            self.camera.frame.set_width(float(_cam_entry.get("width", MAP_W * 1.05)))
            _c = _cam_entry.get("center", [0, 0])
            self.camera.frame.move_to([float(_c[0]), float(_c[1]), 0])
        else:
            self.camera.frame.set_width(MAP_W * 1.05)
            self.camera.frame.move_to(ORIGIN)
            self.wait(0.8)

        for i, seg in enumerate(segments):
            seg_start = float(seg.get("start", 0)) - T0
            seg_end   = float(seg.get("end", seg_start + 3)) - T0
            zoom_lvl  = float(seg.get("zoom", 5))
            text      = seg.get("text", "")
            lat       = float(seg.get("lat", 0))
            lon       = float(seg.get("lon", 0))
            iso       = seg.get("iso", "")
            brands    = seg.get("brands", [])
            cx, cy    = geo_to_manim(lon, lat)

            # Sync to audio
            ct = self.renderer.time
            wait_t = seg_start - ct
            if wait_t > 0.05:
                self.wait(wait_t)

            # ══════════ CAMERA → COUNTRY (fluid) ══════════
            zoom_width = max(8.0 - zoom_lvl * 0.8, 2.5)

            self.play(
                self.camera.frame.animate.move_to([cx, cy, 0]).set(width=zoom_width),
                run_time=1.4 if i > 0 else 2.0,
                rate_func=rate_functions.ease_in_out_cubic
            )

            # ── Country highlight ──
            hi_mob = None
            if iso in highlight_paths:
                hi_mob = ImageMobject(highlight_paths[iso])
                hi_mob.set_width(MAP_W)
                hi_mob.move_to(ORIGIN)
                self.play(FadeIn(hi_mob, run_time=0.3))

            # ══════════ LOGOS — big, scattered, camera follows ══════════
            logo_mobs = []
            bounds = get_country_bounds_manim(iso) if iso else None
            n_brands = len(brands)

            # Pre-compute scattered positions
            positions = []
            if bounds and n_brands > 0:
                bx1, by1, bx2, by2 = bounds
                bcx, bcy = (bx1+bx2)/2, (by1+by2)/2
                bw, bh = abs(bx2-bx1), abs(by2-by1)
                for bi in range(n_brands):
                    if n_brands == 1:
                        positions.append((bcx, bcy))
                    elif n_brands == 2:
                        offx = [-0.25, 0.25]
                        offy = [0.15, -0.15]
                        positions.append((bcx + bw*offx[bi], bcy + bh*offy[bi]))
                    else:
                        angle = (2*math.pi*bi)/n_brands - math.pi/2
                        r = min(bw, bh) * 0.3
                        positions.append((bcx + math.cos(angle)*r, bcy + math.sin(angle)*r))
            else:
                for bi in range(n_brands):
                    offset = 0.3 * (bi - (n_brands-1)/2)
                    positions.append((cx + offset, cy + offset * 0.5))

            for bi, brand in enumerate(brands):
                bname = brand.get("name", "").upper()[:12]
                domain = brand.get("domain", "")
                wf = brand.get("word_frame", 0)
                logo_time = wf / fps - T0

                # Wait for logo timing
                ct2 = self.renderer.time
                logo_wait = logo_time - ct2
                if logo_wait > 0.1:
                    self.wait(min(logo_wait, 2.5))

                px, py = positions[bi]
                logo_sz = zoom_width * 0.28

                # Try to load logo from pre-downloaded dir
                logo_mob = None
                safe_domain = domain.replace("/", "_")
                logo_file = logo_dir / f"{safe_domain}.png"
                if logo_file.exists() and logo_file.stat().st_size > 500:
                    try:
                        li = ImageMobject(str(logo_file))
                        li.set_height(logo_sz)
                        side = max(li.width, li.height) * 1.25
                        bg = Square(side_length=side,
                                    fill_color="#FFFFFF", fill_opacity=0.95,
                                    stroke_width=0)
                        bg.move_to([px, py, 0])
                        li.move_to(bg.get_center())
                        logo_mob = Group(bg, li)
                        print(f"[LOGO] ✅ {bname} from {logo_file.name}")
                    except Exception as e:
                        print(f"[LOGO] render fail {bname}: {e}")

                # Fallback: styled text
                if logo_mob is None:
                    txt = Text(bname, font=raw_font, font_size=48,
                               color="#FFFFFF", weight="BOLD")
                    txt.set_max_width(zoom_width * 0.5)
                    # Dark background behind text
                    bg = Rectangle(
                        width=txt.width * 1.3, height=txt.height * 1.8,
                        fill_color="#000000", fill_opacity=0.7,
                        stroke_width=0)
                    bg.move_to([px, py, 0])
                    txt.move_to(bg.get_center())
                    logo_mob = Group(bg, txt)
                    print(f"[LOGO] ⚠️ {bname} text fallback")

                # Fade in logo
                self.play(FadeIn(logo_mob, run_time=0.35),
                          rate_func=rate_functions.ease_out_sine)
                logo_mobs.append(logo_mob)

                # Camera FOLLOWS logo (zoom in closer)
                self.play(
                    self.camera.frame.animate
                        .move_to([px, py, 0])
                        .set(width=zoom_width * 0.65),
                    run_time=0.5,
                    rate_func=rate_functions.ease_in_out_sine
                )
                self.wait(0.2)

                # Camera pulls back slightly before next logo
                if bi < n_brands - 1:
                    self.play(
                        self.camera.frame.animate.set(width=zoom_width * 0.9),
                        run_time=0.25,
                        rate_func=rate_functions.ease_in_out_sine
                    )

            # ══════════ SUBTITLE — word by word ══════════
            words = text.split() if text else []
            sub_mobs = []
            cam_center = self.camera.frame.get_center()
            cam_w = self.camera.frame.width

            # Build words one by one
            line_x = cam_center[0] - cam_w * 0.4
            line_y = cam_center[1] - self.camera.frame.height * 0.42
            word_spacing = 0

            for wi, word in enumerate(words):
                w_mob = Text(word + " ", font=raw_font, font_size=28,
                             color="#FFFFFF", weight="BOLD")
                if word_spacing + w_mob.width > cam_w * 0.85:
                    # New line
                    line_y -= 0.35
                    word_spacing = 0
                w_mob.move_to([line_x + word_spacing + w_mob.width/2, line_y, 0])
                word_spacing += w_mob.width
                self.play(FadeIn(w_mob, run_time=0.08),
                          rate_func=rate_functions.ease_out_sine)
                sub_mobs.append(w_mob)

            # ── Wait for segment end ──
            ct3 = self.renderer.time
            remaining = seg_end - ct3
            if remaining > 0.15:
                self.wait(remaining * 0.5)

            # ── Cleanup ──
            fade_outs = []
            if hi_mob:
                fade_outs.append(FadeOut(hi_mob, run_time=0.3))
            for lm in logo_mobs:
                fade_outs.append(FadeOut(lm, run_time=0.3))
            for sm in sub_mobs:
                fade_outs.append(FadeOut(sm, run_time=0.2))
            if fade_outs:
                self.play(*fade_outs)

            # Pull back before next country
            if i < len(segments) - 1:
                self.play(
                    self.camera.frame.animate.set(width=zoom_width * 1.3),
                    run_time=0.4,
                    rate_func=rate_functions.ease_in_out_sine
                )
