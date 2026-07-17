"""Deterministic character-into-scene compositor.

Cycle 3: geometry only (scale + ground-anchor placement of an already-alpha
character layer onto a background plate). Shadow, relighting, and
foreground occlusion are added by later pipeline stages (see
scene_integrate.py) so each step is independently testable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from perspective import GroundPlane  # noqa: E402


def load_ground_plane(scene_blocking: dict) -> GroundPlane:
    gp = scene_blocking["ground_plane"]
    calib = gp["calibration"]
    return GroundPlane(
        horizon_y=gp["horizon_y"],
        calib_y=calib["calib_y_foot"],
        calib_height_px=calib["calib_height_px"],
    )


def place_character(
    plate: Image.Image,
    char_layer: Image.Image,
    foot_anchor_px: tuple[float, float],
    ground_plane: GroundPlane,
) -> tuple[Image.Image, dict]:
    """Scale char_layer so its apparent height matches the ground plane at
    foot_anchor_px, then paste it (alpha-composited) so its own visual foot
    point (bottom-center of its opaque bbox, not the raw canvas edge) lands
    exactly on foot_anchor_px."""
    target_h = ground_plane.height_at(foot_anchor_px[1])

    alpha = char_layer.split()[-1]
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("character layer has no opaque pixels")
    cropped = char_layer.crop(bbox)

    scale = target_h / cropped.height
    new_w = max(1, round(cropped.width * scale))
    new_h = max(1, round(cropped.height * scale))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    paste_x = round(foot_anchor_px[0] - new_w / 2)
    paste_y = round(foot_anchor_px[1] - new_h)

    canvas = plate.convert("RGBA").copy()
    canvas.alpha_composite(resized, (paste_x, paste_y))

    return canvas, {
        "target_height_px": round(target_h, 1),
        "source_bbox_in_layer": bbox,
        "scale_factor": round(scale, 4),
        "paste_box": [paste_x, paste_y, paste_x + new_w, paste_y + new_h],
    }


def run(poc_dir: Path) -> dict:
    scene = json.loads((poc_dir / "scene_blocking.json").read_text(encoding="utf-8"))
    pose = json.loads((poc_dir / "pose_spec.json").read_text(encoding="utf-8"))

    root = Path(__file__).resolve().parents[3]
    plate = Image.open(root / scene["background_plate"]).convert("RGBA")
    char_layer = Image.open(root / pose["asset_used"]).convert("RGBA")
    gp = load_ground_plane(scene)

    canvas, report = place_character(
        plate, char_layer, tuple(pose["ground_contact"]["foot_anchor_px"]), gp
    )

    out_path = poc_dir / "01_geometry_placement.png"
    canvas.convert("RGB").save(out_path)
    report["output"] = str(out_path)
    return report


if __name__ == "__main__":
    poc_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] \
        / "00_SYSTEM" / "integration_upgrade" / "poc" / "MZ-2026-09-02_P01_PANEL01"
    print(json.dumps(run(poc_dir), indent=2))
