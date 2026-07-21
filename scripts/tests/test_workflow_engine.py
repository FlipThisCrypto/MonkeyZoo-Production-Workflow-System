from __future__ import annotations

import json
import sys
from pathlib import Path

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



# --- canon-integrity gates in the orchestrator (validate_* helpers) ---

def _bible(*, naming_status="codename_only", personal_name=None, ref=None, glasses=None):
    return {"identification": {"naming_status": naming_status, "personal_name": personal_name},
            "visual_canon": {"primary_reference_image": ref, "glasses_status": glasses}}


def _artifacts(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    (run_dir / "artifacts").mkdir(parents=True)
    return run_dir


def test_character_rules_flags_non_clever_confirmed_glasses(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "load_selected_bibles",
                        lambda config: [("MZ-CHAR-999", _bible(glasses="confirmed_glasses", ref=None))])
    cfg = sample_config(); cfg["validation"]["require_reference_images"] = False
    issues = engine.validate_character_rules(cfg, tmp_path)
    glasses = [i for i in issues if "confirmed glasses" in i["message"]]
    assert glasses and glasses[0]["severity"] == "high"


def test_character_rules_allows_clever_glasses(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "load_selected_bibles",
                        lambda config: [("MZ-CHAR-CLEVER", _bible(glasses="confirmed_glasses", ref=None))])
    cfg = sample_config(); cfg["validation"]["require_reference_images"] = False
    assert not any("glasses" in i["message"] for i in engine.validate_character_rules(cfg, tmp_path))


def test_character_rules_flags_uncanonized_personal_name(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "load_selected_bibles",
                        lambda config: [("MZ-CHAR-X", _bible(naming_status="codename_only",
                                                             personal_name="Bartholomew", ref=None))])
    cfg = sample_config(); cfg["validation"]["require_reference_images"] = False
    assert any("Personal name exists without" in i["message"]
               for i in engine.validate_character_rules(cfg, tmp_path))


def test_character_rules_flags_missing_reference_when_required(tmp_path, monkeypatch):
    monkeypatch.setattr(engine, "load_selected_bibles",
                        lambda config: [("MZ-CHAR-X", _bible(ref=None))])
    cfg = sample_config()  # require_reference_images defaults True
    assert any("Primary reference image is missing" in i["message"]
               for i in engine.validate_character_rules(cfg, tmp_path))


def test_script_outputs_flags_overlong_dialogue(tmp_path):
    run_dir = _artifacts(tmp_path)
    (run_dir / "artifacts" / "generated-script.md").write_text(
        '- Dialogue: "' + " ".join(["word"] * 20) + '"\n', encoding="utf-8")
    assert any("exceeds lettering word limit" in i["message"]
               for i in engine.validate_script_outputs(sample_config(), run_dir))


def test_script_outputs_flags_continuity_not_owner_gated(tmp_path):
    run_dir = _artifacts(tmp_path)
    (run_dir / "artifacts" / "generated-script.md").write_text('- Dialogue: "hi"\n', encoding="utf-8")
    (run_dir / "artifacts" / "proposed-continuity-update.json").write_text(
        json.dumps({"status": "canon"}), encoding="utf-8")
    flagged = [i for i in engine.validate_script_outputs(sample_config(), run_dir)
               if "not marked for owner approval" in i["message"]]
    assert flagged and flagged[0]["severity"] == "high"


def test_script_outputs_accepts_owner_gated_continuity(tmp_path):
    run_dir = _artifacts(tmp_path)
    (run_dir / "artifacts" / "generated-script.md").write_text('- Dialogue: "hi"\n', encoding="utf-8")
    (run_dir / "artifacts" / "proposed-continuity-update.json").write_text(
        json.dumps({"status": "proposed_owner_review_required"}), encoding="utf-8")
    assert not any("not marked for owner approval" in i["message"]
                   for i in engine.validate_script_outputs(sample_config(), run_dir))


def test_counts_12page_front_cover_must_be_single_panel(tmp_path):
    run_dir = _artifacts(tmp_path)
    pages = ([{"page": 1, "panel_count": 3}]
             + [{"page": i, "panel_count": 4} for i in range(2, 12)]
             + [{"page": 12, "panel_count": 1}])
    engine.json_write(run_dir / "artifacts" / "page-plan.json",
                      {"page_count": 12, "total_panels": 44, "pages": pages})
    cfg = sample_config(); cfg["page_count"] = 12; cfg["panel_count"] = 44
    assert any("Front Cover" in i["message"] for i in engine.validate_counts(cfg, run_dir))


def test_counts_12page_interior_panel_range_enforced(tmp_path):
    run_dir = _artifacts(tmp_path)
    pages = ([{"page": 1, "panel_count": 1}]
             + [{"page": i, "panel_count": 4} for i in range(2, 11)]
             + [{"page": 11, "panel_count": 9}]      # over the 2-6 interior range
             + [{"page": 12, "panel_count": 1}])
    engine.json_write(run_dir / "artifacts" / "page-plan.json",
                      {"page_count": 12, "total_panels": 50, "pages": pages})
    cfg = sample_config(); cfg["page_count"] = 12; cfg["panel_count"] = 50
    assert any("expected between 2 and 6" in i["message"] for i in engine.validate_counts(cfg, run_dir))
