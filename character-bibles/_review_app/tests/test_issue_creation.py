import json
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "00_SYSTEM" / "scripts"))
import new_issue


@pytest.fixture()
def factory(tmp_path):
    (tmp_path / "02_MONTHLY_ISSUES").mkdir()
    (tmp_path / "01_IDEAS_INBOX").mkdir()
    for cid, name in (("MZ-CHAR-TEST", "Ash"), ("MZ-CHAR-GUEST", "Moodz")):
        bible = tmp_path / "character-bibles" / cid
        bible.mkdir(parents=True)
        (bible / "bible.yaml").write_text(yaml.safe_dump({"identification": {"character_id": cid, "current_display_name": name}}), encoding="utf-8")
    return tmp_path


def payload(**updates):
    data = {"issue_id": "MZ-2027-01-01", "title": "Test Issue", "month": 1, "year": 2027, "edition_number": 1, "issue_type": "Monthly", "primary_character": "MZ-CHAR-TEST", "guest_character": "MZ-CHAR-GUEST", "core_premise": "A mysterious signal appears", "main_conflict": "The signal divides the team", "emotional_goal": "Trust", "opening_situation": "A quiet morning at the relay", "ending_direction": "The team reconnects", "required_canon_references": "Current season relay rules", "prohibited_story_elements": "No unapproved transformations", "page_count": 8, "panel_count": 20, "output_requirements": ["cover", "metadata", "social copy", "QA"]}
    data.update(updates)
    return data


def test_valid_creation_is_complete_and_schema_valid(factory):
    result = new_issue.create_issue(payload(), factory)
    folder = factory / result["location"]
    assert set(result["files_created"]) == {"cover_prompt.md", "final_export_checklist.md", "generation_log.md", "issue_brief.json", "issue_brief.md", "issue_outline.md", "issue_script.md", "metadata.json", "qa_report.md", "social_posts.md"}
    brief = json.loads((folder / "issue_brief.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "00_SYSTEM" / "issue_brief_schema.json").read_text(encoding="utf-8"))
    validate(brief, schema)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["issue_type"] == "Monthly"
    assert metadata["opening_situation"] == payload()["opening_situation"]
    assert not (folder / "page_panel_plan.json").exists()
    assert not (folder / "art_prompt_pack.json").exists()


@pytest.mark.parametrize("updates,message", [
    ({"issue_id": "../escape"}, "issue_id"), ({"issue_id": "MZ-2027-01-01/evil"}, "issue_id"),
    ({"primary_character": "MZ-CHAR-NOPE"}, "Unknown character"),
    ({"guest_character": "MZ-CHAR-NOPE"}, "Unknown character"),
    ({"guest_character": "MZ-CHAR-TEST"}, "must differ"), ({"title": ""}, "Missing required"),
    ({"year": "nope"}, "year must be"), ({"month": True}, "month must be"),
    ({"page_count": 0}, "page_count must be between"), ({"page_count": 65}, "page_count must be between"),
    ({"panel_count": 0}, "panel_count must be between"), ({"panel_count": 301}, "panel_count must be between"),
    ({"output_requirements": ["cloud publish"]}, "output_requirements"),
    ({"core_premise": ["not text"]}, "core_premise must be text"),
])
def test_invalid_requests_are_rejected(factory, updates, message):
    with pytest.raises(new_issue.IssueCreationError, match=message):
        new_issue.create_issue(payload(**updates), factory)


def test_duplicate_id_and_edition_are_distinct(factory):
    new_issue.create_issue(payload(), factory)
    with pytest.raises(new_issue.IssueCreationError, match="Edition folder"):
        new_issue.create_issue(payload(issue_id="MZ-2027-01-02"), factory)
    (factory / "02_MONTHLY_ISSUES" / "2027-01_Issue_01").rename(factory / "02_MONTHLY_ISSUES" / "2027-01_Issue_02")
    with pytest.raises(new_issue.IssueCreationError, match="Issue ID"):
        new_issue.create_issue(payload(edition_number=3), factory)


@pytest.mark.parametrize("failure_name", ["issue_script.md", "metadata.json"])
def test_write_failure_cleans_temp_and_allows_retry(factory, monkeypatch, failure_name):
    original = new_issue._write_text
    def fail_once(path, content):
        if path.name == failure_name:
            raise OSError("injected")
        original(path, content)
    monkeypatch.setattr(new_issue, "_write_text", fail_once)
    with pytest.raises(new_issue.IssueCreationError, match="no files were committed"):
        new_issue.create_issue(payload(), factory)
    assert not list((factory / "02_MONTHLY_ISSUES").iterdir())
    assert not list((factory / "01_IDEAS_INBOX").iterdir())
    monkeypatch.setattr(new_issue, "_write_text", original)
    assert new_issue.create_issue(payload(), factory)["ok"] is True


def test_idea_failure_rolls_back_issue(factory, monkeypatch):
    original = new_issue.os.rename
    def fail_idea(source, destination):
        if Path(destination).parent.name == "01_IDEAS_INBOX":
            raise OSError("injected idea failure")
        original(source, destination)
    monkeypatch.setattr(new_issue.os, "rename", fail_idea)
    with pytest.raises(new_issue.IssueCreationError, match="no files were committed"):
        new_issue.create_issue(payload(), factory)
    assert not list((factory / "02_MONTHLY_ISSUES").iterdir())
    assert not list((factory / "01_IDEAS_INBOX").iterdir())


def test_non_object_request_rejected(factory):
    with pytest.raises(new_issue.IssueCreationError, match="JSON object"):
        new_issue.create_issue([], factory)


def test_legacy_patch_id_normalizes_to_zombie(factory):
    alias = factory / "character-bibles" / "MZ-CHAR-PATCH"
    alias.mkdir()
    (alias / "bible.yaml").write_text(yaml.safe_dump({"identification": {"character_id": "MZ-CHAR-PATCH", "current_display_name": "Patch", "alias_of": "MZ-CHAR-TEST"}}), encoding="utf-8")
    normalized = new_issue.normalize_request(payload(primary_character="MZ-CHAR-PATCH", guest_character=""), factory)
    assert normalized["primary_character"] == "MZ-CHAR-TEST"
