import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[3] / "00_SYSTEM" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import new_issue


@pytest.fixture()
def factory(tmp_path):
    (tmp_path / "02_MONTHLY_ISSUES").mkdir()
    (tmp_path / "01_IDEAS_INBOX").mkdir()
    bible = tmp_path / "character-bibles" / "MZ-CHAR-TEST"
    bible.mkdir(parents=True)
    (bible / "bible.yaml").write_text(yaml.safe_dump({"identification": {"character_id": "MZ-CHAR-TEST"}}), encoding="utf-8")
    return tmp_path


def payload(**updates):
    data = {"issue_id": "MZ-2027-01-01", "title": "Test Issue", "month": 1, "year": 2027, "edition_number": 1, "issue_type": "Monthly", "primary_character": "MZ-CHAR-TEST", "core_premise": "A signal appears", "main_conflict": "The signal divides the team", "emotional_goal": "Trust", "opening_situation": "A quiet morning", "ending_direction": "The team reconnects"}
    data.update(updates)
    return data


def test_valid_issue_creation(factory):
    result = new_issue.create_issue(payload(), factory)
    folder = factory / result["location"]
    assert result["stage"] == "1. Intake"
    assert (folder / "issue_brief.md").exists()
    assert (folder / "metadata.json").exists()


@pytest.mark.parametrize("updates, message", [
    ({"issue_id": "../escape"}, "Issue ID"),
    ({"primary_character": "MZ-CHAR-NOPE"}, "Unknown character"),
    ({"title": ""}, "Missing required"),
])
def test_invalid_issue_rejected(factory, updates, message):
    with pytest.raises(new_issue.IssueCreationError, match=message):
        new_issue.create_issue(payload(**updates), factory)


def test_duplicate_issue_is_protected(factory):
    new_issue.create_issue(payload(), factory)
    with pytest.raises(new_issue.IssueCreationError, match="already exists"):
        new_issue.create_issue(payload(), factory)
