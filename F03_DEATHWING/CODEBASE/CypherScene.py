#!/usr/bin/env python3
"""CypherScene v7.3 — Country fills 87% screen + logos inside + highlight fades on first logo."""
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
    iso3 = ISO2TO3.get(iso2.upper(), iso2.upper())
    for col in ["ISO_A3", "iso_a3", "ADM0_A3", "ISO_A3_EH"]:
        if col in world.columns:
            hi = world[world[col] == iso3]
            if not hi.empty:
                return hi
    for col in ["ISO_A2", "iso_a2"]:
        if col in world.columns:
            hi = world[world[col] == iso2.upper()]
            if not hi.empty:
                return hi
    return None


def get_country_bounds_manim(iso):
    try:
        world = _get_world()
        hi = _find_country(world, iso)
        if hi is not None:
            b = hi.total_bounds
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
        print(f"[MAP] Esri fail: {e}")
        try:
            ctx.add_basemap(ax, crs="EPSG:4326",
                            source="https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
                            zoom=3, attribution="")
        except:
            _get_world().plot(ax=ax, color="#1a1a2e", edgecolor="#333", linewidth=0.3)
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
        cfill    = map_conf.get("country_fill", "#baa0da")
        copacity = float(map_conf.get("country_opacity", 0.55))
        fps      = int(meta.get("fps", 30))

        # ── v7.3 chunk range ──
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
        print(f"[CYPHER v7.3] segs {SEG_FROM}..{SEG_TO} T0={T0:.2f}s")

        logo_dir = Path("logos")
        wrk = Path(tempfile.mkdtemp())

        # ══════════ PHASE 1: Pre-render ══════════
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

        # ══════════ PHASE 2: Scene ══════════
        base_mob = ImageMobject(base_path)
        base_mob.set_width(MAP_W)
        base_mob.move_to(ORIGIN)
        self.add(base_mob)

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

            # ══════════ ZOOM = COUNTRY FILLS 87% OF SCREEN ══════════
            bounds = get_country_bounds_manim(iso) if iso else None
            if bounds:
                bx1, by1, bx2, by2 = bounds
                country_w = abs(bx2 - bx1)
                country_h = abs(by2 - by1)
                bcx = (bx1 + bx2) / 2
                bcy = (by1 + by2) / 2
                # 9:16 aspect ratio: frame_width/frame_height = 4.5/8.0
                aspect = 4.5 / 8.0
                # Fit country to 87% of screen (whichever dimension is limiting)
                zoom_by_w = country_w / 0.87
                zoom_by_h = (country_h / 0.87) * aspect
                zoom_width = max(zoom_by_w, zoom_by_h, 1.5)  # minimum 1.5
                # Center on country centroid (not lat/lon from spec)
                cx, cy = bcx, bcy
                print(f"[CAM] {iso}: bounds w={country_w:.2f} h={country_h:.2f} -> zoom_width={zoom_width:.2f}")
            else:
                zoom_width = 4.0  # fallback

            # ── Camera travel to country ──
            self.play(
                self.camera.frame.animate.move_to([cx, cy, 0]).set(width=zoom_width),
                run_time=1.4 if i > 0 else 2.0,
                rate_func=rate_functions.ease_in_out_cubic
            )

            # ── Country highlight (appears on arrival) ──
            hi_mob = None
            if iso in highlight_paths:
                hi_mob = ImageMobject(highlight_paths[iso])
                hi_mob.set_width(MAP_W)
                hi_mob.move_to(ORIGIN)
                self.play(FadeIn(hi_mob, run_time=0.3))

            # ══════════ LOGOS ══════════
            logo_mobs = []
            n_brands = len(brands)

            # Scatter positions INSIDE country bounds
            positions = []
            if bounds and n_brands > 0:
                bx1, by1, bx2, by2 = bounds
                bcx_l = (bx1 + bx2) / 2
                bcy_l = (by1 + by2) / 2
                bw = abs(bx2 - bx1)
                bh = abs(by2 - by1)
                for bi in range(n_brands):
                    if n_brands == 1:
                        positions.append((bcx_l, bcy_l))
                    elif n_brands == 2:
                        offsets = [(-0.2, 0.15), (0.2, -0.15)]
                        ox, oy = offsets[bi]
                        positions.append((bcx_l + bw * ox, bcy_l + bh * oy))
                    elif n_brands == 3:
                        offsets = [(0, 0.2), (-0.2, -0.12), (0.2, -0.12)]
                        ox, oy = offsets[bi]
                        positions.append((bcx_l + bw * ox, bcy_l + bh * oy))
                    elif n_brands == 4:
                        offsets = [(-0.18, 0.18), (0.18, 0.18), (-0.18, -0.18), (0.18, -0.18)]
                        ox, oy = offsets[bi]
                        positions.append((bcx_l + bw * ox, bcy_l + bh * oy))
                    else:
                        angle = (2 * math.pi * bi) / n_brands - math.pi / 2
                        r = min(bw, bh) * 0.25
                        positions.append((bcx_l + math.cos(angle) * r, bcy_l + math.sin(angle) * r))
            else:
                for bi in range(n_brands):
                    angle = (2 * math.pi * bi) / n_brands if n_brands > 1 else 0
                    positions.append((cx + math.cos(angle) * 0.5, cy + math.sin(angle) * 0.5))

            # Logo size relative to country on screen (~20% of country width)
            if bounds:
                logo_sz = max(min(bw, bh) * 0.22, 0.3)
            else:
                logo_sz = zoom_width * 0.15

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

                # ── Highlight DISAPPEARS when first logo appears ──
                if bi == 0 and hi_mob is not None:
                    self.play(FadeOut(hi_mob, run_time=0.25))
                    hi_mob = None

                px, py = positions[bi]

                # Load logo from pre-downloaded dir
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
                    except Exception as e:
                        print(f"[LOGO] render fail {bname}: {e}")

                # Fallback: styled text
                if logo_mob is None:
                    txt = Text(bname, font=raw_font, font_size=44,
                               color="#FFFFFF", weight="BOLD")
                    txt.set_max_width(zoom_width * 0.4)
                    bg = Rectangle(
                        width=txt.width * 1.3, height=txt.height * 1.8,
                        fill_color="#000000", fill_opacity=0.7, stroke_width=0)
                    bg.move_to([px, py, 0])
                    txt.move_to(bg.get_center())
                    logo_mob = Group(bg, txt)

                # Fade in logo
                self.play(FadeIn(logo_mob, run_time=0.35),
                          rate_func=rate_functions.ease_out_sine)
                logo_mobs.append(logo_mob)

                # Camera follows logo (smooth pan within country)
                follow_width = zoom_width * 0.75
                self.play(
                    self.camera.frame.animate
                        .move_to([px, py, 0])
                        .set(width=follow_width),
                    run_time=0.5,
                    rate_func=rate_functions.ease_in_out_sine
                )
                self.wait(0.2)

                # Pull back to country view before next logo
                if bi < n_brands - 1:
                    self.play(
                        self.camera.frame.animate
                            .move_to([cx, cy, 0])
                            .set(width=zoom_width),
                        run_time=0.35,
                        rate_func=rate_functions.ease_in_out_sine
                    )

            # ══════════ SUBTITLE — word by word synced ══════════
            sub_mobs = []
            words = text.split() if text else []
            if words:
                cam_c = self.camera.frame.get_center()
                cam_w_now = self.camera.frame.width
                cam_h_now = self.camera.frame.height
                sub_y = cam_c[1] - cam_h_now * 0.43

                # Background bar for subtitles
                sub_bg = Rectangle(
                    width=cam_w_now * 0.95, height=cam_h_now * 0.08,
                    fill_color="#000000", fill_opacity=0.6, stroke_width=0)
                sub_bg.move_to([cam_c[0], sub_y, 0])
                self.play(FadeIn(sub_bg, run_time=0.15))
                sub_mobs.append(sub_bg)

                # Words appear one by one
                built_text = ""
                for wi, word in enumerate(words):
                    built_text += word + " "
                    w_mob = Text(built_text.strip(), font=raw_font, font_size=26,
                                 color="#FFFFFF", weight="BOLD")
                    w_mob.set_max_width(cam_w_now * 0.88)
                    w_mob.move_to([cam_c[0], sub_y, 0])
                    if wi == 0:
                        self.play(FadeIn(w_mob, run_time=0.1))
                    else:
                        # Remove previous, show updated
                        self.remove(sub_mobs[-1] if len(sub_mobs) > 1 else sub_mobs[0])
                        self.add(w_mob)
                        self.wait(0.08)
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
                    self.camera.frame.animate.set(width=zoom_width * 1.4),
                    run_time=0.4,
                    rate_func=rate_functions.ease_in_out_sine
                )
