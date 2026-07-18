"""Stage-1 intake validation tests (new_issue: normalize_request / _integer / _text).

Foundational and security-relevant: every issue is scaffolded through
normalize_request, whose path-traversal guards (unsafe title characters,
issue_id format), year/month cross-check, and strict integer coercion
(rejects bools, non-integer floats, non-numeric strings) were otherwise
untested. Character resolution is faked so these stay hermetic -- no canon
data, no bible_store coupling.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import new_issue as ni  # noqa: E402


def _install_bible_store(monkeypatch, resolver):
    """Put a fake `bible_store` module in sys.modules so normalize_request's
    inline `import bible_store` binds to it regardless of the real one."""
    mod = types.ModuleType("bible_store")
    mod.resolve_character_id = resolver
    monkeypatch.setitem(sys.modules, "bible_store", mod)


@pytest.fixture
def fake_bibles(monkeypatch):
    """Resolve any character id to a canonical (uppercased) form."""
    _install_bible_store(monkeypatch, lambda cid, root: str(cid).strip().upper())


def _req(**over):
    data = dict(
        issue_id="MZ-2026-05-01", title="Static Shock",
        primary_character="MZ-CHAR-STATIC", core_premise="p", main_conflict="c",
        emotional_goal="e", opening_situation="o", ending_direction="end",
        year=2026, month=5, edition_number=2, page_count=16, panel_count=96,
    )
    data.update(over)
    return data


# ---------------------------------------------------------------------------
# _text
# ---------------------------------------------------------------------------

def test_text_required_missing_raises():
    with pytest.raises(ni.IssueCreationError, match="Missing required field: title"):
        ni._text({}, "title", required=True)


def test_text_whitespace_only_is_missing_when_required():
    with pytest.raises(ni.IssueCreationError):
        ni._text({"title": "   "}, "title", required=True)


def test_text_non_string_rejected():
    with pytest.raises(ni.IssueCreationError, match="must be text"):
        ni._text({"title": 5}, "title")


def test_text_optional_absent_returns_empty():
    assert ni._text({}, "subtitle") == ""


def test_text_strips_surrounding_whitespace():
    assert ni._text({"title": "  hi  "}, "title") == "hi"


# ---------------------------------------------------------------------------
# _integer  (strict coercion: bools/non-integer-floats/non-numeric strings out)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [True, False, None, 5.7, "5.7", "abc", "13"])
def test_integer_rejects_bad_values(value):
    with pytest.raises(ni.IssueCreationError):
        ni._integer({"m": value}, "m", 1, 12)


@pytest.mark.parametrize("value,expected", [(5, 5), (5.0, 5), ("5", 5), ("  7  ", 7)])
def test_integer_accepts_and_coerces(value, expected):
    assert ni._integer({"m": value}, "m", 1, 12) == expected


def test_integer_default_used_when_absent():
    assert ni._integer({}, "page_count", 1, 64, 8) == 8


def test_integer_out_of_range_message_distinct_from_type():
    with pytest.raises(ni.IssueCreationError, match="between 1 and 12"):
        ni._integer({"m": 0}, "m", 1, 12)


# ---------------------------------------------------------------------------
# normalize_request -- error paths that fire before character resolution
# ---------------------------------------------------------------------------

def test_normalize_rejects_non_dict():
    with pytest.raises(ni.IssueCreationError, match="JSON object"):
        ni.normalize_request(["nope"])


def test_normalize_missing_required_field():
    with pytest.raises(ni.IssueCreationError, match="Missing required field"):
        ni.normalize_request(_req(title=""))


def test_normalize_rejects_bad_issue_id():
    with pytest.raises(ni.IssueCreationError, match="MZ-YYYY-MM-NN"):
        ni.normalize_request(_req(issue_id="MZ-26-5-1"))


def test_normalize_rejects_year_month_mismatch():
    with pytest.raises(ni.IssueCreationError, match="year and month must match"):
        ni.normalize_request(_req(month=6))  # issue_id says -05-, submitted month 6


@pytest.mark.parametrize("bad", ["a/b", "a\\b", "a..b", "a:b", "a<b", 'a"b', "a|b", "a?b", "a*b"])
def test_normalize_rejects_unsafe_title_chars(bad):
    with pytest.raises(ni.IssueCreationError, match="unsafe path characters"):
        ni.normalize_request(_req(title=bad))


def test_normalize_rejects_out_of_range_month_before_id_checks():
    # _integer fires inside the numeric loop, before issue_id/prefix checks
    with pytest.raises(ni.IssueCreationError, match="between 1 and 12"):
        ni.normalize_request(_req(month=13))


# ---------------------------------------------------------------------------
# normalize_request -- success + post-resolution (fake character store)
# ---------------------------------------------------------------------------

def test_normalize_success_derives_period_and_folder(fake_bibles):
    n = ni.normalize_request(_req())
    assert n["period"] == "2026-05"
    assert n["folder_name"] == "2026-05_Issue_02"
    assert n["issue_type"] == "Monthly"  # default applied


def test_normalize_default_output_requirements(fake_bibles):
    n = ni.normalize_request(_req())
    assert n["output_requirements"] == ["QA", "cover", "metadata", "social copy"]


def test_normalize_dedups_and_sorts_output_requirements(fake_bibles):
    n = ni.normalize_request(_req(output_requirements=["QA", "QA", "cover"]))
    assert n["output_requirements"] == ["QA", "cover"]


def test_normalize_rejects_unknown_output_requirement(fake_bibles):
    with pytest.raises(ni.IssueCreationError, match="output_requirements must be a list"):
        ni.normalize_request(_req(output_requirements=["bogus"]))


def test_normalize_rejects_guest_equal_primary(fake_bibles):
    with pytest.raises(ni.IssueCreationError, match="guest_character must differ"):
        ni.normalize_request(_req(guest_character="MZ-CHAR-STATIC"))


def test_normalize_unknown_character_becomes_clean_error(monkeypatch):
    # BibleStoreError subclasses ValueError; the resolver raising it must be
    # caught and reported as a clean IssueCreationError, not propagate raw.
    def boom(cid, root):
        raise ValueError("no such char")
    _install_bible_store(monkeypatch, boom)
    with pytest.raises(ni.IssueCreationError, match="Unknown character or missing bible"):
        ni.normalize_request(_req())


def test_normalize_missing_bible_store_import_becomes_clean_error(monkeypatch):
    # A None entry in sys.modules makes `import bible_store` raise ImportError;
    # that branch must also degrade to a clean IssueCreationError.
    monkeypatch.setitem(sys.modules, "bible_store", None)
    with pytest.raises(ni.IssueCreationError, match="Unknown character or missing bible"):
        ni.normalize_request(_req())
