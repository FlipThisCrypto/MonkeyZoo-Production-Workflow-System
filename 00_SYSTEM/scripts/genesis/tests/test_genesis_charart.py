"""Tests for the bespoke per-panel art pipeline (offline parts: id map, pose
derivation, HSV backdrop matte). Generation itself needs ComfyUI and is not
unit-tested here."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")
pytest.importorskip("PIL")
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

GEN = Path(__file__).resolve().parents[1]
SCRIPTS = GEN.parents[1]
for p in (str(GEN), str(SCRIPTS), str(SCRIPTS / "integration")):
    if p not in sys.path:
        sys.path.insert(0, p)

import genesis_charart as ca  # noqa: E402


def test_id_map_matches_card_seeds():
    assert ca.ID_MAP["MZ-CHAR-003"] == "static"
    assert ca.ID_MAP["MZ-CHAR-001"] == "moodz"
    assert ca.ID_MAP["MZ-CHAR-006"] == "scarline"


def test_derive_pose_includes_framing_and_emotion():
    p = {"action": "looking up, listening", "emotion": "worried"}
    close = ca.derive_pose(p, "close")
    med = ca.derive_pose(p, "medium")
    assert "close-up" in close and "worried expression" in close
    assert "medium shot" in med and "listening" in med


@pytest.mark.parametrize("bg", [(240, 90, 200), (250, 150, 40), (60, 200, 190), (90, 220, 90)])
def test_hsv_matte_removes_flat_backdrop_keeps_subject(tmp_path, bg):
    # synthetic: saturated flat backdrop + a low-saturation grey subject blob
    im = Image.new("RGB", (160, 200), bg)
    a = np.array(im)
    a[70:170, 50:110] = (110, 110, 110)      # grey "character" in the lower centre
    Image.fromarray(a).save(tmp_path / "c.png")
    ch = ca.key_backdrop(tmp_path / "c.png")
    al = np.asarray(ch)[..., 3]
    assert (al[:8, :8] < 12).all() and (al[:8, -8:] < 12).all(), "corners must be transparent"
    assert al[120, 80] > 200, "the subject blob must stay opaque"
    assert (al > 128).mean() < 0.5, "most of the flat backdrop is removed"
