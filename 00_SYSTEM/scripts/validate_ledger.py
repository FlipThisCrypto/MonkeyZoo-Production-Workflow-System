#!/usr/bin/env python3
"""Validate the MonkeyZoo continuity ledger (canon integrity gate).

The continuity ledger (00_SYSTEM/continuity_ledger.md) is the append-only canon
source-of-truth: every issue appends an entry before Final QA, and downstream
issues read the last entry's OPEN THREADS before writing. A malformed append
(missing section, mistyped ID, or an ID that collides with an existing entry)
silently corrupts that record. This mirrors the character-bible schema gate:
run in CI, it fails (exit 1) on a structurally broken ledger so a bad append
cannot reach main.

Checked per real entry (the fenced format template is excluded):
  * entry ID matches MZ-ED-NN, MZ-YYYY-MM-NN, or ERR-YYYY-MM-DD
  * no two entries share an ID (a duplicate silently overwrites canon history)
  * the five required sections are present: EVENTS, STATE CHANGES, NEW LORE,
    RUNNING JOKES, OPEN THREADS (extra sections such as RETURN PROTOCOL are fine)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]

# Stages at or past Final QA (Gate B). CLAUDE.md / ledger rules 4 & 9: every issue
# MUST append its ledger entry before Final QA can pass, so any issue that has
# reached these stages without a ledger entry is a canon-integrity violation.
LEDGER_REQUIRED_STAGES = {"qa", "release", "published"}

REQUIRED_SECTIONS = ["EVENTS", "STATE CHANGES", "NEW LORE", "RUNNING JOKES", "OPEN THREADS"]
ENTRY_ID = re.compile(r"^(MZ-ED-\d{1,3}|MZ-\d{4}-\d{2}-\d{2}|ERR-\d{4}-\d{2}-\d{2})$")
_HEADER = re.compile(r"^## \[([^\]]+)\].*$", re.M)
# A section label: uppercase words, an optional "(...)" qualifier, then a colon.
_SECTION = re.compile(r"^([A-Z][A-Z ]+?)\s*(?:\([^)]*\))?:", re.M)


def _strip_code_fences(text: str) -> str:
    """Remove ``` fenced blocks so the documented format template (which contains
    a literal ## [ISSUE-ID] header) is not validated as a real entry."""
    return re.sub(r"```.*?```", "", text, flags=re.S)


def validate_ledger(text: str) -> list[str]:
    errors: list[str] = []
    body = _strip_code_fences(text)
    headers = [m.group(1) for m in _HEADER.finditer(body)]
    blocks = _HEADER.split(body)
    # re.split with one capture group yields [pre, id1, block1, id2, block2, ...]
    entry_blocks = blocks[2::2]
    if not headers:
        return ["ledger has no entries"]
    seen: set[str] = set()
    for entry_id, block in zip(headers, entry_blocks):
        if not ENTRY_ID.match(entry_id):
            errors.append(f"[{entry_id}]: malformed entry ID "
                          "(expected MZ-ED-NN, MZ-YYYY-MM-NN, or ERR-YYYY-MM-DD)")
        if entry_id in seen:
            errors.append(f"[{entry_id}]: duplicate entry ID (canon collision — "
                          "corrections must be new ERR-* entries, never a re-use)")
        seen.add(entry_id)
        present = {label.strip() for label in _SECTION.findall(block)}
        for section in REQUIRED_SECTIONS:
            if section not in present:
                errors.append(f"[{entry_id}]: missing required section '{section}'")
    return errors


def ledger_entry_ids(text: str) -> set[str]:
    """The set of entry IDs declared in the ledger (format template excluded)."""
    return {m.group(1) for m in _HEADER.finditer(_strip_code_fences(text))}


def _issue_id_of(folder: Path) -> str | None:
    """Read an issue's canonical ID from metadata.json or its brief."""
    meta = folder / "metadata.json"
    if meta.is_file():
        try:
            value = json.loads(meta.read_text(encoding="utf-8")).get("issue_id")
            if value:
                return str(value)
        except (OSError, ValueError):
            pass
    brief = folder / "issue_brief.md"
    if brief.is_file():
        match = re.search(r"^Issue ID:\s*(\S+)", brief.read_text(encoding="utf-8", errors="replace"), re.M)
        if match:
            return match.group(1)
    return None


def reconcile_with_issues(ledger_text: str, monthly_issues_dir: Path) -> list[dict]:
    """Cross-check the ledger against real production output. Returns the issues
    that have reached Final QA or later but have no ledger entry -- an incomplete
    canon record (the ledger must cover everything that is now true)."""
    entry_ids = ledger_entry_ids(ledger_text)
    missing: list[dict] = []
    if not monthly_issues_dir.is_dir():
        return missing
    for folder in sorted(monthly_issues_dir.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        state_path = folder / ".workflow-status.json"
        if not state_path.is_file():
            continue
        try:
            stage = json.loads(state_path.read_text(encoding="utf-8")).get("active_stage")
        except (OSError, ValueError):
            continue
        if stage not in LEDGER_REQUIRED_STAGES:
            continue
        issue_id = _issue_id_of(folder)
        if issue_id and issue_id not in entry_ids:
            missing.append({"issue_id": issue_id, "stage": stage, "folder": folder.name})
    return missing


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--reconcile" in sys.argv:
        ledger_path = Path(args[0]) if args else FACTORY / "00_SYSTEM" / "continuity_ledger.md"
        issues_dir = Path(args[1]) if len(args) > 1 else FACTORY / "02_MONTHLY_ISSUES"
        if not ledger_path.is_file():
            raise SystemExit(f"Continuity ledger not found: {ledger_path}")
        missing = reconcile_with_issues(ledger_path.read_text(encoding="utf-8"), issues_dir)
        if missing:
            print(f"Ledger reconciliation FAILED: {len(missing)} issue(s) at Final QA or later "
                  "have no ledger entry (append them before treating canon as complete):")
            for item in missing:
                print(f"  - {item['issue_id']} [{item['stage']}] ({item['folder']})")
            raise SystemExit(1)
        print("Ledger reconciliation PASSED: every QA'd/released/published issue has a ledger entry.")
        return

    path = Path(args[0]) if args else FACTORY / "00_SYSTEM" / "continuity_ledger.md"
    if not path.is_file():
        raise SystemExit(f"Continuity ledger not found: {path}")
    text = path.read_text(encoding="utf-8")
    errors = validate_ledger(text)
    entry_count = len(ledger_entry_ids(text))
    if errors:
        print(f"Continuity ledger FAILED with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print(f"Continuity ledger PASSED: {entry_count} entr(y/ies), 0 errors.")


if __name__ == "__main__":
    main()
