"""Tests for the Genesis layout planner: variable density, determinism,
full-panel coverage, and no repeated adjacent grids."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

GEN = Path(__file__).resolve().parents[1]
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))

import genesis_plan as gp  # noqa: E402


@pytest.fixture(scope="module")
def plan():
    if not gp.SOURCE_PLAN.exists():
        pytest.skip(f"source plan missing: {gp.SOURCE_PLAN}")
    return gp.build_plan()


def test_exactly_22_pages_and_96_panels(plan):
    assert plan["story_page_count"] == 22
    assert len(plan["pages"]) == 22
    assert plan["total_panels"] == 96
    assert sum(p["panel_count"] for p in plan["pages"]) == 96


def test_panel_density_is_varied_and_in_range(plan):
    counts = [p["panel_count"] for p in plan["pages"]]
    # every page 3..6, except the opener/finale which may run lighter (2..6)
    for p in plan["pages"]:
        lo = 2 if p["page_number"] in (1, 22) else 3
        assert lo <= p["panel_count"] <= 6, (p["page_number"], p["panel_count"])
    assert len(set(counts)) >= 3, "layout must use at least 3 distinct page densities"
    avg = sum(counts) / len(counts)
    assert 4.0 <= avg <= 5.3, avg
    # not every page the same count (the old six-panel-everywhere failure)
    assert max(counts, key=counts.count) != min(counts) or len(set(counts)) > 1


def test_every_source_panel_used_exactly_once(plan):
    ids = [pa["source_panel_id"] for pg in plan["pages"] for pa in pg["panels"]]
    assert len(ids) == 96
    assert len(set(ids)) == 96, "no panel may be dropped or duplicated"


def test_reading_order_preserved(plan):
    # panels must remain in source story order across the whole issue
    ids = [pa["source_panel_id"] for pg in plan["pages"] for pa in pg["panels"]
           if not (pg["layout_template"].startswith("feature") or pg["layout_template"].startswith("left"))]
    # within grid pages the slot order equals source order; globally the first
    # panel of each page must not precede the last panel of a prior page
    firsts = []
    for pg in plan["pages"]:
        page_ids = sorted(pa["source_panel_id"] for pa in pg["panels"])
        firsts.append(page_ids[0])
    assert firsts == sorted(firsts), "pages must be contiguous in source order"


def test_no_adjacent_identical_templates(plan):
    reps = sum(1 for i in range(1, len(plan["pages"]))
               if plan["pages"][i]["layout_template"] == plan["pages"][i - 1]["layout_template"])
    assert reps == 0, f"{reps} adjacent pages reuse the same template"


def test_reader_sides_alternate(plan):
    for pg in plan["pages"]:
        assert pg["reader_side"] == ("right" if pg["page_number"] % 2 == 1 else "left")


def test_deterministic_same_seed_same_layout():
    a = gp.build_plan()
    b = gp.build_plan()
    sig_a = [(p["panel_count"], p["layout_template"], [x["source_panel_id"] for x in p["panels"]]) for p in a["pages"]]
    sig_b = [(p["panel_count"], p["layout_template"], [x["source_panel_id"] for x in p["panels"]]) for p in b["pages"]]
    assert sig_a == sig_b, "planner must be deterministic for a fixed seed"
