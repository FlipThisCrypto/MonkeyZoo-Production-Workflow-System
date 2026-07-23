import json
import sys
import threading
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


# ---------------------------------------------------------------------------
# hardening: malformed-input error handling + atomic canon writes
# ---------------------------------------------------------------------------

def _boom(*args, **kwargs):
    raise OSError("simulated disk failure")


def test_malformed_bible_raises_clean_error_not_yamlerror(bible_root):
    """One corrupt bible.yaml must surface as a BibleStoreError (HTTP 400),
    not an uncaught yaml.YAMLError that 500s character resolution."""
    bad = bible_root / "MZ-CHAR-BAD"
    bad.mkdir()
    (bad / "bible.yaml").write_text("identification: [unclosed\n:::\n", encoding="utf-8")
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.resolve_character_id("MZ-CHAR-TEST", bible_root)
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.load_all(bible_root)


def test_malformed_history_raises_clean_error(bible_root):
    hp = bible_store.history_path("MZ-CHAR-TEST", bible_root)
    hp.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.load_history("MZ-CHAR-TEST", bible_root)


@pytest.mark.parametrize("data,path", [
    ({"a": {"b": 1}}, "a.nope"),        # missing dict key
    ({"xs": [1, 2]}, "xs.5"),           # list index out of range
    ({"xs": [1, 2]}, "xs.abc"),         # non-numeric list index
    ({"a": 1}, "a.b"),                  # descend into a scalar
])
def test_get_path_bad_path_raises_clean_error(data, path):
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.get_path(data, path)


@pytest.mark.parametrize("data,path", [
    ({"a": {}}, "a.b.c"),               # missing intermediate key
    ({"xs": [1]}, "xs.9"),              # list index out of range
    ({"xs": [1]}, "xs.x"),              # non-numeric list index
])
def test_set_path_bad_path_raises_clean_error(data, path):
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.set_path(data, path, "v")


def test_save_bible_round_trip_preserves_edit(bible_root):
    data = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    data["identification"]["current_display_name"] = "Renamed"
    bible_store.save_bible("MZ-CHAR-TEST", data, bible_root)
    reloaded = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    assert reloaded["identification"]["current_display_name"] == "Renamed"


def test_save_bible_is_atomic_original_intact_on_failure(bible_root, monkeypatch):
    """A crash during the write (os.replace failing) must leave the original
    canon bible.yaml untouched and leave no temp litter behind."""
    path = bible_root / "MZ-CHAR-TEST" / "bible.yaml"
    original = path.read_text(encoding="utf-8")
    data = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    data["identification"]["current_display_name"] = "HALF-WRITTEN"
    monkeypatch.setattr(bible_store.os, "replace", _boom)
    with pytest.raises(OSError):
        bible_store.save_bible("MZ-CHAR-TEST", data, bible_root)
    assert path.read_text(encoding="utf-8") == original          # canon untouched
    leftovers = [p.name for p in (bible_root / "MZ-CHAR-TEST").iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []                                        # temp cleaned up


# --- canon status-transition machine (normalize_trait_updates) ---

@pytest.mark.parametrize("action,status,review", [
    ("approve_canon", "canon", "approve_as_canon"),
    ("approve_established", "established", "approve_as_established"),
    ("keep_experimental", "experimental", "keep_experimental"),
    ("mark_optional", "optional", "mark_optional"),
    ("mark_dormant", "dormant", "mark_dormant"),
    ("retire", "retired", "retire"),
    ("reject", "retired", "reject"),
])
def test_review_action_maps_to_canon_status(action, status, review):
    out = bible_store.normalize_trait_updates({"action": action})
    assert out["status"] == status
    assert out["_review_action"] == review
    assert "action" not in out                       # the action key is consumed
    assert out["status"] in bible_store.VALID_STATUSES


def test_retire_and_reject_force_usage_never():
    assert bible_store.normalize_trait_updates({"action": "retire"})["usage_frequency"] == "never"
    assert bible_store.normalize_trait_updates({"action": "reject"})["usage_frequency"] == "never"


def test_reject_prefixes_existing_notes():
    out = bible_store.normalize_trait_updates({"action": "reject", "notes": "off model"})
    assert out["notes"].startswith("REJECTED:") and "off model" in out["notes"]


@pytest.mark.parametrize("updates", [{"action": "wobble"}, {"value": "x"}, {}])
def test_unknown_or_missing_action_is_plain_edit(updates):
    out = bible_store.normalize_trait_updates(updates)
    assert out["_review_action"] == "edit_trait"
    assert "status" not in out                        # a plain edit must not invent a status


def test_invalid_status_is_rejected():
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.normalize_trait_updates({"status": "not-a-real-status"})


def test_invalid_strength_is_rejected():
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.normalize_trait_updates({"strength": "ludicrous"})


def test_identity_index_invalidated_on_rename(bible_root):
    # The identity index (name/alias -> id) is memoized per root. save_bible must
    # invalidate it, or renaming a character's display name would leave the new name
    # unresolvable until a server restart. Guard that invalidation explicitly.
    root = bible_root
    assert bible_store.resolve_character_id("Test", root) == "MZ-CHAR-TEST"     # builds+caches index
    data = bible_store.load_bible("MZ-CHAR-TEST", root)
    data["identification"]["current_display_name"] = "Renamed Hero"
    bible_store.save_bible("MZ-CHAR-TEST", data, root)                          # must invalidate cache
    assert bible_store.resolve_character_id("Renamed Hero", root) == "MZ-CHAR-TEST"
    assert bible_store.resolve_character_id("MZ-CHAR-TEST", root) == "MZ-CHAR-TEST"
    with pytest.raises(bible_store.BibleStoreError):
        bible_store.resolve_character_id("Test", root)                          # old name is gone


# --- concurrency: per-character write serialization (no lost updates/audit) ----

def test_character_lock_is_per_character_and_stable():
    a1 = bible_store._character_lock("MZ-CHAR-A")
    a2 = bible_store._character_lock("MZ-CHAR-A")
    b = bible_store._character_lock("MZ-CHAR-B")
    assert a1 is a2          # same character -> one lock -> edits serialize
    assert a1 is not b       # different characters -> independent locks -> parallel


def test_concurrent_edits_record_every_audit_entry(bible_root):
    # High-contention: all threads enter the edit at once. Without per-character
    # serialization the racing append_history() calls drop entries; with the lock
    # every edit is durably audited.
    n = 40
    barrier = threading.Barrier(n)
    errors: list[Exception] = []

    def edit(i: int) -> None:
        try:
            barrier.wait()
            bible_store.update_field(
                "MZ-CHAR-TEST", "identification.current_display_name",
                f"Name {i}", root=bible_root,
            )
        except Exception as exc:  # noqa: BLE001 - surface any thread failure to the assert
            errors.append(exc)

    threads = [threading.Thread(target=edit, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    history = bible_store.load_history("MZ-CHAR-TEST", bible_root)
    assert len(history) == n, f"expected {n} audit entries, got {len(history)} (lost under concurrency)"
    # the bible survived concurrent writes intact and readable
    data = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    assert data["identification"]["current_display_name"].startswith("Name ")


def test_concurrent_trait_edits_keep_history_and_bible_consistent(bible_root):
    n = 25
    barrier = threading.Barrier(n)

    def edit() -> None:
        barrier.wait()
        bible_store.update_trait(
            "MZ-CHAR-TEST", "character_core.dominant_traits.0",
            {"action": "keep_experimental"}, root=bible_root,
        )

    threads = [threading.Thread(target=edit) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(bible_store.load_history("MZ-CHAR-TEST", bible_root)) == n
    data = bible_store.load_bible("MZ-CHAR-TEST", bible_root)
    assert data["character_core"]["dominant_traits"][0]["status"] == "experimental"
