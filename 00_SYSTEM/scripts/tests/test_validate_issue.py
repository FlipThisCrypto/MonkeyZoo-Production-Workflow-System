"""Gate-robustness tests for validate_issue.py.

validate_issue is the CLI gate the skills run at Stages 4/5/8/9. It is meant
to REPORT malformed plans/packs, but a non-integer page_number reached an
f"{pn:02d}" format (plan) and a `> 0` comparison (pack) and crashed the gate
with a raw ValueError/TypeError instead of a clean FAIL. These pin that the
gate reports such malformations and exits 1 rather than stack-tracing.

The module keys everything off the module-global FACTORY / SYSTEM / ERRORS;
we point FACTORY at a tmp issue root, keep SYSTEM real so the JSON schemas
still load, and reset ERRORS per call.
"""
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_issue as vi  # noqa: E402


def _panel(pid="MZ-2026-05-01_P01_PANEL01"):
    return {"panel_id": pid, "action": "a", "emotion": "e", "location": "l", "camera_angle": "c"}


def _write_issue(factory: Path, name: str, plan=None, pack=None) -> Path:
    d = factory / "02_MONTHLY_ISSUES" / name
    d.mkdir(parents=True)
    if plan is not None:
        (d / "page_panel_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    if pack is not None:
        (d / "art_prompt_pack.json").write_text(json.dumps(pack), encoding="utf-8")
    return d


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(vi, "FACTORY", tmp_path)  # issue root -> tmp; SYSTEM stays real for schemas
    monkeypatch.setattr(vi, "ERRORS", [])


def _run(name):
    import sys as _sys
    with pytest.raises(SystemExit) as ei:
        _saved = _sys.argv
        _sys.argv = ["validate_issue.py", name]
        try:
            vi.main()
        finally:
            _sys.argv = _saved
    return ei.value.code


def test_string_page_number_in_plan_is_reported_not_crashed(tmp_path, capsys):
    plan = {"issue_id": "MZ-2026-05-01", "page_count": 1,
            "pages": [{"page_number": "1", "panels": [_panel()]}]}  # "1" is a string
    _write_issue(tmp_path, "2026-05_Issue_01", plan=plan)
    code = _run("2026-05_Issue_01")               # must NOT raise ValueError/TypeError
    assert code == 1
    assert "non-integer page_number" in capsys.readouterr().out


def test_missing_page_number_in_plan_is_reported_not_crashed(tmp_path, capsys):
    plan = {"issue_id": "MZ-2026-05-01", "page_count": 1,
            "pages": [{"panels": [_panel()]}]}     # page_number omitted -> None
    _write_issue(tmp_path, "2026-05_Issue_02", plan=plan)
    assert _run("2026-05_Issue_02") == 1
    assert "non-integer page_number" in capsys.readouterr().out


def test_string_page_number_in_pack_is_reported_not_crashed(tmp_path, capsys):
    plan = {"issue_id": "MZ-2026-05-01", "page_count": 1,
            "pages": [{"page_number": 1, "panels": [_panel()]}]}
    pack = {"style_lock_phrase": "MonkeyZoo house style",
            "base_negative_prompt": "bad",
            "panels": [{"panel_id": "x", "page_number": "2",  # "2" is a string
                        "prompt": "MonkeyZoo house style ...", "negative_prompt": "bad ..."}]}
    _write_issue(tmp_path, "2026-05_Issue_03", plan=plan, pack=pack)
    assert _run("2026-05_Issue_03") == 1
    assert "non-integer page_number" in capsys.readouterr().out


# --- gate content checks: Rule-3 style lock, prompt/negative prefixes, cross-ref ---

_PLAN_PID = "MZ-2026-05-01_P01_PANEL01"


def _plan_one(pid=_PLAN_PID):
    return {"issue_id": "MZ-2026-05-01", "issue_title": "T", "page_count": 1,
            "pages": [{"page_number": 1, "page_purpose": "x", "panels": [_panel(pid)]}]}


def _pack(style="MonkeyZoo house style", base="lowres", panels=None):
    return {"issue_id": "MZ-2026-05-01", "style_lock_phrase": style,
            "base_negative_prompt": base, "panels": panels if panels is not None else []}


def _pack_panel(pid=_PLAN_PID, prompt="MonkeyZoo house style, a scene",
                negative="lowres, blurry", page_number=1):
    return {"panel_id": pid, "page_number": page_number, "prompt": prompt, "negative_prompt": negative}


def test_altered_style_lock_phrase_is_flagged(tmp_path, capsys):
    pack = _pack(style="Off-brand house style", panels=[_pack_panel(prompt="Off-brand house style x")])
    _write_issue(tmp_path, "2026-05_Issue_10", plan=_plan_one(), pack=pack)
    assert _run("2026-05_Issue_10") == 1
    assert "style_lock_phrase missing or altered" in capsys.readouterr().out


def test_prompt_not_starting_with_lock_is_flagged(tmp_path, capsys):
    pack = _pack(panels=[_pack_panel(prompt="a non-conforming prompt")])
    _write_issue(tmp_path, "2026-05_Issue_11", plan=_plan_one(), pack=pack)
    assert _run("2026-05_Issue_11") == 1
    assert "prompt does not start with style lock phrase" in capsys.readouterr().out


def test_negative_not_starting_with_base_is_flagged(tmp_path, capsys):
    pack = _pack(panels=[_pack_panel(negative="unrelated negative")])
    _write_issue(tmp_path, "2026-05_Issue_12", plan=_plan_one(), pack=pack)
    assert _run("2026-05_Issue_12") == 1
    assert "negative does not start with base negative" in capsys.readouterr().out


def test_plan_pack_panel_id_mismatch_is_flagged(tmp_path, capsys):
    pack = _pack(panels=[_pack_panel(pid="MZ-2026-05-01_P09_PANEL09")])
    _write_issue(tmp_path, "2026-05_Issue_13", plan=_plan_one(), pack=pack)
    assert _run("2026-05_Issue_13") == 1
    out = capsys.readouterr().out
    assert "missing panels" in out or "unknown panels" in out
