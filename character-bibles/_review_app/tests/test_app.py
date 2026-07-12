import sys
from pathlib import Path

import pytest
import yaml

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import app as review_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    root = tmp_path / "character-bibles"
    char = root / "MZ-CHAR-API"
    (char / "references").mkdir(parents=True)
    data = {
        "schema_version": "1.0",
        "identification": {
            "current_display_name": "API Test",
            "series_name": "API",
            "personal_name": None,
            "codename": None,
            "nicknames": [],
            "naming_status": "unresolved",
            "character_id": "MZ-CHAR-API",
            "development_level": 1,
            "canon_status": "experimental",
        },
        "visual_canon": {
            "primary_reference_image": None,
            "supporting_reference_images": [],
            "features_that_must_never_change": [],
            "features_that_may_vary": [],
            "prohibited_visual_additions": [],
            "glasses_status": "unknown",
        },
        "character_core": {
            "dominant_traits": [{
                "category": "role",
                "name": "test trait",
                "value": "test",
                "status": "experimental",
                "strength": "moderate",
                "usage_frequency": "sometimes",
                "confidence": "experimental suggestion",
                "rationale": "test",
                "evidence": ["test"],
                "compatible_contexts": [],
                "incompatible_contexts": [],
                "first_eligible_issue": "next",
                "last_used_issue": None,
                "source_refs": ["test"],
                "notes": None,
            }]
        },
        "relationships": [],
        "issue_level_usage": {
            "traits_eligible_for_selection": [],
            "maximum_defining_traits_per_issue": 1,
            "maximum_minor_quirks_per_issue": 1,
        },
    }
    (char / "bible.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(review_app, "BIBLES_ROOT", root)
    review_app.app.config.update(TESTING=True)
    with review_app.app.test_client() as test_client:
        yield test_client


def test_character_api_lists_bibles(client):
    res = client.get("/api/characters")
    assert res.status_code == 200
    data = res.get_json()
    assert data[0]["character_id"] == "MZ-CHAR-API"


def test_trait_api_updates_bible(client):
    res = client.post("/api/characters/MZ-CHAR-API/trait", json={
        "path": "character_core.dominant_traits.0",
        "updates": {"action": "approve_established"},
        "note": "approved in API test",
    })
    assert res.status_code == 200
    assert res.get_json()["trait"]["status"] == "established"


def test_story_preview_api_uses_compact_context(client):
    res = client.post("/api/story/preview", json={
        "issue_id": "MZ-API-STORY",
        "characters": [{"character_id": "MZ-CHAR-API", "role": "primary"}],
        "page_count": 1,
        "panel_count": 4,
        "topic": "test",
        "adventure_style": "Mystery",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["packet"]["issue_id"] == "MZ-API-STORY"
    assert data["packet"]["selection_rules"]["full_bible_injected"] is False
    assert "test trait" in data["prompt"]


def test_story_generate_sample_api_returns_script(client):
    res = client.post("/api/story/generate-sample", json={
        "issue_id": "MZ-API-SAMPLE",
        "characters": [{"character_id": "MZ-CHAR-API", "role": "primary"}],
        "page_count": 1,
        "panel_count": 3,
        "topic": "sample",
        "adventure_style": "Comedy of errors",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "Generated Sample Issue" in data["generated_script"]
    assert data["continuity_proposal"]["status"] == "proposed_owner_review_required"


def test_create_issue_api_returns_structured_validation_error(client):
    res = client.post("/api/issues", json={"issue_id": "../escape"})
    assert res.status_code == 400
    assert res.get_json()["ok"] is False
