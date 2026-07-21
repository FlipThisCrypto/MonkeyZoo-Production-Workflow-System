"""Regression coverage for the Genesis QA gate.

genesis_qa is a release gate: genesis_report reads its qa/genesis_qa.json to
decide whether the issue is shippable. A gate must always emit a verdict, so its
two former crash paths are pinned here:
  * structural(): a rendered file whose name lacks a two-digit page prefix used
    to raise ValueError (int('co')); it must now surface as a QA problem instead.
  * shots(): an empty plan used to raise ZeroDivisionError computing
    close_fraction; it must now report 0.0.
Plus characterization of the core shot-distribution accounting.
"""
from __future__ import annotations

import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[1]
SCRIPTS = GEN.parents[1]
for p in (str(GEN), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import genesis_qa as gq  # noqa: E402


def _panel(pid, shot="medium", dialogue="", caption=""):
    return {"source_panel_id": pid, "shot": shot, "dialogue": dialogue, "caption": caption}


def _plan(pages, total=96):
    return {"pages": pages, "total_panels": total, "source_panel_dir": "GENESIS/panels"}


def _make_renders(genesis_dir: Path, names: list[str], story_names: list[str]) -> None:
    covers = genesis_dir / "web" / "covers"
    story = genesis_dir / "web" / "story_pages"
    covers.mkdir(parents=True, exist_ok=True)
    story.mkdir(parents=True, exist_ok=True)
    for n in names:
        (covers / n).write_bytes(b"jpg")
    for n in story_names:
        (story / n).write_bytes(b"jpg")


# ---- shots() ---------------------------------------------------------------

def test_shots_empty_plan_does_not_crash():
    # Formerly ZeroDivisionError: 0 panels -> close_fraction must be 0.0.
    out = gq.shots(_plan([]))
    assert out["close_fraction"] == 0.0
    assert out["by_shot"] == {}
    assert out["distinct_shot_types"] == 0


def test_shots_page_with_no_panels_does_not_crash():
    out = gq.shots(_plan([{"page_number": 1, "panels": []}]))
    assert out["close_fraction"] == 0.0


def test_shots_counts_distribution_and_close_fraction():
    pages = [{"page_number": 1, "panels": [
        _panel("A", "close"), _panel("B", "wide"),
        _panel("C", "extreme_close"), _panel("D", "medium")]}]
    out = gq.shots(_plan(pages))
    assert out["by_shot"] == {"close": 1, "wide": 1, "extreme_close": 1, "medium": 1}
    assert out["close_fraction"] == 0.5  # 2 of 4 are close/extreme_close
    assert out["distinct_shot_types"] == 4


def test_shots_flags_adjacent_closeups_on_same_page():
    pages = [{"page_number": 7, "panels": [
        _panel("A", "close"), _panel("B", "extreme_close"), _panel("C", "wide")]}]
    out = gq.shots(_plan(pages))
    assert out["adjacent_closeups_same_page"] == [7]


def test_shots_closeups_across_page_boundary_are_not_adjacent():
    pages = [
        {"page_number": 1, "panels": [_panel("A", "wide"), _panel("B", "close")]},
        {"page_number": 2, "panels": [_panel("C", "close"), _panel("D", "wide")]}]
    out = gq.shots(_plan(pages))
    assert out["adjacent_closeups_same_page"] == []


# ---- structural() ----------------------------------------------------------

def test_structural_malformed_render_filename_is_reported_not_raised(tmp_path):
    gdir = tmp_path / "G"
    # One cover has a non-numeric prefix -> must be flagged, must not raise.
    _make_renders(gdir, ["cover_front.jpg", "24_back.jpg"],
                  [f"{i:02d}_page.jpg" for i in range(2, 24)])
    out = gq.structural(_plan([]), gdir)
    assert any("without a two-digit page prefix" in p for p in out["problems"])
    assert any("cover_front.jpg" in p for p in out["problems"])


def test_structural_clean_sequence_has_no_sequence_problem(tmp_path):
    gdir = tmp_path / "G"
    _make_renders(gdir, ["01_front.jpg", "24_back.jpg"],
                  [f"{i:02d}_page.jpg" for i in range(2, 24)])
    out = gq.structural(_plan([]), gdir)
    assert not any("sequence not 01..24" in p for p in out["problems"])
    assert not any("two-digit page prefix" in p for p in out["problems"])
    assert out["story_page_files"] == 22
    assert out["cover_files"] == 2


def test_structural_short_sequence_is_reported(tmp_path):
    gdir = tmp_path / "G"
    _make_renders(gdir, ["01_front.jpg"], [f"{i:02d}_page.jpg" for i in range(2, 10)])
    out = gq.structural(_plan([]), gdir)
    assert out["pass"] is False
    assert any("sequence not 01..24" in p for p in out["problems"])
