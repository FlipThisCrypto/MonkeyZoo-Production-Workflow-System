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
    # thing under test is duplicate-id detection, not incidental field errors.
    return {
        "identification": {
            "current_display_name": identification.get("character_id", "X"),
            "naming_status": "codename_only",
            "character_id": identification["character_id"],
            "development_level": 1,
            "canon_status": "canon",
        },
        "visual_canon": {},
        "issue_level_usage": {
            "maximum_defining_traits_per_issue": 1,
            "maximum_minor_quirks_per_issue": 1,
        },
    }


def _write_bible(root: Path, folder: str, character_id: str) -> None:
    d = root / folder
    d.mkdir(parents=True)
    (d / "bible.yaml").write_text(
        yaml.safe_dump(_bible({"character_id": character_id})), encoding="utf-8"
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
