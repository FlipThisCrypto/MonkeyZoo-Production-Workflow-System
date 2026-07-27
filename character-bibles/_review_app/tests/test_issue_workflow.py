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
    assert status["current_stage"]["id"] == "intake"
    assert status["current_stage"]["state"] == "current_ready"
    assert status["state_source"] == "inferred"
    assert "Inferred" in status["state_notice"]
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


def test_list_degrades_issue_whose_id_is_not_operable(workspace):
    # An issue whose id is not a safe MZ-YYYY-MM-NN (e.g. a codename like
    # MZ-2026-07-MANGO) lists fine but every per-issue endpoint 400s it via
    # find_issue -> _safe_issue_id. The list must flag it degraded, not present a
    # normal, clickable issue that breaks the instant it is opened.
    make_issue(workspace)  # valid MZ-2027-01-01
    make_issue(workspace, folder="2026-07_Issue_MANGO", issue_id="MZ-2026-07-MANGO")
    by_id = {item.get("issue_id"): item for item in issue_workflow.list_issues(workspace)}
    assert not by_id["MZ-2027-01-01"].get("degraded")
    mango = by_id["MZ-2026-07-MANGO"]
    assert mango.get("degraded") is True
    assert "MZ-YYYY-MM-NN" in mango.get("error", "")


def test_workflow_status_rejects_unoperable_id(workspace):
    issue = make_issue(workspace, folder="2026-07_Issue_MANGO", issue_id="MZ-2026-07-MANGO")
    with pytest.raises(issue_workflow.IssueWorkflowError, match="MZ-YYYY-MM-NN"):
        issue_workflow.workflow_status(issue, workspace)


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
    with pytest.raises(issue_workflow.IssueWorkflowError, match="skipping"):
        issue_workflow.record_advance(issue, workspace, "script")
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


def test_stateful_intake_canon_outline_transitions(workspace):
    issue = make_issue(workspace)
    before = issue_workflow.workflow_status(issue, workspace)
    assert before["active_stage"] == "intake"
    assert not (issue / issue_workflow.STATE_FILE).exists()
    canon = issue_workflow.record_advance(issue, workspace, "intake")
    assert canon["active_stage"] == "canon_review"
    assert canon["current_stage"]["state"] == "awaiting_approval"
    with pytest.raises(issue_workflow.IssueWorkflowError, match="approval is required"):
        issue_workflow.record_advance(issue, workspace, "canon_review")
    approved = issue_workflow.record_approval(issue, workspace, "canon_review", True, "Canon confirmed")
    assert approved["approval"]["approved"] is True
    outline = issue_workflow.record_advance(issue, workspace, "canon_review")
    assert outline["active_stage"] == "outline"
    (issue / "issue_outline.md").write_text("Valid outline\n", encoding="utf-8")
    assert issue_workflow.workflow_status(issue, workspace)["active_stage"] == "outline"
    script = issue_workflow.record_advance(issue, workspace, "outline")
    assert script["active_stage"] == "script"
    reloaded = issue_workflow.workflow_status(issue, workspace)
    assert reloaded["active_stage"] == "script"
    saved = json.loads((issue / issue_workflow.STATE_FILE).read_text(encoding="utf-8"))
    assert [item["completed_stage"] for item in saved["transitions"]] == ["intake", "canon_review", "outline"]


def test_approval_becomes_stale_when_artifacts_change(workspace):
    issue = make_issue(workspace)
    issue_workflow.record_advance(issue, workspace, "intake")
    issue_workflow.record_approval(issue, workspace, "canon_review", True)
    (issue / "metadata.json").write_text(json.dumps({"issue_id":"MZ-2027-01-01","title":"Changed"}), encoding="utf-8")
    status = issue_workflow.workflow_status(issue, workspace)
    assert status["approval"]["stale"] is True
    assert status["current_stage"]["state"] == "awaiting_approval"
    with pytest.raises(issue_workflow.IssueWorkflowError, match="stale"):
        issue_workflow.record_advance(issue, workspace, "canon_review")


def test_get_is_read_only_and_malformed_state_degrades(workspace):
    issue = make_issue(workspace)
    issue_workflow.workflow_status(issue, workspace)
    assert not (issue / issue_workflow.STATE_FILE).exists()
    (issue / issue_workflow.STATE_FILE).write_text("{broken", encoding="utf-8")
    with pytest.raises(issue_workflow.IssueWorkflowError, match="Malformed workflow state"):
        issue_workflow.workflow_status(issue, workspace)


def test_atomic_writer_leaves_no_temporary_file(workspace):
    issue = make_issue(workspace)
    issue_workflow.record_advance(issue, workspace, "intake")
    assert json.loads((issue / issue_workflow.STATE_FILE).read_text(encoding="utf-8"))["active_stage"] == "canon_review"
    assert not list(issue.glob("*.tmp"))


def test_unknown_mismatch_and_terminal_advancement(workspace):
    issue = make_issue(workspace)
    with pytest.raises(issue_workflow.IssueWorkflowError, match="Unknown stage"):
        issue_workflow.record_advance(issue, workspace, "bogus")
    with pytest.raises(issue_workflow.IssueWorkflowError, match="mismatch"):
        issue_workflow.record_approval(issue, workspace, "canon_review", True)
    state = {"schema_version":"1.0","active_stage":"published","transitions":[],"approvals":{}}
    issue_workflow._atomic_write(issue / issue_workflow.STATE_FILE, state)
    with pytest.raises(issue_workflow.IssueWorkflowError, match="terminal"):
        issue_workflow.record_advance(issue, workspace, "published")
