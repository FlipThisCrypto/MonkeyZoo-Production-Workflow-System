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
