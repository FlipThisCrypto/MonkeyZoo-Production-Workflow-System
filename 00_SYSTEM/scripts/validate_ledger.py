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

import re
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]

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


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "00_SYSTEM" / "continuity_ledger.md"
    if not path.is_file():
        raise SystemExit(f"Continuity ledger not found: {path}")
    errors = validate_ledger(path.read_text(encoding="utf-8"))
    entry_count = len(_HEADER.findall(_strip_code_fences(path.read_text(encoding="utf-8"))))
    if errors:
        print(f"Continuity ledger FAILED with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)
    print(f"Continuity ledger PASSED: {entry_count} entr(y/ies), 0 errors.")


if __name__ == "__main__":
    main()
