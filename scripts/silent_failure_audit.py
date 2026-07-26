"""Detect and classify broad exception handlers in the MonkeyZoo repository.

Walks repository-owned Python files, parses them with ``ast``, and classifies
every ``try/except`` handler body as one of:

* **re-raised** – handler contains ``raise`` (with or without explicit exception).
* **logged** – handler calls a logging function with exception context.
* **intentional-fallback** – handler performs a deliberate assignment, return,
  continue, or break that constitutes a specific fallback path.
* **cleanup-suppression** – narrowly scoped handler (specific exception type)
  whose body contains only ``pass`` or an empty body, suggesting intentional
  narrow suppression.
* **empty-broad** – bare/``Exception``/``BaseException`` handler whose body is
  only ``pass`` or empty — likely a bug.
* **likely-swallowed** – execution continues without logging, propagation,
  a justified fallback, or a clear narrow suppression reason.
* **unable-to-classify** – static analysis cannot prove the handler's behavior.

Reports are written to a deterministic repository-relative location
(``docs/audit/silent_failure_report.md``) unless ``--output`` is given.

Exit codes:
    0 – no likely-swallowed or empty-broad handlers.
    1 – one or more likely-swallowed or empty-broad handlers.
    2 – scanner encountered unreadable/unparseable files.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import List, NamedTuple, Optional, Tuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Secondary guard only -- see `_git_tracked_python_files` for why the primary
# filter is git, not this list. Retained because a few *tracked* trees are not
# source either (inbox drops, vendored snapshots), and because the scanner must
# still work outside a git checkout.
EXCLUDE_DIRS: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "env",
    "build",
    "dist",
    "site-packages",
    "node_modules",
    "_generated",
    ".pytest_cache",
    ".ruff_cache",
    "05_RELEASE_ARCHIVE",
    "06_BACKUPS",
    "04_REJECTED_OUTPUTS",
    "04_APPROVED_FOR_PUSH",
    "02_ANTIGRAVITY_WORK",
    "01_CHATGPT_TO_ANTIGRAVITY",
    "01_IDEAS_INBOX",
})

BROAD_HANDLER_NAMES: frozenset[str] = frozenset({
    "Exception", "BaseException",
})

LOGGING_NAMES: frozenset[str] = frozenset({
    "logging", "logger", "log", "_log", "_logger",
})

LOGGING_METHODS: frozenset[str] = frozenset({
    "debug", "info", "warning", "warn", "error", "critical",
    "exception", "fatal", "log",
})

# This repo imports no logging framework anywhere. Failures are surfaced two
# other ways, and a scanner that does not know them reports almost nothing but
# noise -- the first run flagged 14 handlers of which an independent review
# rejected 11 (79%) as false positives, all on these two idioms.
#
# 1. A reporter function: `err(...)` accumulating into a module-global ERRORS
#    that drives sys.exit(1) (validate_issue.py), `log(...)` writing a FAIL row
#    into a report (live_app_test_issue.py), or plain `print(...)`, which is the
#    only status channel most of these modules have.
REPORTING_FUNCTIONS: frozenset[str] = frozenset({
    "print", "err", "error", "warn", "warning", "fail", "log",
    "report", "abort", "die", "emit",
})

# 2. An accumulator: the failure is appended to a list/set/dict that the
#    function returns, and the caller acts on it -- `skipped.append({...})`,
#    `problems.append(f"invalid JSON: {exc}")`, `errors.append(exc)`. The value
#    is carried out in the return contract, so nothing is swallowed. The old
#    heuristic missed all of these because a method call is not an ast.Assign.
ACCUMULATOR_METHODS: frozenset[str] = frozenset({
    "append", "add", "extend", "insert", "update", "setdefault",
})


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------
class Finding(NamedTuple):
    file: str          # repo-relative, forward-slash
    line: int
    handler_type: str  # e.g. "bare except", "Exception", "(OSError, ValueError)"
    classification: str
    detail: str        # human explanation


class ScanError(NamedTuple):
    file: str   # repo-relative, forward-slash
    reason: str


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------
def _handler_type_str(handler: ast.ExceptHandler) -> str:
    """Return a human-readable string for the exception type(s)."""
    if handler.type is None:
        return "bare except"
    if hasattr(ast, "unparse"):
        return ast.unparse(handler.type)
    # Fallback for older Python versions
    if isinstance(handler.type, ast.Name):
        return handler.type.id
    if isinstance(handler.type, ast.Tuple):
        names = []
        for elt in handler.type.elts:
            if isinstance(elt, ast.Name):
                names.append(elt.id)
            elif isinstance(elt, ast.Attribute):
                names.append(ast.dump(elt))
            else:
                names.append("?")
        return f"({', '.join(names)})"
    return "?"


def _is_broad_handler(handler: ast.ExceptHandler) -> bool:
    """Return True if the handler catches bare, Exception, or BaseException."""
    if handler.type is None:
        return True
    if isinstance(handler.type, ast.Name) and handler.type.id in BROAD_HANDLER_NAMES:
        return True
    if isinstance(handler.type, ast.Attribute):
        # e.g. builtins.Exception
        if isinstance(handler.type.attr, str) and handler.type.attr in BROAD_HANDLER_NAMES:
            return True
    # Tuple containing a broad type
    if isinstance(handler.type, ast.Tuple):
        for elt in handler.type.elts:
            if isinstance(elt, ast.Name) and elt.id in BROAD_HANDLER_NAMES:
                return True
    return False


def _body_has_raise(body: list[ast.stmt]) -> bool:
    """Check if any statement in body (recursively) contains ``raise``."""
    for node in body:
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                return True
    return False


def _body_has_logging_with_context(body: list[ast.stmt], exc_name: str | None) -> bool:
    """Check if the handler logs with exception context.

    We look for calls to ``logging.*()`` or ``logger.*()`` where:
    - the method is a recognized log level, AND
    - (a) the exception variable is referenced as an argument, OR
    - (b) the method is ``exception()`` (which auto-captures exc_info), OR
    - (c) ``exc_info=True`` is passed as a keyword.

    Plain ``logging.info("some message")`` without any exception context
    does NOT count as sufficient logging.
    """
    for node in body:
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if not isinstance(child.func, ast.Attribute):
                continue
            method_name = child.func.attr
            if method_name not in LOGGING_METHODS:
                continue
            # Check the receiver
            receiver = child.func.value
            is_logging_receiver = False
            if isinstance(receiver, ast.Name):
                if receiver.id in LOGGING_NAMES or receiver.id.lower().endswith("logger"):
                    is_logging_receiver = True
            if not is_logging_receiver:
                continue
            # Method is exception() — auto captures traceback
            if method_name == "exception":
                return True
            # exc_info=True keyword
            for kw in child.keywords:
                if kw.arg == "exc_info":
                    if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        return True
            # Exception variable referenced in arguments
            if exc_name:
                for arg in child.args:
                    for n in ast.walk(arg):
                        if isinstance(n, ast.Name) and n.id == exc_name:
                            return True
                # Also check f-strings and format calls
                for arg in child.args:
                    if isinstance(arg, ast.JoinedStr):
                        for val in arg.values:
                            if isinstance(val, ast.FormattedValue):
                                if isinstance(val.value, ast.Name) and val.value.id == exc_name:
                                    return True
    return False


def _walk_same_scope(body: list[ast.stmt]):
    """Yield nodes in *body*, without descending into a nested function/class.

    A `def` or `lambda` inside a handler defines behaviour for later, elsewhere;
    a `return` in there says nothing about whether THIS handler swallows.
    """
    scopes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
    stack = list(body)
    while stack:
        node = stack.pop()
        yield node
        # Yield the `def` itself (it is a statement in this handler) but do not
        # walk into it -- the check must be on the node being descended FROM,
        # not on each child, or the body of a nested function leaks through.
        if isinstance(node, scopes):
            continue
        stack.extend(ast.iter_child_nodes(node))


def _call_mentions(call: ast.Call, exc_name: Optional[str]) -> bool:
    """True if *exc_name* appears anywhere in the call's arguments."""
    if not exc_name:
        return False
    for node in [*call.args, *(kw.value for kw in call.keywords)]:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id == exc_name:
                return True
    return False


def _body_reports_failure(body: list[ast.stmt], exc_name: Optional[str]) -> bool:
    """True if the handler hands the failure to something that surfaces it.

    Covers the two idioms this repo actually uses in place of a logging
    framework (see REPORTING_FUNCTIONS / ACCUMULATOR_METHODS), plus the general
    case of passing the caught exception into any call at all -- if the
    exception value is given to a function, it is not being discarded.

    This cannot prove the report reaches a human. It draws the line between
    "the failure is handed somewhere" and "the failure is dropped on the
    floor", which is the distinction the report is actually claiming.
    """
    for node in _walk_same_scope(body):
        if not isinstance(node, ast.Call):
            continue
        if _call_mentions(node, exc_name):
            return True
        func = node.func
        # An accumulator stores something into a structure the function returns,
        # so the caller can act on it. That is a data path regardless of what is
        # stored, including a constant message.
        if isinstance(func, ast.Attribute) and func.attr in ACCUMULATOR_METHODS:
            return True
        # A reporter call only counts if it carries some context. The same bar
        # the logging check already applies: `print("failed")` names no file, no
        # reason, and no exception, so it cannot tell an operator what broke --
        # that is a swallow with a message on top, not a report.
        is_reporter = (
            (isinstance(func, ast.Name) and func.id in REPORTING_FUNCTIONS)
            or (isinstance(func, ast.Attribute) and func.attr in REPORTING_FUNCTIONS)
        )
        if is_reporter and _call_carries_context(node):
            return True
    return False


def _call_carries_context(call: ast.Call) -> bool:
    """True if any argument is more than a bare literal (an f-string, a name, ...)."""
    for node in [*call.args, *(kw.value for kw in call.keywords)]:
        if isinstance(node, ast.Constant):
            continue
        return True
    return False


def _body_has_fallback(body: list[ast.stmt]) -> bool:
    """Check for deliberate fallback: return, continue, break, or assignment.

    Walks nested statements rather than only the top level. A handler whose body
    is itself a `try/except` where both arms `return` a substitute value is a
    fallback -- just one level deeper than the old top-level-only check could
    see. That misread `assemble_pages._font`, whose three-rung font-resolution
    ladder is the clearest intentional fallback in the repo.
    """
    for node in _walk_same_scope(body):
        if isinstance(node, (ast.Return, ast.Continue, ast.Break, ast.Assign, ast.AugAssign)):
            return True
        # dict/list subscript assignment (d["key"] = value) is an ast.Assign.
    return False


def _body_is_empty_or_pass(body: list[ast.stmt]) -> bool:
    """Return True if body is empty or contains only ``pass``."""
    if not body:
        return True
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return True
    # Single Expr(Constant(Ellipsis)) — ``...``
    if (len(body) == 1
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and body[0].value.value is Ellipsis):
        return True
    return False


def classify_handler(handler: ast.ExceptHandler) -> Tuple[str, str]:
    """Classify a handler.  Returns ``(classification, detail)``."""
    body = handler.body
    exc_name = handler.name  # The ``as exc`` variable, or None
    broad = _is_broad_handler(handler)

    # Empty body
    if _body_is_empty_or_pass(body):
        if broad:
            return "empty-broad", "Empty handler on broad exception type; likely a bug."
        return "cleanup-suppression", "Empty handler on narrow exception type; likely intentional suppression."

    # Re-raised
    if _body_has_raise(body):
        return "re-raised", "Exception is re-raised or wrapped."

    # Logged with context
    if _body_has_logging_with_context(body, exc_name):
        return "logged", "Exception is logged with context."

    # Reported through this repo's actual channels (reporter fn / accumulator /
    # the exception value being passed into any call).
    if _body_reports_failure(body, exc_name):
        return "reported", "Failure is reported (reporter call, accumulator, or exception passed to a call)."

    # Fallback
    if _body_has_fallback(body):
        if broad:
            return "intentional-fallback", "Broad handler with fallback assignment/return (review for adequacy)."
        return "intentional-fallback", "Narrow handler with fallback assignment/return."

    # If we get here, the handler doesn't raise, log, or do an obvious fallback
    if broad:
        return "likely-swallowed", "Broad handler with no raise, logging, or fallback."
    return "likely-swallowed", "Narrow handler with no raise, logging, or fallback."


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------
def is_excluded(path: Path, root: Path) -> bool:
    """Return True if path should be excluded from scanning."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def to_repo_relative(path: Path, root: Path) -> str:
    """Return a forward-slash repo-relative path string."""
    return str(PurePosixPath(path.relative_to(root)))


def _git_tracked_python_files(root: Path) -> Optional[List[Path]]:
    """Return git-tracked ``.py`` files under *root*, or None if git can't answer.

    Why git and not a filesystem walk
    ---------------------------------
    This module's contract is to scan *repository-owned* source. Git tracking is
    the precise definition of that, and a plain ``rglob`` is not: this repo keeps
    full copies of itself on disk (``06_BACKUPS/``, ``05_RELEASE_ARCHIVE/``,
    ``artifacts/release_staging/``), so a walk double-counts every handler in
    every copy.

    That is not hypothetical. Scanning with a walk while ``artifacts/release_staging/``
    existed reported 336 handlers and 29 actionable findings, against a true 167
    and 14 -- an audit report inflated ~2x by duplicates of the same code. An
    audit tool that silently over-reports is worse than none, because the
    duplicate entries look like independent findings.

    The previous guard was a hand-maintained denylist (``EXCLUDE_DIRS``). Three
    separate gates in this repo used that pattern -- pytest, ruff, and this
    scanner -- and all three missed ``artifacts/``. Git tracking needs no
    maintenance and cannot miss a tree nobody anticipated.

    Returns None when *root* is not a git checkout or git is unavailable, so the
    caller can fall back to the walk.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.py"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    decoded = result.stdout.decode("utf-8", errors="surrogateescape")
    return [root / name for name in decoded.split("\0") if name]


def scan_repository(root: Path) -> Tuple[List[Finding], List[ScanError]]:
    """Scan *root* for exception handlers.

    Returns ``(findings, errors)``.
    """
    findings: List[Finding] = []
    errors: List[ScanError] = []

    tracked = _git_tracked_python_files(root)
    candidates = sorted(tracked) if tracked is not None else sorted(root.rglob("*.py"))

    for py_file in candidates:
        if is_excluded(py_file, root):
            continue

        rel_path = to_repo_relative(py_file, root)

        # A file present in the git index but absent from the working tree is
        # reported explicitly rather than skipped: a scanner that quietly drops
        # files understates its own coverage while still looking complete.
        if not py_file.is_file():
            errors.append(ScanError(rel_path, "Tracked in git but missing from the working tree"))
            continue

        # Read
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(ScanError(rel_path, f"Read error: {exc}"))
            continue

        # Parse
        try:
            tree = ast.parse(source, filename=rel_path)
        except SyntaxError as exc:
            errors.append(ScanError(rel_path, f"SyntaxError: {exc}"))
            continue
        except Exception as exc:
            errors.append(ScanError(rel_path, f"Parse error: {exc}"))
            continue

        # Walk
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                handler_type = _handler_type_str(handler)
                classification, detail = classify_handler(handler)
                findings.append(Finding(
                    file=rel_path,
                    line=handler.lineno,
                    handler_type=handler_type,
                    classification=classification,
                    detail=detail,
                ))

    return findings, errors


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def enumeration_mode(root: Path) -> str:
    """Return which file-enumeration strategy :func:`scan_repository` will use."""
    return "git-tracked" if _git_tracked_python_files(root) is not None else "filesystem-walk"


def generate_report(
    findings: List[Finding],
    errors: List[ScanError],
    output_path: Path,
    source_mode: Optional[str] = None,
) -> None:
    """Write a markdown report to *output_path*.

    *source_mode* records how files were enumerated. It belongs in the report
    because the two modes produce materially different totals on this repo (a
    filesystem walk double-counts the on-disk repo copies), and a reader
    comparing two reports must be able to tell a real change from a change of
    enumeration strategy.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Silent Failure Audit Report\n\n")

        if source_mode:
            f.write(f"**Source enumeration:** `{source_mode}`")
            if source_mode == "filesystem-walk":
                f.write(
                    "  \n> **Warning:** not a git checkout, so on-disk copies of the repo "
                    "(backups, release archives, staging trees) may be counted more than "
                    "once. Totals may be inflated."
                )
            f.write("\n\n")

        # Errors section
        if errors:
            f.write("## Files Skipped or Unparseable\n\n")
            f.write("| File | Reason |\n|------|--------|\n")
            for err in errors:
                f.write(f"| {err.file} | {err.reason} |\n")
            f.write("\n")

        if not findings:
            f.write("No `try/except` handlers found in scanned source.\n")
            return

        # Summary counts
        by_class: dict[str, int] = {}
        for finding in findings:
            by_class[finding.classification] = by_class.get(finding.classification, 0) + 1
        f.write("## Summary\n\n")
        f.write(f"Total handlers scanned: {len(findings)}\n\n")
        f.write("| Classification | Count |\n|----------------|-------|\n")
        for cls in sorted(by_class):
            f.write(f"| {cls} | {by_class[cls]} |\n")
        f.write("\n")

        # Full table
        f.write("## All Findings\n\n")
        f.write("| File | Line | Handler | Classification | Detail |\n")
        f.write("|------|------|---------|----------------|--------|\n")
        for finding in sorted(findings):
            f.write(
                f"| {finding.file} | {finding.line} | "
                f"`{finding.handler_type}` | {finding.classification} | "
                f"{finding.detail} |\n"
            )
        f.write("\n")

        # Actionable items
        actionable = [f for f in findings if f.classification in {"likely-swallowed", "empty-broad"}]
        if actionable:
            f.write("## Action Required\n\n")
            f.write("The following handlers require human review:\n\n")
            for finding in sorted(actionable):
                f.write(f"- **{finding.file}:{finding.line}** `{finding.handler_type}` — {finding.detail}\n")
        else:
            suppressed = sum(1 for x in findings if x.classification == "cleanup-suppression")
            f.write("## Result\n\nNo likely-swallowed or empty-broad handlers detected.\n\n")
            # A clean result is itself a claim, and an unqualified all-clear from
            # a static heuristic is the same "empty result presented as valid
            # data" this audit hunts. State the limits with the verdict.
            f.write("### What this does and does not prove\n\n")
            f.write(
                "**Does:** every handler either re-raises, logs with exception context, hands the\n"
                "failure to a reporter or accumulator, or takes a deliberate fallback path. None\n"
                "drops a failure on the floor.\n\n"
            )
            f.write(
                "**Does not:** this is static analysis of handler *shape*. It cannot prove a report\n"
                "reaches a human, that a fallback value is the right one, or that a caller acts on\n"
                "an accumulated error. Those need the caller-level review this report cannot do.\n\n"
            )
            if suppressed:
                f.write(
                    f"**Unreviewed by design:** {suppressed} handlers are classified\n"
                    "`cleanup-suppression` — a narrow exception type with an empty body\n"
                    "(`except FileNotFoundError: pass`). Treating those as intentional is a\n"
                    "judgement, not a finding. If one of them is wrong it will not appear here.\n"
                )

        if errors:
            f.write(f"\n> **Warning:** {len(errors)} file(s) could not be scanned. "
                    "Results may be incomplete.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """CLI entry point.  Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Audit exception handlers for silent failures.",
    )
    parser.add_argument(
        "--output",
        help=(
            "Path to write the markdown report. "
            "Defaults to docs/audit/silent_failure_report.md relative to repo root."
        ),
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to parent of the scripts/ directory.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    output_path = Path(args.output) if args.output else repo_root / "docs" / "audit" / "silent_failure_report.md"

    mode = enumeration_mode(repo_root)
    findings, errors = scan_repository(repo_root)
    generate_report(findings, errors, output_path, source_mode=mode)

    # Print summary to stderr
    actionable = [f for f in findings if f.classification in {"likely-swallowed", "empty-broad"}]
    print(f"Enumeration:      {mode}", file=sys.stderr)
    print(f"Scanned handlers: {len(findings)}", file=sys.stderr)
    print(f"Actionable:       {len(actionable)}", file=sys.stderr)
    print(f"Scan errors:      {len(errors)}", file=sys.stderr)
    print(f"Report:           {output_path}", file=sys.stderr)

    if errors:
        return 2
    if actionable:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
