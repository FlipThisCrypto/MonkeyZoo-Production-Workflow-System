"""Regression: panel-native specs must state the RENDERER's slot geometry.

genesis_specs.build once sized panels with template_rects (uniform bands), but
genesis_build.render_page composites them into synth_page_rects slots (scene/
page-custom). That made target_px/aspect_ratio wrong for every panel and fed the
owner-gated regen prompts a ratio fit_cover would then crop (clipping the exact
ears/chin/hands/feet the prompt forbids). Pin specs to the same geometry the
renderer uses, with the identical count-mismatch fallback.
"""
from __future__ import annotations

import json
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
import genesis_specs as gs  # noqa: E402
from genesis_layout import synth_page_rects  # noqa: E402


def _panel(pid, shot="medium", chars=("MZ-CHAR-003",)):
    return {"source_panel_id": pid, "shot": shot, "characters": list(chars),
            "beat": "rising", "dialogue": "", "sfx": "", "caption": ""}


def _write_plan(genesis_dir: Path, pages: list[dict]) -> None:
    genesis_dir.mkdir(parents=True, exist_ok=True)
    plan = {"source_panel_dir": "GENESIS/panels", "pages": pages}
    (genesis_dir / "GENESIS_LAYOUT_PLAN.json").write_text(json.dumps(plan), encoding="utf-8")


def _render_geometry(pg: dict):
    """Exactly what genesis_build.render_page composites into."""
    rects = synth_page_rects(pg["panels"], pg["page_number"])
    if len(rects) != len(pg["panels"]):
        rects = gb.template_rects(pg["layout_template"], pg["panel_count"])
    return rects


PAGES = [
    {"page_number": 1, "layout_template": "2v", "panel_count": 2, "location": "Signal Lab",
     "panels": [_panel("P01_PANEL01"), _panel("P01_PANEL02")]},
    {"page_number": 2, "layout_template": "hero_two", "panel_count": 3, "location": "Zoo City",
     "panels": [_panel("P02_PANEL01", "wide", ()), _panel("P02_PANEL02"), _panel("P02_PANEL03")]},
]


def test_specs_target_px_and_aspect_match_the_renderer(tmp_path):
    gdir = tmp_path / "G"
    _write_plan(gdir, PAGES)
    data = gs.build(gdir)
    by_pos = {(s["page"], s["panel"]): s for s in data["specs"]}
    assert len(data["specs"]) == 5
    for pg in PAGES:
        for i, (x, y, w, h) in enumerate(_render_geometry(pg), 1):
            spec = by_pos[(pg["page_number"], i)]
            assert spec["target_px"] == [w, h], (
                f"page {pg['page_number']} panel {i}: spec {spec['target_px']} != render {[w, h]}")
            assert spec["aspect_ratio"] == round(w / h, 3)
            assert spec["orientation"] == ("landscape" if w >= h else "portrait")


def test_specs_do_not_regress_to_uniform_template_bands(tmp_path):
    # On a 2-flex-panel page the renderer pairs the panels into a 2-up (each
    # narrower than a full-width band). If specs ever revert to template_rects,
    # the widths would snap back to the full content width -- guard against it.
    gdir = tmp_path / "G2"
    _write_plan(gdir, [PAGES[0]])
    data = gs.build(gdir)
    band = gb.template_rects("2v", 2)
    for i, spec in enumerate(data["specs"]):
        assert spec["target_px"] != [band[i][2], band[i][3]], (
            "specs regressed to the uniform template band geometry")
