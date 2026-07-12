import json
import sys
from pathlib import Path

import pytest
import yaml

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import story_workspace as story


@pytest.fixture()
def factory(tmp_path):
    (tmp_path / "02_MONTHLY_ISSUES").mkdir(); (tmp_path / "05_RELEASE_ARCHIVE").mkdir(); (tmp_path / "00_SYSTEM").mkdir()
    for rel in ("monkeyzoo_master_bible.md", "world_bible.md", "continuity_ledger.md"):
        (tmp_path / "00_SYSTEM" / rel).write_text("approved canon\n", encoding="utf-8")
    for cid, name in (("MZ-CHAR-001","Ash"),("MZ-CHAR-ZOMBIE","Patch")):
        bible = tmp_path / "character-bibles" / cid; bible.mkdir(parents=True)
        (bible / "bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":cid,"current_display_name":name,"canon_status":"approved_canon"},"voice_and_dialogue":{},"relationships":[],"personality_and_behavior":{},"visual_canon":{}}), encoding="utf-8")
    alias = tmp_path / "character-bibles" / "MZ-CHAR-PATCH"; alias.mkdir()
    (alias / "bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":"MZ-CHAR-PATCH","current_display_name":"Patch","alias_of":"MZ-CHAR-ZOMBIE"}}), encoding="utf-8")
    issue = tmp_path / "02_MONTHLY_ISSUES" / "2027-01_Issue_01"; issue.mkdir()
    (issue / "issue_brief.md").write_text("Issue ID: MZ-2027-01-01\nWorking Title: Test\nMain Character: MZ-CHAR-001\nSupporting Characters: MZ-CHAR-PATCH\nPage Count: 2\nPanel Count: 2\n", encoding="utf-8")
    (issue / "metadata.json").write_text(json.dumps({"issue_id":"MZ-2027-01-01","title":"Test","primary_character":"MZ-CHAR-001","guest_character":"MZ-CHAR-PATCH","page_count":2,"panel_count":2}), encoding="utf-8")
    state={"schema_version":"1.0","active_stage":"outline","transitions":[],"approvals":{}}
    story._write_json(issue / ".workflow-status.json", state)
    story.bible_store._IDENTITY_INDEXES.clear()
    return tmp_path, issue


def outline(issue_id="MZ-2027-01-01"):
    return f"# {issue_id} — Test\nLogline: Safe story\nTheme: Trust\nPage count: 2\nEmotional arc: doubt to trust\nConflict: signal\nEnding: reunion\n## Page map\nPage 1 — opening\nPage 2 — ending\n"


def script(issue_id="MZ-2027-01-01"):
    return f"# {issue_id} — Script\n### Page 1 — Opening\n**Panel 1.1 (Full)**\n- Location: Lab\n- Characters: MZ-CHAR-001\n- Action: Enters\n- Dialogue: ASH: Ready.\n- Continuity notes: Current canon\n"


def test_invalid_issue_and_variant_ids_rejected(factory):
    root, issue = factory
    with pytest.raises(story.StoryWorkspaceError): story._safe_variant("../escape", "outline")
    with pytest.raises(story.issue_workflow.IssueWorkflowError): story.issue_workflow.find_issue("../escape", root)


def test_snapshot_hashes_sources_and_deduplicates_alias(factory):
    root, issue = factory
    snap = story.canon_snapshot(issue, root, "outline")
    assert snap["character_ids"] == ["MZ-CHAR-001", "MZ-CHAR-ZOMBIE"]
    assert snap["alias_resolutions"]["MZ-CHAR-PATCH"] == "MZ-CHAR-ZOMBIE"
    assert all(len(source["sha256"]) == 64 for source in snap["canon_sources"])
    assert not (issue / ".story-workspace").exists()


def test_manual_prompt_and_multiple_variants_are_preserved(factory):
    root, issue = factory
    prompt = story.prompt_package(issue, root, "outline")
    assert prompt["provider"] == "manual_prompt" and "Output contract" in prompt["prompt"]
    first = story.import_variant(issue, root, "outline", {"content":outline(),"provider":"manual"})
    second = story.import_variant(issue, root, "outline", {"content":outline()+"\nOwner alternative\n"})
    assert first["variant_id"] != second["variant_id"]
    assert len(story.variants(issue, root, "outline")) == 2
    assert all(v["source_type"] == "manual_import" for v in story.variants(issue, root, "outline"))


def test_validation_approval_staleness_and_immutability(factory):
    root, issue = factory
    bad = story.import_variant(issue, root, "outline", {"content":"MZ-2027-01-01"})
    assert bad["validation"]["status"] == "failed"
    with pytest.raises(story.StoryWorkspaceError, match="validation"): story.approve(issue, root, "outline", bad["variant_id"])
    good = story.import_variant(issue, root, "outline", {"content":outline()})
    approved = story.approve(issue, root, "outline", good["variant_id"])
    assert approved["approval_current"]
    with pytest.raises(story.StoryWorkspaceError, match="immutable"): story.approve(issue, root, "outline", good["variant_id"])
    (root / "00_SYSTEM" / "world_bible.md").write_text("changed canon\n", encoding="utf-8")
    assert story.variants(issue, root, "outline")[1]["canon_stale"]
    with pytest.raises(story.StoryWorkspaceError, match="current approved"): story.promote(issue, root, "outline", good["variant_id"])


def test_outline_promotion_is_atomic_and_overwrite_protected(factory):
    root, issue = factory
    variant = story.import_variant(issue, root, "outline", {"content":outline()}); story.approve(issue, root, "outline", variant["variant_id"])
    result = story.promote(issue, root, "outline", variant["variant_id"])
    assert result["ok"] and (issue / "issue_outline.md").read_text(encoding="utf-8") == outline()
    assert not list(issue.rglob("*.tmp"))
    with pytest.raises(story.StoryWorkspaceError, match="already promoted"): story.promote(issue, root, "outline", variant["variant_id"], True)


def test_existing_final_is_not_silently_overwritten(factory):
    root, issue = factory
    (issue / "issue_outline.md").write_text("owner work", encoding="utf-8")
    variant = story.import_variant(issue, root, "outline", {"content":outline()}); story.approve(issue, root, "outline", variant["variant_id"])
    with pytest.raises(story.StoryWorkspaceError, match="replacement confirmation"): story.promote(issue, root, "outline", variant["variant_id"])
    assert (issue / "issue_outline.md").read_text(encoding="utf-8") == "owner work"


def test_script_requires_approved_outline_and_script_stage(factory):
    root, issue = factory
    with pytest.raises(story.StoryWorkspaceError, match="active workflow stage script"): story.import_variant(issue, root, "script", {"content":script()})
    outline_variant=story.import_variant(issue, root, "outline", {"content":outline()}); story.approve(issue, root, "outline", outline_variant["variant_id"])
    state=json.loads((issue/".workflow-status.json").read_text()); state["active_stage"]="script"; story._write_json(issue/".workflow-status.json",state)
    first=story.import_variant(issue, root, "script", {"content":script()}); second=story.import_variant(issue, root, "script", {"content":script()+"\n### Page 2 — End\n"})
    assert len(story.variants(issue, root, "script")) == 2
    approved=story.approve(issue, root, "script", first["variant_id"]); assert approved["approval_current"]


def test_duplicate_panels_fail_script_validation(factory):
    root, issue = factory
    validation=story._validation("script", script()+script(), story._brief(issue))
    assert any("Duplicate panel" in f["message"] for f in validation["findings"])


def test_records_contain_no_absolute_windows_paths(factory):
    root, issue = factory
    story.prompt_package(issue, root, "outline")
    for path in (issue / ".story-workspace").rglob("*"):
        if path.is_file(): assert "I:\\" not in path.read_text(encoding="utf-8")
