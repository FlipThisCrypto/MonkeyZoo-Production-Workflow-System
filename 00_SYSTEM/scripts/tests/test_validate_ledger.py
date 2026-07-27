"""Regression coverage for the continuity-ledger integrity gate.

The ledger is the append-only canon source-of-truth; these pin the failure modes
a malformed append can introduce (missing section, mistyped ID, duplicate ID)
and confirm the fenced format template is never mistaken for a real entry. The
committed ledger itself must always pass, so that is exercised too.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
FACTORY = SCRIPTS.parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_ledger as vl  # noqa: E402

VALIDATOR = SCRIPTS / "validate_ledger.py"
REAL_LEDGER = FACTORY / "00_SYSTEM" / "continuity_ledger.md"

SECTIONS = ("EVENTS: e\nSTATE CHANGES: s\nNEW LORE: n\n"
            "RUNNING JOKES: r\nOPEN THREADS: o\n")


def _entry(entry_id, body=SECTIONS, title="Title (release 2026-09)"):
    return f"## [{entry_id}] {title}\n{body}\n"


# ---- unit-level: validate_ledger(text) ------------------------------------

def test_well_formed_entry_passes():
    assert vl.validate_ledger(_entry("MZ-2026-09-02")) == []


def test_all_three_id_shapes_accepted():
    text = _entry("MZ-ED-04") + _entry("MZ-2026-09-02") + _entry("ERR-2026-07-06")
    assert vl.validate_ledger(text) == []


def test_missing_required_section_is_flagged():
    body = "EVENTS: e\nSTATE CHANGES: s\nNEW LORE: n\nRUNNING JOKES: r\n"  # no OPEN THREADS
    errs = vl.validate_ledger(_entry("MZ-2026-09-02", body))
    assert any("missing required section 'OPEN THREADS'" in e for e in errs)


def test_malformed_id_is_flagged():
    errs = vl.validate_ledger(_entry("2026-9-2"))
    assert any("malformed entry ID" in e for e in errs)


def test_duplicate_id_is_flagged():
    text = _entry("MZ-2026-09-02") + _entry("MZ-2026-09-02")
    errs = vl.validate_ledger(text)
    assert any("duplicate entry ID" in e for e in errs)


def test_section_with_parenthetical_qualifier_counts():
    # "STATE CHANGES (canon corrections): ..." must still satisfy STATE CHANGES
    body = ("EVENTS: e\nSTATE CHANGES (canon corrections, not redesigns): s\n"
            "NEW LORE: n\nRUNNING JOKES: r\nOPEN THREADS: o\n")
    assert vl.validate_ledger(_entry("ERR-2026-07-06", body)) == []


def test_extra_section_is_allowed():
    body = SECTIONS + "RETURN PROTOCOL: how the cast comes back\n"
    assert vl.validate_ledger(_entry("MZ-2026-08-06", body)) == []


def test_fenced_format_template_is_not_validated():
    # The doc's ``` block contains a literal "## [ISSUE-ID] ..." header; it must be
    # ignored, not treated as a real (malformed-ID, section-less) entry.
    doc = ("# Ledger\n```\n## [ISSUE-ID] Title (release YYYY-MM)\nEVENTS: ...\n```\n\n"
           + _entry("MZ-2026-09-02"))
    assert vl.validate_ledger(doc) == []


def test_empty_ledger_reports_no_entries():
    assert vl.validate_ledger("# Ledger\n\nNo entries yet.\n") == ["ledger has no entries"]


# ---- the committed ledger + CLI contract ----------------------------------

def test_real_committed_ledger_passes():
    assert vl.validate_ledger(REAL_LEDGER.read_text(encoding="utf-8")) == []


def test_cli_exit_zero_on_real_ledger():
    result = subprocess.run([sys.executable, str(VALIDATOR), str(REAL_LEDGER)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout


def test_cli_exit_one_on_broken_ledger(tmp_path):
    bad = tmp_path / "ledger.md"
    bad.write_text(_entry("BAD-ID", "EVENTS: only this\n"), encoding="utf-8")
    result = subprocess.run([sys.executable, str(VALIDATOR), str(bad)],
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert "FAILED" in result.stdout


# ---- reconciliation: ledger completeness vs real production output ------------

def _issue(issues_dir, folder, issue_id, stage, use_brief=False):
    d = issues_dir / folder
    d.mkdir(parents=True)
    (d / ".workflow-status.json").write_text(json.dumps({"active_stage": stage}), encoding="utf-8")
    if use_brief:
        (d / "issue_brief.md").write_text(f"Issue ID: {issue_id}\nWorking Title: X\n", encoding="utf-8")
    else:
        (d / "metadata.json").write_text(json.dumps({"issue_id": issue_id}), encoding="utf-8")
    return d


def test_reconcile_flags_published_issue_missing_from_ledger(tmp_path):
    ledger = _entry("MZ-2026-08-01")  # only this one recorded
    issues = tmp_path / "issues"
    _issue(issues, "2026-08_Issue_01", "MZ-2026-08-01", "published")
    _issue(issues, "2026-09_Issue_01", "MZ-2026-09-01", "published")  # NOT in ledger
    missing = vl.reconcile_with_issues(ledger, issues)
    assert {m["issue_id"] for m in missing} == {"MZ-2026-09-01"}
    assert missing[0]["stage"] == "published"


def test_reconcile_ignores_pre_qa_issues(tmp_path):
    ledger = _entry("MZ-2026-08-01")
    issues = tmp_path / "issues"
    _issue(issues, "2026-09_Issue_01", "MZ-2026-09-01", "script")   # not yet at QA -> exempt
    _issue(issues, "2026-10_Issue_01", "MZ-2026-10-01", "intake")
    assert vl.reconcile_with_issues(ledger, issues) == []


def test_reconcile_passes_when_all_qad_issues_present(tmp_path):
    ledger = _entry("MZ-2026-08-01") + _entry("MZ-2026-09-01")
    issues = tmp_path / "issues"
    _issue(issues, "2026-08_Issue_01", "MZ-2026-08-01", "release")
    _issue(issues, "2026-09_Issue_01", "MZ-2026-09-01", "qa")
    assert vl.reconcile_with_issues(ledger, issues) == []


def test_reconcile_reads_issue_id_from_brief(tmp_path):
    ledger = _entry("MZ-2026-08-01")
    issues = tmp_path / "issues"
    _issue(issues, "2026-09_Issue_01", "MZ-2026-09-01", "published", use_brief=True)
    assert {m["issue_id"] for m in vl.reconcile_with_issues(ledger, issues)} == {"MZ-2026-09-01"}


def test_reconcile_missing_issues_dir_is_empty(tmp_path):
    assert vl.reconcile_with_issues(_entry("MZ-2026-08-01"), tmp_path / "nope") == []


def test_reconcile_real_data_returns_wellformed_results():
    # Runs against the committed repo. Robust to the ledger being completed later:
    # asserts correctness (every flagged issue is genuinely absent and QA'd+),
    # not the specific transient gap.
    ledger_text = REAL_LEDGER.read_text(encoding="utf-8")
    entry_ids = vl.ledger_entry_ids(ledger_text)
    for item in vl.reconcile_with_issues(ledger_text, FACTORY / "02_MONTHLY_ISSUES"):
        assert set(item) == {"issue_id", "stage", "folder"}
        assert item["issue_id"] not in entry_ids
        assert item["stage"] in vl.LEDGER_REQUIRED_STAGES


def test_reconcile_cli_exit_codes(tmp_path, monkeypatch, capsys):
    ledger_file = tmp_path / "ledger.md"
    ledger_file.write_text(_entry("MZ-2026-08-01"), encoding="utf-8")
    issues = tmp_path / "issues"
    _issue(issues, "2026-08_Issue_01", "MZ-2026-08-01", "published")
    monkeypatch.setattr(sys, "argv", ["validate_ledger.py", "--reconcile", str(ledger_file), str(issues)])
    vl.main()
    assert "reconciliation PASSED" in capsys.readouterr().out
    _issue(issues, "2026-09_Issue_01", "MZ-2026-09-01", "published")  # now one is missing
    monkeypatch.setattr(sys, "argv", ["validate_ledger.py", "--reconcile", str(ledger_file), str(issues)])
    with pytest.raises(SystemExit) as exc:
        vl.main()
    assert exc.value.code == 1
    assert "reconciliation FAILED" in capsys.readouterr().out
