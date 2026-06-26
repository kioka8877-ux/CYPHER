#!/usr/bin/env python3
"""cyp_camera_plan.py — Genere camera_plan.json depuis render_spec.json.
Continuite caméra entre chunks : entry[i] = etat ou le segment i-1 a laisse la camera.
Reutilise EXACTEMENT la geometrie de CypherScene (geo_to_manim, MAP_W)."""
import json
from pathlib import Path
import CypherScene as CS  # constants + geo_to_manim (config manim importee, pas de rendu)

spec = json.loads(Path("render_spec.json").read_text())
segs = spec.get("segments", [])
MAP_W = CS.MAP_W

plan = []
settled = {"center": [0.0, 0.0], "width": MAP_W * 1.05}  # vue monde
for seg in segs:
    plan.append({"center": list(settled["center"]), "width": settled["width"]})
    iso = seg.get("iso")
    lon = float(seg.get("lon", 0) or 0)
    lat = float(seg.get("lat", 0) or 0)
    zoom = float(seg.get("zoom", 5))
    if iso and (lon or lat):
        x, y = CS.geo_to_manim(lon, lat)
        zoom_width = max(10.0 - zoom * 1.0, 3.0)
        settled = {"center": [float(x), float(y)], "width": float(zoom_width)}

Path("camera_plan.json").write_text(json.dumps(plan, indent=2))
print(f"[CYPHER] camera_plan.json written: {len(plan)} entries")
