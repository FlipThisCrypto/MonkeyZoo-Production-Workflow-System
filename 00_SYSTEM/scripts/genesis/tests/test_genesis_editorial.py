"""Characterization for the Genesis page-by-page editorial audit.

audit() is the owner-facing record of what the editorial pass changed per page
(hero pick, crop-variation reframes, layout-adjacency, dialogue/SFX tallies). It
was untested; these pin the contract and guard the hero pick against an
empty-panel page (formerly panels[0] -> IndexError), matching the crash-proofing
the technical QA gate already has.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")  # genesis_editorial imports assemble_pages -> PIL at import

GEN = Path(__file__).resolve().parents[1]
SCRIPTS = GEN.parents[1]
for p in (str(GEN), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import genesis_editorial as ge  # noqa: E402


def _panel(pid, shot="medium", chars=("MZ-CHAR-001",), dialogue="", sfx="",
           dwords=0, emphasis=False):
    pa = {"source_panel_id": pid, "shot": shot, "characters": list(chars),
          "dialogue": dialogue, "sfx": sfx, "dialogue_words": dwords}
    if emphasis:
        pa["emphasis"] = True
    return pa


def _page(num, panels, template="grid_four", reader_side="right",
          location="Signal Lab", beats=("setup",), turn="reveal"):
    return {"page_number": num, "reader_side": reader_side, "panel_count": len(panels),
            "layout_template": template, "location": location, "panels": panels,
            "beat_summary": list(beats), "page_turn_purpose": turn}


def _write(genesis_dir: Path, pages, *, crops=None, dupes=None) -> None:
    genesis_dir.mkdir(parents=True, exist_ok=True)
    (genesis_dir / "GENESIS_LAYOUT_PLAN.json").write_text(
        json.dumps({"pages": pages}), encoding="utf-8")
    if crops is not None:
        (genesis_dir / "metadata").mkdir(parents=True, exist_ok=True)
        (genesis_dir / "metadata" / "panel_crops.json").write_text(
            json.dumps({"crops": crops}), encoding="utf-8")
    if dupes is not None:
        (genesis_dir / "qa").mkdir(parents=True, exist_ok=True)
        (genesis_dir / "qa" / "duplicate_panel_report.json").write_text(
            json.dumps(dupes), encoding="utf-8")


def test_hero_is_the_emphasis_panel_when_present(tmp_path):
    g = tmp_path / "G"
    _write(g, [_page(1, [_panel("P01_A"), _panel("P01_B", emphasis=True), _panel("P01_C")])])
    data = ge.audit(g)
    assert data["pages"][0]["hero_panel"] == "P01_B"


def test_hero_falls_back_to_first_panel(tmp_path):
    g = tmp_path / "G"
    _write(g, [_page(1, [_panel("P01_A"), _panel("P01_B")])])
    assert ge.audit(g)["pages"][0]["hero_panel"] == "P01_A"


def test_empty_panel_page_does_not_crash_and_hero_is_none(tmp_path):
    g = tmp_path / "G"
    _write(g, [_page(1, [])])
    page = ge.audit(g)["pages"][0]
    assert page["hero_panel"] is None
    assert page["panel_count"] == 0
    assert page["dialogue_words"] == 0


def test_reframed_count_uses_non_full_crops(tmp_path):
    g = tmp_path / "G"
    panels = [_panel("P01_A"), _panel("P01_B"), _panel("P01_C")]
    # P01_B reframed (non-full), P01_A explicitly full, P01_C absent (=> full)
    crops = {"P01_A": [0.0, 0.0, 1.0, 1.0], "P01_B": [0.1, 0.0, 0.9, 1.0]}
    _write(g, [_page(1, panels)], crops=crops)
    data = ge.audit(g)
    assert data["pages"][0]["panels_reframed"] == 1
    assert data["summary"]["total_panels_reframed"] == 1
    assert data["summary"]["pages_reframed"] == 1


def test_dialogue_sfx_and_balloon_tallies(tmp_path):
    g = tmp_path / "G"
    panels = [_panel("P01_A", dialogue="Hi there", dwords=2, sfx="BOOM"),
              _panel("P01_B", dialogue="", dwords=0),
              _panel("P01_C", dialogue="Yes", dwords=1)]
    _write(g, [_page(1, panels)])
    p = ge.audit(g)["pages"][0]
    assert p["dialogue_words"] == 3
    assert p["balloon_count"] == 2   # two panels carry dialogue text
    assert p["sfx_count"] == 1


def test_adjacent_same_template_is_flagged(tmp_path):
    g = tmp_path / "G"
    pages = [_page(1, [_panel("P01_A")], template="grid_four"),
             _page(2, [_panel("P02_A")], template="grid_four"),
             _page(3, [_panel("P03_A")], template="hero_two")]
    _write(g, pages)
    data = ge.audit(g)
    assert data["pages"][0]["layout_same_as_next"] is True
    assert data["pages"][1]["layout_same_as_prev"] is True
    assert data["pages"][2]["layout_same_as_prev"] is False
    assert data["summary"]["adjacent_same_template"] == 1  # page 2 matches its prev


def test_close_background_repeats_tallied_per_page(tmp_path):
    g = tmp_path / "G"
    _write(g, [_page(1, [_panel("P01_A")]), _page(2, [_panel("P02_A")])],
           dupes={"close_background_repeats": [{"page_a": 1}, {"page_a": 1}, {"page_a": 2}]})
    pages = ge.audit(g)["pages"]
    assert pages[0]["close_background_repeats"] == 2
    assert pages[1]["close_background_repeats"] == 1


def test_write_audit_round_trips_including_empty_page(tmp_path):
    g = tmp_path / "G"
    _write(g, [_page(1, [_panel("P01_A", emphasis=True)]), _page(2, [])])
    data = ge.audit(g)
    ge.write_audit(g, data)
    js = g / "qa" / "GENESIS_PAGE_BY_PAGE_EDITORIAL_AUDIT.json"
    md = g / "qa" / "GENESIS_PAGE_BY_PAGE_EDITORIAL_AUDIT.md"
    assert js.exists() and md.exists()
    text = md.read_text(encoding="utf-8")
    assert "Hero panel: `—`" in text          # empty page renders a dash, no crash
    assert json.loads(js.read_text(encoding="utf-8"))["summary"]["total_pages"] == 2
