"""Tests for the crop-budget audit: side-crop is what endangers characters."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")
GEN = Path(__file__).resolve().parents[1]
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))

import genesis_crop_audit as ca  # noqa: E402


def test_full_width_band_barely_side_crops_16x9():
    # a 16:9 source in a wide band loses almost no width (characters safe)
    m = ca.cover_metrics(1280, 720, 2280, 900)   # band ratio 2.53
    assert m["crop_left_pct"] < 6
    assert m["crop_top_pct"] > 0                  # trims sky top/bottom instead


def test_tall_slot_heavily_side_crops_16x9():
    # a 16:9 source forced into a tall column loses the sides (characters)
    m = ca.cover_metrics(1280, 720, 900, 1600)   # tall slot ratio 0.56
    assert m["crop_left_pct"] > 25


def test_classify_band_is_safe_tall_is_recompose():
    band = ca.cover_metrics(1280, 720, 2280, 900)
    tall = ca.cover_metrics(1280, 720, 900, 1600)
    assert ca.classify(band, "wide") in ("keep", "minor_crop")
    assert ca.classify(tall, "wide") == "recompose_or_regenerate"


def test_metrics_symmetry_and_retained_bounds():
    m = ca.cover_metrics(1280, 720, 1000, 1000)
    assert m["crop_left_pct"] == m["crop_right_pct"]
    assert m["crop_top_pct"] == m["crop_bottom_pct"]
    assert 0 < m["retained_area_pct"] <= 100


def test_audit_runs_end_to_end(tmp_path, monkeypatch):
    # regression: audit() referenced an undefined `pid` and crashed with NameError
    # on ANY run (the pure-function tests above never exercised this path).
    import json
    from PIL import Image
    monkeypatch.setattr(ca, "FACTORY", tmp_path)
    panels = tmp_path / "panels"
    panels.mkdir()
    for name in ("P01", "P02"):
        Image.new("RGB", (1280, 720), "white").save(panels / f"{name}.png")
    gd = tmp_path / "GEN"
    gd.mkdir()
    plan = {
        "source_panel_dir": "panels",
        "pages": [{
            "page_number": 1, "layout_template": "band2", "panel_count": 2,
            "panels": [
                {"source_panel_id": "P01", "shot": "wide"},
                {"source_panel_id": "P02", "shot": "medium"},
            ],
        }],
    }
    (gd / "GENESIS_LAYOUT_PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
    result = ca.audit(gd)
    assert result["total_panels"] == 2
    assert {r["panel_id"] for r in result["panels"]} == {"P01", "P02"}
    assert all("classification" in r and "retained_area_pct" in r for r in result["panels"])
