import json
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(APP))
import art_prompt_workspace as pack  # noqa: E402


@pytest.fixture()
def factory(tmp_path):
    (tmp_path / "02_MONTHLY_ISSUES").mkdir()
    (tmp_path / "05_RELEASE_ARCHIVE").mkdir()
    (tmp_path / "00_SYSTEM").mkdir()
    for name in ("art_prompt_pack_schema.json", "page_panel_plan_schema.json"):
        (tmp_path / "00_SYSTEM" / name).write_text(
            (ROOT / "00_SYSTEM" / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (tmp_path / "00_SYSTEM" / "visual_style_bible.md").write_text(
        (ROOT / "00_SYSTEM" / "visual_style_bible.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    issue = tmp_path / "02_MONTHLY_ISSUES" / "2027-07_Issue_01"
    issue.mkdir()
    (issue / "issue_brief.md").write_text("Issue ID: MZ-2027-07-01\n", encoding="utf-8")
    (issue / "metadata.json").write_text(
        json.dumps({"issue_id": "MZ-2027-07-01", "title": "Pack Test"}),
        encoding="utf-8",
    )
    plan = {
        "issue_id": "MZ-2027-07-01",
        "issue_title": "Pack Test",
        "page_count": 1,
        "pages": [
            {
                "page_number": 1,
                "page_purpose": "Open",
                "panels": [
                    {
                        "panel_id": "MZ-2027-07-01_P01_PANEL01",
                        "characters": ["MZ-CHAR-001"],
                        "location": "Quiet Relay Courtyard",
                        "camera_angle": "Wide",
                        "action": "Moodz approaches the silent mast",
                        "emotion": "Cautious",
                        "dialogue": "MOODZ: Still dark.",
                        "caption": "",
                        "visual_notes": "Soft dusk",
                        "continuity_notes": "Keep identity markers",
                        "art_prompt": "",
                        "negative_prompt": "",
                        "references_required": ["MZ-CHAR-001"],
                        "lora_required": [],
                        "controlnet_required": "",
                        "seed_strategy": "per_panel",
                    }
                ],
            }
        ],
    }
    (issue / "page_panel_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    pack._write_json(
        issue / ".workflow-status.json",
        {"schema_version": "1.0", "active_stage": "art_prompts", "transitions": [], "approvals": {}},
    )
    return tmp_path, issue


def test_build_pack_is_schema_valid(factory):
    root, issue = factory
    built = pack.build_pack(issue, root)
    result = pack.validate_pack(built, root)
    assert result["status"] == "passed"
    assert built["panels"][0]["style_lock_phrase_included"] is True
    assert len(built["style_lock_phrase"]) >= 20
    assert len(built["panels"][0]["prompt"]) >= 40


def test_variant_approve_promote_and_overwrite_guard(factory):
    root, issue = factory
    variant = pack.create_variant(issue, root)
    assert variant["validation"]["status"] == "passed"
    approved = pack.approve(issue, root, variant["variant_id"], "owner")
    assert approved["approval_current"]
    with pytest.raises(pack.ArtPromptError, match="immutable"):
        pack.approve(issue, root, variant["variant_id"])
    result = pack.promote(issue, root, variant["variant_id"])
    assert result["ok"]
    written = json.loads((issue / "art_prompt_pack.json").read_text(encoding="utf-8"))
    assert written["issue_id"] == "MZ-2027-07-01"
    with pytest.raises(pack.ArtPromptError, match="already promoted"):
        pack.promote(issue, root, variant["variant_id"], True)


def test_plan_change_stales_and_blocks_promotion(factory):
    root, issue = factory
    variant = pack.create_variant(issue, root)
    pack.approve(issue, root, variant["variant_id"])
    plan = json.loads((issue / "page_panel_plan.json").read_text(encoding="utf-8"))
    plan["pages"][0]["panels"][0]["action"] = "Changed action"
    (issue / "page_panel_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    decorated = pack.variants(issue)[0]
    assert decorated["plan_stale"] is True
    with pytest.raises(pack.ArtPromptError, match="current approved"):
        pack.promote(issue, root, variant["variant_id"])


def test_wrong_stage_and_existing_pack_require_replace(factory):
    root, issue = factory
    state = json.loads((issue / ".workflow-status.json").read_text(encoding="utf-8"))
    state["active_stage"] = "page_plan"
    pack._write_json(issue / ".workflow-status.json", state)
    with pytest.raises(pack.ArtPromptError, match="current stage is page_plan"):
        pack.create_variant(issue, root)
    state["active_stage"] = "art_prompts"
    pack._write_json(issue / ".workflow-status.json", state)
    variant = pack.create_variant(issue, root)
    pack.approve(issue, root, variant["variant_id"])
    (issue / "art_prompt_pack.json").write_text('{"owner":true}\n', encoding="utf-8")
    with pytest.raises(pack.ArtPromptError, match="replacement confirmation"):
        pack.promote(issue, root, variant["variant_id"])
    pack.promote(issue, root, variant["variant_id"], True)
    assert "owner" not in (issue / "art_prompt_pack.json").read_text(encoding="utf-8")
