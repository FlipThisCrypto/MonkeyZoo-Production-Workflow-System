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


def test_clever_in_id_map_and_prompt_has_identity():
    assert ca.ID_MAP["MZ-CHAR-CLEVER"] == "clever"
    for token in ("glasses", "ponytail", "olive", "blue", "red shorts"):
        assert token in ca.CLEVER_PROMPT.lower()


def test_fit_char_size_clamps_to_max_width_and_keeps_aspect():
    # in a tall/narrow cell, height-based sizing would be too wide -> clamp to max_w
    tw, th = ca._fit_char_size(cw=800, chh=1000, H=1280, scale_h=0.8, max_w=500)
    assert tw == 500
    assert abs(th - round(1000 * 500 / 800)) <= 1     # aspect preserved


def test_fit_char_size_uses_height_when_uncapped():
    tw, th = ca._fit_char_size(cw=800, chh=1000, H=540, scale_h=0.8, max_w=None)
    assert th == int(540 * 0.8)
    assert tw == round(800 * th / 1000)


def test_compose_multi_returns_band_size_with_two_characters(tmp_path):
    loc = "Zoo City Streets"
    if not (ca.FACTORY / ca.PLATES[loc]).exists():
        pytest.skip("plate missing")
    a = Image.new("RGBA", (200, 300), (0, 0, 0, 0)); a.paste((120, 120, 120, 255), (60, 120, 140, 300))
    b = Image.new("RGBA", (200, 300), (0, 0, 0, 0)); b.paste((90, 90, 90, 255), (60, 140, 140, 300))
    out = ca.compose_multi(loc, [(a, 0.27, 0.80), (b, 0.71, 0.74)], band_px=(1280, 540))
    assert out.size == (1280, 540) and out.mode == "RGB"


def test_green_bg_override_targets_fur_conflict_chars_only():
    # moodz (orange card = fur hue) and scarline (grey card = unkeyable) get a
    # hue-safe green backdrop for generation; proven hue-safe cards are untouched
    assert ca.GREEN_BG_CHARS == {"moodz", "scarline"}
    assert "static" not in ca.GREEN_BG_CHARS and "twotone" not in ca.GREEN_BG_CHARS
    assert "green" in ca.CHROMA_BG.lower()


def test_matte_keeps_brown_fur_body_on_green_backdrop(tmp_path):
    # the original bug: on an orange card the key ate brown fur and left a floating
    # head. On the green backdrop the whole body (head + neck + torso) must survive.
    im = Image.new("RGB", (160, 200), (0, 200, 0))       # chroma green
    a = np.array(im)
    a[30:80, 55:105] = (120, 72, 48)                     # brown head
    a[80:95, 72:88] = (120, 72, 48)                      # slim brown neck
    a[95:180, 45:115] = (120, 72, 48)                    # brown torso
    Image.fromarray(a).save(tmp_path / "m.png")
    al = np.asarray(ca.key_backdrop(tmp_path / "m.png"))[..., 3]
    assert al[50, 80] > 200, "head kept"
    assert al[140, 80] > 200, "torso kept (not a floating head)"
    assert (al[:8, :8] < 12).all() and (al[:8, -8:] < 12).all(), "green backdrop removed"


def test_matte_drops_painted_ground_platform(tmp_path):
    # the model sometimes paints a solid floor slab under the feet; it must be cut
    # so it doesn't composite as a pale rectangle beneath the character
    im = Image.new("RGB", (160, 220), (0, 200, 0))
    a = np.array(im)
    a[30:150, 55:105] = (120, 72, 48)        # narrow character body
    a[150:220, 0:160] = (95, 92, 98)         # full-width floor slab at the bottom
    Image.fromarray(a).save(tmp_path / "f.png")
    al = np.asarray(ca.key_backdrop(tmp_path / "f.png"))[..., 3]
    assert al[90, 80] > 200, "character body kept"
    assert (al[210, :] < 40).all(), "full-width floor slab removed"


def test_matte_keeps_wide_head_when_character_framed_large(tmp_path):
    # a large-in-frame character can span ~0.9 width at the head; that mid-frame wide
    # row must NOT be cut as floor (the bug that sliced a flat line across the head)
    im = Image.new("RGB", (200, 240), (0, 200, 0))
    a = np.array(im)
    a[20:110, 10:190] = (120, 72, 48)        # very wide head near the top (mid-frame)
    a[110:210, 70:130] = (120, 72, 48)       # narrower body/legs below
    Image.fromarray(a).save(tmp_path / "h.png")
    al = np.asarray(ca.key_backdrop(tmp_path / "h.png"))[..., 3]
    assert al[60, 100] > 200, "wide head kept"
    assert al[35, 100] > 200, "top of head intact (no horizontal slice)"
    assert al[160, 100] > 200, "body kept"


def test_matte_keeps_legs_below_a_wide_hip_row(tmp_path):
    # elbows-out hip pose: a near-full-width row mid-lower-body, with narrow legs/feet
    # reaching the bottom. The floor scan starts at the (narrow) feet and must cut
    # nothing -- the bug sliced the legs off at the wide hip row (Moodz/Neonblue).
    im = Image.new("RGB", (200, 260), (0, 200, 0))
    a = np.array(im)
    a[20:120, 60:140] = (120, 72, 48)        # head + torso
    a[120:150, 6:194] = (120, 72, 48)        # WIDE hips/elbows (0.94 width)
    a[150:250, 82:118] = (120, 72, 48)       # narrow legs + feet down to the bottom
    Image.fromarray(a).save(tmp_path / "e.png")
    al = np.asarray(ca.key_backdrop(tmp_path / "e.png"))[..., 3]
    assert al[135, 100] > 200, "wide hips kept"
    assert al[240, 100] > 200, "legs/feet kept (floor scan stopped at the narrow feet)"


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
