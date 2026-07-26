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


# ---------------------------------------------------------------------------
# build(): completion must not be inferred from a file merely existing.
#
# build() derived its bespoke set from `native.glob("*.png")` alone, and
# classify() turns membership in that set into status="DONE" /
# visual_qa_result="pass". A zero-byte or partially-written panel therefore
# reported a FAILED generation as finished and QA-passed -- directly against the
# CLAUDE.md rule that nothing generated is canon until it passes QA.
#
# Reachable in practice: genesis_charart used to save straight to the final
# path, and these are multi-hour 96-panel ComfyUI batches where killing the
# process is the documented ZLUDA hang recovery (mz-art-run). An interrupted
# save is an expected event.
# ---------------------------------------------------------------------------
import json


def _write_genesis(tmp_path, pid="P01_PANEL01"):
    """Minimal GENESIS dir that build() can read."""
    plan = {
        "source_panel_dir": "src",
        "pages": [{
            "page_number": 1, "location": "alley",
            "panels": [{"source_panel_id": pid, "shot": "medium",
                        "characters": ["MZ-CHAR-001"], "beat": "rising"}],
        }],
    }
    (tmp_path / "GENESIS_LAYOUT_PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
    (tmp_path / "qa").mkdir(parents=True, exist_ok=True)
    (tmp_path / "qa" / "PANEL_CROP_AUDIT.json").write_text(
        json.dumps({"panels": [{"panel_id": pid, "retained_area_pct": 100, "crop_left_pct": 0}]}),
        encoding="utf-8")
    native = tmp_path / "generated_art" / "panel_native"
    native.mkdir(parents=True, exist_ok=True)
    return native


def _row(result, pid="P01_PANEL01"):
    return next(r for r in result["panels"] if r["panel_id"] == pid)


def test_zero_byte_panel_is_not_reported_done_and_qa_passed(tmp_path):
    native = _write_genesis(tmp_path)
    (native / "P01_PANEL01.png").write_bytes(b"")     # interrupted save

    row = _row(gm.build(tmp_path))

    assert row["status"] != "DONE", "an empty panel file was reported as finished"
    assert row["visual_qa_result"] != "pass", "an empty panel file was reported QA-passed"
    assert row["current_source"] != "bespoke_zimage"


def test_written_panel_is_reported_done(tmp_path):
    """Over-correction guard: a real panel must still count as complete."""
    native = _write_genesis(tmp_path)
    (native / "P01_PANEL01.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)

    row = _row(gm.build(tmp_path))

    assert row["status"] == "DONE"
    assert row["visual_qa_result"] == "pass"
    assert row["current_source"] == "bespoke_zimage"


def test_partial_render_file_is_not_counted_as_a_panel(tmp_path):
    """`.part` scratch files must never enter the completion set."""
    native = _write_genesis(tmp_path)
    (native / "P01_PANEL01.png.part").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)

    row = _row(gm.build(tmp_path))

    assert row["status"] != "DONE"
    assert row["current_source"] != "bespoke_zimage"
