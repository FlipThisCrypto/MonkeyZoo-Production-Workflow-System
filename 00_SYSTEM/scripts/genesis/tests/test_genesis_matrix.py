"""Characterization of the panel-native completion matrix classifier.

classify() decides, per panel, whether the reused integrated composite is a
legitimate KEEP or a bespoke-art REGENERATE candidate — the guidance the owner
acts on. It is pure and was untested, so these pin every branch and guard the
side-crop verdict against a null/absent crop measurement (formerly `None < 10`
-> TypeError).
"""
from __future__ import annotations

import sys
from pathlib import Path

GEN = Path(__file__).resolve().parents[1]
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))

import genesis_matrix as gm  # noqa: E402

PG = {"page_number": 1}  # classify does not read page fields; kept for signature parity


def _panel(pid="P01_PANEL01", shot="medium", chars=("MZ-CHAR-001",), beat="rising"):
    return {"source_panel_id": pid, "shot": shot, "characters": list(chars), "beat": beat}


def _crop(pid, left):
    return {pid: {"crop_left_pct": left}}


def test_bespoke_panel_is_regenerated_done():
    pa = _panel()
    out = gm.classify(pa, PG, {}, bespoke={pa["source_panel_id"]})
    assert out["classification"] == "CHARACTER_REGENERATED"
    assert out["status"] == "DONE"
    assert out["visual_qa_result"] == "pass"


def test_zero_character_panel_is_kept_resolved():
    out = gm.classify(_panel(chars=()), PG, {}, bespoke=set())
    assert out["classification"] == "KEEP"
    assert out["status"] == "RESOLVED"
    assert out["owner_review_required"] is False


def test_wide_with_small_side_crop_passes():
    # needs >=1 character so it reaches the wide branch (0-char returns KEEP earlier)
    pa = _panel(shot="wide", chars=("MZ-CHAR-001",))
    out = gm.classify(pa, PG, _crop(pa["source_panel_id"], 5), bespoke=set())
    assert out["classification"] == "KEEP"
    assert out["visual_qa_result"] == "pass"


def test_wide_with_large_side_crop_needs_review():
    pa = _panel(shot="wide", chars=("MZ-CHAR-001",))
    out = gm.classify(pa, PG, _crop(pa["source_panel_id"], 25), bespoke=set())
    assert out["visual_qa_result"] == "review"


def test_wide_with_null_side_crop_reviews_instead_of_crashing():
    pa = _panel(shot="wide", chars=("MZ-CHAR-001",))
    out = gm.classify(pa, PG, _crop(pa["source_panel_id"], None), bespoke=set())
    assert out["classification"] == "KEEP"
    assert out["visual_qa_result"] == "review"


def test_wide_with_missing_crop_row_reviews_instead_of_crashing():
    pa = _panel(shot="wide", chars=("MZ-CHAR-001",))
    out = gm.classify(pa, PG, {}, bespoke=set())  # panel absent from crop map
    assert out["visual_qa_result"] == "review"


def test_solo_closeup_with_recipe_is_regenerate_candidate():
    pa = _panel(shot="close", chars=("MZ-CHAR-003",))
    out = gm.classify(pa, PG, {}, bespoke=set())
    assert out["classification"] == "REGENERATE_CHARACTER"
    assert out["status"] == "CANDIDATE"
    assert "single-character pose" in out["proposed_solution"]


def test_solo_closeup_without_recipe_flags_missing_descriptor():
    pa = _panel(shot="close", chars=("MZ-CHAR-UNKNOWN",))
    out = gm.classify(pa, PG, {}, bespoke=set())
    assert out["classification"] == "REGENERATE_CHARACTER"
    assert out["proposed_solution"] == "needs a recipe descriptor first"


def test_multi_character_with_recipe_is_regenerate():
    pa = _panel(shot="medium", chars=("MZ-CHAR-001", "MZ-CHAR-002"))
    out = gm.classify(pa, PG, {}, bespoke=set())
    assert out["classification"] == "REGENERATE_CHARACTER"
    assert out["generation_method"] == "zimage_multichar_stage"


def test_multi_character_without_recipe_needs_descriptor():
    pa = _panel(shot="medium", chars=("MZ-CHAR-001", "MZ-CHAR-UNKNOWN"))
    out = gm.classify(pa, PG, {}, bespoke=set())
    assert out["classification"] == "REGENERATE_CHARACTER_NEEDS_DESCRIPTOR"
