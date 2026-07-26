"""Guard the integrity of the default `pytest` run itself.

Context — the defect these tests exist to prevent
-------------------------------------------------
This repo keeps full copies of itself on disk: backup snapshots under
``06_BACKUPS/``, release archives under ``05_RELEASE_ARCHIVE/``, and ad-hoc
staging trees such as ``artifacts/release_staging/``. Every one of those copies
contains a duplicate of the test suite. pytest imports test modules by their
basename, so as soon as it recurses into one of these trees it dies at
COLLECTION time on ``import file mismatch`` -- not one failing test, the entire
suite.

That has now happened twice. The first time (``06_BACKUPS``) it was patched by
adding the offending directory to a ``norecursedirs`` denylist. A denylist only
protects against trees somebody remembered to add, so the second occurrence
(``artifacts/release_staging/``) took the suite down again -- 52 collection
errors locally while CI stayed green, because a fresh CI checkout has no such
directory. "Local != CI" is what let it go unnoticed.

The fix was to invert the guard: ``pytest.ini`` now declares ``testpaths``, an
ALLOWLIST of the live test roots, which is immune to artifact trees whether or
not anyone anticipated them.

An allowlist has the opposite failure mode, though: adding a new test directory
and forgetting to list it means those tests silently stop running, and a suite
that quietly shrinks looks exactly like a suite that passes. These tests close
both ends:

* :func:`test_testpaths_cover_every_tracked_test_directory` -- nothing can be
  silently dropped from the default run.
* :func:`test_every_configured_testpath_exists_and_has_tests` -- no dead or
  typo'd entry can sit in the allowlist pretending to contribute coverage.
* :func:`test_bare_collection_from_repo_root_is_clean` -- the end-to-end
  behavioral check: bare ``pytest`` still collects cleanly on THIS machine,
  with whatever artifact trees happen to exist here.
"""

from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTEST_INI = REPO_ROOT / "pytest.ini"


def _configured_testpaths() -> list[str]:
    """Return the ``testpaths`` entries declared in pytest.ini, in order."""
    parser = configparser.ConfigParser()
    parser.read(PYTEST_INI, encoding="utf-8")
    raw = parser.get("pytest", "testpaths", fallback="")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _is_pytest_module(basename: str) -> bool:
    """Match pytest's own default ``python_files`` rule.

    Deliberately stricter than a ``*test_*.py`` glob: pytest only collects
    modules whose basename STARTS with ``test_`` (or ends with ``_test``).
    ``scripts/live_app_test_issue.py`` is a driver script, not a test module,
    and treating it as one would make this guard demand a testpath entry for a
    directory that has no collectable tests in it.
    """
    return basename.startswith("test_") or basename.endswith("_test.py")


def _tracked_test_directories() -> list[str]:
    """Every git-tracked directory that holds test modules, repo-relative.

    Uses git rather than a filesystem walk on purpose: the untracked artifact
    copies are precisely what we must not confuse for real test roots, and git
    already knows the difference.
    """
    result = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    dirs = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        path = Path(line)
        if not _is_pytest_module(path.name):
            continue
        dirs.add(str(path.parent).replace("\\", "/"))
    return sorted(dirs)


def _git_available() -> bool:
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def _is_covered(directory: str, testpaths: list[str]) -> bool:
    """True if *directory* is at or below one of the configured testpaths."""
    candidate = Path(directory)
    for testpath in testpaths:
        root = Path(testpath)
        if candidate == root or root in candidate.parents:
            return True
    return False


def test_pytest_ini_declares_testpaths() -> None:
    """The allowlist must exist at all -- without it the denylist is the guard."""
    assert _configured_testpaths(), (
        "pytest.ini declares no `testpaths`. Collection has fallen back to "
        "denylist-only protection, which is what allowed artifacts/release_staging/ "
        "to take down the entire suite. Restore the testpaths allowlist."
    )


def test_testpaths_cover_every_tracked_test_directory() -> None:
    """No tracked test directory may be silently excluded from the default run."""
    if not _git_available():
        pytest.skip("git unavailable; cannot enumerate tracked test directories")

    testpaths = _configured_testpaths()
    tracked = _tracked_test_directories()
    assert tracked, "found no tracked test files at all -- the enumeration is broken"

    uncovered = [d for d in tracked if not _is_covered(d, testpaths)]
    assert not uncovered, (
        "These tracked test directories are NOT covered by `testpaths` in "
        "pytest.ini, so their tests do not run in a bare `pytest` invocation:\n  "
        + "\n  ".join(uncovered)
        + "\n\nAdd them to testpaths. A shrinking suite passes just as green as a "
        "complete one, which is exactly why this guard exists."
    )


def test_every_configured_testpath_exists_and_has_tests() -> None:
    """A dead or misspelled allowlist entry contributes no coverage -- catch it."""
    problems = []
    for testpath in _configured_testpaths():
        directory = REPO_ROOT / testpath
        if not directory.is_dir():
            problems.append(f"{testpath}: directory does not exist")
            continue
        if not any(directory.rglob("test_*.py")):
            problems.append(f"{testpath}: directory contains no test_*.py modules")
    assert not problems, "Dead entries in pytest.ini `testpaths`:\n  " + "\n  ".join(problems)


def test_bare_collection_from_repo_root_is_clean() -> None:
    """Bare `pytest` must collect without errors on this machine.

    This is the behavioral end of the guard. The unit-level checks above verify
    the configuration; this one verifies the actual outcome against whatever
    backup, archive, and staging trees are really present locally -- the
    local-vs-CI divergence that hid the original break.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr

    assert "errors during collection" not in combined, (
        "Bare `pytest` from the repo root hits collection errors. A directory "
        "containing a duplicate copy of the test suite is almost certainly being "
        "recursed into. Output tail:\n" + combined[-3000:]
    )
    assert result.returncode == 0, (
        f"`pytest --collect-only` exited {result.returncode}. Output tail:\n"
        + combined[-3000:]
    )
