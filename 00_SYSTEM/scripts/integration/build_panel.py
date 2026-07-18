"""One-command panel builder for the 96-panel integration effort.

Author a small per-panel spec JSON and call:
    python build_panel.py <spec.json>
It resolves the location's calibrated scene, builds the panel by type
(establish / closeup / scene), stages it into the issue preview, runs the
pixel gate, and prints a JSON result. Agents author specs; this handles
all compositor/closeup/staging boilerplate and the gate call.

Spec schema:
{
  "panel_id": "MZ-2026-09-02_P05_PANEL02",
  "type": "scene" | "closeup" | "establish",
  "location": "Transit Announcement Hub",
  "foreground_rain": false,            # scene only
  "rain_density": 90,                  # scene only, optional
  # type == scene:
  "characters": [
    {"character": "static", "pose_file": "...png", "foot_anchor": [520,565],
     "shadow": "down-left", "reflection_surface": "glossy_floor_full",
     "boost": {"shadow_opacity": 0.55}, "note": ""}
  ],
  # type == closeup:
  "closeup": {"character": "static", "pose_file": "...png",
              "crop_box": [520,150,1160,510], "char_x_frac": 0.5,
              "head_window": [0.05,0.60]},
  # type == establish: nothing extra (plate is the panel), optional "darken"
  "establish": {"darken": 1.0}
}
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image, ImageEnhance  # noqa: E402
from compositor import run_scene  # noqa: E402
from closeup import closeup_panel  # noqa: E402
from validate_integration import run_gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ISSUE = ROOT / "02_MONTHLY_ISSUES" / "2026-09_Issue_02"
POC = ROOT / "00_SYSTEM" / "integration_upgrade" / "poc"
PREVIEW = ISSUE / "generated_art" / "integration_preview"

# location -> (calibrated scene_blocking template, plate)
LOC = {
    "Zoo City Streets": ("MZ-2026-09-02_P01_PANEL03",
                         "03_APPROVED_CANON/approved_locations/zoo-city-streets/primary-reference.png"),
    "School / Public Address Zone": ("MZ-2026-09-02_P01_PANEL06",
                         "03_APPROVED_CANON/approved_locations/school-pa-zone/primary-reference.png"),
    "Transit Announcement Hub": ("MZ-2026-09-02_P04_PANEL05",
                         "03_APPROVED_CANON/approved_locations/transit-announcement-hub/primary-reference.png"),
    "Early-Fall Storm Streets and Routine Nodes": ("MZ-2026-09-02_P03_PANEL02",
                         "03_APPROVED_CANON/approved_locations/storm-routines/primary-reference.png"),
    "Old Relay Junction": ("MZ-2026-09-02_P13_PANEL06",
                         "03_APPROVED_CANON/approved_locations/old-relay-junction/primary-reference.png"),
}


def _plate(location):
    return ROOT / LOC[location][1]


def _scene_template(location):
    return POC / LOC[location][0] / "scene_blocking.json"


def build_establish(spec):
    plate = Image.open(_plate(spec["location"])).convert("RGB")
    dk = spec.get("establish", {}).get("darken", 1.0)
    if dk != 1.0:
        plate = ImageEnhance.Brightness(plate).enhance(dk)
    out = PREVIEW / f"{spec['panel_id']}.png"
    plate.save(out)
    return out, True  # skip flat-region gate


def build_closeup(spec):
    c = spec["closeup"]
    kw = {}
    if "char_x_frac" in c: kw["char_x_frac"] = c["char_x_frac"]
    if "head_window" in c: kw["head_window"] = tuple(c["head_window"])
    img = closeup_panel(ROOT / c["pose_file"], _plate(spec["location"]),
                        tuple(c["crop_box"]), **kw)
    out = PREVIEW / f"{spec['panel_id']}.png"
    img.save(out)
    return out, True  # close-up: skip flat-region gate


def build_scene(spec):
    pid = spec["panel_id"]
    d = POC / pid
    d.mkdir(exist_ok=True)
    sc = json.loads(_scene_template(spec["location"]).read_text(encoding="utf-8"))
    sc["panel_id"] = pid
    (d / "scene_blocking.json").write_text(json.dumps(sc, indent=2), encoding="utf-8")
    chars = []
    for c in spec["characters"]:
        entry = {"character": c["character"], "asset_used": c["pose_file"],
                 "asset_note": c.get("note", ""),
                 "ground_contact": {"surface": c.get("surface", "per scene"),
                                    "foot_anchor_px": list(c["foot_anchor"])},
                 "lighting": {"shadow_direction": c.get("shadow", "down-left")}}
        if c.get("reflection_surface"):
            entry["reflection"] = {"enabled": True, "surface": c["reflection_surface"]}
        if c.get("boost"):
            entry["grounding_boost"] = c["boost"]
        chars.append(entry)
    cspec = {"panel_id": pid, "source_script_line": spec.get("action", ""),
             "foreground_rain": spec.get("foreground_rain", False),
             "rain_density": spec.get("rain_density", 90), "characters": chars}
    (d / "characters_spec.json").write_text(json.dumps(cspec, indent=2), encoding="utf-8")
    rep = run_scene(d)
    out = PREVIEW / f"{pid}.png"
    shutil.copyfile(d / "final_integrated.png", out)
    return out, False, rep


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    t = spec["type"]
    # Validate the location up front: the build_* helpers index LOC[location]
    # and would otherwise raise a bare KeyError before the line-136 guard runs.
    if spec.get("location") not in LOC:
        raise ValueError(
            f"unknown location {spec.get('location')!r}; calibrated locations are {sorted(LOC)}")
    rep = None
    if t == "establish":
        out, skip_flat = build_establish(spec)
    elif t == "closeup":
        out, skip_flat = build_closeup(spec)
    elif t == "scene":
        out, skip_flat, rep = build_scene(spec)
    else:
        raise ValueError(f"unknown type {t!r}")

    plate = _plate(spec["location"]) if spec["location"] in LOC else None
    gate = run_gate(out, plate_path=plate, skip_flat_regions=skip_flat)
    result = {"panel_id": spec["panel_id"], "type": t, "output": str(out),
              "gate": gate["verdict"], "fail_reasons": gate["fail_reasons"]}
    if rep:
        result["characters"] = {k: {"h": v["target_height_px"],
                                    "refl": bool(v.get("reflection"))}
                                for k, v in rep["characters"].items()}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main(sys.argv[1])
