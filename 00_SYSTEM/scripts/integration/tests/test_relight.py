"""Characterization tests for the environmental relight pass (compositor step).

relight() recolors a flat cel-shaded character layer to sit in the scene's
light WITHOUT touching alpha or redrawing linework -- that alpha/identity
guarantee is the whole reason this pass exists instead of a full regen. It is
live (compositor.py imports it) yet had no tests. Pin the contracts that are
easy to break silently: exact alpha preservation, shape/mode invariance,
determinism, the deliberate exposure clamp (darken-only, never brighten), and
the directional key/fill tint.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")
pytest.importorskip("PIL")

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from relight import _match_ambient_exposure, relight  # noqa: E402


def _char(rgb=(180, 180, 180), size=(40, 30), alpha_pattern="disc"):
    """An RGBA character sprite: solid rgb over a soft-ish alpha shape so there
    are opaque, edge, and transparent pixels for the pass to act on."""
    w, h = size
    a = np.zeros((h, w), dtype=np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    if alpha_pattern == "disc":
        r = min(w, h) / 2 - 2
        a[((xx - w / 2) ** 2 + (yy - h / 2) ** 2) <= r * r] = 255
    else:  # full
        a[:] = 255
    arr = np.dstack([np.full((h, w), rgb[0], np.uint8),
                     np.full((h, w), rgb[1], np.uint8),
                     np.full((h, w), rgb[2], np.uint8), a])
    return Image.fromarray(arr, "RGBA")


def test_alpha_channel_is_preserved_exactly():
    src = _char()
    src_alpha = np.array(src)[..., 3].copy()
    out_alpha = np.array(relight(src, ambient_luma=120.0))[..., 3]
    # the core identity guarantee: not one alpha value may move
    assert np.array_equal(out_alpha, src_alpha)


def test_output_shape_and_mode_invariant():
    src = _char(size=(50, 25))
    out = relight(src, ambient_luma=120.0)
    assert out.mode == "RGBA"
    assert out.size == src.size
    assert np.array(out).shape == np.array(src).shape


def test_relight_is_deterministic():
    src = _char()
    a = np.array(relight(src, ambient_luma=90.0))
    b = np.array(relight(src, ambient_luma=90.0))
    assert np.array_equal(a, b)


def test_exposure_darkens_a_character_brighter_than_the_scene():
    # bright sprite (luma ~250) dropped into a dark scene (ambient 40) must dim
    rgb = np.full((10, 10, 3), 250, np.float32)
    alpha = np.full((10, 10), 255, np.uint8)
    out = _match_ambient_exposure(rgb.copy(), alpha, ambient_luma=40.0)
    assert out.mean() < rgb.mean()
    assert out.mean() >= rgb.mean() * 0.35 - 1   # never below the 0.35 floor


def test_exposure_never_brightens_a_dark_character():
    # factor is clipped at 1.0, so a dark sprite in a bright scene is left as-is
    rgb = np.full((10, 10, 3), 40, np.float32)
    alpha = np.full((10, 10), 255, np.uint8)
    out = _match_ambient_exposure(rgb.copy(), alpha, ambient_luma=250.0)
    assert np.array_equal(out, rgb)


def test_exposure_noops_when_nothing_is_opaque():
    rgb = np.full((8, 8, 3), 200, np.float32)
    alpha = np.zeros((8, 8), np.uint8)          # fully transparent -> no opaque pixels
    out = _match_ambient_exposure(rgb.copy(), alpha, ambient_luma=50.0)
    assert np.array_equal(out, rgb)


def test_directional_tint_puts_key_colour_on_the_high_side():
    # horizontal gradient, key on high side: the right half should pick up more
    # of the bluish key colour than the magenta-ish fill on the left half.
    src = _char(rgb=(128, 128, 128), size=(60, 20), alpha_pattern="full")
    out = np.array(relight(src, ambient_luma=128.0,
                           key_color=(120, 210, 255), fill_color=(230, 90, 170)))
    blue = out[..., 2].astype(np.float32)
    left_blue = blue[:, :30].mean()
    right_blue = blue[:, 30:].mean()
    assert right_blue > left_blue
