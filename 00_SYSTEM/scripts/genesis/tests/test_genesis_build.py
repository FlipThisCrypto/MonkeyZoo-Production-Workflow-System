"""Tests for the Genesis assembler: dialogue splitting + template geometry."""
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

import genesis_build as gb  # noqa: E402


# --- speaker splitting ---

def test_split_pulls_speaker_prefix_out_of_balloon():
    assert gb.split_dialogue("NEONBLUE: Hey, the city creaks!") == [("NEONBLUE", "Hey, the city creaks!")]


def test_split_strips_delivery_parenthetical_from_speaker():
    assert gb.split_dialogue("STATIC (small): Nobody else stopped.") == [("STATIC", "Nobody else stopped.")]


def test_split_blank_marker_is_empty():
    assert gb.split_dialogue("—") == []
    assert gb.split_dialogue("") == []


def test_split_multiple_balloons():
    assert gb.split_dialogue("MOODZ: You heard it. / STATIC: Yeah.") == [
        ("MOODZ", "You heard it."), ("STATIC", "Yeah.")]


def test_split_unattributed_line_keeps_text():
    assert gb.split_dialogue("the city hums") == [("", "the city hums")]


# --- template geometry ---

@pytest.mark.parametrize("template,count", [
    ("grid4", 4), ("feature_top3", 4), ("feature_left3", 4), ("grid6", 6),
    ("feature_top5", 6), ("grid5", 5), ("feature_top4", 5), ("left_feature4", 5),
    ("feature_left2", 3), ("row3", 3), ("stack2", 2), ("splash", 1),
])
def test_template_yields_correct_count_within_bounds(template, count):
    rects = gb.template_rects(template, count)
    assert len(rects) == count
    for (x, y, w, h) in rects:
        assert w > 0 and h > 0
        assert x >= 0 and y >= 0
        assert x + w <= gb.PAGE_W + 2 and y + h <= gb.PAGE_H + 2


def test_feature_template_slot0_is_the_largest():
    rects = gb.template_rects("feature_left3", 4)
    areas = [w * h for (x, y, w, h) in rects]
    assert areas[0] == max(areas), "feature/emphasis slot 0 must be the largest panel"


def test_unknown_template_falls_back_to_even_stack():
    rects = gb.template_rects("no-such-template", 3)
    assert len(rects) == 3
    # even vertical stack: same widths, increasing y
    assert rects[0][1] < rects[1][1] < rects[2][1]


def test_count_mismatch_falls_back_gracefully():
    # grid4 defined for 4 slots but asked for 5 -> safe fallback of 5
    rects = gb.template_rects("grid4", 5)
    assert len(rects) == 5


# --- speaker-tag policy: cast speech unlabelled, devices labelled ---

@pytest.mark.parametrize("spk", ["STATIC", "MOODZ", "CLEVER", "NEONBLUE", "SCARLINE", "TWOTONE", "ASH"])
def test_cast_speech_has_no_speaker_tag(spk):
    assert gb.speaker_tag(spk) == ""


@pytest.mark.parametrize("spk", ["PA", "SCREEN", "RADIO", "RELAY", "SIGNAL", "MONITOR"])
def test_device_voices_keep_a_label(spk):
    assert gb.speaker_tag(spk) == spk


# --- SFX loudness styling ---

def test_sfx_loud_allcaps_is_large():
    size, _ = gb._sfx_style("BZZT")
    assert size >= 150


def test_sfx_quiet_lowercase_is_small():
    size, _ = gb._sfx_style("tik")
    assert size <= 90


def test_sfx_medium_between():
    lo, _ = gb._sfx_style("tik")
    md, _ = gb._sfx_style("Rmmml")
    hi, _ = gb._sfx_style("WRRRN")
    assert lo < md < hi
