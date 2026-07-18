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
