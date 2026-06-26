#!/usr/bin/env python3
"""cyp_camera_plan.py — Genere camera_plan.json depuis render_spec (v2 split)."""
import json
from pathlib import Path

EXTENT = (-180, 180, -60, 85)
MAP_W = 24.0
MAP_H = MAP_W * (EXTENT[3] - EXTENT[2]) / (EXTENT[1] - EXTENT[0]) * 1.2

ISO2TO3 = {
    "US":"USA","DE":"DEU","JP":"JPN","KR":"KOR","FR":"FRA","IT":"ITA",
    "SE":"SWE","CN":"CHN","CA":"CAN","GB":"GBR","AE":"ARE","TW":"TWN",
    "CH":"CHE","NL":"NLD","ES":"ESP","IN":"IND","AU":"AUS","SG":"SGP",
    "FI":"FIN","DK":"DNK","BR":"BRA",
}

def geo_to_manim(lon, lat):
    x = (lon - EXTENT[0]) / (EXTENT[1] - EXTENT[0]) * MAP_W - MAP_W / 2
    y = (lat - EXTENT[2]) / (EXTENT[3] - EXTENT[2]) * MAP_H - MAP_H / 2
    return x, y

# Load spec (prefer v2)
for name in ["render_spec_v2.json", "render_spec.json"]:
    p = Path(name)
    if p.exists():
        spec = json.loads(p.read_text())
        print(f"[CAM-PLAN] Using {name}")
        break

segs = spec.get("segments", [])
plan = []
settled = {"center": [0.0, 0.0], "width": MAP_W * 1.05}

for seg in segs:
    plan.append({"center": list(settled["center"]), "width": settled["width"]})
    lon = float(seg.get("lon", 0) or 0)
    lat = float(seg.get("lat", 0) or 0)
    zoom = float(seg.get("zoom", 5))
    if lon or lat:
        x, y = geo_to_manim(lon, lat)
        zoom_width = max(10.0 - zoom * 1.0, 3.0)
        settled = {"center": [round(x,4), round(y,4)], "width": round(zoom_width,4)}

Path("camera_plan.json").write_text(json.dumps(plan, indent=2))
print(f"[CAM-PLAN] camera_plan.json: {len(plan)} entries")
