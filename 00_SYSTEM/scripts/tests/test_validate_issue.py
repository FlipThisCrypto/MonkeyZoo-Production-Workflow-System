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
    # Module-global latch: without this reset, the one test that hides
    # jsonschema would leave every later test asserting against the
    # "schema validation SKIPPED" verdict.
    monkeypatch.setattr(vi, "SCHEMA_CHECKS_SKIPPED", False)


def _run(name, *extra):
    """Run the gate and return its exit code (0 when main() returns normally).

    main() only calls sys.exit() on FAIL; a PASS just returns. Normalising both
    into a code lets a test assert "this input must NOT pass", which is the
    whole point of the false-PASS tests below.
    """
    import sys as _sys
    _saved = _sys.argv
    _sys.argv = ["validate_issue.py", name, *extra]
    try:
        vi.main()
        return 0
    except SystemExit as exc:
        return exc.code
    finally:
        _sys.argv = _saved


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


# --- false-PASS: the gate must never report a package valid without checking it ---
#
# load() used to return whatever json.loads produced, and main() guarded every
# check with truthiness (`if plan:` / `if pack:`). Any document that PARSES but
# is falsy -- {}, null, [], "" -- therefore skipped its entire check block while
# recording no error, and the gate printed "PASS - issue package is structurally
# valid." and exited 0. Reproduced before the fix: an issue whose plan and pack
# were both `{}`, run with --art and with zero selected panels on disk, exited 0.
# The `null` case was worse: json.loads("null") raises nothing, so load()
# recorded no error at all and its None was indistinguishable from the
# missing-file sentinel.
#
# This is the gate the mz-new-issue / mz-art-run / mz-package skills require to
# PASS at Stages 4/5/8/9, so a false PASS here green-lights an unvalidated issue
# package downstream.


def _write_raw(factory: Path, name: str, plan_text=None, pack_text=None) -> Path:
    """Write plan/pack as raw text, so non-object JSON like `null` can be tested."""
    d = factory / "02_MONTHLY_ISSUES" / name
    d.mkdir(parents=True)
    if plan_text is not None:
        (d / "page_panel_plan.json").write_text(plan_text, encoding="utf-8")
    if pack_text is not None:
        (d / "art_prompt_pack.json").write_text(pack_text, encoding="utf-8")
    return d


def test_empty_pack_object_does_not_pass(tmp_path, capsys):
    _write_issue(tmp_path, "2026-05_Issue_20", plan=_plan_one(), pack={})
    assert _run("2026-05_Issue_20") == 1
    assert "art_prompt_pack.json" in capsys.readouterr().out


def test_null_pack_does_not_pass(tmp_path, capsys):
    _write_raw(tmp_path, "2026-05_Issue_21",
               plan_text=json.dumps(_plan_one()), pack_text="null")
    assert _run("2026-05_Issue_21") == 1
    assert "art_prompt_pack.json" in capsys.readouterr().out


def test_empty_plan_object_does_not_pass(tmp_path, capsys):
    _write_issue(tmp_path, "2026-05_Issue_22", plan={}, pack=_pack())
    assert _run("2026-05_Issue_22") == 1
    assert "page_panel_plan.json" in capsys.readouterr().out


def test_list_instead_of_object_does_not_pass(tmp_path, capsys):
    _write_raw(tmp_path, "2026-05_Issue_23", plan_text="[]", pack_text="{}")
    assert _run("2026-05_Issue_23") == 1
    assert "page_panel_plan.json" in capsys.readouterr().out


def test_both_files_empty_do_not_pass_even_with_art_and_no_art_on_disk(tmp_path, capsys):
    """The exact reproduction: nothing validated, no art present, yet exit 0."""
    _write_raw(tmp_path, "2026-05_Issue_24", plan_text="{}", pack_text="{}")
    code = _run("2026-05_Issue_24", "--art")
    out = capsys.readouterr().out
    assert code == 1, f"gate passed an entirely unvalidated package:\n{out}"
    assert "PASS" not in out


def test_art_check_with_no_planned_panels_is_reported(tmp_path, capsys):
    """`--art` that checks zero panels must say so, not pass silently.

    A plan with `pages: []` is a well-formed object, so the load() guard does not
    catch it; `if check_art and plan_ids:` then skipped the art check entirely
    and the gate passed while verifying no art at all.
    """
    plan = {"issue_id": "MZ-2026-05-01", "issue_title": "T", "page_count": 0, "pages": []}
    _write_issue(tmp_path, "2026-05_Issue_25", plan=plan, pack=_pack())
    code = _run("2026-05_Issue_25", "--art")
    out = capsys.readouterr().out
    assert code == 1, f"--art passed without checking a single panel:\n{out}"
    assert "no panels" in out


def test_wellformed_package_is_not_flagged_by_the_object_guard(tmp_path, capsys):
    """Over-correction guard: a populated plan/pack must not trip the new checks.

    Scoped to the new error strings on purpose. This minimal fixture is
    deliberately not schema-complete (the JSON Schemas require a dozen more
    per-panel fields), so asserting a clean exit here would assert the wrong
    thing. The end-to-end "still passes" signal is
    test_real_committed_issue_still_passes below, which runs against real data.
    """
    _write_issue(tmp_path, "2026-05_Issue_26",
                 plan=_plan_one(), pack=_pack(panels=[_pack_panel()]))
    _run("2026-05_Issue_26", "--art")
    out = capsys.readouterr().out
    assert "EMPTY OR NON-OBJECT" not in out
    assert "no panels" not in out


def test_real_committed_issue_still_passes(monkeypatch, capsys):
    """End-to-end over-correction guard against real committed canon data.

    Mirrors docs/tests/test_verify_static_site.py::test_real_committed_docs_passes.
    If tightening load() ever starts rejecting a package the factory actually
    ships, this fails loudly rather than surfacing as a mystery FAIL mid-release.
    """
    real_factory = Path(__file__).resolve().parents[3]
    issue = real_factory / "02_MONTHLY_ISSUES" / "2026-07_Issue_05"
    if not issue.is_dir():
        pytest.skip("real issue 2026-07_Issue_05 not present in this checkout")

    monkeypatch.setattr(vi, "FACTORY", real_factory)  # override the _isolate fixture
    monkeypatch.setattr(vi, "ERRORS", [])
    code = _run("2026-07_Issue_05", "--art")
    out = capsys.readouterr().out
    assert code == 0, f"a real, shipped issue package stopped passing the gate:\n{out}"
    assert "PASS" in out


# --- schema-blind PASS: an operator must be able to tell what was checked ---


def test_pass_message_discloses_that_schema_validation_was_skipped(tmp_path, capsys, monkeypatch):
    """Without jsonschema the gate skips ALL JSON-Schema validation.

    schema_check() returned silently on ImportError, so a schema-blind run was
    indistinguishable from a fully validated one -- both printed the unqualified
    "PASS - issue package is structurally valid." The built-in fallback checks
    are genuinely narrower (no types, no enums, no schema-required field it
    never inspects), so the operator needs to know which kind of PASS this was.
    """
    monkeypatch.setitem(sys.modules, "jsonschema", None)  # `import jsonschema` -> ImportError
    _write_issue(tmp_path, "2026-05_Issue_27",
                 plan=_plan_one(), pack=_pack(panels=[_pack_panel()]))
    code = _run("2026-05_Issue_27")
    out = capsys.readouterr().out
    assert code == 0, out
    assert "jsonschema" in out, f"schema-blind PASS did not disclose itself:\n{out}"
    assert "SKIPPED" in out
