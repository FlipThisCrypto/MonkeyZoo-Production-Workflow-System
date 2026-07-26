# Full-System Audit — Progress Tracker

**Purpose:** durable record of the FULL-SYSTEM CODE CLEANUP, FUNCTIONAL AUDIT,
REPAIR, AND HARDENING LOOP. Written incrementally so the work survives a
context or usage limit. If you are resuming cold, read this file top to bottom
before touching anything.

- **Branch:** `claude/genesis-production-loop`
- **Loop position on resume:** round 2, iteration 12 committed (`8d259a7`)
- **Loop position now:** round 2, iteration 19 committed
- **Session started:** 2026-07-26

---

## How to resume this work

1. `git log --oneline -20` — the loop commits one iteration per fix, message
   format `round 2 iteration NN: <what>`.
2. Read the **Iteration Log** below for what is done and what is next.
3. Re-establish the baseline: `python -m pytest -q` from the repo root.
   Expected: **795 tests, all passing**, and `python -m ruff check .` clean.
   (It was 747 at session start and bare `pytest` was broken — see F-001.)
4. Pick the top unchecked item from **Open Findings**.

---

## Baseline (measured, not assumed)

| Measurement | Value | How measured | Date |
|---|---|---|---|
| Tests collected (bare `pytest` from root) | 747 | `python -m pytest --collect-only -q` | 2026-07-26 |
| Bare `pytest` from root, as committed | **BROKEN — 52 collection errors** | see F-001 | 2026-07-26 |
| Tests passing, after iteration 13 | **751** | `python -m pytest -q` | 2026-07-26 |
| Tests passing, after iteration 17 | **786** | `python -m pytest -q` | 2026-07-26 |
| Tests passing, after iteration 19 | **795** (+48 this session) | `python -m pytest -q` | 2026-07-26 |
| Clean-clone run (tracked files only) | **795 passed, 0 skipped** | `git clone` + `pytest -q -rs` | 2026-07-26 |
| `ruff check .` | clean (was 3 errors) | `python -m ruff check .` | 2026-07-26 |
| `try/except` handlers in repo-owned code | 170 | `python scripts/silent_failure_audit.py` | 2026-07-26 |
| — of which actionable, after iteration 17 | **0** (was 14, all false positives) | same | 2026-07-26 |

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
| Repository mapped | 80% | root tree, 8 test roots, script inventory, CI steps, all 8 issue folders, 5-lens sweep | — | — | High |
| Features inventoried | 20% | Truth matrix not yet built | — | — | Low |
| User workflows tested | 25% | all 8 issue folders swept through the CLI gate; Studio UI not driven this session | 2 | 0 | Low |
| Silent failures audited | 85% | 170 handlers scanned; all 14 flagged triaged by 13 agents; scanner FP rate 79%→0 | 14 flagged + 3 real | 3 | High |
| Dead code reviewed | 55% | 5-lens sweep, adversarially verified; 4 orphaned drivers found (see CLEANUP_SWEEP_FINDINGS U01/U02/U03/U13) | 4 | 0 | Medium |
| Redundancy reviewed | 50% | dup-logic lens: 3 upheld divergences between the CLI pipeline and the Studio app (U04/U05/U06) | 3 | 1 | Medium |
| Dependencies reviewed | 60% | full import-vs-declaration diff; undeclared selenium fixed, 4 low leads open | 5 | 1 | Medium |
| Performance measured | 10% | `artifacts/verification/benchmark_perf.py` exists from a prior session, unreviewed | — | — | Low |
| Security reviewed | 30% | CSRF boundary landed r2-i1; no fresh pass this round | — | — | Low |
| Data integrity reviewed | 50% | r2-i2/i3/i10 + atomic panel publishing (i16) + gate false-PASS closed (i15) | 2 | 2 | Medium |
| Tests audited (meaningfulness) | 55% | 620 test fns scanned: 0 that cannot fail, 0 always-true asserts, 0 skips in a clean clone; every fix this session mutation-verified | 1 | 1 | High |
| Repairs completed | — | see Iteration Log | — | — | — |
| Regression testing completed | 60% | 39 new tests this session; each fix mutation-verified to fail pre-fix | — | — | Medium |
| Documentation reconciled | 40% | doc-reality lens: 4 upheld mismatches (U11/U16/U17 + genesis --help), 6 low leads | 10 | 1 | Medium |
| Production readiness reviewed | 45% | clean-clone run of all 4 CI gates passed; readiness decision recorded below | — | — | Medium |

---

## Open Findings

Severity per the prompt's scale: Critical / High / Medium / Low / Informational.

| ID | Sev | Finding | Status |
|---|---|---|---|
| F-001 | High | Bare `pytest` from repo root dies with 52 collection errors — `artifacts/release_staging/` is a full repo copy with duplicate test basenames | **FIXED** (iteration 13) |
| F-002 | Low | `scripts/audit_user_paths.py` is a stray script from another toolchain (writes to `$ANTIGRAVITY_BRAIN_DIR`, swallows all parse errors) | Open — see below |
| F-003 | Medium | 14 `likely-swallowed` exception handlers pending triage | **DONE** — all 14 false positives; 3 real defects found nearby (F-003a/b/c) |
| F-004 | Low | `.coverage` (binary, machine-specific) is tracked in git and shows as modified every run | **FIXED** (iteration 13) |
| F-005 | Medium | `artifacts/` untracked and un-ignored — `git add -A` would commit a second full copy of the repo | **FIXED** (iteration 13) |
| F-006 | Medium | `ruff check .` fails locally with 3 errors, all inside `artifacts/` — the lint gate had the same local-vs-CI divergence as F-001 | **FIXED** (iteration 13) |
| F-003a | High | `validate_issue.py` prints PASS/exit 0 on a plan+pack of `{}` or `null` — dangerous false success in the Stage 4/5/8/9 gate | **FIXED** (iteration 15) |
| F-003b | Medium | `genesis_charart.py` non-atomic PNG save + existence-based resume: a truncated/zero-byte panel counts as DONE and QA-passed | **FIXED** (iteration 16) |
| F-003c | Low | `validate_issue.py` schema-blind PASS indistinguishable from a validated one when `jsonschema` is absent | **FIXED** (iteration 15) |
| F-007 | Informational | 2 of 8 real issue folders fail the gate: `2026-10_Issue_02` (empty scaffold, both files missing) and `2026-07_Mango_Pier` (issue_id `MZ-2026-07-MANGO` violates the `MZ-\d{4}-\d{2}-\d{2}` pattern). Both **pre-existing**, neither caused by iteration 15. Likely intentional WIP/experimental folders — flagged for the operator, not auto-"fixed", since changing canon data is human-only per CLAUDE.md | Open — operator decision |
| F-009 | Medium | 3 of 7 shipped art packs contain a `style_lock_phrase` polluted with markdown blockquote gutters (`2026-08_Issue_01`, `2026-09_Issue_02`, `2026-10_Issue_01`; two published). Extractor fixed in i19; the shipped packs are canon + reproducibility records and were **not** rewritten | Open - operator decision |
| F-010 | Informational | `genesis_release.py --verfiy` (typo) used to rebuild the release instead of verifying it. If a release was ever "verified" that way before iteration 18, its artifacts were silently rebuilt - and the manifest sha256s would still match, since both were written together, so it is not detectable after the fact | Open - operator awareness |
| F-008 | Medium | `silent_failure_audit.py` false-positive rate 11/14 (79%) — heuristic blind to `list.append(...)` fallbacks and `print()`/`err()` reporting | **FIXED** (iteration 17) |

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

### Round 2, iteration 15 — validate_issue gate cannot report PASS without checking

**Problem (F-003a, High — dangerous false success).** `validate_issue.py` is the
CLI gate the `mz-new-issue` / `mz-art-run` / `mz-package` skills require to PASS
at Stages 4/5/8/9. `load()` returned whatever `json.loads` produced, and `main()`
guarded each block with truthiness (`if plan:` / `if pack:`). Any document that
*parses* but is falsy — `{}`, `null`, `[]`, `""` — skipped its entire check block
while recording no error, so the gate printed **"PASS — issue package is
structurally valid."** and exited 0.

**Reproduced by execution** (not inferred), via a tmp issue root:

| Input | Before | After |
|---|---|---|
| plan valid, pack `{}` | exit 1 *(only because the plan itself failed schema)* | exit 1 (pack reported) |
| plan valid, pack `null` | exit 1 *(same reason)* | exit 1 (pack reported) |
| plan `{}`, pack `{}`, `--art`, no art on disk | **exit 0, "PASS"** | exit 1 |
| plan `null`, pack `null`, `--art` | **exit 0, "PASS"** | exit 1 |
| plan `[]`, pack `{}` | **exit 0, "PASS"** | exit 1 |

`null` was the sharpest edge: `json.loads("null")` raises nothing, so `load()`
recorded no error and its `None` was indistinguishable from the missing-file
sentinel. The app-side sibling (`issue_workflow._json`) already got this right,
so the two implementations of the same gate disagreed.

**Fixes.**
1. `load()` rejects a parsed payload that is not a non-empty object; every falsy
   return now carries a recorded error, so `main()` always reaches `sys.exit(1)`.
2. `--art` with zero planned panels is now reported instead of silently
   skipped (`if check_art and plan_ids:` → `if check_art:` + explicit error).
   A plan with `pages: []` is a well-formed object, so fix 1 does not catch it.
3. **F-003c (Low).** `schema_check()` returned silently when `jsonschema` was
   absent, so a schema-blind run printed the same unqualified PASS as a fully
   validated one. The verdict now discloses it: *"PASS — built-in checks only
   (jsonschema not installed: JSON Schema validation SKIPPED)."* Fallback-only
   mode stays intended behaviour per the module docstring; the defect was that
   it was invisible.

**Evidence.**
- 9 new tests in `00_SYSTEM/scripts/tests/test_validate_issue.py`, written red
  first: all 8 behavioural ones failed before the fix, all pass after.
- Over-correction guarded two ways: a scoped check that the new errors do not
  fire on a populated package, and `test_real_committed_issue_still_passes`,
  which runs the gate against real committed canon (`2026-07_Issue_05 --art`).
- Swept all 8 real issue folders. 6 PASS. The 2 failures (`2026-07_Mango_Pier`,
  `2026-10_Issue_02`) are **pre-existing and unrelated** — verified by grepping
  their output for the new error strings: 0 occurrences in both. See F-007.
- `768 passed` / `ruff All checks passed!`

**Triage provenance.** 14 scanner-flagged handlers were triaged by 12 independent
agents plus an adversarial synthesis pass. **11 of 14 were rejected as false
positives** with quoted code and named callers. Only 3 survived. The scanner's
heuristic misses two idioms this repo uses constantly — a fallback expressed as
`list.append(...)` (a method call, not `ast.Assign`) and status reported via
`print()` (the repo imports no logging framework) — which is where nearly all
the noise came from. See F-008.

### Round 2, iteration 16 — a panel file stops being a false completion record

**Problem (F-003b, Medium — data integrity / false success).** In the Genesis art
pipeline the panel file at its final path is not just an image, it *is* the
completion record, read by two independent consumers:
- `genesis_charart.run_full_batch` resumes on `out.exists()`;
- `genesis_matrix.build` derives its bespoke set from `native.glob("*.png")`,
  and `classify()` turns membership into `status="DONE"`,
  `visual_qa_result="pass"`.

All three writers (`make_panel_native`, `make_multi_panel`, `make_panel`) wrote
with `img.save(out)` straight onto that path. A save interrupted part-way left a
truncated file that permanently claims success: the resume guard skips it
forever and the matrix reports the panel finished and QA-passed. That
contradicts the CLAUDE.md rule that nothing generated is canon until it passes
QA.

Not an exotic path: these are multi-hour 96-panel ComfyUI batches and killing
the process is the documented ZLUDA hang recovery (`mz-art-run`), so an
interrupted save is an expected event.

**Fix — placed at the root, not at the symptom.** The first attempt wrapped only
`run_full_batch`'s call site, which left the sibling `run_batch` still exposed.
Atomicity now lives in one helper, `_save_atomic(img, out)`, used by all three
writers, so every caller present and future is covered: render to
`<name>.png.part`, rename onto the final path only on a complete write, delete
the scratch file on failure. The scratch name is invisible to both readers — the
resume guard looks for `<name>.png`, and `glob("*.png")` does not match a name
ending `.part`.

Two supporting guards for files left by earlier runs:
- `run_full_batch` resume guard now requires `st_size > 0`, so an empty leftover
  is regenerated rather than masking a missing panel forever.
- `genesis_matrix.build` counts a panel as bespoke only if its file has bytes,
  so a leftover cannot be reported DONE/QA-passed.

**A real bug the new tests caught in the fix itself.** Pillow infers its encoder
from the filename extension, and `.part` is not a known extension — the first
version of `_save_atomic` raised `unknown file extension: .part` on every save,
which would have broken the entire art pipeline. The format is now taken from
the final name via `Image.registered_extensions()`. This is the argument for
writing the tests before trusting the fix.

**Evidence.**
- 8 new tests (5 in `test_genesis_charart.py`, 3 in `test_genesis_matrix.py`).
- Mutation-verified twice. Reverting `_save_atomic` to a direct save fails
  `test_save_atomic_leaves_no_file_at_the_final_path_when_the_write_fails` and
  `test_save_atomic_does_not_destroy_an_existing_panel_when_a_rewrite_fails`.
  Reverting the matrix guard to existence-only fails
  `test_zero_byte_panel_is_not_reported_done_and_qa_passed`.
- Over-correction guarded: the happy path still publishes to `<pid>.png`, and a
  real written panel still classifies DONE/pass.
- `776 passed` / `ruff All checks passed!`

### Round 2, iteration 17 — the audit tool stops crying wolf

**Problem (F-008, Medium).** The scanner's first real run flagged 14 handlers;
independent triage rejected **11 of 14 (79%)** as false positives. Every
rejection came down to two idioms the heuristic did not know, both used
constantly here because the repo imports no logging framework anywhere:

- a **reporter function** — `err(...)` accumulating into a module-global that
  drives `sys.exit(1)`, `log(...)` writing a FAIL row, or plain `print(...)`;
- an **accumulator** — `skipped.append({...})`, `problems.append(f"...{exc}")`,
  whose contents are returned to the caller.

Neither is an `ast.Assign`, so both read as "no raise, no logging, no fallback".
A tool with a 79% false-positive rate gets ignored, which is worse than no tool.

**Fix.** New `reported` classification; `_body_has_fallback` now walks nested
statements (catching the `assemble_pages._font` three-rung ladder); the walk
stops at a nested `def`/`lambda`/`class`.

**Deliberately not more permissive than that.** A reporter call counts only if it
carries context — the same bar the logging check already applied. `print("failed")`
stays `likely-swallowed`: a swallow with a message on top is still a swallow.

**Guarded in both directions.** `TestStillCatchesRealSwallows` pins that a bare
`pass`, a contextless report, an unrelated call, and a `return` inside a nested
`def` all remain actionable, and that a repo containing a swallow still exits 1.
A permissive classifier is its own silent failure — "0 actionable" must mean the
code is clean, not that the tool stopped looking.

**Result.** 170 handlers, **0 actionable**: 54 re-raised, 55 intentional-fallback,
31 reported, 30 cleanup-suppression. Four reclassifications spot-checked against
the triage evidence; all match.

Because a clean verdict is itself a claim, the report now publishes its own
limits next to it — what shape analysis proves, what it cannot (that a report
reaches a human, that a fallback value is correct, that a caller acts on an
accumulated error), and that the 30 `cleanup-suppression` handlers are
unreviewed by design.

`786 passed` / `ruff All checks passed!`

**Honest note on the 3 "confirmed" findings.** None of them was actually one of
the 14 flagged handlers. The agents found them by reasoning *around* the flagged
sites — `load()`'s falsy return (F-003a), the resume guard above the handler
(F-003b), the `ImportError` arm classified `intentional-fallback` (F-003c). So
of the handlers the scanner flagged, **all 14 were false positives**. The value
came from directing careful attention at that code, not from the flags.

### Round 2, iteration 18 - a typo can no longer destroy a release

Four findings from the adversarially-verified sweep (see
[CLEANUP_SWEEP_FINDINGS.md](CLEANUP_SWEEP_FINDINGS.md), U07/U08/U09/U12).

1. **`genesis_release.py` unknown flags reached the destructive path.** `main()`
   split argv with `[a for a in sys.argv[1:] if not a.startswith("--")]`, so any
   unrecognised flag was silently discarded and execution fell through to
   `package()`, which rewrites the CBZ, PDF, manifest and SHA256SUMS. `--help`
   rebuilt the release instead of printing help. Worse: a typo'd **`--verfiy`
   rebuilt the release instead of verifying it** - the one command an operator
   reaches for to confirm a release is intact was the one most likely to destroy
   it, and it reported success while doing so. Now aborts with usage/exit 2
   before writing anything. Verified as the only genesis script with this shape;
   the other nine take `sys.argv[1]` as a path and fail loudly on a stray flag.
2. **`pytest.ini` `norecursedirs` replaces pytest's defaults** rather than
   extending them, dropping `.*`/`venv`/`build`/`dist`/`*.egg`. Defaults restated.
   Verified behaviourally: a failing test planted in `.venv/Lib/site-packages/`
   is still not collected (791, not 792).
3. **`.venv/` absent from `.gitignore`** while both launchers create it at the
   repo root - `git add -A` would have committed an interpreter tree.
4. **`selenium` imported but declared nowhere.** `docs/SHIP_READINESS_ASSESSMENT.md`
   tells operators to run `live_app_test_issue.py`, whose `except Exception`
   folded `ModuleNotFoundError` in with real browser failures - so on a clean
   install the documented verification reported a **UI regression** when the real
   problem was a missing package. Declared, plus a dedicated `ImportError` arm
   that says the UI check *did not run* and names the fix. Still a FAIL: claiming
   PASS for a UI never exercised would be a false success.

5 new CLI-safety tests, mutation-verified. `791 passed` / ruff clean.

### Round 2, iteration 19 - markdown gutters out of the Rule 3 style lock

**Problem (U04, Medium - canon correctness, already shipped).** The canonical
style lock lives in `visual_style_bible.md` as a five-line markdown blockquote.
The Studio captured it raw, so the newline-plus-`> ` gutter of every
continuation line ended up *inside* the phrase:

```
MonkeyZoo house style: ... round head,\n> huge white oval eyes ...
```

That became `style_lock_phrase` in the art prompt pack, and Rule 3 requires
every panel prompt to start with it - so literal `>` characters and newlines
were sent to the image model inside the phrase that defines house style.

**Already shipped: 3 of 7 issue packs carry it** - `2026-08_Issue_01`,
`2026-09_Issue_02`, `2026-10_Issue_01`; two are published to `05_RELEASE_ARCHIVE`.

**Why the gate never caught it.** `validate_issue.py` checks
`style_lock_phrase.startswith("MonkeyZoo house style")` - true for the polluted
phrase - and the per-panel check compares each prompt against *that same
polluted value*. Both sides agreed with each other and passed. A consistency
check between two things derived from the same wrong source proves nothing.

**Fix.** `_unwrap_blockquote()` strips the gutter and collapses whitespace before
the canonicality check. The extracted phrase is now byte-identical to
`DEFAULT_STYLE_LOCK`, and the tests assert exactly that: two independent
constructions of the canonical phrase must agree, or one is wrong and every
prompt built from the loser is off-canon.

**The three affected packs are deliberately NOT rewritten** - they are canon and
the reproducibility record for art already generated and human-QA'd. Editing
them would break that record, and canon changes are human-only per CLAUDE.md.
Recorded for the operator as F-009.

4 new tests, mutation-verified. `795 passed` / ruff clean.

### Clean-environment verification (Phase 16) - passed

Cloned the repo to a scratch dir (tracked files only, no local state) and ran
every CI gate there:

| Gate | Result |
|---|---|
| `pytest -q -rs` | **795 passed, 0 skipped** |
| `ruff check .` | All checks passed |
| `validate-character-bibles.py` | 12 bibles, PASSED, 0 warnings |
| `validate_ledger.py` | 9 entries, 0 errors |

**Zero skips is the significant number.** Twelve `pytest.skip("fixture missing")`
guards exist across the genesis/integration suites; the concern was that they
fire in CI (where gitignored heavy art is absent), making CI's green weaker than
local green. They do not fire - every fixture they guard is git-tracked. No test
depends on untracked local state.

One false alarm, recorded so it is not re-investigated: the first clone attempt
failed checkout with `Filename too long`. That was my scratch destination
(~135 chars) plus the repo's longest tracked path (137 chars) exceeding Windows'
260-char limit - **not** a repo defect. Any clone destination deeper than
~120 chars needs `git clone -c core.longpaths=true` on Windows. Linux CI is
unaffected.

---

## Deferred / Not Doing (with reasons)

Recorded so a resuming session does not redo the analysis.

- _(none yet)_

---

## Executive assessment (as of round 2, iteration 19)

### Overall condition

The system is **materially healthier than it looked at session start, and the
gap was not visible from the outside**. Every automated gate reported green
while, locally, neither gate was actually running: bare `pytest` died with 52
collection errors and `ruff check .` reported 3 — both caused by an artifact
tree that CI never sees. A green CI badge was being produced by a checkout that
happened to lack the directory that broke everything else.

That is the theme of this round. Nothing found here was announced by a failing
test. Each defect was a mechanism that produced a **confident, passing signal
while doing less than it claimed**.

### The pattern worth naming

Five of the seven defects repaired share one shape: *a check that agrees with
itself*.

- `validate_issue.py` guarded its checks with `if plan:` and reported PASS when
  the plan was `{}` — the absence of errors came from the absence of checking.
- The Rule 3 style-lock gate compared each panel prompt against the pack's own
  `style_lock_phrase`. Both were derived from the same polluted source, so they
  matched, and the gate passed 3 shipped packs containing markdown gutters.
- A panel file's existence was treated as proof the panel finished, by both the
  resume guard and the completion matrix — so a half-written file claimed DONE
  and QA-passed to both readers.
- `pytest.ini` and `ruff.toml` each guarded themselves with a hand-maintained
  denylist, and the silent-failure scanner did too. All three missed the same
  directory, independently.
- The scanner then reported 14 findings, of which **all 14 were false
  positives** — a tool loudly confirming its own assumptions.

A consistency check between two things derived from the same wrong source proves
nothing. Most of the repairs here amount to giving each check an *independent*
reference point.

### Strongest areas

- **Test suite integrity is genuinely high.** 620 test functions: zero that
  cannot fail, zero always-true assertions, and — verified in a fresh clone —
  zero skips. The twelve `pytest.skip("fixture missing")` guards never fire
  because every fixture they guard is tracked.
- **Canon data handling is conservative by design** and that discipline held:
  the ledger gate, backup verification, and reconciliation from earlier
  iterations all pass in a clean environment.
- **Failure reporting is better than it appeared.** After correcting the
  scanner's blind spots, all 170 exception handlers either re-raise, log with
  context, report through a reporter/accumulator, or take a deliberate fallback.
  None drops a failure on the floor.

### Weakest areas

- **Two implementations of the same pipeline.** The CLI scripts and the Studio
  app independently implement issue validation, style-lock construction, cover
  location, and page-plan requirements — and they **disagree**. One divergence
  is fixed (U04); two remain open (U05: 3 of 7 issues have a cover the Studio
  cannot see; U06: the Studio promotes plans the CLI gate rejects). This is the
  single largest source of remaining risk.
- **Orphaned one-off drivers armed with destructive calls.** Four scripts in
  `scripts/` have no reference from any skill, runbook, CI step or test, yet sit
  beside live operator entry points and carry `{"replace": True}` publish calls
  against already-published archives (U01/U02/U13).
- **Performance is unmeasured.** No baseline was established this round. The
  10% figure is honest, not modest.
- **Security had no fresh pass** beyond what earlier iterations landed.

### Production readiness decision

**Approved for controlled testing only — with documented limitations.**

Reasoning, on evidence:

- *Supporting approval:* all four CI gates pass from a clean clone of tracked
  files only (795 tests, 0 skips; ruff clean; 12 character bibles valid; ledger
  valid). Every repair this session is mutation-verified to fail against the
  pre-fix code, so the regression net is known to work rather than assumed to.
- *Blocking full approval:* the CLI/Studio divergences (U05, U06) mean an
  operator can complete a workflow in one surface that the other rejects, and
  neither surface reports the disagreement. Until those are reconciled, a
  release path exists that passes every gate and still produces an
  inconsistent package.
- *Also unresolved:* performance has no baseline, and no security pass was run
  this round. Neither is known-bad; both are unmeasured, and unmeasured is not
  the same as fine.

This is a deliberate downgrade from what the passing gates alone would suggest.
The gates passing is exactly the condition this audit found to be untrustworthy
at session start.

### What an operator should decide (not mine to decide)

- **F-009** — 3 shipped packs contain a polluted style lock; 2 are published.
  The extractor is fixed, but rewriting the shipped packs would break the
  reproducibility record for art already generated and human-QA'd. Canon is
  human-only.
- **F-010** — if any release was ever "verified" with a typo'd flag before
  iteration 18, it was silently rebuilt instead, and the manifest hashes would
  still match because both were written together. Not detectable after the fact.
- **F-007** — `2026-07_Mango_Pier` uses a non-conforming issue id and
  `2026-10_Issue_02` is an empty scaffold. Both fail the gate; both look
  intentional.
- **F-002** — `scripts/audit_user_paths.py`, an untracked stray from another
  toolchain, is superseded and writes to an unpredictable relative path.

### Honest limits of this audit

- Phases 3 (real user paths through the Studio UI), 7 (performance measurement),
  10 (security) and 12 (failure injection) were **not** run this round. Their
  tracker percentages reflect that.
- The functionality truth matrix (Phase 2) is not built; only the slices touched
  by repairs were classified.
- 21 low-severity leads from the sweep were never sent for verification and
  remain unproven. They are recorded as leads, not findings.
