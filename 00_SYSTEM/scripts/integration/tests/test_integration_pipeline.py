"""Regression tests for the character-integration pipeline (Cycles 1-7).

Run with: python -m pytest 00_SYSTEM/scripts/integration/tests -v
(from the repo root, or point PYTHONPATH at 00_SYSTEM/scripts/integration).

Pins the exact negative-control result from Cycle 7's manual testing so a
future change can't silently reintroduce either of the two bugs found
during that cycle (fragmented-card false negative, neon-sign false
positive) without a test catching it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alpha_matte import extract  # noqa: E402
from perspective import GroundPlane  # noqa: E402
from shadow import draw_contact_shadow  # noqa: E402
from validate_integration import run_gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
# renamed P01_PANEL01 -> P01_PANEL03 by the 16-page/96-panel decompression (same locked beat)
POC_DIR = ROOT / "00_SYSTEM" / "integration_upgrade" / "poc" / "MZ-2026-09-02_P01_PANEL03"
BEFORE_IMG = ROOT / "02_MONTHLY_ISSUES" / "2026-09_Issue_02" / "generated_art" / \
    "selected_panels" / "MZ-2026-09-02_P01_PANEL01.png"


# ---------------------------------------------------------------------------
# alpha_matte
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("char", ["static", "scarline", "ash"])
def test_alpha_matte_corners_transparent(tmp_path, char):
    src = ROOT / "03_APPROVED_CANON" / "approved_characters" / char / f"{char}_00_clean_base.png"
    if not src.exists():
        pytest.skip(f"fixture missing: {src}")
    dst = tmp_path / f"{char}.png"
    report = extract(src, dst)
    assert report["corners_fully_transparent"]
    assert 0.15 <= report["opaque_frac"] <= 0.60


def test_alpha_matte_preserves_enclosed_similar_color(tmp_path):
    """Scarline's fur is nearly the same grey as her backdrop -- the
    border-connected flood fill must keep it (this was the adversarial
    case verified visually in Cycle 2)."""
    src = ROOT / "03_APPROVED_CANON" / "approved_characters" / "scarline" / "scarline_00_clean_base.png"
    if not src.exists():
        pytest.skip(f"fixture missing: {src}")
    dst = tmp_path / "scarline.png"
    extract(src, dst)
    out = np.array(Image.open(dst))
    center = out[out.shape[0] // 2 - 20:out.shape[0] // 2 + 20, out.shape[1] // 2 - 20:out.shape[1] // 2 + 20]
    assert (center[..., 3] > 200).mean() > 0.5, "character center should stay opaque"


# ---------------------------------------------------------------------------
# perspective
# ---------------------------------------------------------------------------

def test_ground_plane_height_scales_with_depth():
    gp = GroundPlane(horizon_y=200, calib_y=500, calib_height_px=100)
    near = gp.height_at(600)
    far = gp.height_at(300)
    assert near > far > 0, "objects closer to the camera (larger y) must appear taller"


def test_ground_plane_round_trip():
    gp = GroundPlane(horizon_y=200, calib_y=500, calib_height_px=100)
    h = gp.height_at(450)
    y = gp.foot_y_for_height(h)
    assert abs(y - 450) < 1e-6


def test_ground_plane_rejects_above_horizon():
    gp = GroundPlane(horizon_y=200, calib_y=500, calib_height_px=100)
    with pytest.raises(ValueError):
        gp.height_at(100)


# ---------------------------------------------------------------------------
# shadow
# ---------------------------------------------------------------------------

def test_contact_shadow_darkens_ground():
    canvas = Image.new("RGBA", (200, 200), (180, 180, 180, 255))
    out = draw_contact_shadow(canvas, foot_anchor_px=(100, 150), character_width_px=60)
    before = np.array(canvas.convert("RGB"))[140:150, 80:120].mean()
    after = np.array(out.convert("RGB"))[140:150, 80:120].mean()
    assert after < before, "shadow must darken the ground near the foot anchor"


# ---------------------------------------------------------------------------
# validate_integration -- pinned negative control from Cycle 7
# ---------------------------------------------------------------------------

def test_qa_gate_fails_on_known_bad_pasted_card():
    if not BEFORE_IMG.exists():
        pytest.skip(f"fixture missing: {BEFORE_IMG}")
    result = run_gate(BEFORE_IMG, foot_anchor_px=(300, 640))
    assert result["verdict"] == "FAIL"
    assert result["known_bad_color_regions_found"] > 0, \
        "must catch the literal pasted NFT card by color signature"


def test_qa_gate_passes_on_integrated_poc():
    final = POC_DIR / "04_final_integrated.png"
    if not final.exists():
        pytest.skip(f"fixture missing: {final} -- run compositor.py first")
    result = run_gate(final, foot_anchor_px=(300, 640))
    assert result["verdict"] == "PASS", result["fail_reasons"]


# ---------------------------------------------------------------------------
# identity_check -- calibrated against the real Cycle-13 drift renders
# ---------------------------------------------------------------------------

LAYERS = ROOT / "00_SYSTEM" / "integration_upgrade" / "character_layers"
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("char", ["static", "scarline", "moodz"])
def test_identity_check_passes_canon_layers(char):
    from identity_check import check_identity
    layer = LAYERS / char / f"{char}_00_clean_base.png"
    if not layer.exists():
        pytest.skip(f"fixture missing: {layer}")
    r = check_identity(layer, char)
    assert r["verdict"] == "PASS" and r["identity_score"] >= 0.95


def test_identity_check_passes_cross_pose():
    from identity_check import check_identity
    layer = LAYERS / "static" / "static_16_worried.png"
    if not layer.exists():
        pytest.skip(f"fixture missing: {layer}")
    assert check_identity(layer, "static")["verdict"] == "PASS"


# ---------------------------------------------------------------------------
# behind-geometry occlusion
# ---------------------------------------------------------------------------

def test_repaint_occluders_restores_plate_inside_polygon():
    from compositor import repaint_occluders
    from PIL import Image
    import numpy as np
    plate = Image.new("RGBA", (100, 100), (0, 200, 0, 255))
    canvas = plate.copy()
    canvas.paste(Image.new("RGBA", (40, 40), (255, 0, 0, 255)), (30, 30))  # "character"
    out = np.array(repaint_occluders(canvas, plate, [[(30, 30), (70, 30), (70, 70), (30, 70)]]))
    assert tuple(out[50, 50][:3]) == (0, 200, 0), "occluder region must show plate again"
    assert tuple(np.array(canvas)[50, 50][:3]) == (255, 0, 0), "input canvas must be untouched"


def test_run_rejects_unknown_occluder(tmp_path):
    import json as _json
    from compositor import run
    import shutil
    src = ROOT / "00_SYSTEM" / "integration_upgrade" / "poc" / "MZ-2026-09-02_P01_PANEL03"
    if not src.exists():
        pytest.skip("POC dir missing")
    work = tmp_path / "panel"
    shutil.copytree(src, work)
    pose = _json.loads((work / "pose_spec.json").read_text(encoding="utf-8"))
    pose["behind"] = ["no-such-object"]
    (work / "pose_spec.json").write_text(_json.dumps(pose), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown occluder"):
        run(work)


# ---------------------------------------------------------------------------
# haze
# ---------------------------------------------------------------------------

def test_haze_zero_at_calibration_depth_and_nearer():
    from haze import depth_haze_factor
    assert depth_haze_factor(490, 330, 490, 0.55) == 0.0
    assert depth_haze_factor(640, 330, 490, 0.55) == 0.0  # nearer than calib


def test_haze_grows_toward_horizon():
    from haze import depth_haze_factor
    mid = depth_haze_factor(410, 330, 490, 0.55)
    deep = depth_haze_factor(350, 330, 490, 0.55)
    assert 0 < mid < deep <= 0.55


def test_haze_shifts_colors_toward_haze_color():
    from haze import apply_haze
    from PIL import Image
    import numpy as np
    layer = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    out = np.array(apply_haze(layer, 0.5, (76, 80, 103)))
    assert abs(int(out[5, 5, 0]) - 165) <= 2  # 255*0.5 + 76*0.5
    assert out[5, 5, 3] == 255  # alpha untouched


@pytest.mark.parametrize("seed", [777001, 777011])
def test_identity_check_fails_beige_drift(seed):
    """The actual failed renders from Cycle 13 -- the exact drift class
    this check exists to catch. If a tolerance change makes these pass,
    the check has regressed to useless."""
    from identity_check import check_identity
    fixture = FIXTURES / f"drift_static_seed{seed}.png"
    if not fixture.exists():
        pytest.skip(f"fixture missing: {fixture}")
    r = check_identity(fixture, "static")
    assert r["verdict"] == "FAIL", f"drift render scored {r['identity_score']} -- tolerances too loose"
