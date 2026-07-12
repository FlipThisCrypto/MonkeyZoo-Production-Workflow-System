import json
import sys
from pathlib import Path

import pytest
import yaml

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import bible_store


def sample_trait():
    return {
        "category": "speech_pattern",
        "name": "short line",
        "value": "Uses short lines.",
        "status": "experimental",
        "strength": "moderate",
        "usage_frequency": "sometimes",
        "confidence": "experimental suggestion",
        "rationale": "Test rationale",
        "evidence": ["test"],
        "compatible_contexts": ["quiet scenes"],
        "incompatible_contexts": ["long speeches"],
        "first_eligible_issue": "next",
        "last_used_issue": None,
        "source_refs": ["test"],
        "notes": None,
    }


@pytest.fixture()
def bible_root(tmp_path):
    root = tmp_path / "character-bibles"
    char = root / "MZ-CHAR-TEST"
    (char / "references" / "primary").mkdir(parents=True)
    image = char / "references" / "primary" / "primary-reference.png"
    image.write_bytes(b"fake image bytes")
    data = {
        "schema_version": "1.0",
        "identification": {
            "current_display_name": "Test",
            "series_name": "Test Series",
            "personal_name": None,
            "codename": None,
            "nicknames": [],
            "naming_status": "unresolved",
            "character_id": "MZ-CHAR-TEST",
            "development_level": 1,
            "canon_status": "experimental",
        },
        "visual_canon": {
            "primary_reference_image": "references/primary/primary-reference.png",
            "supporting_reference_images": [],
            "features_that_must_never_change": [],
            "features_that_may_vary": [],
            "prohibited_visual_additions": [],
            "glasses_status": "unknown",
        },
        "character_core": {"dominant_traits": [sample_trait()]},
        "relationships": [],
        "issue_level_usage": {
            "traits_eligible_for_selection": [sample_trait()],
            "maximum_defining_traits_per_issue": 1,
            "maximum_minor_quirks_per_issue": 1,
            "catchphrase_cooldown": {"minimum_issues_between_uses": 1, "last_used_issue": None, "notes": None},
            "running_gag_cooldown": {"minimum_issues_between_uses": 1, "last_used_issue": None, "notes": None},
            "recent_traits_used": [],
            "traits_that_should_not_appear_together": [],
            "required_context_for_special_traits": [],
        },
        "growth_and_continuity": {"published_appearances": ["MZ-TEST"]},
    }
    (char / "bible.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    (char / "references" / "source-map.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    return root


def test_read_summary_counts(bible_root):
    data = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    summary = bible_store.character_summary("MZ-CHAR-TEST", data)
    assert summary["display_name"] == "Test"
    assert summary["experimental_traits"] == 2
    assert "Naming unresolved" in summary["continuity_warnings"]


def test_edit_trait_saves_and_records_history(bible_root):
    updated = bible_store.update_trait(
        "MZ-CHAR-TEST",
        "character_core.dominant_traits.0",
        {"action": "approve_canon", "strength": "strong"},
        "owner approved",
        bible_root,
    )
    assert updated["status"] == "canon"
    assert updated["strength"] == "strong"
    saved = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    assert saved["character_core"]["dominant_traits"][0]["status"] == "canon"
    history = bible_store.load_history("MZ-CHAR-TEST", bible_root)
    assert history[-1]["approval_status"] == "approve_as_canon"
    assert history[-1]["previous_value"]["status"] == "experimental"


def test_undo_restores_previous_value(bible_root):
    bible_store.update_field(
        "MZ-CHAR-TEST",
        "identification.naming_status",
        "personal_name_canon",
        "mark_name_canon",
        "test",
        bible_root,
    )
    assert bible_store.load_bible("MZ-CHAR-TEST", bible_root)["identification"]["naming_status"] == "personal_name_canon"
    bible_store.undo_last("MZ-CHAR-TEST", bible_root)
    assert bible_store.load_bible("MZ-CHAR-TEST", bible_root)["identification"]["naming_status"] == "unresolved"


def test_comparison_returns_overlap(bible_root):
    result = bible_store.comparison(["MZ-CHAR-TEST"], bible_root)
    assert result["characters"][0]["summary"]["character_id"] == "MZ-CHAR-TEST"
    assert "personality" in result["overlap"]


def test_comparison_uses_trait_value_for_generic_role_names():
    items = [
        {
            "summary": {"character_id": "A", "experimental_traits": 1, "canon_traits": 5},
            "traits": [{"path": "character_core.team_role.0", "name": "team role", "value": "emotional anchor"}],
        },
        {
            "summary": {"character_id": "B", "experimental_traits": 1, "canon_traits": 5},
            "traits": [{"path": "character_core.team_role.0", "name": "team role", "value": "technical explainer"}],
        },
        {
            "summary": {"character_id": "C", "experimental_traits": 1, "canon_traits": 5},
            "traits": [{"path": "character_core.team_role.0", "name": "team role", "value": "technical explainer"}],
        },
    ]
    overlap = bible_store.compute_overlap(items)
    assert "team role" not in overlap["story_role"]
    assert overlap["story_role"]["technical explainer"] == ["B", "C"]


def test_comparison_dedupes_same_character_and_ignores_shared_writing_rules():
    items = [
        {
            "summary": {"character_id": "A", "experimental_traits": 1, "canon_traits": 5},
            "traits": [
                {"path": "story_use.situations_to_avoid.0", "name": "avoid caricature", "value": "Do not reduce the character to the easiest visual joke or single trait."},
                {"path": "character_core.team_role.0", "name": "team role", "value": "emotional anchor"},
                {"path": "story_use.best_adventure_roles.0", "name": "best adventure role", "value": "emotional anchor"},
            ],
        },
        {
            "summary": {"character_id": "B", "experimental_traits": 1, "canon_traits": 5},
            "traits": [
                {"path": "story_use.situations_to_avoid.0", "name": "avoid caricature", "value": "Do not reduce the character to the easiest visual joke or single trait."},
                {"path": "character_core.team_role.0", "name": "team role", "value": "emotional anchor"},
            ],
        },
    ]
    overlap = bible_store.compute_overlap(items)
    assert "do not reduce the character to the easiest visual joke or single trait." not in overlap["story_role"]
    assert overlap["story_role"]["emotional anchor"] == ["A", "B"]
