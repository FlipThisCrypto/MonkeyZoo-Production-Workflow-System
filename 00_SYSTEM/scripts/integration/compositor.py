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
from shadow import draw_contact_shadow  # noqa: E402
from relight import relight  # noqa: E402
from occlusion import add_foreground_rain  # noqa: E402
import numpy as np  # noqa: E402


NAMED_LIGHT_COLORS = {
    "cool cyan-white": (170, 230, 255),
    "cyan-white": (170, 230, 255),
    "magenta": (230, 70, 190),
    "spring green": (110, 230, 120),
    "warm-magenta": (230, 90, 180),
}


def _hex_or_named(name: str) -> tuple[int, int, int]:
    return NAMED_LIGHT_COLORS.get(name.strip().lower(), (200, 200, 200))


def load_ground_plane(scene_blocking: dict) -> GroundPlane:
    gp = scene_blocking["ground_plane"]
    calib = gp["calibration"]
    return GroundPlane(
        horizon_y=gp["horizon_y"],
        calib_y=calib["calib_y_foot"],
        calib_height_px=calib["calib_height_px"],
    )


SHADOW_DIRECTIONS = {
    "down": 90, "down-left": 135, "down-and-left": 135, "left": 180,
    "down-right": 45, "down-and-right": 45, "right": 0, "up": 270,
}


def _shadow_angle(direction_text: str) -> float:
    key = direction_text.strip().lower()
    return SHADOW_DIRECTIONS.get(key, 135)


def sample_ambient_luma(plate: Image.Image, anchor_px: tuple[float, float], radius: int = 60) -> float:
    x, y = anchor_px
    w, h = plate.size
    box = (max(0, int(x - radius)), max(0, int(y - radius * 1.4)),
           min(w, int(x + radius)), min(h, int(y)))
    patch = np.array(plate.convert("RGB").crop(box), dtype=np.float32)
    return float(patch.mean()) if patch.size else 128.0


def place_character(
    plate: Image.Image,
    char_layer: Image.Image,
    foot_anchor_px: tuple[float, float],
    ground_plane: GroundPlane,
    shadow_direction: str | None = None,
    relight_spec: dict | None = None,
) -> tuple[Image.Image, dict]:
    """Scale char_layer so its apparent height matches the ground plane at
    foot_anchor_px, draw a contact shadow under the anchor if requested,
    then paste the character (alpha-composited) so its own visual foot
    point (bottom-center of its opaque bbox, not the raw canvas edge) lands
    exactly on foot_anchor_px."""
    target_h = ground_plane.height_at(foot_anchor_px[1])

    alpha = char_layer.split()[-1]
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("character layer has no opaque pixels")
    cropped = char_layer.crop(bbox)
    relit = False
    if relight_spec:
        ambient = sample_ambient_luma(plate, foot_anchor_px)
        cropped = relight(cropped, ambient_luma=ambient, **relight_spec)
        relit = True

    scale = target_h / cropped.height
    new_w = max(1, round(cropped.width * scale))
    new_h = max(1, round(cropped.height * scale))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    paste_x = round(foot_anchor_px[0] - new_w / 2)
    paste_y = round(foot_anchor_px[1] - new_h)

    canvas = plate.convert("RGBA").copy()
    shadow_used = False
    if shadow_direction:
        canvas = draw_contact_shadow(
            canvas, foot_anchor_px, new_w, shadow_direction_deg=_shadow_angle(shadow_direction)
        )
        shadow_used = True
    canvas.alpha_composite(resized, (paste_x, paste_y))

    return canvas, {
        "target_height_px": round(target_h, 1),
        "source_bbox_in_layer": bbox,
        "scale_factor": round(scale, 4),
        "paste_box": [paste_x, paste_y, paste_x + new_w, paste_y + new_h],
        "contact_shadow_applied": shadow_used,
        "relit": relit,
    }


def run(poc_dir: Path) -> dict:
    scene = json.loads((poc_dir / "scene_blocking.json").read_text(encoding="utf-8"))
    pose = json.loads((poc_dir / "pose_spec.json").read_text(encoding="utf-8"))

    root = Path(__file__).resolve().parents[3]
    plate = Image.open(root / scene["background_plate"]).convert("RGBA")
    char_layer = Image.open(root / pose["asset_used"]).convert("RGBA")
    gp = load_ground_plane(scene)

    foot_anchor = tuple(pose["ground_contact"]["foot_anchor_px"])
    key = next((l for l in scene["light_sources"] if l["type"] == "key"), None)
    fill = next((l for l in scene["light_sources"] if l["type"] == "fill"), None)
    relight_spec = None
    if key and fill:
        key_on_high_side = key["position_px"][0] >= foot_anchor[0]
        relight_spec = {
            "key_color": _hex_or_named(key["color"]),
            "fill_color": _hex_or_named(fill["color"]),
            "gradient_axis": "horizontal",
            "key_on_high_side": key_on_high_side,
        }

    canvas, report = place_character(
        plate, char_layer, foot_anchor, gp,
        shadow_direction=pose.get("lighting", {}).get("shadow_direction"),
        relight_spec=relight_spec,
    )

    occlusion_applied = False
    if "rain layer in front of the character" in " ".join(pose.get("occlusion", [])):
        canvas = add_foreground_rain(canvas, tuple(report["paste_box"]))
        occlusion_applied = True
    report["foreground_rain_applied"] = occlusion_applied

    out_path = poc_dir / "04_final_integrated.png"
    canvas.convert("RGB").save(out_path)
    report["output"] = str(out_path)
    return report


if __name__ == "__main__":
    poc_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] \
        / "00_SYSTEM" / "integration_upgrade" / "poc" / "MZ-2026-09-02_P01_PANEL01"
    print(json.dumps(run(poc_dir), indent=2))
