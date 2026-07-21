"""Stage-8 lettering unit tests (assemble_pages.py).

The module loads fonts at import; it now degrades gracefully when the
Windows fonts are absent, so it is importable (and these tests run) on any
platform / CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

pytest.importorskip("PIL")
import assemble_pages as ap  # noqa: E402


@pytest.mark.parametrize("marker", ["—", "–", "-", "―", "", "   ", " — ", "--"])
def test_none_markers_are_blank_and_draw_nothing(marker):
    """The scripts use "—" (and blanks/dashes) as the empty-field marker;
    these must NOT produce a literal em-dash bubble/caption/SFX."""
    assert ap._is_blank(marker) is True
    assert ap.parse_dialogue(marker) == []


def _draw():
    from PIL import Image, ImageDraw
    return ImageDraw.Draw(Image.new("RGB", (10, 10)))


def test_wrap_normal_text_stays_within_width():
    d = _draw()
    for line in ap.wrap(d, "the city creaks and the signal repeats twice", ap.F_BUBBLE, 300):
        assert d.textbbox((0, 0), line, font=ap.F_BUBBLE)[2] <= 300


def test_wrap_hard_breaks_an_unbreakable_token():
    # a token longer than the balloon must be split so no line overflows the panel
    d = _draw()
    lines = ap.wrap(d, "A" * 60, ap.F_BUBBLE, 300)
    assert len(lines) > 1
    assert "".join(lines) == "A" * 60                       # no characters lost
    assert all(d.textbbox((0, 0), line, font=ap.F_BUBBLE)[2] <= 300 for line in lines)


def test_wrap_mixes_words_and_a_long_token_without_overflow():
    d = _draw()
    lines = ap.wrap(d, "look at this " + "Z" * 50 + " now", ap.F_BUBBLE, 300)
    assert all(d.textbbox((0, 0), line, font=ap.F_BUBBLE)[2] <= 300 for line in lines)
    assert "".join(lines).replace(" ", "").count("Z") == 50  # the token survives intact


def test_real_dialogue_is_not_blank():
    assert ap._is_blank("STATIC: hello") is False
    assert ap._is_blank("BZZT") is False


def test_unquoted_dialogue_preserved_inline():
    assert ap.parse_dialogue("STATIC: That click repeated.") == [("", "STATIC: That click repeated.")]


def test_quoted_dialogue_splits_speaker():
    assert ap.parse_dialogue('SCARLINE: "Don\'t drown him out."') == [("SCARLINE", "Don't drown him out.")]


def test_multiple_balloons_split_and_drop_blank_parts():
    assert ap.parse_dialogue("MOODZ: hey / STATIC: yeah") == [("", "MOODZ: hey"), ("", "STATIC: yeah")]
    # a trailing/again em-dash part is dropped, real ones kept
    assert ap.parse_dialogue("MOODZ: hey / —") == [("", "MOODZ: hey")]


# --- compute_slots: page layout geometry (regression for the empty-page crash) ---

def test_compute_slots_empty_page_returns_no_slots_no_crash():
    # a non-splash page with zero panels previously hit `usable_h // 0`
    # (ZeroDivisionError) and aborted the whole Stage-8 run
    assert ap.compute_slots("grid", 0) == []


def test_compute_slots_splash_is_one_full_bleed_slot():
    assert ap.compute_slots("splash", 0) == [(0, 0, ap.PAGE_W, ap.PAGE_H)]
    # splash ignores panel count -- always one full-bleed slot
    assert ap.compute_slots("splash", 5) == [(0, 0, ap.PAGE_W, ap.PAGE_H)]


def test_compute_slots_grid_partitions_page_within_margins():
    slots = ap.compute_slots("grid", 3)
    assert len(slots) == 3
    for (sx, sy, sw, shh) in slots:
        assert sx == ap.MARGIN
        assert sw == ap.PAGE_W - 2 * ap.MARGIN
        assert shh > 0
        assert sy >= ap.MARGIN
        assert sy + shh <= ap.PAGE_H  # stays on the page
    # slots are stacked top-to-bottom, non-overlapping
    tops = [s[1] for s in slots]
    assert tops == sorted(tops)
    assert slots[1][1] >= slots[0][1] + slots[0][3]


# --- fit_cover robustness: a bad crop window must never crash the page build ---

@pytest.mark.parametrize("crop", [
    None,
    (0.1, 0.1, 0.9, 0.9),          # normal
    (0.5, 0.5, 0.5, 0.5),          # degenerate (zero area) -> used to ZeroDivisionError
    (0.9, 0.1, 0.1, 0.9),          # inverted L>R -> used to raise "right < left"
    (-0.5, 0.0, 1.5, 1.0),         # out of [0,1]
    (0.0, 0.9, 1.0, 0.1),          # inverted T>B
])
def test_fit_cover_never_crashes_and_returns_slot_size(crop):
    from PIL import Image
    out = ap.fit_cover(Image.new("RGB", (200, 200), "white"), 128, 96, crop)
    assert out.size == (128, 96)


def test_fit_cover_normal_crop_matches_previous_behaviour():
    # a valid window still crops then covers to the slot (regression guard)
    from PIL import Image
    src = Image.new("RGB", (400, 300), "white")
    assert ap.fit_cover(src, 160, 90, (0.25, 0.25, 0.75, 0.75)).size == (160, 90)
