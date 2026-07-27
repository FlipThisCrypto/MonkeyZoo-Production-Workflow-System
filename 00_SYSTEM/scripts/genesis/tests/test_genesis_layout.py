"""Tests for the scene/page-custom layout synthesizer.

The synth must preserve reading order, cover the content box, keep 16:9 KEEP
panels in wide (landscape) slots, and give bespoke character beats varied slot
shapes so pages aren't a uniform stack of identical bands.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")
GEN = Path(__file__).resolve().parents[1]
SCRIPTS = GEN.parents[1]
for p in (str(GEN), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import genesis_layout as gl  # noqa: E402


def _wide(cid="MZ-CHAR-003"):
    return {"source_panel_id": "P", "shot": "wide", "characters": [cid]}


def _solo(cid="MZ-CHAR-003", shot="medium"):
    return {"source_panel_id": "P", "shot": shot, "characters": [cid]}


def _duo(shot="medium"):
    return {"source_panel_id": "P", "shot": shot, "characters": ["MZ-CHAR-003", "MZ-CHAR-CLEVER"]}


def _trio(shot="medium"):
    return {"source_panel_id": "P", "shot": shot,
            "characters": ["MZ-CHAR-003", "MZ-CHAR-CLEVER", "MZ-CHAR-001"]}


def _establishing():
    return {"source_panel_id": "P", "shot": "wide", "characters": []}


def test_is_flex_only_for_recipe_close_medium():
    assert gl.is_flex(_solo(shot="close"))
    assert gl.is_flex(_solo(shot="medium"))
    assert not gl.is_flex(_solo(shot="wide"))            # wide beat -> band
    assert not gl.is_flex(_establishing())               # zero-char -> band
    assert not gl.is_flex({"shot": "close", "characters": ["MZ-CHAR-XYZ"]})  # no recipe


def test_rects_count_matches_panels():
    for n in range(1, 7):
        panels = [_solo() for _ in range(n)]
        assert len(gl.synth_page_rects(panels, 3)) == n


def test_single_panel_is_full_content_box():
    (x, y, w, h) = gl.synth_page_rects([_solo()], 1)[0]
    assert x == gl.MARGIN and y == gl.MARGIN
    assert w == gl.CONTENT_W and h == gl.CONTENT_H


def test_reading_order_top_to_bottom_then_left_to_right():
    # two solo flex beats pair into a 2-up (same row), the rest stack below
    panels = [_solo(), _solo(), _establishing()]
    r = gl.synth_page_rects(panels, 3)
    # panels 0 and 1 share a row (same y band), panel 0 left of panel 1
    assert abs(r[0][1] - r[1][1]) < 5 and r[0][0] < r[1][0]
    # panel 2 is below the pair
    assert r[2][1] > r[0][1]


def test_two_solo_flex_pair_into_a_two_up_row():
    r = gl.synth_page_rects([_solo(), _solo()], 4)
    # not full width -> genuine columns, and both narrower than a full band
    assert r[0][2] < gl.CONTENT_W and r[1][2] < gl.CONTENT_W


def test_three_char_beat_stays_full_width_band():
    # a 3-character staged beat has no room in a half cell -> full-width row
    r = gl.synth_page_rects([_trio(), _establishing()], 2)
    assert r[0][2] == gl.CONTENT_W, "a 3-character staged beat keeps a full band"


def test_two_char_bespoke_beats_can_pair_into_a_two_up():
    # bespoke 2-char beats are generated to fit, so they may share a 2-up row
    r = gl.synth_page_rects([_duo(), _duo()], 2)
    assert abs(r[0][1] - r[1][1]) < 5 and r[0][0] < r[1][0]
    assert r[0][2] < gl.CONTENT_W and r[1][2] < gl.CONTENT_W


def test_only_bespoke_flex_panels_ever_get_a_sub_full_width_slot():
    # a 16:9 KEEP/establishing panel must never land in a narrow cell (it would
    # be side-clipped); only flex/bespoke panels may be narrower than full width
    panels = [_establishing(), _duo(), _duo(), _trio(), _solo(), _solo()]
    for pa, (x, y, w, h) in zip(panels, gl.synth_page_rects(panels, 4)):
        if w < gl.CONTENT_W - 2:
            assert gl.is_flex(pa), "only bespoke flex art may occupy a narrow cell"


def test_wide_keep_panels_are_landscape_full_width():
    r = gl.synth_page_rects([_establishing(), _establishing()], 2)
    for (x, y, w, h) in r:
        assert w == gl.CONTENT_W and w > h, "KEEP/wide panels stay wide full-width bands"


def test_layout_has_size_variety_not_uniform():
    # a mixed page should not collapse to one repeated slot size
    panels = [_establishing(), _solo(), _solo(), _duo()]
    r = gl.synth_page_rects(panels, 5)
    sizes = {(w, h) for (x, y, w, h) in r}
    assert len(sizes) >= 3, "panels must vary in size, not be near-identical"


def test_rects_stay_within_the_page():
    panels = [_establishing(), _solo(), _solo(), _duo(), _solo(), _solo()]
    for (x, y, w, h) in gl.synth_page_rects(panels, 7):
        assert x >= 0 and y >= 0 and w > 0 and h > 0
        assert x + w <= gl.PAGE_W + 2 and y + h <= gl.PAGE_H + 2


def test_slot_band_px_preserves_aspect_and_caps_long_edge():
    assert gl.slot_band_px((0, 0, 2000, 1000)) == (1280, 640)      # landscape
    assert gl.slot_band_px((0, 0, 800, 1600)) == (640, 1280)       # portrait
    bw, bh = gl.slot_band_px((0, 0, 1000, 1000))
    assert bw == 1280 and bh == 1280 and bw % 2 == 0               # square, even
