import json
import sys
from pathlib import Path

import pytest
import yaml

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import story_context


def trait(name, value, status="established", strength="strong", category="role", last_used_issue=None):
    return {
        "category": category,
        "name": name,
        "value": value,
        "status": status,
        "strength": strength,
        "usage_frequency": "sometimes",
        "confidence": "test",
        "rationale": f"Long rationale for {name} that should not appear in compact prompts.",
        "evidence": ["test evidence"],
        "compatible_contexts": ["mystery", "team"],
        "incompatible_contexts": [],
        "first_eligible_issue": "next",
        "last_used_issue": last_used_issue,
        "source_refs": ["source ref that should not be in prompt"],
        "notes": None,
    }


def write_bible(root, character_id, name, glasses_status="confirmed_no_glasses", personal_name=None,
                naming_status="unresolved", catchphrase_last=None):
    char = root / character_id
    (char / "references" / "primary").mkdir(parents=True)
    data = {
        "schema_version": "1.0",
        "identification": {
            "current_display_name": name,
            "series_name": name,
            "personal_name": personal_name,
            "codename": None,
            "nicknames": [],
            "naming_status": naming_status,
            "character_id": character_id,
            "development_level": 2,
            "canon_status": "approved_canon",
        },
        "visual_canon": {
            "primary_reference_image": "references/primary/primary-reference.png",
            "supporting_reference_images": ["references/alternate/pose.png"],
            "features_that_must_never_change": [trait("visual anchor", f"{name} visual", "canon", "defining", "visual_feature")],
            "features_that_may_vary": [],
            "prohibited_visual_additions": [],
            "glasses_status": glasses_status,
        },
        "character_core": {
            "team_role": [trait("team role", f"{name} role")],
            "dominant_traits": [
                trait("defining trait", f"{name} defining", "established", "defining", "role"),
                trait("experimental edge", f"{name} experiment", "experimental", "moderate", "specific_weakness"),
            ],
            "strengths": [trait("strength", f"{name} strength", "established", "strong", "specific_talent")],
            "flaws": [trait("flaw", f"{name} flaw", "experimental", "moderate", "specific_weakness")],
        },
        "voice_and_dialogue": {
            "catchphrase": [trait("catchphrase", f"{name} says go", "established", "moderate", "speech_pattern")],
        },
        "behavior": {"quirks": [trait("quirk", f"{name} quirk", "established", "subtle", "physical_behavior")]},
        "running_elements": {"running_gags": [trait("running gag", f"{name} gag", "established", "moderate", "running_gag")]},
        "relationships": [],
        "growth_and_continuity": {"published_appearances": ["MZ-OLD"], "open_character_arcs": []},
        "issue_level_usage": {
            "traits_eligible_for_selection": [
                trait("defining trait", f"{name} defining", "established", "defining", "role"),
                trait("strength", f"{name} strength", "established", "strong", "specific_talent"),
                trait("flaw", f"{name} flaw", "experimental", "moderate", "specific_weakness"),
                trait("quirk", f"{name} quirk", "established", "subtle", "physical_behavior"),
            ],
            "maximum_defining_traits_per_issue": 1,
            "maximum_minor_quirks_per_issue": 1,
            "catchphrase_cooldown": {"minimum_issues_between_uses": 1, "last_used_issue": catchphrase_last, "notes": None},
            "running_gag_cooldown": {"minimum_issues_between_uses": 1, "last_used_issue": None, "notes": None},
            "recent_traits_used": [],
            "traits_that_should_not_appear_together": [],
            "required_context_for_special_traits": [],
        },
    }
    (char / "bible.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return data


@pytest.fixture()
def story_root(tmp_path):
    root = tmp_path / "character-bibles"
    write_bible(root, "MZ-CHAR-CLEVER", "Clever", "confirmed_glasses")
    write_bible(root, "MZ-CHAR-OTHER", "Other", "confirmed_no_glasses", personal_name="Hidden", naming_status="unresolved", catchphrase_last="MZ-OLD")
    write_bible(root, "MZ-CHAR-GLASSES", "Glasses Conflict", "confirmed_glasses")
    return root


def setup(characters, panel_count=12, strictness="balanced"):
    return {
        "issue_id": "MZ-TEST",
        "characters": characters,
        "page_count": 4,
        "panel_count": panel_count,
        "topic": "mystery",
        "adventure_style": "Mystery",
        "canon_strictness": strictness,
    }


def test_prompt_uses_compact_packet_not_full_bible(story_root, tmp_path):
    preview = story_context.build_preview(setup([{"character_id": "MZ-CHAR-CLEVER", "role": "primary"}]), story_root, tmp_path)
    prompt = preview["prompt"]
    assert "Do not load or paste full Character Bibles" in prompt
    assert "Long rationale" not in prompt
    assert "source ref that should not be in prompt" not in prompt
    assert len(prompt) < len((story_root / "MZ-CHAR-CLEVER" / "bible.yaml").read_text(encoding="utf-8"))


def test_catchphrase_cooldown_excludes_phrase(story_root):
    packet = story_context.build_context_packet(story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-OTHER", "role": "primary"}])), story_root)
    character = packet["selected_cast"][0]
    assert character["catchphrases_allowed"] == []
    assert any("cooldown active" in item["reason"] for item in character["excluded_traits"])


def test_minor_and_short_comics_get_fewer_traits(story_root):
    long_packet = story_context.build_context_packet(story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-CLEVER", "role": "primary"}], panel_count=24)), story_root)
    short_packet = story_context.build_context_packet(story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-CLEVER", "role": "primary"}], panel_count=4)), story_root)
    cameo_packet = story_context.build_context_packet(story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-CLEVER", "role": "cameo"}], panel_count=24)), story_root)
    assert len(short_packet["selected_cast"][0]["selected_traits"]) < len(long_packet["selected_cast"][0]["selected_traits"])
    assert len(cameo_packet["selected_cast"][0]["selected_traits"]) == 1


def test_clever_only_glasses_conflict_is_flagged(story_root):
    packet = story_context.build_context_packet(story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-GLASSES", "role": "primary"}])), story_root)
    warnings = packet["warnings"] + story_context.validate_packet(packet)
    assert any("Clever-only glasses" in warning or "Clever-only glasses conflict" in warning for warning in warnings)


def test_experimental_not_canon_and_unresolved_name_blank(story_root):
    packet = story_context.build_context_packet(story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-OTHER", "role": "primary"}])), story_root)
    character = packet["selected_cast"][0]
    assert character["personal_name"] is None
    assert any(trait["status"] == "experimental" for trait in character["experimental_review_required"])
    assert all(trait["status"] != "canon" for trait in character["experimental_review_required"])


def test_post_issue_changes_require_approval_and_packet_saves(story_root, tmp_path):
    preview = story_context.save_preview(setup([{"character_id": "MZ-CHAR-CLEVER", "role": "primary"}]), story_root, tmp_path)
    proposal = preview["continuity_proposal"]
    assert proposal["status"] == "proposed_owner_review_required"
    out_dir = tmp_path / "issues" / "MZ-TEST"
    saved = json.loads((out_dir / "character-context.json").read_text(encoding="utf-8"))
    assert saved["issue_id"] == "MZ-TEST"
    assert (out_dir / "proposed-continuity-update.json").exists()


def test_generate_sample_issue_saves_script_and_proposed_update(story_root, tmp_path):
    result = story_context.generate_sample_issue(
        setup([
            {"character_id": "MZ-CHAR-CLEVER", "role": "primary"},
            {"character_id": "MZ-CHAR-OTHER", "role": "secondary"},
        ], panel_count=6),
        story_root,
        tmp_path,
    )
    out_dir = tmp_path / "issues" / "MZ-TEST"
    script = (out_dir / "generated-script.md").read_text(encoding="utf-8")
    assert "Generated Sample Issue" in script
    assert (out_dir / "script-validation.json").exists()
    assert result["continuity_proposal"]["status"] == "proposed_owner_review_required"
    assert result["continuity_proposal"]["growth_notes"]
    assert script.count("Clever says go") <= 1


def test_glasses_validation_allows_explicit_no_glasses(story_root):
    packet = story_context.build_context_packet(
        story_context.normalize_setup(setup([{"character_id": "MZ-CHAR-OTHER", "role": "primary"}])),
        story_root,
    )
    warnings = story_context.validate_script_text("Other has no glasses in this panel.", packet)
    assert "Other may have incorrect glasses." not in warnings
    warnings = story_context.validate_script_text("Other has unresolved eyewear; do not add glasses.", packet)
    assert "Other may have incorrect glasses." not in warnings
    warnings = story_context.validate_script_text("Other adjusts the glasses in this panel.", packet)
    assert "Other may have incorrect glasses." in warnings
