"""Regression coverage for the character-bible schema validator.

Focus: duplicate character_id detection. Two Bibles sharing a character_id is a
canon-integrity violation (identity resolution downstream is last-write-wins, so
the two characters silently collapse into one). The validator must FAIL (exit 1)
on that, while a clean tree of distinct IDs still PASSES (exit 0). Invoked as a
subprocess because that is exactly how workflow_engine.py runs it and the exit
code is the contract other stages depend on. The module's filename is hyphenated
(not importable), so subprocess is also the only clean entry point.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

VALIDATOR = Path(__file__).resolve().parents[1] / "validate-character-bibles.py"


def _bible(identification: dict) -> dict:
    # A minimal but schema-complete Bible: enough valid structure that the ONLY
    # thing under test is the identity check, not incidental field errors.
    ident = {
        "current_display_name": identification.get("character_id", "X"),
        "naming_status": "codename_only",
        "character_id": identification["character_id"],
        "development_level": 1,
        "canon_status": "canon",
    }
    ident.update(identification)
    return {
        "identification": ident,
        "visual_canon": {},
        "issue_level_usage": {
            "maximum_defining_traits_per_issue": 1,
            "maximum_minor_quirks_per_issue": 1,
        },
    }


def _write_bible(root: Path, folder: str, character_id: str, **ident) -> None:
    d = root / folder
    d.mkdir(parents=True)
    (d / "bible.yaml").write_text(
        yaml.safe_dump(_bible({"character_id": character_id, **ident})), encoding="utf-8"
    )


def _run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(root), "--workspace-root", str(root)],
        capture_output=True, text=True,
    )


def test_distinct_ids_pass(tmp_path):
    _write_bible(tmp_path, "MZ-CHAR-001", "MZ-CHAR-001")
    _write_bible(tmp_path, "MZ-CHAR-002", "MZ-CHAR-002")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "duplicate character_id" not in result.stdout


def test_duplicate_id_fails_with_named_error(tmp_path):
    # two different Bible folders both claim MZ-CHAR-001 -> identity collision
    _write_bible(tmp_path, "folder_a", "MZ-CHAR-001")
    _write_bible(tmp_path, "folder_b", "MZ-CHAR-001")
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "duplicate character_id 'MZ-CHAR-001'" in result.stdout
    # the error must name BOTH offending files so the owner can resolve it
    assert "folder_a" in result.stdout and "folder_b" in result.stdout


def test_display_name_collision_across_characters_fails(tmp_path):
    # distinct character_ids, but both resolve from the handle "Moodz" -> the
    # script reference "Moodz" would silently load the wrong character.
    _write_bible(tmp_path, "MZ-CHAR-001", "MZ-CHAR-001", current_display_name="Moodz")
    _write_bible(tmp_path, "MZ-CHAR-009", "MZ-CHAR-009", current_display_name="Moodz")
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "identity handle 'moodz' resolves to 2 different characters" in result.stdout
    assert "MZ-CHAR-001" in result.stdout and "MZ-CHAR-009" in result.stdout


def test_nickname_collision_across_characters_fails(tmp_path):
    # a shared nickname is also a resolution handle -> ambiguous identity.
    _write_bible(tmp_path, "MZ-CHAR-001", "MZ-CHAR-001", current_display_name="Moodz", nicknames=["shadow"])
    _write_bible(tmp_path, "MZ-CHAR-002", "MZ-CHAR-002", current_display_name="TwoTone", nicknames=["Shadow"])
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "identity handle 'shadow' resolves to 2 different characters" in result.stdout


def test_shared_series_name_archetype_is_allowed(tmp_path):
    # series_name is a shared archetype descriptor (every lead carries the same
    # value); it is NOT a unique resolution handle, so sharing it must PASS.
    _write_bible(tmp_path, "MZ-CHAR-001", "MZ-CHAR-001", current_display_name="Moodz",
                 series_name="Emo Monkey / Fusion Squad lead")
    _write_bible(tmp_path, "MZ-CHAR-002", "MZ-CHAR-002", current_display_name="TwoTone",
                 series_name="Emo Monkey / Fusion Squad lead")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "identity handle" not in result.stdout


def test_alias_sharing_its_target_handle_is_not_a_collision(tmp_path):
    # an alias Bible resolves to its alias_of target, so a nickname it shares with
    # that same target maps to ONE character -> not a collision.
    _write_bible(tmp_path, "MZ-CHAR-002", "MZ-CHAR-002", current_display_name="TwoTone", nicknames=["Two Tone"])
    _write_bible(tmp_path, "MZ-CHAR-TT", "MZ-CHAR-TT", current_display_name="TT",
                 alias_of="MZ-CHAR-002", nicknames=["Two Tone"])
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "identity handle" not in result.stdout
