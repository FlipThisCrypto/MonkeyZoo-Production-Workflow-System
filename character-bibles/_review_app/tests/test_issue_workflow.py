import json
import sys
from pathlib import Path

import pytest
import yaml

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import issue_workflow


@pytest.fixture()
def workspace(tmp_path):
    (tmp_path / "02_MONTHLY_ISSUES").mkdir()
    (tmp_path / "05_RELEASE_ARCHIVE").mkdir()
    (tmp_path / "00_SYSTEM").mkdir()
    real_root = Path(__file__).resolve().parents[3]
    for name in ("page_panel_plan_schema.json", "art_prompt_pack_schema.json"):
        (tmp_path / "00_SYSTEM" / name).write_text((real_root / "00_SYSTEM" / name).read_text(encoding="utf-8"), encoding="utf-8")
    bible = tmp_path / "character-bibles" / "MZ-CHAR-TEST"
    bible.mkdir(parents=True)
    (bible / "bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":"MZ-CHAR-TEST","current_display_name":"Test","naming_status":"personal_name_canon","development_level":1,"canon_status":"approved_canon"},"visual_canon":{"primary_reference_image":None,"features_that_must_never_change":[],"prohibited_visual_additions":[]},"issue_level_usage":{}}), encoding="utf-8")
    return tmp_path


def make_issue(root, folder="2027-01_Issue_01", issue_id="MZ-2027-01-01"):
    issue = root / "02_MONTHLY_ISSUES" / folder
    issue.mkdir()
    (issue / "issue_brief.md").write_text(f"Issue ID: {issue_id}\nWorking Title: Test\nIssue Number: 1\nIssue Month: 2027-01\nMain Character: MZ-CHAR-TEST\n", encoding="utf-8")
    (issue / "metadata.json").write_text(json.dumps({"issue_id":issue_id,"title":"Test","primary_character":"MZ-CHAR-TEST"}), encoding="utf-8")
    return issue


def test_status_uses_real_evidence_and_missing_files_block(workspace):
    issue = make_issue(workspace)
    status = issue_workflow.workflow_status(issue, workspace)
    assert status["current_stage"]["id"] == "outline"
    assert any("issue_outline.md" in item for item in status["blockers"])
    assert status["owner_approval_required"] is False


def test_list_ignores_temporary_and_degrades_malformed(workspace):
    make_issue(workspace)
    (workspace / "02_MONTHLY_ISSUES" / ".2027-02_Issue_02.creating-token").mkdir()
    (workspace / "02_MONTHLY_ISSUES" / "legacy-broken").mkdir()
    result = issue_workflow.list_issues(workspace)
    assert len(result) == 2
    assert sum(bool(item.get("degraded")) for item in result) == 1


@pytest.mark.parametrize("value", ["../escape", "MZ-2027-01-01/../../x", "not-an-id"])
def test_invalid_issue_ids_are_rejected(workspace, value):
    with pytest.raises(issue_workflow.IssueWorkflowError):
        issue_workflow.find_issue(value, workspace)


def test_unknown_issue_rejected(workspace):
    with pytest.raises(issue_workflow.IssueWorkflowError, match="Unknown issue"):
        issue_workflow.find_issue("MZ-2027-01-01", workspace)


def test_artifact_viewer_cannot_escape(workspace):
    issue = make_issue(workspace)
    assert issue_workflow.view_artifact(issue, "issue_brief.md")["content"].startswith("Issue ID")
    with pytest.raises(issue_workflow.IssueWorkflowError, match="Unsafe"):
        issue_workflow.view_artifact(issue, "../secret.txt")


def test_failed_validation_and_stage_skipping_block_advancement(workspace):
    issue = make_issue(workspace)
    with pytest.raises(issue_workflow.IssueWorkflowError, match="Stage skipping"):
        issue_workflow.record_advance(issue, workspace, "script")
    with pytest.raises(issue_workflow.IssueWorkflowError, match="Advancement blocked"):
        issue_workflow.record_advance(issue, workspace, "outline")
    assert not (issue / ".workflow-status.json").exists()


def test_qa_failure_and_release_assets_are_real_gates(workspace):
    issue = make_issue(workspace)
    for name in ("issue_outline.md", "issue_script.md", "cover_prompt.md", "social_posts.md", "final_export_checklist.md"):
        (issue / name).write_text("real content\n", encoding="utf-8")
    (issue / "qa_report.md").write_text("VERDICT: HOLD — blocking items remain\n", encoding="utf-8")
    qa = issue_workflow._stage_validation("qa", issue, workspace)
    release = issue_workflow._stage_validation("release", issue, workspace)
    assert qa["status"] == "failed"
    assert any("PDF" in message for message in release["messages"])
    assert issue_workflow._stage_validation("published", issue, workspace)["status"] == "failed"


def test_alias_character_reference_resolves(workspace):
    alias = workspace / "character-bibles" / "MZ-CHAR-ALIAS"
    alias.mkdir()
    (alias / "bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":"MZ-CHAR-ALIAS","current_display_name":"Alias","alias_of":"MZ-CHAR-TEST"}}), encoding="utf-8")
    issue = make_issue(workspace)
    (issue / "issue_brief.md").write_text("Issue ID: MZ-2027-01-01\nMain Character: MZ-CHAR-ALIAS\n", encoding="utf-8")
    issue_workflow.bible_store._IDENTITY_INDEXES.clear()
    assert issue_workflow._stage_validation("canon_review", issue, workspace)["status"] == "passed"


def test_owner_approval_is_never_fabricated(workspace):
    issue = make_issue(workspace)
    status = issue_workflow.workflow_status(issue, workspace)
    assert "approved" not in status
    assert status["owner_approval_required"] is False
