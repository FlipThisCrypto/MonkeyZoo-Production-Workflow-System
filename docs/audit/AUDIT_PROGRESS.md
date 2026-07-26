# Full-System Audit — Progress Tracker

**Purpose:** durable record of the FULL-SYSTEM CODE CLEANUP, FUNCTIONAL AUDIT,
REPAIR, AND HARDENING LOOP. Written incrementally so the work survives a
context or usage limit. If you are resuming cold, read this file top to bottom
before touching anything.

- **Branch:** `claude/genesis-production-loop`
- **Loop position on resume:** round 2, iteration 12 committed (`8d259a7`)
- **Session started:** 2026-07-26

---

## How to resume this work

1. `git log --oneline -20` — the loop commits one iteration per fix, message
   format `round 2 iteration NN: <what>`.
2. Read the **Iteration Log** below for what is done and what is next.
3. Re-establish the baseline: `python -m pytest -q` from the repo root.
   Expected: **747 tests, all passing** (see Baseline below).
4. Pick the top unchecked item from **Open Findings**.

---

## Baseline (measured, not assumed)

| Measurement | Value | How measured | Date |
|---|---|---|---|
| Tests collected (bare `pytest` from root) | 747 | `python -m pytest --collect-only -q` | 2026-07-26 |
| Bare `pytest` from root, as committed | **BROKEN — 52 collection errors** | see F-001 | 2026-07-26 |
| Tests passing (with `--ignore=artifacts`) | see Iteration Log | `python -m pytest -q --ignore=artifacts` | 2026-07-26 |
| `try/except` handlers in repo-owned code | 167 | `python scripts/silent_failure_audit.py` | 2026-07-26 |
| — of which `likely-swallowed` | 14 | same | 2026-07-26 |

### Live test roots (all tracked test dirs — coverage must never silently drop)

```
00_SYSTEM/scripts/genesis/tests
00_SYSTEM/scripts/integration/tests
00_SYSTEM/scripts/tests
character-bibles/_library/tests
character-bibles/_review_app/tests
character-bibles/_schema/tests
docs/tests
scripts/tests
```

Distribution of the 747: `_review_app` 335, `00_SYSTEM/scripts/tests` 133,
`genesis` 123, `integration` 55, `docs/tests` ~37, `scripts/tests` ~45,
`_schema` 8, `_library` 5.

---

## Completion tracker (Phase 18)

Percentages are evidence-backed. Nothing reaches 100% without a command whose
output is recorded in this file.

| Category | % | Evidence | Issues found | Resolved | Confidence |
|---|---|---|---|---|---|
| Repository mapped | 60% | Root tree + test roots + script inventory enumerated | — | — | Medium |
| Features inventoried | 20% | Truth matrix not yet built | — | — | Low |
| User workflows tested | 15% | `scripts/live_app_test_issue.py` exists; not re-run this round | — | — | Low |
| Silent failures audited | 45% | 167 handlers scanned, 14 actionable triaged in-flight | 14 | 0 | Medium |
| Dead code reviewed | 10% | `scripts/audit_user_paths.py` identified as stray (F-002) | 1 | 0 | Low |
| Redundancy reviewed | 5% | not started | — | — | Low |
| Dependencies reviewed | 5% | not started | — | — | Low |
| Performance measured | 10% | `artifacts/verification/benchmark_perf.py` exists from a prior session, unreviewed | — | — | Low |
| Security reviewed | 30% | CSRF boundary landed r2-i1; no fresh pass this round | — | — | Low |
| Data integrity reviewed | 35% | ledger integrity gate r2-i2, backup verify r2-i3, reconcile r2-i10 | — | — | Medium |
| Tests audited (meaningfulness) | 15% | collection integrity fixed (F-001); assertion-quality pass not started | 1 | 1 | Low |
| Repairs completed | — | see Iteration Log | — | — | — |
| Regression testing completed | 20% | per-iteration only | — | — | Low |
| Documentation reconciled | 10% | not started this round | — | — | Low |
| Production readiness reviewed | 0% | not started | — | — | None |

---

## Open Findings

Severity per the prompt's scale: Critical / High / Medium / Low / Informational.

| ID | Sev | Finding | Status |
|---|---|---|---|
| F-001 | High | Bare `pytest` from repo root dies with 52 collection errors — `artifacts/release_staging/` is a full repo copy with duplicate test basenames | **FIXED** (iteration 13) |
| F-002 | Low | `scripts/audit_user_paths.py` is a stray script from another toolchain (writes to `$ANTIGRAVITY_BRAIN_DIR`, swallows all parse errors) | Open — see below |
| F-003 | Medium | 14 `likely-swallowed` exception handlers pending triage | **IN PROGRESS** (workflow) |
| F-004 | Low | `.coverage` (binary, machine-specific) is tracked in git and shows as modified every run | **FIXED** (iteration 13) |
| F-005 | Medium | `artifacts/` untracked and un-ignored — `git add -A` would commit a second full copy of the repo | **FIXED** (iteration 13) |
| F-006 | Medium | `ruff check .` fails locally with 3 errors, all inside `artifacts/` — the lint gate had the same local-vs-CI divergence as F-001 | **FIXED** (iteration 13) |

### F-002 detail — `scripts/audit_user_paths.py` (untracked, NOT deleted)

Left in place deliberately; it is an untracked local file and deleting another
toolchain's work is not mine to do. Recommendation recorded for the operator:

- Belongs to a different agent toolchain — writes its report to
  `Path(os.getenv("ANTIGRAVITY_BRAIN_DIR", "")) / "user_paths.md"`. When that
  env var is unset the path collapses to a **relative** `user_paths.md`, i.e. it
  silently writes into whatever the current working directory happens to be.
- `except Exception: continue` around the parse loop (line 55) means a file that
  fails to parse is dropped from the report with no record — the report then
  understates coverage while looking complete. Same silent-failure class this
  audit is hunting.
- Functionally superseded by `scripts/silent_failure_audit.py`, which is tested
  (34 tests) and writes to a deterministic repo-relative path.
- **Disposition: Remove** — but operator's call, since it is untracked.

### F-001 detail — pytest collection death

**Evidence**
```
python -m pytest -q
!!!!!!!!!!!!!!!!!! Interrupted: 52 errors during collection !!!!!!!!!!!!!!!!!!!

ERROR collecting artifacts/release_staging/00_SYSTEM/scripts/genesis/tests/test_genesis_build.py
import file mismatch:
imported module 'test_genesis_build' has this __file__ attribute:
  ...\00_SYSTEM\scripts\genesis\tests\test_genesis_build.py
which is not the same as the test file we want to collect:
  ...\artifacts\release_staging\00_SYSTEM\scripts\genesis\tests\test_genesis_build.py
```

**Root cause.** `pytest.ini` guards against exactly this failure mode with a
hand-maintained `norecursedirs` **denylist** (its own comment documents the
`06_BACKUPS` incident). A denylist only protects against artifact trees someone
remembered to add. `artifacts/release_staging/` — a full repo copy staged by a
prior audit session — is new, so the guard missed it and the entire suite died.
CI passes only because a fresh checkout has no `artifacts/` dir, so **local != CI**,
which is the same latent condition the `06_BACKUPS` comment describes.

**Class of defect.** Not "one missing entry" — a fragile guard design. Any future
scratch/staging/export tree re-breaks the whole suite.

**Fix.** Convert the guard from a denylist to an allowlist (`testpaths`), which is
immune to new artifact trees, and add a regression test asserting the allowlist
covers every tracked test directory so coverage cannot silently shrink.

---

## Iteration Log

Newest last. One entry per committed iteration.

### Rounds 1–2 (pre-existing, iterations 1–50 and round 2 iterations 1–12)
Landed before this session; see `git log`. Highlights: CSRF trust boundary,
continuity-ledger integrity gate, verifiable backups, per-character edit
serialization, readiness probe, structured operations log, release
integrity/provenance verification, ledger reconciliation, request correlation
IDs, recent-operations endpoint.

### Round 2, iteration 13 — restore test-suite and lint collection integrity
**Problems fixed:** F-001, F-004, F-005, F-006.

**Root cause.** Both quality gates (`pytest`, `ruff check .`) protected themselves
with hand-maintained *denylists* of artifact trees. A denylist only excludes what
someone remembered to add, so the new `artifacts/release_staging/` tree (a full
repo copy) broke both gates locally while CI stayed green. Same failure the
`pytest.ini` comment already documented for `06_BACKUPS` — patched once by
denylist, so it recurred.

**Changes.**
1. `pytest.ini` — added `testpaths`, an **allowlist** of the 8 live test roots.
   Immune to any artifact tree, anticipated or not. `norecursedirs` retained as
   defense-in-depth (plus `artifacts`) for explicitly-targeted runs.
2. `scripts/tests/test_pytest_collection_integrity.py` — new, 4 tests. Closes the
   allowlist's opposite failure mode (a new test root silently not running):
   asserts `testpaths` covers every git-tracked test directory, that no allowlist
   entry is dead/misspelled, and — behaviorally, via subprocess — that bare
   `pytest` collects cleanly against whatever trees exist on the local machine.
3. `ruff.toml` — added `artifacts` to `extend-exclude`, restoring the stated
   intent that excludes mirror pytest's.
4. `.gitignore` — added `artifacts/`, `.coverage`, `.coverage.*`, `htmlcov/`.
5. `git rm --cached .coverage` — untracked. Zero references anywhere in the repo;
   it was committed by accident around iterations 4–5 and made the working tree
   permanently dirty, which masks real changes in `git status`.

**Evidence.**
- Before: `python -m pytest -q` → `Interrupted: 52 errors during collection`.
- Before: `python -m ruff check .` → `Found 3 errors` (all in `artifacts/`).
- After: `python -m pytest -q` → **751 passed in 62.79s**.
- After: `python -m ruff check .` → `All checks passed!`
- No coverage lost: 747 collected before the fix with `--ignore=artifacts`,
  747 + 4 new guard tests = 751 after.

**Guard proven able to fail (mutation-tested, not assumed).**
- Mutation 1 — removed `docs/tests` from `testpaths`:
  `test_testpaths_cover_every_tracked_test_directory` FAILED. ✅
- Mutation 2 — reverted `pytest.ini` to its pre-fix state entirely:
  `test_pytest_ini_declares_testpaths`, `test_testpaths_cover_every_tracked_test_directory`,
  and `test_bare_collection_from_repo_root_is_clean` all FAILED. ✅
- `pytest.ini` restored and re-verified after each mutation.

**Note.** The guard found a genuine discrepancy on its first run: `scripts/live_app_test_issue.py`
matches a naive `*test_*.py` glob but is a driver script, not a pytest module
(pytest requires the basename to *start* with `test_`). The enumeration was
tightened to pytest's real `python_files` rule rather than widening the allowlist.

---

## Deferred / Not Doing (with reasons)

Recorded so a resuming session does not redo the analysis.

- _(none yet)_
