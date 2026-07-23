"""Tests for the Genesis duplicate detector: perceptual hash + crop variants."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("numpy")
pytest.importorskip("PIL")
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

GEN = Path(__file__).resolve().parents[1]
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))

import genesis_dupes as gd  # noqa: E402


def test_dhash_identical_images_zero_distance():
    im = Image.new("RGB", (128, 72))
    for x in range(128):
        for y in range(72):
            im.putpixel((x, y), (x * 2 % 256, y * 3 % 256, 0))
    a, b = gd.dhash(im), gd.dhash(im)
    assert gd.hamming(a, b) == 0


def test_dhash_distinguishes_different_images():
    a = gd.dhash(Image.new("RGB", (128, 72), (0, 0, 0)))
    # a left-to-right gradient has many bright-to-dark transitions
    grad = Image.new("RGB", (128, 72))
    for x in range(128):
        for y in range(72):
            grad.putpixel((x, y), (x * 2 % 256,) * 3)
    b = gd.dhash(grad)
    assert gd.hamming(a, b) > 0


def test_hamming_symmetric_and_bounded():
    a = np.array([True, False, True, False])
    b = np.array([True, True, False, False])
    assert gd.hamming(a, b) == gd.hamming(b, a) == 2


def test_crop_variants_first_is_full_frame():
    assert gd.CROP_VARIANTS[0] == (0.0, 0.0, 1.0, 1.0)
    # every variant is a valid (L,T,R,B) box inside the unit square
    for (l, t, r, b) in gd.CROP_VARIANTS:
        assert 0.0 <= l < r <= 1.0 and 0.0 <= t < b <= 1.0


def test_crop_variants_are_distinct():
    assert len(set(gd.CROP_VARIANTS)) == len(gd.CROP_VARIANTS)
