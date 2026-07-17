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
from reflection import add_puddle_reflection  # noqa: E402
from haze import depth_haze_factor, apply_haze  # noqa: E402
import numpy as np  # noqa: E402


NAMED_LIGHT_COLORS = {
    "cool cyan-white": (170, 230, 255),
    "cyan-white": (170, 230, 255),
    "magenta": (230, 70, 190),
    "spring green": (110, 230, 120),
    "warm-magenta": (230, 90, 180),
    # added for the Cycle-18 plate calibrations (agents documented these
    # names falling back to neutral grey): relay-junction crystal glow and
    # the school hallway's fluorescent tint
    "teal": (45, 195, 190),
    "pale yellow-green": (215, 230, 170),
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
    reflection_polygon: list | None = None,
    atmosphere: dict | None = None,
    behind_polygons: list[list] | None = None,
    shadow_opacity: float | None = None,
    reflection_opacity: float | None = None,
    character_height_factor: float = 1.0,
) -> tuple[Image.Image, dict]:
    """Scale char_layer so its apparent height matches the ground plane at
    foot_anchor_px, draw a contact shadow under the anchor if requested,
    then paste the character (alpha-composited) so its own visual foot
    point (bottom-center of its opaque bbox, not the raw canvas edge) lands
    exactly on foot_anchor_px."""
    target_h = ground_plane.height_at(foot_anchor_px[1]) * character_height_factor

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

    haze_k = 0.0
    # an atmosphere block only drives haze when it declares a sampled
    # haze_color -- agent-authored scene specs may carry atmosphere
    # metadata (mood, humidity notes) without one (found on the relay
    # plate spec)
    if atmosphere and atmosphere.get("haze_color"):
        haze_k = depth_haze_factor(foot_anchor_px[1], ground_plane.horizon_y,
                                   ground_plane.calib_y, atmosphere.get("haze_max", 0.5))
        cropped = apply_haze(cropped, haze_k, tuple(atmosphere["haze_color"]))

    scale = target_h / cropped.height
    new_w = max(1, round(cropped.width * scale))
    new_h = max(1, round(cropped.height * scale))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    paste_x = round(foot_anchor_px[0] - new_w / 2)
    paste_y = round(foot_anchor_px[1] - new_h)

    canvas = plate.convert("RGBA").copy()
    shadow_used = False
    if shadow_direction:
        shadow_kwargs = {"shadow_direction_deg": _shadow_angle(shadow_direction)}
        if shadow_opacity is not None:
            shadow_kwargs["opacity"] = shadow_opacity
        canvas = draw_contact_shadow(canvas, foot_anchor_px, new_w, **shadow_kwargs)
        shadow_used = True

    paste_box = [paste_x, paste_y, paste_x + new_w, paste_y + new_h]
    reflection_report = None
    if reflection_polygon:
        # reflection drawn before the character so it never overlaps the sprite
        refl_kwargs = {}
        if reflection_opacity is not None:
            refl_kwargs["opacity"] = reflection_opacity
        canvas, reflection_report = add_puddle_reflection(
            canvas, resized, tuple(paste_box), reflection_polygon, **refl_kwargs
        )
    canvas.alpha_composite(resized, (paste_x, paste_y))
    occluded = False
    if behind_polygons:
        canvas = repaint_occluders(canvas, plate, behind_polygons)
        occluded = True

    return canvas, {
        "occluded_by_geometry": occluded,
        "target_height_px": round(target_h, 1),
        "source_bbox_in_layer": bbox,
        "scale_factor": round(scale, 4),
        "paste_box": paste_box,
        "contact_shadow_applied": shadow_used,
        "relit": relit,
        "haze_k": round(haze_k, 3),
        "reflection": reflection_report,
    }


def repaint_occluders(canvas: Image.Image, plate: Image.Image,
                      occluder_polygons: list[list]) -> Image.Image:
    """Re-paints the ORIGINAL plate pixels of each occluder polygon over
    the canvas, so a character pasted before this call reads as standing
    BEHIND those scene objects. Solid objects only (a traced trash can,
    console, railing slat) -- see-through occluders like chain-link would
    need a wire-level mask, which polygon tracing can't provide."""
    from PIL import ImageDraw
    mask = Image.new("L", canvas.size, 0)
    d = ImageDraw.Draw(mask)
    for poly in occluder_polygons:
        d.polygon([tuple(p) for p in poly], fill=255)
    out = canvas.copy()
    out.paste(plate.convert("RGBA"), (0, 0), mask)
    return out


def derive_relight_spec(scene: dict, foot_anchor: tuple[float, float]) -> dict | None:
    """Key/fill tint from the scene's declared light sources, with the key
    side decided per character position (a character left of the lamp is
    lit from its right, and vice versa)."""
    key = next((l for l in scene["light_sources"] if l["type"] == "key"), None)
    fill = next((l for l in scene["light_sources"] if l["type"] == "fill"), None)
    if not (key and fill):
        return None
    return {
        "key_color": _hex_or_named(key["color"]),
        "fill_color": _hex_or_named(fill["color"]),
        "gradient_axis": "horizontal",
        "key_on_high_side": key["position_px"][0] >= foot_anchor[0],
    }


def run_scene(spec_dir: Path) -> dict:
    """Multi-character staging: characters_spec.json holds a `characters`
    array; all share one ground plane and light set from scene_blocking.
    Characters are composited far-to-near (sorted by foot y ascending) so
    nearer figures correctly overlap farther ones. Foreground rain, if
    requested at scene level, is applied once at the end over the union of
    paste boxes so streaks cross every figure consistently."""
    scene = json.loads((spec_dir / "scene_blocking.json").read_text(encoding="utf-8"))
    spec = json.loads((spec_dir / "characters_spec.json").read_text(encoding="utf-8"))

    root = Path(__file__).resolve().parents[3]
    canvas = Image.open(root / scene["background_plate"]).convert("RGBA")
    gp = load_ground_plane(scene)

    surfaces = {s["id"]: s["polygon"] for s in scene.get("reflective_surfaces", [])}
    occluders = {o["id"]: o["polygon"] for o in scene.get("occluders", [])}
    reports = {}
    ordered = sorted(spec["characters"], key=lambda c: c["ground_contact"]["foot_anchor_px"][1])
    for inst in ordered:
        char_layer = Image.open(root / inst["asset_used"]).convert("RGBA")
        foot = tuple(inst["ground_contact"]["foot_anchor_px"])
        refl_poly = None
        if inst.get("reflection", {}).get("enabled"):
            refl_poly = surfaces.get(inst["reflection"]["surface"])
            if refl_poly is None:
                raise ValueError(f"{inst['character']}: unknown reflective surface "
                                 f"{inst['reflection']['surface']!r}")
        behind = [occluders[b] for b in inst.get("behind", [])
                  if b in occluders] or None
        missing = [b for b in inst.get("behind", []) if b not in occluders]
        if missing:
            raise ValueError(f"{inst['character']}: unknown occluder(s) {missing}")
        canvas, rep = place_character(
            canvas, char_layer, foot, gp,
            shadow_direction=inst.get("lighting", {}).get("shadow_direction"),
            relight_spec=derive_relight_spec(scene, foot),
            reflection_polygon=refl_poly,
            atmosphere=scene.get("atmosphere"),
            behind_polygons=behind,
            shadow_opacity=inst.get("grounding_boost", {}).get("shadow_opacity"),
            reflection_opacity=inst.get("grounding_boost", {}).get("reflection_opacity"),
            character_height_factor=scene["ground_plane"]["calibration"].get(
                "calib_to_character_factor", 1.0),
        )
        reports[inst["character"]] = rep

    if spec.get("foreground_rain"):
        boxes = [r["paste_box"] for r in reports.values()]
        union = [min(b[0] for b in boxes), min(b[1] for b in boxes),
                 max(b[2] for b in boxes), max(b[3] for b in boxes)]
        canvas = add_foreground_rain(canvas, tuple(union),
                                     density=spec.get("rain_density", 110))

    out_path = spec_dir / "final_integrated.png"
    canvas.convert("RGB").save(out_path)
    return {"characters": reports, "depth_order": [c["character"] for c in ordered],
            "output": str(out_path)}


def run(poc_dir: Path) -> dict:
    scene = json.loads((poc_dir / "scene_blocking.json").read_text(encoding="utf-8"))
    pose = json.loads((poc_dir / "pose_spec.json").read_text(encoding="utf-8"))

    root = Path(__file__).resolve().parents[3]
    plate = Image.open(root / scene["background_plate"]).convert("RGBA")
    char_layer = Image.open(root / pose["asset_used"]).convert("RGBA")
    gp = load_ground_plane(scene)

    foot_anchor = tuple(pose["ground_contact"]["foot_anchor_px"])
    relight_spec = derive_relight_spec(scene, foot_anchor)

    reflection_polygon = None
    refl_req = pose.get("reflection", {})
    if refl_req.get("enabled"):
        surfaces = {s["id"]: s["polygon"] for s in scene.get("reflective_surfaces", [])}
        reflection_polygon = surfaces.get(refl_req.get("surface"))
        if reflection_polygon is None:
            raise ValueError(f"pose_spec requests reflection on surface "
                             f"{refl_req.get('surface')!r} but scene_blocking declares no such surface")

    occluders = {o["id"]: o["polygon"] for o in scene.get("occluders", [])}
    behind = [occluders[b] for b in pose.get("behind", []) if b in occluders] or None
    missing = [b for b in pose.get("behind", []) if b not in occluders]
    if missing:
        raise ValueError(f"pose_spec declares unknown occluder(s) {missing}")

    canvas, report = place_character(
        plate, char_layer, foot_anchor, gp,
        shadow_direction=pose.get("lighting", {}).get("shadow_direction"),
        relight_spec=relight_spec,
        reflection_polygon=reflection_polygon,
        atmosphere=scene.get("atmosphere"),
        behind_polygons=behind,
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
    entry = run_scene if (poc_dir / "characters_spec.json").exists() else run
    print(json.dumps(entry(poc_dir), indent=2))
