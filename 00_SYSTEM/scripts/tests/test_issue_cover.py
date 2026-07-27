"""The canonical cover-location contract, and proof every surface shares it.

The defect
----------
Two independently written resolvers disagreed about where an issue's final
cover lives, and production data was genuinely split across both conventions:

* Studio release gate (`release_workspace.evidence`) searched ONLY
  `generated_art/` via `rglob("*cover*.png")` and raised
  `"No final cover image found"` -- naming no path it had searched;
* CLI packager (`build_release._find_cover`) tried `exports/cover.png` FIRST.

The trap was reachable straight from the designated instructions: the
`mz-package` skill (CLAUDE.md assigns it Stages 8-10) and three 00_SYSTEM docs
all said to save `exports/cover.png`; only `docs/OPERATOR_RUNBOOK.md` named
`generated_art/covers/main_cover.png`.

Measured before the fix: 2026-07_Issue_05, 2026-08_Issue_06 and
2026-07_Mango_Pier each held a real cover at `exports/cover.png` and were
reporting "No final cover image found".

The contract now lives in exactly one module, `00_SYSTEM/scripts/issue_cover.py`,
used by the Studio release gate, the Studio visual-QA evidence set, the CLI
validator (`--cover`), the CBZ/PDF builder, and archive publishing.
`package_issue.py` inherits it by delegating to `build_release.py`.

`exports/cover.png` is a DEPRECATED fallback, not a second permanent source --
two accepted locations would just recreate the divergence. It is accepted so the
three issues already on it are not stranded, every surface that accepts it says
so, and `issue_cover.py --audit` prints the migration and the removal criterion.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]           # 00_SYSTEM/scripts
FACTORY = Path(__file__).resolve().parents[3]
REVIEW_APP = FACTORY / "character-bibles" / "_review_app"
for _p in (str(SCRIPTS), str(REVIEW_APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import issue_cover  # noqa: E402
import build_release  # noqa: E402
import validate_issue as vi  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 64


def _issue(tmp_path: Path, *, canonical=False, legacy=False, name="2026-05_Issue_09") -> Path:
    d = tmp_path / "02_MONTHLY_ISSUES" / name
    d.mkdir(parents=True)
    if canonical:
        p = d / issue_cover.CANONICAL_RELPATH
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(PNG)
    if legacy:
        p = d / issue_cover.LEGACY_RELPATH
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(PNG)
    return d


# --- Case 1: a canonical cover is recognised -------------------------------

def test_canonical_cover_is_resolved(tmp_path):
    res = issue_cover.resolve_final_cover(_issue(tmp_path, canonical=True))
    assert res.source == "canonical"
    assert res.found and res.blocker is None and res.warning is None


def test_canonical_wins_when_both_locations_exist(tmp_path):
    """Otherwise migration would be ambiguous while both files linger."""
    res = issue_cover.resolve_final_cover(_issue(tmp_path, canonical=True, legacy=True))
    assert res.source == "canonical"
    assert res.path.as_posix().endswith(issue_cover.CANONICAL_RELPATH)


# --- Case 2: legacy is accepted, loudly, with a migration -------------------

def test_legacy_cover_is_accepted_but_announces_itself(tmp_path):
    res = issue_cover.resolve_final_cover(_issue(tmp_path, legacy=True))
    assert res.source == "legacy" and res.found
    assert res.blocker is None, "a real cover must not be reported as missing"
    assert "DEPRECATED" in res.warning
    assert issue_cover.CANONICAL_RELPATH in res.warning, "the warning must name where to put it"
    assert "git mv" in res.warning, "the warning must carry the migration command"


def test_audit_reports_legacy_issues_and_the_removal_criterion(capsys, tmp_path):
    """The fallback is temporary; the audit is how anyone knows when it can go."""
    _issue(tmp_path, legacy=True, name="2026-05_Issue_09")
    _issue(tmp_path, canonical=True, name="2026-06_Issue_10")
    code = issue_cover._audit(tmp_path)
    out = capsys.readouterr().out
    assert code == 1, "audit must exit non-zero while any issue still uses the fallback"
    assert "2026-05_Issue_09" in out
    assert "Remove the exports/cover.png fallback once" in out


# --- Case 3: no cover fails both surfaces, consistently --------------------

def test_missing_cover_blocker_names_every_searched_location(tmp_path):
    res = issue_cover.resolve_final_cover(_issue(tmp_path))
    assert res.source == "missing" and not res.found
    assert issue_cover.CANONICAL_RELPATH in res.blocker
    assert issue_cover.LEGACY_RELPATH in res.blocker, (
        "the old message named no path at all, which is what made it misleading")


def test_zero_byte_cover_is_not_a_cover(tmp_path):
    d = _issue(tmp_path)
    p = d / issue_cover.CANONICAL_RELPATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"")
    assert issue_cover.resolve_final_cover(d).source == "missing"


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({"canonical": True}, "canonical"),
    ({"legacy": True}, "legacy"),
    ({}, "missing"),
])
def test_cli_and_studio_agree_on_every_cover_state(tmp_path, monkeypatch, kwargs, expected):
    """The whole point: one question, one answer, on both surfaces."""
    import release_workspace as rw

    folder = _issue(tmp_path, **kwargs)

    # Match the contract's exact blocker, not a substring. A loose "cover" match
    # also catches the unrelated "cover_prompt.md is missing or empty" blocker
    # this bare fixture raises, which made the assertion pass for the wrong
    # reason in both directions.
    marker = "No final cover image found"

    studio = rw.evidence(folder, tmp_path)
    studio_blocked = any(b.startswith(marker) for b in studio["blockers"])

    monkeypatch.setattr(vi, "FACTORY", tmp_path)
    monkeypatch.setattr(vi, "ERRORS", [])
    monkeypatch.setattr(sys, "argv", ["validate_issue.py", folder.name, "--cover"])
    resolved = issue_cover.resolve_final_cover(folder)
    if resolved.blocker:
        vi.err(f"cover: {resolved.blocker}")
    cli_blocked = any(marker in e for e in vi.ERRORS)

    assert studio["final_cover"]["source"] == expected
    assert studio_blocked == cli_blocked, (
        f"surfaces disagree for {expected}: studio_blocked={studio_blocked} "
        f"cli_blocked={cli_blocked}")
    assert studio_blocked is (expected == "missing")


# --- Case 5: packaging uses the cover Studio displayed ---------------------

@pytest.mark.parametrize("kwargs", [{"canonical": True}, {"legacy": True}])
def test_packaging_uses_the_same_cover_the_studio_reports(tmp_path, kwargs):
    import release_workspace as rw

    folder = _issue(tmp_path, **kwargs)
    studio_path = rw.evidence(folder, tmp_path)["final_cover"]["path"]
    packaged = build_release._find_cover(folder)

    assert packaged is not None
    assert packaged.relative_to(folder).as_posix() == studio_path, (
        "the CBZ would embed a different image than the release gate approved")


def test_packaging_finds_no_cover_when_the_studio_reports_none(tmp_path):
    folder = _issue(tmp_path)
    assert build_release._find_cover(folder) is None


# --- Evidence-set semantics: list, not first-match -------------------------

def test_evidence_set_keeps_list_semantics(tmp_path):
    """Collapsing to first-match would drop COVER_FRONT/BACK from the archive."""
    d = _issue(tmp_path, canonical=True)
    prev = d / "generated_art" / "integration_preview"
    prev.mkdir(parents=True)
    (prev / "COVER_FRONT.png").write_bytes(PNG)
    (prev / "COVER_BACK.png").write_bytes(PNG)

    images = issue_cover.cover_evidence_images(d)
    names = sorted(p.name for p in images)
    assert names == ["COVER_BACK.png", "COVER_FRONT.png", "main_cover.png"]


def test_evidence_set_is_case_insensitive_on_every_platform(tmp_path):
    """The old rglob was case-insensitive on Windows and case-sensitive on POSIX.

    2026-09_Issue_02 therefore contributed 4 covers on the Windows dev rig and 2
    on Linux CI -- so its release evidence hash, which gates approval and is
    written into release_hash_manifest.json, did not reproduce across the two
    machines that both compute it.
    """
    d = _issue(tmp_path, canonical=True)
    prev = d / "generated_art" / "integration_preview"
    prev.mkdir(parents=True)
    (prev / "COVER_BACK.png").write_bytes(PNG)

    names = {p.name for p in issue_cover.cover_evidence_images(d)}
    assert "COVER_BACK.png" in names, "uppercase cover excluded; hash is platform-dependent again"


def test_evidence_set_includes_a_legacy_cover(tmp_path):
    """A legacy cover must still contribute evidence, not vanish from the record."""
    d = _issue(tmp_path, legacy=True)
    assert [p.name for p in issue_cover.cover_evidence_images(d)] == ["cover.png"]


# --- Case 4: real data is detected without altering canon ------------------

def test_published_issues_keep_the_exact_evidence_set_they_had(tmp_path):
    """Real-data guard: widening discovery must not disturb what already shipped.

    The evidence set feeds the release evidence hash and is copied wholesale
    into the published archive, so a changed set for an already-released issue
    would invalidate its approval and alter what was published.

    Compares against the literal pre-fix expression. Issues that resolve via the
    legacy fallback are expected to change -- gaining the cover is the fix -- and
    none of them has a release manifest.
    """
    issues_root = FACTORY / "02_MONTHLY_ISSUES"
    if not issues_root.is_dir():
        pytest.skip("no issue folders in this checkout")

    checked = 0
    for folder in sorted(p for p in issues_root.iterdir() if p.is_dir()):
        if issue_cover.resolve_final_cover(folder).source == "legacy":
            continue
        generated = folder / "generated_art"
        before = sorted(generated.rglob("*cover*.png")) if generated.exists() else []
        after = issue_cover.cover_evidence_images(folder)
        assert [p.name for p in before] == [p.name for p in after], (
            f"{folder.name}: evidence set changed for an issue that did not need "
            f"migrating; this would alter a published archive")
        checked += 1
    assert checked, "guard checked nothing -- it is not actually protecting anything"


def test_the_three_known_legacy_issues_are_no_longer_blocked_on_cover():
    """The concrete defect: real covers that the release gate could not see."""
    issues_root = FACTORY / "02_MONTHLY_ISSUES"
    if not issues_root.is_dir():
        pytest.skip("no issue folders in this checkout")
    for name in ("2026-07_Issue_05", "2026-08_Issue_06"):
        folder = issues_root / name
        if not folder.is_dir():
            continue
        res = issue_cover.resolve_final_cover(folder)
        assert res.found, f"{name} has a real cover that is still not being found"
        assert res.blocker is None
