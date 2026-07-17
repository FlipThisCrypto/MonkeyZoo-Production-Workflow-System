"""Render a visual verification overlay for a scene_blocking.json:
horizon line, calibration object marker with its declared pixel height,
light-source positions colored by type, and reflective-surface polygons.

Estimate-then-inspect discipline: every calibration value is an
art-directed estimate, so every calibration gets an overlay render that a
human (or agent) actually looks at before the spec is trusted.

Usage: python calibrate_check.py <scene_blocking.json> [out.png]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]


def render_overlay(scene_path: Path, out_path: Path | None = None) -> Path:
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    plate = Image.open(ROOT / scene["background_plate"]).convert("RGB")
    d = ImageDraw.Draw(plate, "RGBA")
    w, h = plate.size

    gp = scene["ground_plane"]
    hy = gp["horizon_y"]
    d.line([(0, hy), (w, hy)], fill=(255, 220, 0, 255), width=3)
    d.text((8, hy - 16), f"horizon_y={hy}", fill=(255, 220, 0, 255))

    calib = gp["calibration"]
    cy, ch = calib["calib_y_foot"], calib["calib_height_px"]
    cx = calib.get("calib_x", w // 2)
    d.line([(cx, cy), (cx, cy - ch)], fill=(0, 255, 80, 255), width=4)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=(0, 255, 80, 255), width=3)
    d.text((cx + 10, cy - ch), f"{calib['reference_object']} h={ch}px", fill=(0, 255, 80, 255))

    for light in scene.get("light_sources", []):
        lx, ly = light["position_px"]
        color = (120, 220, 255, 255) if light["type"] == "key" else (255, 120, 220, 255)
        d.ellipse([lx - 10, ly - 10, lx + 10, ly + 10], outline=color, width=3)
        d.text((lx + 12, ly - 6), f"{light['id']} ({light['type']})", fill=color)

    for surf in scene.get("reflective_surfaces", []):
        d.polygon([tuple(p) for p in surf["polygon"]], fill=(255, 60, 60, 70), outline=(255, 0, 0, 255))
        d.text(tuple(surf["polygon"][0]), surf["id"], fill=(255, 90, 90, 255))

    for occ in scene.get("occluders", []):
        d.polygon([tuple(p) for p in occ["polygon"]], fill=(60, 120, 255, 70), outline=(0, 120, 255, 255))
        d.text(tuple(occ["polygon"][0]), occ["id"], fill=(120, 180, 255, 255))

    if out_path is None:
        out_path = scene_path.parent / "calibration_check.png"
    plate.save(out_path)
    return out_path


if __name__ == "__main__":
    scene_path = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    print(render_overlay(scene_path, out))
