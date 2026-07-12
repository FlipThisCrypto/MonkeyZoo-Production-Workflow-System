from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import workflow_engine as engine


def sample_config() -> dict:
    return {
        "issue_id": "MZ-TEST-WORKFLOW",
        "topic": "a tiny rescue rehearsal",
        "adventure_style": "Comedy of errors",
        "page_count": 2,
        "panel_count": 6,
        "audience": "all ages",
        "tone": "warm funny adventure",
        "continuity_mode": "current canon only",
        "canon_strictness": "balanced",
        "character_growth_mode": "small reversible beat",
        "characters": [
            {"character_id": "MZ-CHAR-CLEVER", "role": "primary"},
            {"character_id": "MZ-CHAR-001", "role": "secondary"},
        ],
        "production": {
            "stages": ["concept", "outline", "page_plan", "script", "image_generation", "lettering", "assembly", "qc"],
            "max_dialogue_words_per_balloon": 15,
            "panel_image_size": {"width": 2480, "height": 3508},
        },
        "validation": {
            "require_reference_images": True,
            "continuity_updates_require_approval": True,
        },
    }


def write_config(tmp_path: Path, config: dict) -> Path:
    path = tmp_path / "production_config.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def test_load_config_and_validate_good_sample(tmp_path: Path) -> None:
    path = write_config(tmp_path, sample_config())
    config = engine.load_config(path)
    issues = engine.validate_config(config)
    assert not [item for item in issues if item["severity"] == "high"]


def test_validate_config_catches_missing_character(tmp_path: Path) -> None:
    config = sample_config()
    config["characters"] = [{"character_id": "MZ-CHAR-NOT-REAL", "role": "primary"}]
    issues = engine.validate_config(config)
    assert any("Bible is missing" in item["message"] for item in issues)


def test_script_stage_writes_reviewable_context(tmp_path: Path) -> None:
    config = sample_config()
    result = engine.run_stage("script", config, tmp_path)
    run_dir = Path(result["run_dir"])
    proposal = json.loads((run_dir / "artifacts" / "proposed-continuity-update.json").read_text(encoding="utf-8"))
    prompt = (run_dir / "artifacts" / "script-generation-prompt.md").read_text(encoding="utf-8")
    assert result["validation"]["status"] == "pass"
    assert proposal["status"] == "proposed_owner_review_required"
    assert "Do not canonize experimental traits" in prompt


def test_count_validation_detects_panel_mismatch(tmp_path: Path) -> None:
    config = sample_config()
    run_dir = engine.ensure_dirs(config, tmp_path)
    engine.json_write(run_dir / "artifacts" / "page-plan.json", {"page_count": 2, "total_panels": 5, "pages": [{"page": 1, "panel_count": 2}, {"page": 2, "panel_count": 3}]})
    issues = engine.validate_counts(config, run_dir)
    assert any("panel count" in item["message"].lower() for item in issues)


def test_full_workflow_writes_improvement_and_reproducibility(tmp_path: Path) -> None:
    config = sample_config()
    result = engine.run_workflow(config, tmp_path)
    run_dir = tmp_path / config["issue_id"]
    assert result["results"]
    assert (run_dir / "improvement" / "improvement-report.md").exists()
    assert (run_dir / "reproducibility" / "capture.json").exists()

