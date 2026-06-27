#!/usr/bin/env python3
"""CYPHER Renderer v8.0 — PIL + FFmpeg pipeline (no Manim).
Generates frames with PIL, pipes to FFmpeg for encoding.
100x faster than Manim Cairo renderer.
"""
import json, math, os, subprocess, sys, time, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# ── Config ──────────────────────────────────────────────
FPS = 30
WIDTH, HEIGHT = 1920, 1080
TRANSITION_FRAMES = int(0.6 * FPS)   # 0.6s camera travel between countries
LOGO_APPEAR_FRAMES = int(0.15 * FPS) # quick fade-in for logos (4-5 frames)

# ── Paths ───────────────────────────────────────────────
BASE = Path(os.environ.get("CYPHER_BASE", "."))
LOGO_DIR = Path(os.environ.get("LOGO_DIR", "logos"))
OUT_DIR = Path(os.environ.get("OUT_DIR", "out"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

def get_font(size):
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()

# ── Mercator helpers ────────────────────────────────────
def lonlat_to_merc(lon, lat):
    lat = max(-85, min(85, lat))
    x = lon * 20037508.34 / 180
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 20037508.34 / math.pi
    return x, y

def merc_to_pixel(mx, my, extent, iw, ih):
    """extent = (mx0, mx1, my0, my1)"""
    px = (mx - extent[0]) / (extent[1] - extent[0]) * iw
    py = (1.0 - (my - extent[2]) / (extent[3] - extent[2])) * ih
    return px, py

# ── Easing ──────────────────────────────────────────────
def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2

# ── Download satellite background ──────────────────────
def download_satellite(all_lons, all_lats):
    """Download satellite tiles via contextily and return (PIL Image, mercator extent)."""
    import contextily as cx

    margin_lon, margin_lat = 20, 15
    min_lon = min(all_lons) - margin_lon
    max_lon = max(all_lons) + margin_lon
    min_lat = max(min(all_lats) - margin_lat, -60)
    max_lat = min(max(all_lats) + margin_lat, 75)

    x0, y0 = lonlat_to_merc(min_lon, min_lat)
    x1, y1 = lonlat_to_merc(max_lon, max_lat)

    print(f"[SAT] Downloading tiles for lon[{min_lon:.0f},{max_lon:.0f}] lat[{min_lat:.0f},{max_lat:.0f}]")
    url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    img_arr, ext = cx.bounds2img(x0, y0, x1, y1, source=url, zoom=4, ll=False)
    # ext = (left, right, bottom, top) in mercator
    bg = Image.fromarray(img_arr).convert("RGB")
    extent = (ext[0], ext[1], ext[2], ext[3])
    print(f"[SAT] Background: {bg.size}, extent: {extent}")
    return bg, extent

# ── Country highlight polygon ──────────────────────────
def load_country_polygons():
    """Load Natural Earth shapefiles and return a dict {ISO_A3: [(lon,lat),...]}."""
    try:
        import geopandas as gpd
        from shapely.geometry import MultiPolygon, Polygon
    except ImportError:
        print("[GEO] geopandas not available, skipping highlights")
        return {}

    shp_path = Path("ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp")
    if not shp_path.exists():
        shp_path = Path("ne_110m_admin_0_countries.shp")
    if not shp_path.exists():
        # Try download
        import urllib.request, zipfile
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        print("[GEO] Downloading Natural Earth...")
        urllib.request.urlretrieve(url, "ne_110m.zip")
        with zipfile.ZipFile("ne_110m.zip") as z:
            z.extractall("ne_110m_admin_0_countries")
        shp_path = Path("ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp")

    gdf = gpd.read_file(shp_path)

    # Find ISO column
    iso_col = None
    for col in ["ISO_A3", "ISO_A3_EH", "ADM0_A3"]:
        if col in gdf.columns:
            iso_col = col
            break
    if not iso_col:
        print("[GEO] No ISO column found")
        return {}

    ISO2TO3 = {
        "US":"USA","DE":"DEU","JP":"JPN","KR":"KOR","FR":"FRA","IT":"ITA",
        "SE":"SWE","CN":"CHN","CA":"CAN","GB":"GBR","AE":"ARE","TW":"TWN",
        "CH":"CHE","NL":"NLD","ES":"ESP","IN":"IND","AU":"AUS","SG":"SGP",
        "FI":"FIN","DK":"DNK","BR":"BRA",
    }

    polygons = {}
    for iso2, iso3 in ISO2TO3.items():
        rows = gdf[gdf[iso_col] == iso3]
        if rows.empty:
            for c in ["ISO_A3_EH", "ADM0_A3", "ISO_A3"]:
                if c in gdf.columns:
                    rows = gdf[gdf[c] == iso3]
                    if not rows.empty:
                        break
        if rows.empty:
            continue

        geom = rows.iloc[0].geometry
        polys = []
        if isinstance(geom, MultiPolygon):
            polys = list(geom.geoms)
        elif isinstance(geom, Polygon):
            polys = [geom]

        # Keep largest polygon (mainland)
        if polys:
            largest = max(polys, key=lambda p: p.area)
            coords = list(largest.exterior.coords)
            polygons[iso2] = coords

    print(f"[GEO] Loaded {len(polygons)} country polygons")
    return polygons

def draw_highlight(draw, coords_lonlat, extent, iw, ih, color=(0, 150, 255, 80)):
    """Draw a filled polygon for country highlight."""
    pixel_coords = []
    for lon, lat in coords_lonlat:
        mx, my = lonlat_to_merc(lon, lat)
        px, py = merc_to_pixel(mx, my, extent, iw, ih)
        pixel_coords.append((px, py))
    if len(pixel_coords) > 2:
        draw.polygon(pixel_coords, fill=color, outline=(0, 180, 255, 200))

# ── Camera state ────────────────────────────────────────
class Camera:
    """Camera defined by center (lon, lat) and zoom_deg (visible degrees of longitude)."""
    def __init__(self, lon=0, lat=20, zoom_deg=360):
        self.lon = lon
        self.lat = lat
        self.zoom_deg = zoom_deg

    def get_crop_box(self, bg, extent, zoom_factor=1.0):
        """Return (left, top, right, bottom) pixel crop on the background image."""
        iw, ih = bg.size
        cx_merc, cy_merc = lonlat_to_merc(self.lon, self.lat)
        # Visible width in mercator units
        half_lon = self.zoom_deg / 2 * zoom_factor
        left_merc, _ = lonlat_to_merc(self.lon - half_lon, 0)
        right_merc, _ = lonlat_to_merc(self.lon + half_lon, 0)
        vis_w_merc = right_merc - left_merc
        vis_h_merc = vis_w_merc * HEIGHT / WIDTH  # maintain aspect ratio

        # Convert to pixels
        left_px, top_px = merc_to_pixel(cx_merc - vis_w_merc/2, cy_merc + vis_h_merc/2, extent, iw, ih)
        right_px, bot_px = merc_to_pixel(cx_merc + vis_w_merc/2, cy_merc - vis_h_merc/2, extent, iw, ih)

        return (int(left_px), int(top_px), int(right_px), int(bot_px))

    def interpolate(self, other, t):
        """Interpolate between self and other camera with eased t."""
        et = ease_in_out_cubic(t)
        return Camera(
            lon=self.lon + (other.lon - self.lon) * et,
            lat=self.lat + (other.lat - self.lat) * et,
            zoom_deg=self.zoom_deg + (other.zoom_deg - self.zoom_deg) * et,
        )

# ── Zoom from render_spec zoom level ───────────────────
def zoom_to_deg(zoom_level):
    """Convert render_spec zoom (1-10) to visible degrees of longitude.
    zoom=4 → ~60deg (big countries), zoom=8 → ~5deg (small countries like SG)."""
    return max(360 / (2 ** (zoom_level - 1)), 3)

# ── Main render ─────────────────────────────────────────
def main():
    t0 = time.time()

    # Which segments to render (for chunked rendering)
    seg_start = int(os.environ.get("SEG_START", 0))
    seg_end_env = os.environ.get("SEG_END", None)

    # Load spec
    spec = None
    for name in ["render_spec_v2.json", "render_spec.json"]:
        p = BASE / name
        if p.exists():
            spec = json.loads(p.read_text())
            print(f"[SPEC] Loaded {name}")
            break
    if not spec:
        sys.exit("[ERR] No render_spec found")

    segments = spec["segments"]
    fps = spec["meta"]["fps"]
    total_dur = spec["meta"]["duration_seconds"]
    seg_end_idx = int(seg_end_env) if seg_end_env else len(segments)
    segments = segments[seg_start:seg_end_idx]
    print(f"[SPEC] Rendering segments {seg_start}-{seg_end_idx-1} ({len(segments)} segs, {total_dur:.1f}s total)")

    # Collect all coordinates
    all_lons, all_lats = [], []
    for seg in spec["segments"]:  # ALL segments for background extent
        lon = float(seg.get("lon") or 0)
        lat = float(seg.get("lat") or 0)
        if lon or lat:
            all_lons.append(lon)
            all_lats.append(lat)

    # Download satellite
    bg, extent = download_satellite(all_lons, all_lats)
    bg_w, bg_h = bg.size

    # Load country polygons
    polygons = load_country_polygons()

    # Load logos
    logos_cache = {}
    for seg in segments:
        for brand in seg.get("brands", []):
            domain = brand.get("domain", "")
            if domain and domain not in logos_cache:
                safe = domain.replace("/", "_")
                lp = LOGO_DIR / f"{safe}.png"
                if lp.exists() and lp.stat().st_size > 500:
                    try:
                        logos_cache[domain] = Image.open(lp).convert("RGBA")
                    except:
                        pass
    print(f"[LOGO] Cached {len(logos_cache)} logos")

    # ── Build keyframe timeline ─────────────────────────
    # Each segment → camera target
    keyframes = []  # (time, Camera, segment_data)

    # Initial wide shot
    keyframes.append((0, Camera(lon=0, lat=20, zoom_deg=300), None))

    for seg in segments:
        lon = float(seg.get("lon") or 0)
        lat = float(seg.get("lat") or 0)
        zoom = float(seg.get("zoom") or 4)
        zdeg = zoom_to_deg(zoom) * 0.95  # 95% fill

        # Cap wide countries (USA, Canada, etc.)
        if zdeg > 80:
            zdeg = 80

        t_start = seg["start"]
        t_end = seg["end"]

        # Arrive at country 0.3s after segment start
        keyframes.append((t_start + 0.3, Camera(lon=lon, lat=lat, zoom_deg=zdeg), seg))

        # Stay until segment end
        keyframes.append((t_end, Camera(lon=lon, lat=lat, zoom_deg=zdeg), seg))

    # Sort by time
    keyframes.sort(key=lambda x: x[0])

    # ── Compute camera for each frame ───────────────────
    # Calculate actual frame range for this chunk
    if segments:
        chunk_start_time = segments[0]["start"]
        chunk_end_time = segments[-1]["end"]
    else:
        chunk_start_time = 0
        chunk_end_time = total_dur

    total_frames = int(math.ceil((chunk_end_time - chunk_start_time) * FPS))
    print(f"[RENDER] {total_frames} frames @ {FPS}fps ({chunk_end_time - chunk_start_time:.1f}s)")

    def get_camera_at(t):
        """Interpolate camera position at time t."""
        if t <= keyframes[0][0]:
            return keyframes[0][1]
        if t >= keyframes[-1][0]:
            return keyframes[-1][1]
        # Find surrounding keyframes
        for i in range(len(keyframes) - 1):
            if keyframes[i][0] <= t <= keyframes[i+1][0]:
                before = keyframes[i]
                after = keyframes[i+1]
                dt = after[0] - before[0]
                if dt < 0.001:
                    return after[1]
                frac = (t - before[0]) / dt
                return before[1].interpolate(after[1], frac)
        return keyframes[-1][1]

    def get_active_segment(t):
        """Return the active segment at time t."""
        for seg in segments:
            if seg["start"] <= t <= seg["end"]:
                return seg
        return None

    # ── FFmpeg pipe setup ───────────────────────────────
    chunk_label = f"chunk_{seg_start}_{seg_end_idx}"
    out_path = OUT_DIR / f"{chunk_label}.mp4"

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]
    print(f"[FFMPEG] Piping to: {' '.join(ffmpeg_cmd)}")
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # ── Render loop ─────────────────────────────────────
    font_sub = get_font(36)
    font_logo = get_font(28)
    last_pct = -1

    for frame_idx in range(total_frames):
        t = chunk_start_time + frame_idx / FPS
        cam = get_camera_at(t)
        active_seg = get_active_segment(t)

        # 1. Crop background for current camera view
        crop_box = cam.get_crop_box(bg, extent)
        # Clamp to image bounds
        cx0 = max(0, min(crop_box[0], bg_w - 1))
        cy0 = max(0, min(crop_box[1], bg_h - 1))
        cx1 = max(cx0 + 1, min(crop_box[2], bg_w))
        cy1 = max(cy0 + 1, min(crop_box[3], bg_h))

        cropped = bg.crop((cx0, cy0, cx1, cy1))
        frame = cropped.resize((WIDTH, HEIGHT), Image.LANCZOS)

        # Convert to RGBA for compositing
        frame = frame.convert("RGBA")

        if active_seg:
            iso2 = active_seg.get("iso", "").upper()

            # 2. Country highlight
            if iso2 in polygons:
                overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
                odraw = ImageDraw.Draw(overlay)
                # Transform polygon coords to frame pixel coords
                poly_pixels = []
                for lon_p, lat_p in polygons[iso2]:
                    mx, my = lonlat_to_merc(lon_p, lat_p)
                    # Convert mercator → background pixel → frame pixel
                    bg_px, bg_py = merc_to_pixel(mx, my, extent, bg_w, bg_h)
                    # Map from bg coordinates to crop coordinates to frame coordinates
                    fx = (bg_px - cx0) / (cx1 - cx0) * WIDTH
                    fy = (bg_py - cy0) / (cy1 - cy0) * HEIGHT
                    poly_pixels.append((fx, fy))

                # Check if first logo has appeared
                brands = active_seg.get("brands", [])
                first_wf = brands[0].get("word_frame", 0) if brands else 9999
                first_logo_time = first_wf / fps
                show_highlight = t < first_logo_time

                if show_highlight and len(poly_pixels) > 2:
                    odraw.polygon(poly_pixels, fill=(0, 120, 255, 70),
                                  outline=(0, 180, 255, 180))
                    frame = Image.alpha_composite(frame, overlay)

            # 3. Logos
            brands = active_seg.get("brands", [])
            n_brands = len(brands)
            seg_lon = float(active_seg.get("lon") or 0)
            seg_lat = float(active_seg.get("lat") or 0)

            for bi, brand in enumerate(brands):
                wf = brand.get("word_frame", 0)
                logo_time = wf / fps
                if t < logo_time:
                    continue  # not yet visible

                domain = brand.get("domain", "")
                bname = brand.get("name", "").upper()[:12]

                # Position: scatter around country center
                if n_brands == 1:
                    blon, blat = seg_lon, seg_lat
                else:
                    angle = (2 * math.pi * bi) / n_brands - math.pi / 2
                    zdeg = cam.zoom_deg
                    r = zdeg * 0.12
                    blon = seg_lon + math.cos(angle) * r
                    blat = seg_lat + math.sin(angle) * r * 0.6

                # Convert to frame pixel
                mx, my = lonlat_to_merc(blon, blat)
                bg_px, bg_py = merc_to_pixel(mx, my, extent, bg_w, bg_h)
                fx = (bg_px - cx0) / (cx1 - cx0) * WIDTH
                fy = (bg_py - cy0) / (cy1 - cy0) * HEIGHT

                # Fade-in alpha
                fade_t = (t - logo_time) * FPS / max(LOGO_APPEAR_FRAMES, 1)
                alpha = min(1.0, max(0.0, fade_t))

                # Draw logo
                logo_size = int(min(WIDTH, HEIGHT) * 0.12)
                logo_img = logos_cache.get(domain)

                overlay_logo = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

                if logo_img:
                    li = logo_img.copy()
                    li.thumbnail((logo_size, logo_size), Image.LANCZOS)
                    # White background card
                    card_w = li.width + 16
                    card_h = li.height + 16
                    card = Image.new("RGBA", (card_w, card_h), (255, 255, 255, int(240 * alpha)))
                    card.paste(li, (8, 8), li if li.mode == "RGBA" else None)
                    # Paste card centered at (fx, fy)
                    paste_x = int(fx - card_w / 2)
                    paste_y = int(fy - card_h / 2)
                    if 0 <= paste_x < WIDTH - card_w and 0 <= paste_y < HEIGHT - card_h:
                        overlay_logo.paste(card, (paste_x, paste_y), card)
                else:
                    # Text fallback
                    odraw = ImageDraw.Draw(overlay_logo)
                    bbox = odraw.textbbox((0,0), bname, font=font_logo)
                    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
                    rx, ry = int(fx - tw/2 - 10), int(fy - th/2 - 6)
                    odraw.rectangle([rx, ry, rx+tw+20, ry+th+12],
                                    fill=(0,0,0,int(180*alpha)))
                    odraw.text((rx+10, ry+6), bname, font=font_logo,
                               fill=(255,255,255,int(255*alpha)))

                frame = Image.alpha_composite(frame, overlay_logo)

            # 4. Subtitle
            text = active_seg.get("text", "").strip()
            if text:
                overlay_sub = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
                sdraw = ImageDraw.Draw(overlay_sub)
                # Word wrap if needed
                max_w = int(WIDTH * 0.85)
                # Simple wrap
                words = text.split()
                lines_out = []
                current = ""
                for w in words:
                    test = current + " " + w if current else w
                    bbox = sdraw.textbbox((0,0), test, font=font_sub)
                    if bbox[2] - bbox[0] > max_w and current:
                        lines_out.append(current)
                        current = w
                    else:
                        current = test
                if current:
                    lines_out.append(current)

                line_h = font_sub.size + 8
                total_h = len(lines_out) * line_h
                bar_y = HEIGHT - total_h - 40
                sdraw.rectangle([0, bar_y - 10, WIDTH, HEIGHT],
                                fill=(0, 0, 0, 150))
                for li, line in enumerate(lines_out):
                    bbox = sdraw.textbbox((0,0), line, font=font_sub)
                    tw = bbox[2] - bbox[0]
                    tx = (WIDTH - tw) // 2
                    ty = bar_y + li * line_h
                    sdraw.text((tx, ty), line, font=font_sub, fill=(255,255,255,240))

                frame = Image.alpha_composite(frame, overlay_sub)

        # Convert to RGB and write raw bytes to FFmpeg
        rgb = frame.convert("RGB")
        proc.stdin.write(rgb.tobytes())

        # Progress
        pct = int(frame_idx / total_frames * 100)
        if pct % 5 == 0 and pct != last_pct:
            elapsed = time.time() - t0
            eta = elapsed / max(frame_idx, 1) * (total_frames - frame_idx)
            print(f"[RENDER] {pct}% ({frame_idx}/{total_frames}) elapsed={elapsed:.0f}s eta={eta:.0f}s")
            last_pct = pct

    # ── Finalize ────────────────────────────────────────
    proc.stdin.close()
    stderr = proc.stderr.read().decode()
    proc.wait()
    elapsed = time.time() - t0
    print(f"[DONE] {out_path} rendered in {elapsed:.1f}s (rc={proc.returncode})")
    if proc.returncode != 0:
        print(f"[FFMPEG STDERR] {stderr[-1000:]}")
    return str(out_path)

if __name__ == "__main__":
    main()
