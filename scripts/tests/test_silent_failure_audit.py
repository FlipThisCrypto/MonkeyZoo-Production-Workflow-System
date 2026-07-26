"""Unit tests for scripts/silent_failure_audit.py."""
from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import silent_failure_audit as sfa


# ---------------------------------------------------------------------------
# classify_handler tests
# ---------------------------------------------------------------------------
def _handler_from(code: str) -> ast.ExceptHandler:
    """Parse a ``try/except`` snippet and return the first handler."""
    tree = ast.parse(textwrap.dedent(code))
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            return node.handlers[0]
    raise AssertionError("No try/except found")


class TestClassifyHandler:
    def test_bare_except_pass_is_empty_broad(self):
        h = _handler_from("""
            try:
                pass
            except:
                pass
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "empty-broad"

    def test_exception_pass_is_empty_broad(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                pass
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "empty-broad"

    def test_narrow_pass_is_cleanup_suppression(self):
        h = _handler_from("""
            try:
                pass
            except FileNotFoundError:
                pass
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "cleanup-suppression"

    def test_raise_is_reraised(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                raise
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "re-raised"

    def test_raise_wrapped_is_reraised(self):
        h = _handler_from("""
            try:
                pass
            except ValueError as exc:
                raise RuntimeError("wrap") from exc
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "re-raised"

    def test_logging_exception_is_logged(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                logging.exception("fail")
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "logged"

    def test_logging_error_with_exc_info_is_logged(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                logging.error("fail", exc_info=True)
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "logged"

    def test_logging_info_without_context_is_not_logged(self):
        """Plain logging.info('message') without exception context is NOT sufficient."""
        h = _handler_from("""
            try:
                pass
            except Exception:
                logging.info("something happened")
        """)
        cls, _ = sfa.classify_handler(h)
        # Should NOT be "logged" — no exception context
        assert cls == "likely-swallowed"

    def test_return_is_fallback(self):
        h = _handler_from("""
            try:
                pass
            except ValueError:
                return None
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "intentional-fallback"

    def test_assignment_is_fallback(self):
        h = _handler_from("""
            try:
                pass
            except OSError:
                result = "default"
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "intentional-fallback"

    def test_continue_is_fallback(self):
        h = _handler_from("""
            for x in items:
                try:
                    pass
                except OSError:
                    continue
        """)
        # Need to dig into the for-loop
        tree = ast.parse(textwrap.dedent("""
            for x in items:
                try:
                    pass
                except OSError:
                    continue
        """))
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                h = node.handlers[0]
                break
        cls, _ = sfa.classify_handler(h)
        assert cls == "intentional-fallback"

    def test_dict_assignment_is_fallback(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                env["git_head"] = "not_available"
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "intentional-fallback"

    def test_broad_no_action_is_swallowed(self):
        h = _handler_from("""
            try:
                pass
            except Exception as e:
                print("oh no")
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "likely-swallowed"

    def test_narrow_no_action_is_swallowed(self):
        h = _handler_from("""
            try:
                pass
            except ValueError:
                print("oh no")
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "likely-swallowed"

    def test_tuple_handler_with_broad(self):
        h = _handler_from("""
            try:
                pass
            except (OSError, Exception):
                pass
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "empty-broad"  # tuple includes Exception

    def test_ellipsis_body_is_empty(self):
        h = _handler_from("""
            try:
                pass
            except FileNotFoundError:
                ...
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "cleanup-suppression"

    def test_logging_with_exc_name_reference(self):
        h = _handler_from("""
            try:
                pass
            except Exception as exc:
                logger.error("Failed: %s", exc)
        """)
        cls, _ = sfa.classify_handler(h)
        assert cls == "logged"


# ---------------------------------------------------------------------------
# is_excluded tests
# ---------------------------------------------------------------------------
class TestIsExcluded:
    def test_excludes_pycache(self, tmp_path):
        p = tmp_path / "__pycache__" / "foo.py"
        assert sfa.is_excluded(p, tmp_path)

    def test_excludes_venv(self, tmp_path):
        p = tmp_path / ".venv" / "lib" / "foo.py"
        assert sfa.is_excluded(p, tmp_path)

    def test_excludes_backups(self, tmp_path):
        p = tmp_path / "06_BACKUPS" / "snapshot" / "foo.py"
        assert sfa.is_excluded(p, tmp_path)

    def test_allows_scripts(self, tmp_path):
        p = tmp_path / "scripts" / "foo.py"
        assert not sfa.is_excluded(p, tmp_path)

    def test_allows_docs(self, tmp_path):
        p = tmp_path / "docs" / "foo.py"
        assert not sfa.is_excluded(p, tmp_path)


# ---------------------------------------------------------------------------
# to_repo_relative tests
# ---------------------------------------------------------------------------
class TestToRepoRelative:
    def test_uses_forward_slashes(self, tmp_path):
        p = tmp_path / "scripts" / "foo.py"
        result = sfa.to_repo_relative(p, tmp_path)
        assert "/" in result or "\\" not in result
        assert result == "scripts/foo.py"


# ---------------------------------------------------------------------------
# scan_repository tests
# ---------------------------------------------------------------------------
class TestScanRepository:
    def test_finds_handlers_in_simple_file(self, tmp_path):
        (tmp_path / "example.py").write_text(textwrap.dedent("""\
            try:
                x = 1
            except Exception:
                pass
        """), encoding="utf-8")
        findings, errors = sfa.scan_repository(tmp_path)
        assert len(findings) == 1
        assert findings[0].classification == "empty-broad"
        assert errors == []

    def test_records_parse_errors(self, tmp_path):
        (tmp_path / "bad.py").write_text("def broken(:\n", encoding="utf-8")
        findings, errors = sfa.scan_repository(tmp_path)
        assert len(errors) == 1
        assert "SyntaxError" in errors[0].reason

    def test_excludes_venv_files(self, tmp_path):
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "pkg.py").write_text("try:\n x=1\nexcept:\n pass\n", encoding="utf-8")
        findings, errors = sfa.scan_repository(tmp_path)
        assert findings == []
        assert errors == []

    def test_no_files_returns_empty(self, tmp_path):
        findings, errors = sfa.scan_repository(tmp_path)
        assert findings == []
        assert errors == []


# ---------------------------------------------------------------------------
# generate_report tests
# ---------------------------------------------------------------------------
class TestGenerateReport:
    def test_creates_report_file(self, tmp_path):
        output = tmp_path / "report.md"
        sfa.generate_report([], [], output)
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "Silent Failure Audit Report" in content

    def test_report_includes_errors_section(self, tmp_path):
        output = tmp_path / "report.md"
        errors = [sfa.ScanError("bad.py", "SyntaxError: invalid syntax")]
        sfa.generate_report([], errors, output)
        content = output.read_text(encoding="utf-8")
        assert "Files Skipped" in content
        assert "bad.py" in content

    def test_report_includes_actionable_section(self, tmp_path):
        output = tmp_path / "report.md"
        findings = [sfa.Finding("x.py", 10, "Exception", "likely-swallowed", "test")]
        sfa.generate_report(findings, [], output)
        content = output.read_text(encoding="utf-8")
        assert "Action Required" in content


# ---------------------------------------------------------------------------
# main / exit code tests
# ---------------------------------------------------------------------------
class TestMain:
    def test_exit_0_when_clean(self, tmp_path):
        (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
        output = tmp_path / "report.md"
        code = sfa.main(["--repo-root", str(tmp_path), "--output", str(output)])
        assert code == 0

    def test_exit_1_when_swallowed(self, tmp_path):
        (tmp_path / "bad.py").write_text(textwrap.dedent("""\
            try:
                x = 1
            except Exception:
                print("swallowed")
        """), encoding="utf-8")
        output = tmp_path / "report.md"
        code = sfa.main(["--repo-root", str(tmp_path), "--output", str(output)])
        assert code == 1

    def test_exit_2_when_parse_error(self, tmp_path):
        (tmp_path / "broken.py").write_text("def broken(:\n", encoding="utf-8")
        output = tmp_path / "report.md"
        code = sfa.main(["--repo-root", str(tmp_path), "--output", str(output)])
        assert code == 2

    def test_output_path_is_created(self, tmp_path):
        (tmp_path / "x.py").write_text("x = 1\n", encoding="utf-8")
        output = tmp_path / "sub" / "dir" / "report.md"
        sfa.main(["--repo-root", str(tmp_path), "--output", str(output)])
        assert output.exists()


# ---------------------------------------------------------------------------
# Source-enumeration tests
#
# These cover the fix for the scanner's own worst failure mode: it used to
# enumerate with `root.rglob("*.py")`, which walks straight into the full copies
# of this repo that live on disk (06_BACKUPS/, 05_RELEASE_ARCHIVE/,
# artifacts/release_staging/). Real observed effect: 336 handlers and 29
# "actionable" findings reported against a true 163 and 14 -- an audit report
# inflated ~2x by duplicates of the same source, where each duplicate reads as
# an independent finding.
#
# The guard used to be a hand-maintained denylist. Three gates in this repo used
# that pattern (pytest, ruff, this scanner) and all three missed artifacts/.
# Git tracking is now the primary filter: it needs no maintenance and cannot
# miss a tree nobody anticipated.
# ---------------------------------------------------------------------------
import subprocess


def _init_git_repo(path: Path) -> None:
    """Create a real git repo at *path*. Only the index is needed, not a commit."""
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)


def _git_add(repo: Path, *relpaths: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "--", *relpaths], check=True, capture_output=True)


SWALLOWING_SOURCE = textwrap.dedent("""\
    try:
        x = 1
    except Exception:
        print("swallowed")
""")


class TestSourceEnumeration:
    def test_untracked_repo_copy_is_not_double_counted(self, tmp_path):
        """The regression: an on-disk copy of the source must not inflate the report."""
        _init_git_repo(tmp_path)
        (tmp_path / "real.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")
        _git_add(tmp_path, "real.py")

        # A staging/backup tree holding a byte-identical copy of the same module.
        staging = tmp_path / "artifacts" / "release_staging"
        staging.mkdir(parents=True)
        (staging / "real.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")

        findings, errors = sfa.scan_repository(tmp_path)

        assert errors == []
        assert len(findings) == 1, (
            "the untracked copy under artifacts/ was counted as a separate finding; "
            f"got {[f.file for f in findings]}"
        )
        assert findings[0].file == "real.py"

    def test_untracked_file_in_a_git_repo_is_not_scanned(self, tmp_path):
        _init_git_repo(tmp_path)
        (tmp_path / "tracked.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")
        (tmp_path / "untracked.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")
        _git_add(tmp_path, "tracked.py")

        findings, _ = sfa.scan_repository(tmp_path)
        assert [f.file for f in findings] == ["tracked.py"]

    def test_exclude_dirs_still_apply_to_tracked_files(self, tmp_path):
        """Git is the primary filter, but tracked non-source trees stay excluded."""
        _init_git_repo(tmp_path)
        backup = tmp_path / "06_BACKUPS" / "snap"
        backup.mkdir(parents=True)
        (backup / "old.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")
        _git_add(tmp_path, "06_BACKUPS/snap/old.py")

        findings, _ = sfa.scan_repository(tmp_path)
        assert findings == []

    def test_falls_back_to_filesystem_walk_outside_a_git_repo(self, tmp_path):
        """The scanner must still work on an exported tree with no .git."""
        (tmp_path / "loose.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")

        assert sfa.enumeration_mode(tmp_path) == "filesystem-walk"
        findings, _ = sfa.scan_repository(tmp_path)
        assert [f.file for f in findings] == ["loose.py"]

    def test_enumeration_mode_reports_git_inside_a_repo(self, tmp_path):
        _init_git_repo(tmp_path)
        assert sfa.enumeration_mode(tmp_path) == "git-tracked"

    def test_tracked_but_deleted_file_is_reported_not_silently_skipped(self, tmp_path):
        """A file in the index but absent on disk must surface, not vanish."""
        _init_git_repo(tmp_path)
        (tmp_path / "gone.py").write_text(SWALLOWING_SOURCE, encoding="utf-8")
        _git_add(tmp_path, "gone.py")
        (tmp_path / "gone.py").unlink()

        findings, errors = sfa.scan_repository(tmp_path)
        assert findings == []
        assert len(errors) == 1
        assert errors[0].file == "gone.py"
        assert "missing from the working tree" in errors[0].reason

    def test_report_records_the_enumeration_mode(self, tmp_path):
        output = tmp_path / "report.md"
        sfa.generate_report([], [], output, source_mode="git-tracked")
        assert "**Source enumeration:** `git-tracked`" in output.read_text(encoding="utf-8")

    def test_report_warns_when_walking_the_filesystem(self, tmp_path):
        """A walk-mode report may be inflated; the report must say so itself."""
        output = tmp_path / "report.md"
        sfa.generate_report([], [], output, source_mode="filesystem-walk")
        text = output.read_text(encoding="utf-8")
        assert "Warning" in text
        assert "more than\nonce" in text or "more than once" in text.replace("\n", " ")


# ---------------------------------------------------------------------------
# The "reported" classification.
#
# The first real run flagged 14 handlers; an independent review rejected 11 of
# them (79%) as false positives, and every rejection came down to two idioms the
# heuristic did not know. This repo imports no logging framework anywhere, so
# failures are surfaced by (a) a reporter function -- err()/log()/print() -- or
# (b) an accumulator whose contents are returned to the caller. Neither is an
# ast.Assign, so both read as "no raise, no logging, no fallback".
#
# An audit tool with a 79% false-positive rate gets ignored, which is worse than
# no tool: the real findings are indistinguishable from the noise.
#
# The opposite failure matters just as much -- see TestStillCatchesRealSwallows.
# ---------------------------------------------------------------------------
class TestReportedClassification:
    def test_accumulator_append_is_reported(self):
        h = _handler_from("""
            try:
                pass
            except ValueError as exc:
                problems.append(f"invalid JSON: {exc}")
        """)
        assert sfa.classify_handler(h)[0] == "reported"

    def test_accumulator_append_of_a_constant_is_reported(self):
        """The stored value reaches the caller even if it names no cause."""
        h = _handler_from("""
            try:
                pass
            except FileNotFoundError:
                skipped.append("missing")
        """)
        assert sfa.classify_handler(h)[0] == "reported"

    def test_reporter_function_with_context_is_reported(self):
        """validate_issue's `err(f"MISSING FILE: {path.name}")` drives sys.exit(1)."""
        h = _handler_from("""
            try:
                pass
            except FileNotFoundError:
                err(f"MISSING FILE: {path.name}")
        """)
        assert sfa.classify_handler(h)[0] == "reported"

    def test_exception_passed_to_any_call_is_reported(self):
        h = _handler_from("""
            try:
                pass
            except Exception as exc:
                record_failure(exc)
        """)
        assert sfa.classify_handler(h)[0] == "reported"

    def test_nested_try_returning_a_substitute_is_a_fallback(self):
        """assemble_pages._font's three-rung font ladder -- fallback one level down."""
        h = _handler_from("""
            try:
                pass
            except OSError:
                try:
                    return load_by_name(name)
                except OSError:
                    return load_default()
        """)
        assert sfa.classify_handler(h)[0] == "intentional-fallback"


class TestStillCatchesRealSwallows:
    """Guard the other direction: a permissive classifier is its own silent failure.

    "0 actionable" must mean the code is clean, not that the tool stopped
    looking. Each of these is a genuine swallow and must stay actionable.
    """

    def test_bare_pass_is_still_empty_broad(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                pass
        """)
        assert sfa.classify_handler(h)[0] == "empty-broad"

    def test_report_with_no_context_is_still_swallowed(self):
        """`print("failed")` names no file, no reason, no exception."""
        h = _handler_from("""
            try:
                pass
            except Exception:
                print("failed")
        """)
        assert sfa.classify_handler(h)[0] == "likely-swallowed"

    def test_unrelated_call_is_still_swallowed(self):
        h = _handler_from("""
            try:
                pass
            except Exception:
                cleanup_unrelated_thing()
        """)
        assert sfa.classify_handler(h)[0] == "likely-swallowed"

    def test_return_inside_a_nested_function_does_not_count_as_a_fallback(self):
        """A `def` in the handler defines later behaviour; it is not this handler's."""
        h = _handler_from("""
            try:
                pass
            except Exception:
                def later():
                    return 1
        """)
        assert sfa.classify_handler(h)[0] == "likely-swallowed"

    def test_a_swallowing_handler_in_a_repo_still_exits_1(self):
        """End-to-end: the tool must still fail a repo that swallows."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "bad.py").write_text(textwrap.dedent("""\
                try:
                    x = 1
                except Exception:
                    print("failed")
            """), encoding="utf-8")
            assert sfa.main(["--repo-root", str(root), "--output", str(root / "r.md")]) == 1
