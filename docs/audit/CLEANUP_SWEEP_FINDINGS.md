# Cleanup / Redundancy / Dependency Sweep — Findings Backlog

Phases 5, 6, 8 and 17 of the full-system audit. Produced by five parallel
lenses (dead code, duplicated logic, dependencies, config drift, docs-vs-reality),
each finding then handed to an independent skeptic instructed to **refute** it.
Only findings a skeptic could not refute by reading real code appear as upheld.

**Result: 41 raised → 17 upheld, 3 refuted outright, 21 low-severity/Retain not sent to verification.**

Severity and disposition below are the *skeptic's corrected* values, not the finder's.

> Status column is maintained by hand as the loop works through these.

---

## Upheld findings

| # | Sev | Disposition | Location | Finding | Status |
|---|---|---|---|---|---|
| U01 | High | Deprecate | `scripts/drive_issue_02_pipeline.py:577` | Orphaned multi-stage Issue 02 driver, also armed with replace:True publish | Open |
| U02 | Medium | Deprecate | `scripts/prepare_issue01_release_assets.py:339` | Orphaned one-off driver republishes an already-published release archive with replace:True | Open |
| U03 | Medium | Investigate Further | `00_SYSTEM/scripts/file_story_bible_and_refs.py` | 00_SYSTEM/scripts/file_story_bible_and_refs.py has zero references of any kind — 403 lines, no test, no doc, no skill, no CI | Open |
| U04 | Medium | Repair | `character-bibles/_review_app/art_prompt_workspace.py:157` | Style-lock (Rule 3) phrase has two constructions; the Studio's scrape leaks markdown blockquote gutters into every promoted panel prompt | **FIXED** (r2-i19) |
| U05 | Medium | Repair | `character-bibles/_review_app/release_workspace.py:90` | Release gate and CLI packager disagree on where the final cover lives; 3 of 7 real issues have a cover the Studio cannot see | Open |
| U06 | Medium | Consolidate | `character-bibles/_review_app/page_panel_workspace.py:177` | Studio promotes page plans that validate_issue.py (the Stage 4/5/9 gate) rejects: emotion and camera_angle are required by one implementation and not the other | **FIXED** (r2-i20) |
| U07 | Medium | Repair | `scripts/live_app_test_issue.py:345` | `selenium` is imported but declared nowhere; on a clean install the documented verification script reports a UI regression instead of a missing dependency | **FIXED** (r2-i18) |
| U08 | Medium | Repair | `pytest.ini:40-52` | pytest.ini `norecursedirs` REPLACES pytest's built-in defaults, silently dropping `.*`, `venv`, `build`, `dist`, `*.egg` — so `pytest .` now recurses into the `.venv/` both launchers create at the repo root | **FIXED** (r2-i18) |
| U09 | Medium | Repair | `.gitignore` | `.venv/` is absent from .gitignore although both documented launchers create it at the repo root — `git add -A` would commit the entire virtualenv | **FIXED** (r2-i18) |
| U10 | Medium | Repair | `scripts/backup_production.py:19-27` | backup_production.py `DEFAULT_TARGETS` omits `GENESIS/`, so the 137 MB of print masters that GENESIS/.gitignore deliberately keeps out of git exist in neither git nor any backup | Open |
| U11 | Medium | Repair | `CONTRIBUTING.md:22` | CONTRIBUTING says CI runs "exactly" ruff + pytest; CI runs four more gates, and one has no local pytest equivalent | Open |
| U12 | Medium | Repair | `00_SYSTEM/scripts/genesis/genesis_release.py:158` | Genesis scripts silently ignore unknown flags; `genesis_release.py --help` performs a destructive release rebuild instead of printing help | **FIXED** (r2-i18) |
| U13 | Low | Deprecate | `scripts/compose_issue01_draft_panels.py:221` | scripts/compose_issue01_draft_panels.py is orphaned and mutates a published issue's workflow state | Open |
| U14 | Low | Consolidate | `Start-BananaLab.ps1:83` | Three launcher/runbook surfaces hardcode a four-package install list, contradicting CONTRIBUTING.md's "single source of truth" claim | Open |
| U15 | Low | Repair | `00_SYSTEM/scripts/genesis/genesis_charart.py:36` | Four tracked pipeline scripts hard-code `I:\ai\nft\...` as a module-level constant with no env-var or config override | Open |
| U16 | Low | Repair | `README.md:22` | $env:PORT is documented in three places as a way to set the Studio port, but Start-BananaLab.ps1 unconditionally overwrites it | Open |
| U17 | Low | Repair | `00_SYSTEM/automation_rules.md:109` | automation_rules §6A documents an `alpha_matte.py --inset` mode that the CLI does not expose | Open |

---

## Upheld findings — full evidence

### U01 — Orphaned multi-stage Issue 02 driver, also armed with replace:True publish

- **Location:** `scripts/drive_issue_02_pipeline.py:577`
- **Lens:** dead-python  |  **Category:** dead-code
- **Severity:** High  |  **Disposition:** Deprecate

**Evidence**

`git grep -n drive_issue_02_pipeline` over all tracked files: three provenance hits in `00_SYSTEM/project_direction.json` (lines 339, 350, 361 — all inside `"docs"` arrays of tasks marked `"DONE 2026-07-16."`), the same three in the `docs/static/` mirror, auto-generated audit-report rows, and one architectural criticism at `00_SYSTEM/integration_upgrade/ARCHITECTURE_FINDINGS.md:11` describing `compose()` as pasting "each character's whole 220×220 opaque square ref onto a darkened background plate". Zero hits in skills, CI, README, runbooks, `*.ps1`, or any Python import. It is a full 616-line stage runner with a dispatch table and CLI (`STAGES[sys.argv[1]]()`, `if __name__ == "__main__": raise SystemExit(main())`) targeting `MZ-2026-09-02`, which `ls 05_RELEASE_ARCHIVE/2026/` shows is already published as `2026-09_Issue_02`. It force-overwrites at four points: lines 80, 100, 311 promote variants with `{"replace": True}` and line 577 does `req("POST", f"/api/issues/{ISSUE}/release/publish-archive", {"replace": True})`.

**Rationale**

Same loaded-gun profile as prepare_issue01, at 616 lines the largest orphan in `scripts/`. Its `compose()` is additionally flagged by the repo's own ARCHITECTURE_FINDINGS.md as the card-cutout paste technique the integration upgrade was built to replace, so it is not just unreachable but supersedes-by-design dead.

**Risk if this disposition is acted on and the analysis is wrong**

Its six named stages (page_plan|art_prompts|art_production|qa|release_assets|publish) are the only end-to-end scripted walk of the Studio API for a full issue; deprecating it without first extracting that sequence into the tested `rc_real_issue_run.py` path would lose coverage of stage transitions no unit test exercises.

**Skeptic's verdict**

Independently confirmed every claim by reading the files. scripts/drive_issue_02_pipeline.py is 616 lines with a real CLI dispatch (`STAGES[sys.argv[1]]()` at :611, `if __name__ == "__main__"` at :615) targeting ISSUE = "MZ-2026-09-02" (:21), which 05_RELEASE_ARCHIVE/2026/ shows already published as 2026-09_Issue_02. The force-overwrite is real and the guard it bypasses is real: release_workspace.py:182-183 raises `ReleaseError(f"Release archive already exists at {archive.as_posix()}; explicit replacement confirmation is required", 409)` only `if archive.exists() and not replace`, then :218-220 does `shutil.rmtree(archive); os.replace(staging, archive)`. stage_publish() manufactures its own preconditions — /release/approve at :569 and /release/promote-manifest {"replace": True} at :574 — immediately before the destructive publish-archive {"replace": True} at :577. compose() matches ARCHITECTURE_FINDINGS.md:11 verbatim (`box_w, box_h = 220, 220` at :171, fixed bottom row `y0 = H - box_h - 80`, solid frame `Image.new("RGB", (box_w + 8, box_h + 8), (120, 200, 255))`, opaque `canvas.paste(face, (x, y0))`, self-label `f"{pid}  ·  DRAFT COMPOSITE"` at :201), and that doc's later status table confirms the replacement shipped ("True-alpha character layers | **Built**"). Orphan status survives all required checks: the four SKILL.md files name only assemble_pages/build_release/run_art_batch/genesis_release/gen_char_refs/validate_issue; validate.yml runs only ruff, pytest, and three named validators; zero hits across 14 tracked *.ps1, scripts/tests/*, README, runbooks; no importlib/glob dispatch over scripts/. The project_direction.json hits at 339/350/361 are "docs" provenance arrays on tasks whose instructions begin "DONE 2026-07-16.". TWO CORRECTIONS, both strengthening the claim: (1) they undercount the force-overwrite points as four — there are five, they missed :574 promote-manifest {"replace": True}; (2) `git ls-files 05_RELEASE_ARCHIVE/2026/2026-09_Issue_02` returns 0 files, so the overwrite target is UNTRACKED and not recoverable by git checkout — recovery depends on 06_BACKUPS/. "Largest orphan in scripts/" also holds (workflow_engine.py 759 and silent_failure_audit.py 639 are larger but both have tests). Severity High upheld on the untracked-target blast radius plus CLAUDE.md's own grant that agents "run scripts/*.py", making a conventionally-named stage runner agent-discoverable. Deprecate upheld over Remove: project_direction.json cites this script as the provenance record for the shipped selected_panels/ and the published archive, and since that archive is untracked this file is the only in-repo account of how those artifacts were produced — neutering it (refuse-to-run guard or dropping replace:True) disarms the gun without destroying the record.

---

### U02 — Orphaned one-off driver republishes an already-published release archive with replace:True

- **Location:** `scripts/prepare_issue01_release_assets.py:339`
- **Lens:** dead-python  |  **Category:** dead-code
- **Severity:** Medium  |  **Disposition:** Deprecate

**Evidence**

No executable reference exists. `git grep -n prepare_issue01_release_assets` over all tracked files returns exactly three non-self hits, none of them an invocation: `00_SYSTEM/project_direction.json:620` and its mirror `docs/static/project-direction.json:620` (both inside a `"docs": [...]` provenance array of a task whose `"instructions"` begin `"DONE 2026-07-16."`), plus auto-generated rows in `docs/audit/silent_failure_report.md`. It is absent from all four `.claude/skills/*/SKILL.md`, `.github/workflows/validate.yml`, `README.md`, `docs/OPERATOR_RUNBOOK.md`, `config/production_config.yaml`, and all 14 tracked `*.ps1`. I confirmed the `docs` array is inert: `character-bibles/_review_app/project_direction.py` (read in full, 101 lines) reads only `tracks`/`tasks`/`id`/`title`/`status`/`priority`/`recommended_order` and never a `docs` key; `character-bibles/_review_app/static/app.js:1021` renders it as inert text: `${(task.docs && task.docs.length) ? `<p><strong>Docs:</strong> ${task.docs.map(d => `<code>${escapeHtml(d)}</code>`).join(" · ")}</p>` : ""}`. Meanwhile the script is armed and runnable: it hardcodes `ISSUE = "MZ-2026-08-01"`, ends with `if __name__ == "__main__": raise SystemExit(main())`, and main() ends by force-overwriting the published archive:
```
code, promo = req("POST", f"/api/issues/{ISSUE}/release/promote-manifest", {"replace": True})
must(code == 200, "promote_manifest", promo)

code, pub = req("POST", f"/api/issues/{ISSUE}/release/publish-archive", {"replace": True})
```
`ls 05_RELEASE_ARCHIVE/2026/` confirms `2026-08_Issue_01` is already published.

**Rationale**

This is dead code holding a loaded gun. Nothing reaches it, so it earns no keep-value, yet it sits in the same `scripts/` directory as two live operator entry points (`package_issue.py`, `rc_real_issue_run.py`) that README.md tells operators to run by name. An operator or agent pattern-matching on `scripts/*.py` can run it against a live Studio and silently overwrite a shipped release. Deprecate rather than Remove because the file is the only executable record of how Issue 01's CHIP-0015/cover/PDF/CBZ package was actually built; move it under an explicitly archived path or gate `main()` behind a `--i-know-this-republishes` flag before deleting.

**Risk if this disposition is acted on and the analysis is wrong**

If this is in fact the intended re-run path for regenerating Issue 01 release deliverables, deprecating it removes the only reproducible recipe for a published archive — and the 05_RELEASE_ARCHIVE copy is a build output, not a build script, so the recipe would not be recoverable from it.

**Skeptic's verdict**

Facts fully confirmed by independent reading; severity corrected High -> Medium.

CONFIRMED: scripts/prepare_issue01_release_assets.py:20 is `ISSUE = "MZ-2026-08-01"`; :364-365 is `if __name__ == "__main__": raise SystemExit(main())`; :339-342 matches their quote verbatim. The destructive mechanism is real: character-bibles/_review_app/release_workspace.py:182-183 `if archive.exists() and not replace: raise ReleaseError(...)` and :218-219 `if archive.exists(): shutil.rmtree(archive)`, with `_archive()` (:51-53) resolving to 05_RELEASE_ARCHIVE/<year>/<folder>, i.e. 05_RELEASE_ARCHIVE/2026/2026-08_Issue_01 — which exists and is recorded published in .release-workspace/publication.json ("published_at": "2026-07-16T00:05:22+00:00"). Orphan status holds: git grep returns only 00_SYSTEM/project_direction.json:620, its mirror docs/static/project-direction.json:620, and three auto-generated docs/audit/silent_failure_report.md rows. Zero hits across .claude/ (all four SKILL.md files), README.md, docs/*.md, .github/workflows/validate.yml, all *.ps1, and all tests; no runpy/importlib/scripts-glob dispatch outside 06_BACKUPS/ and artifacts/. The `docs` array is inert exactly as claimed — project_direction.py (read in full) reads only tracks/tasks/recommended_order/id/title/status/priority, and app.js:1021 matches their quote character-for-character.

SEVERITY CORRECTED to Medium on four independent grounds:
(1) The hazard is class-level, not file-level. scripts/drive_issue_02_pipeline.py:574,577 and scripts/live_app_test_issue.py:331,333 contain the byte-identical `promote-manifest {"replace": True}` + `publish-archive {"replace": True}` pair against MZ-2026-09-02 and MZ-2026-10-01, both of which have published archives (05_RELEASE_ARCHIVE/2026/ holds 2026-09_Issue_02 and 2026-10_Issue_01). docs/SHIP_READINESS_ASSESSMENT.md:93 actively tells operators to run `python scripts/live_app_test_issue.py` (app running). Deprecating this one file does not remove the stated risk.
(2) The path is heavily gated. _stage() (release_workspace.py:36-38) requires active stage release/published; approve() (:130) raises 409 "Current release evidence is already approved" on unchanged evidence, and the script's `must(code == 200, "release_approve", appr)` exits 1 there — before line 339 is ever reached. A non-running Studio raises an uncaught URLError (only HTTPError is handled at :36).
(3) publish_archive was already hardened against precisely this destruction: :201-208 stages into a temp dir and swaps only after every copy succeeds ("so a failed/interrupted copy cannot destroy the previously published release archive").
(4) Blast radius is local and largely git-recoverable. 05_RELEASE_ARCHIVE/ is gitignored (.gitignore:20), but every file in it is a copy of the issue folder, and metadata.json, qa_report.md, social_posts.md, release_hash_manifest.json, cover_prompt.md and final_export_checklist.md are all git-tracked. The script pushes/mints/pins nothing external.

DISPOSITION Deprecate upheld — it breaks nothing (no test names the file; CI only runs `ruff check .` over it) — but it must be applied to the whole class of one-off drivers, not to this file alone, or the risk it describes is untouched.

---

### U03 — 00_SYSTEM/scripts/file_story_bible_and_refs.py has zero references of any kind — 403 lines, no test, no doc, no skill, no CI

- **Location:** `00_SYSTEM/scripts/file_story_bible_and_refs.py`
- **Lens:** dead-python  |  **Category:** dead-code
- **Severity:** Medium  |  **Disposition:** Investigate Further

**Evidence**

This is the only tracked module in `00_SYSTEM/scripts/` with a completely empty reachability set. I ran a per-basename sweep across every tracked non-test .py in `00_SYSTEM/scripts/` (`for f in $(git ls-files '00_SYSTEM/scripts/*.py'); do git grep -l -I "$(basename $f .py)" ...`) — every other module returned at least one SKILL.md, README, runbook, test, or importer; `file_story_bible_and_refs` returned nothing. Confirmed separately with `git grep -rn "file_story_bible\|story_bible_and_refs"` — no output. It has no test file (contrast: `00_SYSTEM/scripts/tests/` covers assemble_pages, build_release, gen_char_refs, new_issue, run_art_batch, validate_issue, validate_ledger). It is a mutating filing script — `import shutil`, `def copy_if_present(...)`, `def file_season_bible()`, `def file_source_images()`, `def file_patch_reference()`, `def write_character_index(...)` — that writes into the human-only canon tree `APPROVED_ROOT = REPO_ROOT / "03_APPROVED_CANON" / "approved_characters"` and runs unconditionally via `if __name__ == "__main__": main()`. It also reaches outside the repo: `WORKSPACE_ROOT = REPO_ROOT.parent` / `CHARACTER_BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"`, i.e. `I:/MonkeyZoo Comic Strip/Fusion Squad/character-bibles` — a directory that exists on this machine but `git check-ignore` reports as "outside repository", so it is untracked and absent on any fresh clone or in CI. `git log -1` dates the file to 2026-07-12, the initial workflow-engine commit.

**Rationale**

Largest fully-unreferenced module in the repo and the strongest single removal candidate, but it writes into `03_APPROVED_CANON/` — which CLAUDE.md declares HUMAN-ONLY — and it embeds a hardcoded 10+ character roster (MZ-CHAR-001 Moodz through Clever) plus season-bible filing rules that may be the provenance record for how approved canon was originally laid down. Its dependence on an out-of-repo `../character-bibles` means it cannot run correctly on a fresh clone, so it is already effectively broken as well as unreachable. Escalate to the owner rather than deleting an artifact touching locked canon.

**Risk if this disposition is acted on and the analysis is wrong**

If this is the documented (but undocumented) bootstrap for `03_APPROVED_CANON/approved_characters/CHARACTER_IMAGE_INDEX.md`, removing it destroys the only reproducible path to regenerate the canon index, and canon regeneration is human-gated so nobody would notice until a rebuild was needed.

**Skeptic's verdict**

UPHELD on the core claim, with severity corrected and one evidence error noted.

CONFIRMED INDEPENDENTLY:
- 403 lines exactly (wc -l). Single commit bbac506 dated 2026-07-12, never modified since.
- Zero references, any casing, across the entire tracked tree: `git grep -i -n -I -e "file_story" -e "story_bible_and" -e "bible_and_refs" -- .` returns exit 1 with no output. Absent from all 4 tracked SKILL.md files, README.md, docs/OPERATOR_RUNBOOK.md, docs/PACKAGE_EXPORTS.md, 00_SYSTEM/automation_rules.md, and .github/workflows/validate.yml. No importlib/getattr/runpy/__import__/pkgutil dispatch anywhere; no subprocess runner names it (scripts/package_issue.py invokes only assemble_pages and build_release). No conftest sys.path injection. Only CI contact is the blanket `ruff check .`.
- I reproduced their per-basename sweep: it is genuinely the ONLY module in 00_SYSTEM/scripts/ scoring 0; next-lowest (genesis_crop_audit, genesis_editorial, genesis_specs, batch_matte, edge_unify, smoke_render) all score >=1.
- Code quotes verified verbatim: line 13 `APPROVED_ROOT = REPO_ROOT / "03_APPROVED_CANON" / "approved_characters"`; line 12 `WORKSPACE_ROOT = REPO_ROOT.parent`; line 15 `CHARACTER_BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"`; lines 402-403 `if __name__ == "__main__": main()`. No test file exists for it.

THEIR EVIDENCE ERROR (does not overturn the claim): they assert character-bibles "is untracked and absent on any fresh clone or in CI." False at the repo level — `git ls-files character-bibles` returns 253 tracked files, including the exact artifacts this script writes (character-bibles/MZ-CHAR-PATCH/references/primary/primary-reference.png and .../references/source-map.json), and CI runs `python character-bibles/_schema/validate-character-bibles.py --root character-bibles`. The accurate narrower fact is that the script's CONSTANT resolves to the out-of-repo sibling copy, so it would write to the wrong tree. This strengthens the "stale" conclusion rather than refuting it.

CONTEXT THEY MISSED (reinforces Investigate Further over Remove): the script is the provable generator of six tracked files. story-bibles/seasons/2026-emo-monkeys-the-signal-between-us/season-metadata.yaml matches its hardcoded `metadata` dict byte-for-byte, and root MonkeyZoo_Emo_Monkeys_Season_Bible.md matches its pointer text exactly. Two outputs are live-referenced: 00_SYSTEM/automation_rules.md:61 names 03_APPROVED_CANON/approved_characters/CHARACTER_IMAGE_INDEX.md as "The current character/image routing page", and SEASON-BIBLE.md appears 9x in 00_SYSTEM/project_direction.json and is glob-loaded by the Studio app at character-bibles/_review_app/story_workspace.py:187. So it is the provenance record for live canon artifacts, not pure waste.

CONCRETE HAZARD: file_season_bible() rewrites the season README unconditionally. The tracked README has diverged — it now carries three curated lines the script does not emit (location-and-prop-tracker.md, "Location canon: 03_APPROVED_CANON/approved_locations/", "Prop canon: 03_APPROVED_CANON/approved_props/"). Running main() would silently revert them and overwrite CHARACTER_IMAGE_INDEX.md plus character-image-manifest.json inside the HUMAN-ONLY canon tree.

SEVERITY CORRECTED High -> Medium: with zero invocation paths the hazard is latent, not active (it requires deliberate invocation of a script nothing points to); the file is lint-clean under CI, imposes no ongoing breakage, and carries offsetting provenance value. Disposition Investigate Further is correct and must not be downgraded to Remove — deletion would destroy the only record of how the season bible and approved-canon character index were laid down.

---

### U04 — Style-lock (Rule 3) phrase has two constructions; the Studio's scrape leaks markdown blockquote gutters into every promoted panel prompt

- **Location:** `character-bibles/_review_app/art_prompt_workspace.py:157`
- **Lens:** dup-logic  |  **Category:** duplication
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

Studio builds the lock by scraping visual_style_bible.md:
`match = re.search(r">\s*\*\*\"([^\"]+)\"\*\*", text)` (art_prompt_workspace.py:157), guarded only by `if len(phrase) >= 20 and phrase.startswith(STYLE_LOCK_PREFIX):`.
The bible stores the phrase as a 5-line markdown blockquote (00_SYSTEM/visual_style_bible.md:14-18, each continuation line beginning `> `). I executed `art_prompt_workspace._style_lock(ROOT)`; it returns:
`'MonkeyZoo house style: chibi cartoon monkey with oversized round head,\n> huge white oval eyes with tiny black dot pupils, two small dot nostrils,\n> thick uniform black outlines, ...'` — 4 embedded `\n> ` sequences.
I then counted `\n> ` in every tracked art_prompt_pack.json:
  2026-08_Issue_01: lock=4, panel[0].prompt=4
  2026-09_Issue_02: lock=4, panel[0].prompt=4
  2026-10_Issue_01: lock=4, panel[0].prompt=4
  2026-07_Issue_05: 0    2026-08_Issue_06: 0    2026-09_Issue_01: 0
The clean CLI/authoring form is what the same module hardcodes as its own fallback (`DEFAULT_STYLE_LOCK`, art_prompt_workspace.py:26-32) and what validate_issue.py's Rule 3 check (`validate_issue.py:130`) was written against. `_style_lock(ROOT) == apw.DEFAULT_STYLE_LOCK` -> False.
Both validators pass the polluted phrase (`startswith("MonkeyZoo house style")` is true), so nothing catches it. 00_SYSTEM/visual_style_bible.md:12 says "Use verbatim, at the start of every art prompt".

**Rationale**

Two implementations of "read the Rule 3 locked style phrase": the CLI/authoring convention writes the flattened verbatim sentence; the Studio scrapes the markdown and keeps the blockquote gutter. Three of seven production packs ship literal `> ` tokens straight to the ComfyUI text encoder. run_art_batch.py:44-48 then does clause surgery (`prompt_text.split(", ")`, `prompt_text.replace("MonkeyZoo house style: ", "")`) that assumes the clean form. Fix is a single flattening step in `_style_lock` (collapse `\n>\s*` to a space), not a second validator.

**Risk if this disposition is acted on and the analysis is wrong**

If the blockquote form were somehow intentional, flattening changes the style_lock_phrase bytes, which changes every panel prompt, which invalidates plan_hash/pack_hash and the art already generated under the old prompts. Any repair must be treated as a pack revision, not a silent normalization.

**Skeptic's verdict**

Independently confirmed at every step. art_prompt_workspace.py:157 is verbatim `match = re.search(r">\s*\*\*\"([^\"]+)\"\*\*", text)`; `[^\"]+` spans newlines, and 00_SYSTEM/visual_style_bible.md:14-18 stores the Rule 3 phrase as a 5-line blockquote (cat -A confirms each continuation line begins `> `). Executing the regex against the real bible returns the phrase with exactly 4 embedded `\n> ` sequences; the only guard (:163 `if len(phrase) >= 20 and phrase.startswith(STYLE_LOCK_PREFIX)`) is prefix-only and passes it. build_pack (:186, :243) writes that string to `style_lock_phrase` and to every panel prompt. Claim is UNDERSTATED: I scanned all 7 tracked packs -- 2026-08_Issue_01 (24/24), 2026-09_Issue_02 (96/96) and 2026-10_Issue_01 (2/2) have ALL panels polluted, not just panel[0]; the other four are clean. All 7 page_panel_plan.json files contain 0 gutters, proving _style_lock is the sole injection point. Reaches the encoder for real, not inferred: I called run_art_batch.build_workflow() on the actual polluted panel with --engine zimage and wf["4"]["inputs"]["text"] (CLIPTextEncode) contains 4 literal `\n> ` sequences; load_pack does no whitespace normalization and .claude/skills/mz-art-run/SKILL.md:30 is the invoker. validate_issue.py:130 is verbatim as cited (prefix-only), and validate_pack (art_prompt_workspace.py:279-283) is likewise prefix-only, so both validators pass it. Flattening `\s*\n>\s*` to a space yields a string byte-identical to DEFAULT_STYLE_LOCK (verified True), so the proposed one-line repair is provably correct and both existing _style_lock tests (test_art_prompt_workspace.py:150-166) use single-line synthetic bibles, so flattening is a no-op for them -- nothing breaks. No reference was missed: CI (.github/workflows/validate.yml) never runs validate_issue.py on packs, and no runbook, .ps1 or dynamic path relies on the multi-line form. TWO CORRECTIONS to their impact story: (1) the plate-lock leak is NOT caused by the gutters -- after flattening, run_art_batch.py:53 `prompt_text.split("dark cartoon sci-fi cyberpunk backdrop, ", 1)` still fails because Studio-built prompts lack the ", " separator hand-authored packs have; that is a separate defect. (2) The Studio's own art path does not consume pack prompts (2026-10_Issue_01/.art-workspace/prompts/*.json carries "prompt": "Moodz powers on the quiet desk monitors." from the plan), so only the run_art_batch.py CLI path is affected. Severity lowered High -> Medium: the data path is proven and both validators are blind, but there is no crash, no data loss and no demonstrated visual degradation -- the payload is a few low-weight noise tokens inside a prompt the runner already mangles heuristically, and one of the three affected packs is a 2-panel RC artifact. Repair is the right disposition, with the caveat that it fixes only future builds; the three already-promoted packs on disk need a separate rebuild/re-promote.

---

### U05 — Release gate and CLI packager disagree on where the final cover lives; 3 of 7 real issues have a cover the Studio cannot see

- **Location:** `character-bibles/_review_app/release_workspace.py:90`
- **Lens:** dup-logic  |  **Category:** duplication
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

Studio release evidence looks in exactly one place:
`covers=sorted((folder/"generated_art").rglob("*cover*.png")) if (folder/"generated_art").exists() else []` (release_workspace.py:90)
`if not covers:blockers.append("No final cover image found")` (release_workspace.py:103)
CLI packager looks in exports first:
```
candidates = [
    issue_dir / "exports" / "cover.png",
    issue_dir / "generated_art" / "covers" / "main_cover.png",
]
```
(build_release.py:26-29), and `check_exports` (build_release.py:60-65) lists `"cover.png"` under exports/ as a required export.
Both conventions are documented, in the same runbook: docs/OPERATOR_RUNBOOK.md:195 `- Cover: \`generated_art/covers/main_cover.png\` (name must contain \`cover\`)` vs docs/OPERATOR_RUNBOOK.md:209 `- Cover discovery order: \`exports/cover.png\`, then \`generated_art/covers/main_cover.png\`...`; docs/PACKAGE_EXPORTS.md:40 lists `1. \`exports/cover.png\`` first.
I enumerated every issue folder on disk:
  2026-07_Issue_05   exports/cover.png=1  generated_art covers=0
  2026-07_Mango_Pier exports/cover.png=1  generated_art covers=0
  2026-08_Issue_06   exports/cover.png=1  generated_art covers=0
  2026-08_Issue_01 / 2026-09_* / 2026-10_01: exports=0, generated_art>=1
`02_MONTHLY_ISSUES/2026-07_Mango_Pier/exports/cover.png` is git-tracked.

**Rationale**

One concept ("the final cover deliverable"), two independently-written resolvers, and production data is genuinely split across both conventions. An operator who follows build_release.py/PACKAGE_EXPORTS.md and puts the cover at exports/cover.png is blocked at Studio Release with "No final cover image found" and no hint that the file location is the problem. Extract build_release._find_cover's ordered search into one shared resolver used by release_workspace.evidence and visual_qa_workspace.evidence.

**Risk if this disposition is acted on and the analysis is wrong**

release_workspace.evidence's cover list feeds the release evidence_hash (release_workspace.py:97,114-116). Widening cover discovery changes that hash, invalidating existing release approvals and promoted release_hash_manifest.json for already-approved issues. Must be sequenced as a deliberate re-approval, not a hotfix.

**Skeptic's verdict**

Core defect CONFIRMED by reading the real code; supporting claims partially refuted; proposed fix would regress.

VERIFIED VERBATIM: release_workspace.py:90 `covers=sorted((folder/"generated_art").rglob("*cover*.png")) if (folder/"generated_art").exists() else []` and :103 `if not covers:blockers.append("No final cover image found")`. build_release.py:26-29 candidate list and check_exports (:60-65) listing `"cover.png"` under exports/. Docs quotes at OPERATOR_RUNBOOK.md:195/:209 and PACKAGE_EXPORTS.md are accurate. Disk enumeration reproduced exactly: 2026-07_Issue_05, 2026-07_Mango_Pier, 2026-08_Issue_06 have exports/cover.png and zero generated_art covers; 2026-07_Mango_Pier/exports/cover.png is git-tracked.

THE CLAIM UNDERSTATED THE DOC CONFLICT (strengthens it): the trap is reachable from the designated source of truth. `.claude/skills/mz-package/SKILL.md:16-18` — the skill CLAUDE.md assigns to Stages 8-10 — instructs "save `exports/cover.png` + `promo_images/variant_cover.png`", and 00_SYSTEM (which CLAUDE.md calls "the source of truth") repeats it in automation_rules.md:50, qa_checklist.md:82, monthly_issue_template.md:22. Only docs/OPERATOR_RUNBOOK.md:195 says generated_art/covers/main_cover.png. So an agent following the canonical instructions produces a cover the Release gate cannot see, and gets a message ("No final cover image found") that names no searched path.

REFUTED #1 — "3 of 7 real issues" is 2. 2026-07_Mango_Pier is not gateable by the Studio at all: issue_workflow.workflow_status raises IssueWorkflowError('Issue ID must match MZ-YYYY-MM-NN'), so readiness() throws before any cover check. It also lacks cover_prompt.md, final_export_checklist.md, and CHIP-0015 metadata (7 blockers total).

REFUTED #2 — impact is prospective, not live. I ran release_workspace.evidence() against every issue: all three cited folders are at active_stage=intake with independent blockers (QA verdict pending/failed, unresolved TODO metadata). None is blocked solely by cover location. All four issues that actually reached release/published (2026-08_Issue_01, 2026-09_Issue_01, 2026-09_Issue_02, 2026-10_Issue_01) used generated_art/covers/main_cover.png, written by rc_real_issue_run.py:345-349, live_app_test_issue.py:285-287, prepare_issue01_release_assets.py:58-84. The exports/cover.png files are legacy, added in bulk historical commits (202c1fd, b935116), not produced by the current pipeline.

REFUTED #3 — "two independently-written resolvers" is wrong. release_workspace.py:90 and visual_qa_workspace.py:71 are a deliberately synchronized pair: line 71 carries the comment "# sorted: evidence hash must be order-stable across platforms/restores (matches release_workspace)", and visual_qa_workspace.py:85 reads "cover image is absent; Release owns the blocking cover-deliverable requirement". Stage ownership of the cover blocker was explicitly reasoned about. Only build_release.py:_find_cover is genuinely independent — and it is a strict superset (it falls back to generated_art rglob at :33-37), so the disagreement is one-directional.

REFUTED #4 — the proposed disposition would cause a regression. "Extract build_release._find_cover's ordered search into one shared resolver used by release_workspace.evidence and visual_qa_workspace.evidence" mixes incompatible cardinalities: _find_cover returns a single `Path | None`, while the workspaces use `covers` as a LIST folded into a SHA256 evidence hash (release_workspace.py:97 and :115; visual_qa_workspace.py:72) and copied wholesale into the publication archive (release_workspace.py:195-196). Measured read-only on 2026-09_Issue_02, which has 4 matching covers (covers/main_cover.png, integration_preview/COVER_BACK.png, COVER_FRONT.png, pages_preview/covers_preview.png): current evidence hash 5aa0f00cc510c2b32ebd03152d3deaf581eb02305c78c60cfc37bdf0993a8f2f vs first-match-only 096118e4510b93805e21cf5451683f9fc564809115693514eb5a45e2cdb3e3ec. Adopting first-match semantics would also silently drop COVER_FRONT.png/COVER_BACK.png from the published archive.

SEVERITY corrected High -> Medium: nothing is broken today, no in-flight issue is blocked solely by this, and 4/4 released issues used the working convention. But the trap is genuinely reachable from the designated skill + 00_SYSTEM canon, and the blocker message is actively misleading, so it is above Low.

DISPOSITION corrected Consolidate -> Repair: the two workspace resolvers are already intentionally consolidated with each other; consolidating them onto build_release._find_cover is the specific action shown above to regress hashing and archiving. The correct repair is to widen release_workspace.evidence's cover discovery to also include exports/cover.png while KEEPING list semantics, make the blocker message name the locations searched, and reconcile mz-package/SKILL.md:18 + 00_SYSTEM docs with docs/OPERATOR_RUNBOOK.md:195 so one location is canonical.

ADJACENT (not part of this claim, flagged for the sweep): rglob("*cover*.png") is case-insensitive on Windows but case-sensitive on POSIX, so COVER_BACK.png/COVER_FRONT.png enter the evidence set only on Windows — which contradicts the "order-stable across platforms" intent stated in visual_qa_workspace.py:71. Also, all four published issues currently report qa_hash_current=False.

---

### U06 — Studio promotes page plans that validate_issue.py (the Stage 4/5/9 gate) rejects: emotion and camera_angle are required by one implementation and not the other

- **Location:** `character-bibles/_review_app/page_panel_workspace.py:177`
- **Lens:** dup-logic  |  **Category:** duplication
- **Severity:** Medium  |  **Disposition:** Consolidate

**Evidence**

CLI gate (validate_issue.py:122-124):
```
for field in ("action", "emotion", "location", "camera_angle"):
    if not str(panel.get(field, "")).strip():
        err(f"plan {pid}: empty field {field!r}")
```
Studio, both validators (page_panel_workspace.py:177-178 and :202-203):
`for field in ("location","action"):` / `for field in ("location", "action"):`
The schema does not close the gap — page_panel_plan_schema.json declares emotion/camera_angle as `{ "type": "string" }` with no minLength, so `""` is schema-valid.
I ran a plan with `"camera_angle": "", "emotion": ""` through all three:
  STUDIO validate_canonical_payload: passed
  STUDIO validate_plan            : passed
  CLI validate_issue fields check  : ["plan MZ-2026-05-01_P01_PANEL01: empty field 'emotion'", "plan MZ-2026-05-01_P01_PANEL01: empty field 'camera_angle'"]
Both CLI call sites are live: .claude/skills/mz-new-issue/SKILL.md:42 `7. **Validate:** \`python 00_SYSTEM/scripts/validate_issue.py <folder>\` must` and 00_SYSTEM/agents/stage_09_final_qa.md:12 `\`scripts/validate_issue.py\` — it cross-checks plan JSON vs files on disk);`.

**Rationale**

Same artifact, same question ("is this page plan complete?"), two field lists. The Studio's promotion gate (page_panel_workspace.promote, which runs validate_plan AND validate_canonical_payload AND post-write re-validation) can green-light a plan that then hard-fails the Stage 9 release gate — after art has been generated from it. The field list belongs in one place; camera_angle in particular is consumed downstream (validate_issue.py:199 `is_close = cameras.get(pid, "").lower().startswith("close")` drives the --integration flat-region skip).

**Risk if this disposition is acted on and the analysis is wrong**

Tightening the Studio to match would newly block promotion for in-flight plans that currently pass. Loosening the CLI instead would silently drop the camera_angle signal the --integration gate depends on. Pick tightening, and check the 7 existing plans first.

**Skeptic's verdict**

UPHELD on the facts, severity corrected High -> Medium. Every citation is verbatim-accurate: validate_issue.py:122-124 checks ("action","emotion","location","camera_angle") with str(...).strip(); page_panel_workspace.py:177 and :202 both check only ("location","action"); page_panel_plan_schema.json:47-49 declares emotion/camera_angle as bare {"type":"string"} with no minLength, so "" is schema-valid. I reproduced the divergence myself: STUDIO validate_plan passed, STUDIO validate_canonical_payload passed, CLI produced ["plan MZ-2026-05-01_P01_PANEL01: empty field 'emotion'", "... 'camera_angle'"]. Both CLI call sites are live (.claude/skills/mz-new-issue/SKILL.md:42, 00_SYSTEM/agents/stage_09_final_qa.md:12) and the Studio promote route is live (app.py:365-368). Three refutation attempts all failed and instead strengthened the finding: (1) a THIRD Studio gate on the same artifact is equally blind - issue_workflow.py:140-141 `elif stage_id == "page_plan" and not missing: messages += _schema_errors(folder / "page_panel_plan.json", ...)` is schema-only; (2) the Studio never invokes the CLI - app.py:299-302 `/api/issues/<issue_id>/validate` merely returns workflow_status, and there is no subprocess call anywhere in _review_app/*.py, nor any validate_issue step in .github/workflows/validate.yml or the tracked *.ps1 wrappers, so the earliest CLI catch on a Studio-authored plan is mz-art-run SKILL.md:56 (--art) or Stage 9, both after art generation; (3) the CLI list is the documented contract, not an arbitrary second opinion - 00_SYSTEM/agents/stage_04_script.md:13 "## Every panel must include (no field left blank -- use "--" deliberately)" enumerates camera angle and emotion, so the Studio list is the deficient one. Two additional gaps they missed: the Studio uses falsy `if not panel.get(field)` while the CLI uses `.strip()`, so whitespace-only location/action passes Studio and fails the CLI (reproduced); and reachability is trivial because _field_block keys on exact lowercase labels with FIELDS containing only "camera" -- a panel written "- Camera angle: Wide" (the exact label the Studio's own generator emits at story_context.py:629) silently parses to camera_angle:"" (reproduced), while story_workspace.py:19 SCRIPT_FIELDS = ["- Location:", "- Characters:", "- Action:", "- Dialogue:", "- Continuity notes:"] never requires Emotion or Camera and checks whole-document substrings (:205), not per-panel. Severity lowered to Medium because the outcome is loud rework, not corruption: all 7 tracked page_panel_plan.json files have zero empties in these four fields (no historical incidence), the CLI names the exact failing field, and nothing bad reaches canon or release -- the cost is wasted art generated against fabricated defaults (art_prompt_workspace.py:196-197 substitutes "medium shot"/"neutral"), which is expensive but bounded and self-announcing. Consolidate retained and verified safe: the single point both the CLI and all three Studio validators already read is the schema, so "minLength": 1 on exactly location/camera_angle/action/emotion fixes all four at once and breaks no tracked plan. It must be scoped to those four -- art_prompt/negative_prompt/controlnet_required are legitimately "" per stage_04_script.md rule 8 ("Leave `art_prompt`/`negative_prompt` fields as "" -- Stage 5 fills them"), confirmed present as "" in the promoted 2026-09_Issue_02 plan, so a blanket minLength would break production.

---

### U07 — `selenium` is imported but declared nowhere; on a clean install the documented verification script reports a UI regression instead of a missing dependency

- **Location:** `scripts/live_app_test_issue.py:345`
- **Lens:** deps  |  **Category:** dependency
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

`scripts/live_app_test_issue.py:345-348` imports selenium inside `main()`:

```python
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
```

`selenium` appears nowhere in `requirements-dev.txt` (full file read; the declared set is flask, Pillow, pyyaml, jsonschema, numpy, scipy, pytest, pytest-asyncio, anyio, ruff) and nowhere in `Start-BananaLab.ps1`, `start-banana-lab.sh`, or `docs/OPERATOR_RUNBOOK.md`. I grepped every non-backup tracked file for "selenium": the only hits are these four import lines.

The failure mode is the problem. `scripts/live_app_test_issue.py:387-392`:

```python
    except Exception as exc:  # noqa: BLE001
        log("ui_selenium", False, f"{type(exc).__name__}: {exc}")

    write_report()
    fails = sum(1 for r in REPORT if r["status"] == "FAIL")
    return 1 if fails else 0
```

`except Exception` catches `ModuleNotFoundError`, logs a **FAIL** row, and the process exits **1**.

The script is a documented verification command — `docs/SHIP_READINESS_ASSESSMENT.md:93`: "- `python scripts/live_app_test_issue.py` (app running) — see LIVE_APP_TEST_REPORT.md".

**Rationale**

This is the dangerous direction the audit was asked to find: works on the dev rig, fails on a clean install. Worse than a plain crash, the guard launders the missing dependency into a red test result. A fresh contributor who follows `CONTRIBUTING.md` (`pip install -r requirements-dev.txt`) and then runs the documented command gets `**FAIL** ui_selenium` written into `docs/LIVE_APP_TEST_REPORT.md` plus exit 1 — indistinguishable in the report from a genuine Studio UI regression, and it will be read as one. Repair has two halves: declare selenium (a `requirements-test.txt` extra or a commented optional block is fine — it also needs a real Chrome/chromedriver, so it is legitimately not a hard dep), and narrow the handler so `ModuleNotFoundError` logs a distinct SKIP status that does not contribute to `fails`, leaving `except Exception` for actual WebDriver failures.

**Risk if this disposition is acted on and the analysis is wrong**

If selenium is deliberately optional and every operator who runs this script is expected to have it, declaring it unconditionally in `requirements-dev.txt` would add a heavyweight package (and an implicit chromedriver expectation) to every CI run and every contributor's first install for zero CI benefit — CI never invokes this script. That is why the recommendation is an optional/extras declaration plus a SKIP status, not a bare append to the main file. Narrowing the except is near-zero-risk: a genuine WebDriver failure still raises a non-ImportError exception and still logs FAIL.

**Skeptic's verdict**

UPHELD IN SUBSTANCE, with two of their evidence claims refuted and severity corrected down.

CONFIRMED BY READING THE CODE:
1. `scripts/live_app_test_issue.py:344-348` is verbatim as quoted — `try:` then `from selenium import webdriver` / `from selenium.webdriver.chrome.options import Options` / `from selenium.webdriver.common.by import By` / `from selenium.webdriver.support.ui import WebDriverWait`.
2. `scripts/live_app_test_issue.py:387-392` is verbatim as quoted: `except Exception as exc:  # noqa: BLE001` → `log("ui_selenium", False, ...)` → `write_report()` → `fails = sum(1 for r in REPORT if r["status"] == "FAIL")` → `return 1 if fails else 0`. `log()` at line 29-33 sets `status = "PASS" if ok else "FAIL"`, so `ok=False` does count into `fails`. `ModuleNotFoundError` ⊂ `ImportError` ⊂ `Exception`, so it is caught.
3. `selenium` is in no dependency manifest. `git ls-files | grep -iE "requirement|pyproject|setup.py|setup.cfg|Pipfile|poetry"` returns exactly one file: `requirements-dev.txt`, whose full contents are flask, Pillow, pyyaml, jsonschema, numpy, scipy, pytest, pytest-asyncio, anyio, ruff. `CONTRIBUTING.md:17`: "`requirements-dev.txt` is the single source of truth for dependencies, shared by CI and this guide."
4. It is a documented run command — `docs/SHIP_READINESS_ASSESSMENT.md:93`: "- `python scripts/live_app_test_issue.py` (app running) — see LIVE_APP_TEST_REPORT.md".
5. No missed reference rescues it: `.github/workflows/validate.yml` runs only `ruff check .`, `pytest`, and the three validator scripts — it never invokes this script, so CI is unaffected. `git grep -n "live_app_test"` over tracked files returns only the two SHIP_READINESS lines, two docs/audit rows, a comment in `scripts/silent_failure_audit.py:88`, and `scripts/tests/test_pytest_collection_integrity.py:64`, which explicitly names it "a driver script, not a test module". No .ps1 wrapper, skill, or runbook runs it.

REFUTED — EVIDENCE ERROR #1: "I grepped every non-backup tracked file for 'selenium': the only hits are these four import lines." False. `git grep -i selenium` over all tracked files returns 8 hits in 2 files. They missed `docs/SHIP_READINESS_ASSESSMENT.md:15` — "| Test tools | urllib HTTP client + Selenium headless Chrome + pytest |" — and `:23` — "| UI navigation / controls | Selenium smoke under writable capability |". Those are in the very document they cite at line 93 for the run command, i.e. the operator reading the command is told in the same file's Environment table that Selenium headless Chrome is a test tool. Selenium is documented in prose; it is undeclared in the manifest. Only the narrower statement survives.

REFUTED — EVIDENCE ERROR #2: "indistinguishable in the report from a genuine Studio UI regression." False. `write_report()` at line 411 emits `f"- **{r['status']}** \`{r['step']}\` — {r['detail']}"`, and the detail passed at line 388 is `f"{type(exc).__name__}: {exc}"`. The clean-install row therefore reads literally: "- **FAIL** `ui_selenium` — ModuleNotFoundError: No module named 'selenium'". The step name `ui_selenium` never appears in a healthy run; `docs/LIVE_APP_TEST_REPORT.md:64-74` shows the healthy rows are `ui_create_issue_enabled`, `ui_nav:dashboard`…`ui_nav:release`, `ui_art_prompt_pack_control`, `ui_release_publish_control`, `ui_console_severe`. The exception type is named in the artifact, so any reader can distinguish it. The real (smaller) defect is at the aggregate level: the summary line "- Results: **N passed**, **1 failed**" and the exit code 1 conflate a missing optional tool with a product failure.

SEVERITY CORRECTED High → Medium: (a) not in CI and not in any enforced gate — `CONTRIBUTING.md:22` says "CI (`.github/workflows/validate.yml`) runs exactly these" and lists only `ruff check .` and `pytest`; (b) the failure is loud and self-describing (exit 1 plus the exception name written into the report), not silent; (c) `main()` requires the Flask app already reachable and writable at 127.0.0.1:8765 (`wait_ready()` at line 73-80, guard at 132-136) plus `webdriver.Chrome()` at line 355 requires a real Chrome/chromedriver — a machine with selenium declared but no browser produces the identical FAIL row, so declaring the dependency alone does not make the clean-install path green; (d) no production, canon, or release path is touched.

DISPOSITION Repair holds, but the load-bearing half is the second one they proposed: narrow the handler so `ModuleNotFoundError` (and arguably `WebDriverException`) logs a distinct SKIP status excluded from `fails`, leaving `except Exception` for real WebDriver failures. Declaring selenium as an optional extra is correct hygiene but insufficient on its own for the reason in (c).

---

### U08 — pytest.ini `norecursedirs` REPLACES pytest's built-in defaults, silently dropping `.*`, `venv`, `build`, `dist`, `*.egg` — so `pytest .` now recurses into the `.venv/` both launchers create at the repo root

- **Location:** `pytest.ini:40-52`
- **Lens:** config-drift  |  **Category:** config
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

pytest.ini:40 declares its own list:
```
norecursedirs =
    artifacts
    06_BACKUPS
    05_RELEASE_ARCHIVE
    04_REJECTED_OUTPUTS
    04_APPROVED_FOR_PUSH
    02_ANTIGRAVITY_WORK
    01_CHATGPT_TO_ANTIGRAVITY
    01_IDEAS_INBOX
    .git
    node_modules
    __pycache__
    .pytest_cache
    *.egg-info
```
pytest's installed default (read from `_pytest/main.py` via `parser.addini("norecursedirs", ..., type="args", default=[...])`) is:
`["*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"]`.
An ini value for this key replaces the default, it does not extend it. Set-diff of default minus the configured list: `['*.egg', '.*', 'CVS', '_darcs', 'build', 'dist', 'venv', '{arch}']` — all lost.

The lost `.*` and `venv` matter here specifically because both launchers create a virtualenv at the repo root:
- Start-BananaLab.ps1:68-70 — `Write-Step "Creating virtualenv at .venv"` / `& py -3 -m venv (Join-Path $Root ".venv")`
- start-banana-lab.sh:20 — `"$PYTHON" -m venv "$ROOT/.venv"`

pytest.ini:21-23 states the intended role of the list: "`norecursedirs` is kept as defense-in-depth for explicitly-targeted runs (`pytest .`)" — that is exactly the invocation this regression breaks. `testpaths` (pytest.ini:30) protects only the bare no-argument invocation.
Verified `.venv` is absent from the working tree right now (`ls -d .venv` → no such dir), so the break is latent, not currently firing.

**Rationale**

The file's own comment assigns `norecursedirs` the job of protecting `pytest .`; overriding the ini key without re-listing pytest's defaults removed `.venv`, `venv`, `build`, and `dist` from that protection. The moment an operator follows the documented setup path (Start-BananaLab.ps1 / start-banana-lab.sh) and then runs `pytest .`, collection walks site-packages test suites — the identical duplicate-basename collection death that pytest.ini and scripts/tests/test_pytest_collection_integrity.py exist to prevent. `test_bare_collection_from_repo_root_is_clean` runs bare `pytest`, which `testpaths` shields, so the guard suite cannot catch this.

**Risk if this disposition is acted on and the analysis is wrong**

If the defaults were actually additive (they are not), re-adding `.*`/`venv`/`build`/`dist` is still harmless — it re-states behaviour pytest already has. The only real risk of acting is if a tracked test directory begins with a dot or is literally named `build`/`dist`/`venv`; none exists today (checked all 8 entries of `testpaths` and every tracked `test_*.py` directory).

**Skeptic's verdict**

Mechanism independently confirmed and empirically reproduced. (1) pytest.ini:40-53 declares its own norecursedirs (claim cites 40-52; `*.egg-info` is line 53 — non-material). (2) The installed pytest 8.4.2 default, read from `_pytest/main.py`'s `parser.addini("norecursedirs", ..., default=[...])`, is verbatim `["*.egg", ".*", "_darcs", "build", "CVS", "dist", "node_modules", "venv", "{arch}"]`; only `node_modules` survives in the repo list. (3) Replacement-not-extension PROVEN, not assumed: built a scratch tree containing `.venv/Lib/site-packages/somepkg/tests/test_dup.py`, `build/lib/pkg/test_dup.py`, and `realtests/test_dup.py`. With the repo's norecursedirs, `pytest --collect-only -q .` produced `import file mismatch` / `ERROR build/lib/pkg/test_dup.py` / `ERROR realtests/test_dup.py` / `Interrupted: 2 errors during collection`. Control run on the identical tree with an empty `[pytest]` (pytest defaults active) collected cleanly: `1 test collected`. Exactly the collection death the guard exists to prevent. (4) Launchers confirmed verbatim: Start-BananaLab.ps1:68 `Write-Step "Creating virtualenv at .venv"`, :70 `& py -3 -m venv (Join-Path $Root ".venv")`; start-banana-lab.sh:20 `"$PYTHON" -m venv "$ROOT/.venv"`. (5) pytest.ini:21-22 verbatim assigns norecursedirs the `pytest .` job. (6) The guard suite genuinely cannot catch it: test_pytest_collection_integrity.py:170 invokes `pytest --collect-only -q` with NO path argument, so `testpaths` shields it. No root conftest.py, no `addopts`, no `importmode` setting that could compensate.

SEVERITY CORRECTED High -> Medium. I grepped every tracked .md/.ps1/.sh/.yml: `pytest .` appears nowhere in the repo except inside pytest.ini's own comment. Every documented invocation is either bare (.github/workflows/validate.yml:40 `pytest`; README.md:75; CONTRIBUTING.md:26; docs/audit/AUDIT_PROGRESS.md:31 `python -m pytest -q --ignore=artifacts` — `--ignore` is not a path argument, so testpaths still applies) or an explicit deep test path. The primary guard (testpaths) is fully intact, CI is unaffected, and the trigger requires two conditions that do not hold today. Verified latent: `.venv` is absent, `find` for `test_*.py` under any dot-dir/build/dist returns nothing, and `pytest .` currently collects 786 tests with zero errors from exactly the 8 testpaths directories. A degraded defense-in-depth layer with a conditional, non-firing trigger is Medium; High would imply active or imminent breakage on a documented path.

DISPOSITION Repair upheld and verified safe: re-adding pytest's defaults (`.*`, `venv`, `build`, `dist`, `*.egg`, `_darcs`, `CVS`, `{arch}`) cannot drop any real test, because no tracked test directory lives under a dot-dir, `build`, or `dist` — test_testpaths_cover_every_tracked_test_directory would already be failing if one did.

Incidental (separate finding, not this claim): `.gitignore` contains no `venv`/`.venv` entry, so a launcher-created `.venv` is untracked AND unignored — the same `git add -A` hazard its own comment block documents for `artifacts/`.

---

### U09 — `.venv/` is absent from .gitignore although both documented launchers create it at the repo root — `git add -A` would commit the entire virtualenv

- **Location:** `.gitignore`
- **Lens:** config-drift  |  **Category:** config
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

`git check-ignore -v .venv/x` → `NOT IGNORED`. The full .gitignore contains no `venv`, `.venv`, `env/`, `build/`, or `dist/` entry (only `__pycache__/`, `*.pyc`, `.coverage`, `.coverage.*`, `htmlcov/`, plus the artifact trees).

Meanwhile every other gate knows about it:
- scripts/silent_failure_audit.py:48-51 lists `".venv"`, `"venv"`, `".env"`, `"env"`, `"build"`, `"dist"`, `"site-packages"` in `EXCLUDE_DIRS`.
- ruff.toml is safe by accident: `extend-exclude` *extends* ruff's built-in default exclude, which already contains `.venv`/`venv`/`build`/`dist`.

Creators of the directory:
- Start-BananaLab.ps1:70 `& py -3 -m venv (Join-Path $Root ".venv")`
- start-banana-lab.sh:20 `"$PYTHON" -m venv "$ROOT/.venv"`
- Backup-BananaLab.ps1:22 `$venv = Join-Path $Root ".venv\Scripts\python.exe"`
- README/Start-BananaLab.ps1:160 instructs `python -m venv .venv`

This is the same defect class the repo already fixed once: docs/audit/AUDIT_PROGRESS.md:89 — "F-005 | Medium | `artifacts/` untracked and un-ignored — `git add -A` would commit a second full copy of the repo | **FIXED**".

**Rationale**

The repo's own audit log records fixing exactly this hazard for `artifacts/`, and .gitignore:23-28 carries a long comment about why an untracked-but-unignored full tree is dangerous. `.venv/` is the remaining instance and is created by the first command a new operator is told to run. `.pytest_cache/` and `.ruff_cache/` are NOT a problem here — both tools drop a self-ignoring `.gitignore` inside them (verified via `git check-ignore -v`), so `.venv` is the genuine gap.

**Risk if this disposition is acted on and the analysis is wrong**

Adding `.venv/` to .gitignore cannot hide tracked content — git ignores have no effect on already-tracked files, and no tracked path contains a `.venv` component (verified against `git ls-files`). Worst case it is a no-op on machines that place the venv elsewhere.

**Skeptic's verdict**

Every cited fact verified by reading the real files; I could not refute it. (1) `git check-ignore -v .venv/x` exits 1 — not ignored; the full .gitignore has no venv/.venv/env//build//dist/ entry, .git/info/exclude is stock comments, and core.excludesfile is unset, so no hidden rule rescues it. (2) Both launchers create it at the REPO ROOT, which I checked rather than assumed: Start-BananaLab.ps1:20 `$Root = Split-Path -Parent $MyInvocation.MyCommand.Path` (script sits at repo root) then :70 `& py -3 -m venv (Join-Path $Root ".venv")`; start-banana-lab.sh:4 `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` then :20 `"$PYTHON" -m venv "$ROOT/.venv"`. It is also in the documented onboarding path twice: Start-BananaLab.ps1:160 `"  2. From repo root: python -m venv .venv"` and docs/OPERATOR_RUNBOOK.md:17 `python -m venv .venv`. (3) scripts/silent_failure_audit.py:48-51 verified verbatim (`".venv",` `"venv",` `".env",` `"env",`; 52-54 add build/dist/site-packages), present in `git show HEAD:` not just the dirty copy. (4) Their .pytest_cache/.ruff_cache exclusion is correct — `git check-ignore -v .pytest_cache/x` returns `.pytest_cache/.gitignore:2:*`, self-ignoring. (5) AUDIT_PROGRESS.md:89 and .gitignore:23-28 quoted exactly. No missed reference exists.

SEVERITY CORRECTED High -> Medium on two grounds I verified: (a) `git grep "git add"` across ALL tracked files returns only two hits, both prose (.gitignore:26 and the audit table) — no script, workflow, skill, or .ps1 in this repo runs `git add -A`, so the hazard needs a manual operator action; (b) the repo's own precedent rates the identical defect class Medium (AUDIT_PROGRESS.md:89 F-005 is `| Medium |`) and that one was ACTIVE (artifacts/ existed on disk), whereas .venv/ does not currently exist at the repo root. Also no backup amplifier: scripts/backup_production.py:19-27 DEFAULT_TARGETS is an explicit allowlist that never copies the repo root.

DISPOSITION Repair confirmed safe: `git ls-files` returns zero tracked files under any `.venv|venv|env|build|dist` path, so adding the ignore cannot orphan anything or perturb pytest.ini's testpaths allowlist, ruff.toml, .github/workflows/validate.yml (uses setup-python + bare pip, never creating an in-repo venv), or the four tracked .claude/skills/*/SKILL.md.

Adjacent, NOT part of this claim: pytest.ini `norecursedirs` replaces pytest's built-in default (`*.egg .* build dist venv`) and omits .venv/venv — bare `pytest` is saved by `testpaths`, but explicit `pytest .` would recurse into a created .venv. Same drift family, separate finding. One item I could not execute-verify: ruff was not on PATH (`ruff --version` exit 127), so their "ruff is safe by accident via default extend-exclude" rests on documented ruff defaults — but it is not load-bearing for the claim.

---

### U10 — backup_production.py `DEFAULT_TARGETS` omits `GENESIS/`, so the 137 MB of print masters that GENESIS/.gitignore deliberately keeps out of git exist in neither git nor any backup

- **Location:** `scripts/backup_production.py:19-27`
- **Lens:** config-drift  |  **Category:** config
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

scripts/backup_production.py:19-27:
```
DEFAULT_TARGETS = [
    "02_MONTHLY_ISSUES",
    "03_APPROVED_CANON",
    "05_RELEASE_ARCHIVE",
    "character-bibles",
    "01_IDEAS_INBOX",
    "story-bibles",
    "04_REJECTED_OUTPUTS",
]
```
GENESIS/.gitignore:4-5 removes two trees from git:
```
/story_pages/
/covers/*.png
```
Disk-vs-index counts confirm they are the only untracked GENESIS content and they are large:
`GENESIS/story_pages  disk=22 tracked=0` (128 MB), `GENESIS/covers  disk=2 tracked=0` (9.5 MB); every other GENESIS subtree is fully tracked (`web 24/24`, `generated_art 75/75`, `previews 10/10`).
GENESIS is not a substring of any DEFAULT_TARGETS entry, so backup() skips it entirely (backup_production.py:47-51 iterates only `targets`).

The policy doc mirrors the code faithfully and therefore cannot catch the gap — docs/BACKUPS.md "## What is copied" table lists exactly those seven paths, no GENESIS row. docs/OPERATOR_RUNBOOK.md:166-173 "Protect outside Git:" also omits GENESIS.

Same class, smaller: .gitignore:57-59 excludes `00_SYSTEM/integration_upgrade/character_layers/` and `00_SYSTEM/integration_upgrade/poc/*/final_integrated.png`, and `00_SYSTEM` is likewise absent from DEFAULT_TARGETS.

Note the inversion: `01_IDEAS_INBOX` IS a backup target and is 4 fully-tracked .md files (`git ls-files 01_IDEAS_INBOX` → 4 files), i.e. the list backs up a tree git already covers while skipping the tree git deliberately does not.

**Rationale**

backup_production.py's own docstring states the contract: "Git is not sufficient for untracked art, PDF/CBZ packages, release archives, or owner-managed assets." The `.gitignore`/`DEFAULT_TARGETS` pair is supposed to partition the repo into git-covered and backup-covered; GENESIS/story_pages and GENESIS/covers fall through both halves. Severity is Medium rather than High because GENESIS/.gitignore:1-2 asserts a real regeneration path ("deterministically regenerable ... via 00_SYSTEM/scripts/genesis/genesis_build.py") and the source panels it needs (GENESIS/generated_art, 75/75) are tracked — so this is a recovery-time cost, not unconditional data loss.

**Risk if this disposition is acted on and the analysis is wrong**

Adding `GENESIS` to DEFAULT_TARGETS grows every backup by ~280 MB (GENESIS totals ~380 MB on disk, most already git-tracked and therefore duplicated into the snapshot). If regeneration truly is deterministic and cheap, the correct fix may instead be an explicit note in docs/BACKUPS.md rather than a target — verify genesis_build.py's runtime before choosing.

**Skeptic's verdict**

UPHELD after failed refutation on every axis. Core mechanism verified verbatim: backup_production.py:19-27 is exactly the seven-entry DEFAULT_TARGETS quoted, and backup() at :47-51 resolves `source = ROOT / rel` — an exact path join, not substring matching — so GENESIS is never visited. GENESIS/.gitignore:4-5 (`/story_pages/`, `/covers/*.png`) confirmed by `git check-ignore -v`; counts/sizes exact (story_pages disk=22 tracked=0 @128M, covers disk=2 tracked=0 @9.5M; web 24/24, generated_art 75/75, previews 10/10). Doc claims accurate: docs/BACKUPS.md:29-37 table lists precisely those seven paths; docs/OPERATOR_RUNBOOK.md:166-173 "Protect outside Git:" omits GENESIS (GENESIS appears nowhere in that file). The 01_IDEAS_INBOX inversion is real (4 tracked .md, 4 on disk).

Refutation attempts that FAILED and instead corroborate: (1) Backup-BananaLab.ps1:42-45 — the documented one-command entry point — builds $argsList from only --dest/--dry-run and never passes --targets, so it inherits DEFAULT_TARGETS; docs/HOSTING_PLAN.md:132 nightly job likewise. (2) The only real backup on disk, 06_BACKUPS/monkeyzoo-backup-20260716T153542Z, has exactly the seven target dirs at top level and its manifest "targets" matches — no GENESIS. (3) GENESIS is absent from 05_RELEASE_ARCHIVE (`find -iname "*enesis*"` empty). (4) The tracked GENESIS/release CBZ/PDF is NOT a hidden copy of the masters: reading the zip shows 24 entries, all .jpg, and release_manifest.json records `"edition": "web (1600px wide, JPG q88)"`; genesis_release.py:32-33 globs only web/covers + web/story_pages. (5) scripts/tests/test_backup_production.py never asserts on DEFAULT_TARGETS (uses a fabricated `_targets()`), so no test guards the contract. No skill, CI workflow, or runbook compensates.

ONE EVIDENCE ERROR, corrected not fatal: their rationale states the regeneration inputs are "GENESIS/generated_art, 75/75 tracked." False. genesis_build.py:297 reads `panel_dir = FACTORY / plan["source_panel_dir"]`, and GENESIS_LAYOUT_PLAN.json sets source_panel_dir = 02_MONTHLY_ISSUES/2026-09_Issue_02/generated_art/integration_preview, whose 102 MZ-2026-09-02_*.png composites are gitignored by .gitignore:58. GENESIS/generated_art/panel_native is only an override (genesis_build.py:320-321, "bespoke panel-native art ... overrides the source composite"). The regeneration path survives — but via git (plan + script + panel_native + tracked COVER_FRONT/BACK.png) PLUS the backup (that dir sits under target #1, 02_MONTHLY_ISSUES) — a two-hop dependency, not git alone. This makes the mitigation more fragile than stated, so it argues against downgrading.

Severity Medium is correct and not inflated: the missing bytes are 100% derived output, the shipped deliverable (release CBZ/PDF, web JPGs, previews, all QA reports) is fully tracked, and a deterministic rebuild exists (seed 20260718). It is recovery-time cost, not unique data loss — so not High; but the .gitignore/DEFAULT_TARGETS partition gap is systemic (same class hits 00_SYSTEM/integration_upgrade/character_layers, verified 78M on disk, .gitignore:56-57, with 00_SYSTEM also absent from DEFAULT_TARGETS) and the docs mirror the gap rather than catching it — so not Low. Disposition Repair is safe: adding targets only widens copying and cannot break any caller.

Minor nit in their citation: the character_layers/poc pair is .gitignore:56-57, not 57-59 (58-59 are the integration_preview rules); content quoted is correct.

---

### U11 — CONTRIBUTING says CI runs "exactly" ruff + pytest; CI runs four more gates, and one has no local pytest equivalent

- **Location:** `CONTRIBUTING.md:22`
- **Lens:** doc-reality  |  **Category:** doc-mismatch
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

CONTRIBUTING.md:22-27 states: "CI (`.github/workflows/validate.yml`) runs exactly these; run them first:" followed by a block containing only `ruff check .` and `pytest`, then line 30: "Both must be green." `.github/workflows/validate.yml` actually contains four further gate steps after "Run pytest suite": "Validate character bibles (canon integrity)" → `python character-bibles/_schema/validate-character-bibles.py --root character-bibles --workspace-root .`; "Validate continuity ledger (canon integrity)" → `python 00_SYSTEM/scripts/validate_ledger.py 00_SYSTEM/continuity_ledger.md`; "Validate static pages assets" (inline python asserting docs/index.html, docs/static/styles.css, docs/static/app.js exist and contain no root-relative `"/static/` or `"/media/` paths); and "Verify deployed static-site consistency" → `python docs/verify_static_site.py docs`. I then checked which of these bare `pytest` reproduces. The ledger gate IS covered: 00_SYSTEM/scripts/tests/test_validate_ledger.py:89 `def test_real_committed_ledger_passes():` and :93 `def test_cli_exit_zero_on_real_ledger():` both read `REAL_LEDGER = FACTORY / "00_SYSTEM" / "continuity_ledger.md"`. The static-site gate IS covered: docs/tests/test_verify_static_site.py:122 `assert vss.verify_static_site(vss.DOCS) == []`. The character-bible gate is NOT: every one of the eight tests in character-bibles/_schema/tests/test_validate_bibles.py takes `tmp_path` (`test_distinct_ids_pass(tmp_path)`, `test_duplicate_id_fails_with_named_error(tmp_path)`, … `test_alias_sharing_its_target_handle_is_not_a_collision(tmp_path)`) and runs the validator against synthesised fixtures via `_run(tmp_path)`; `git grep -l "validate-character-bibles" -- "*.py"` returns only that test file and scripts/workflow_engine.py. README.md:82-83 undercounts the same way: "CI runs the same suite plus a static-asset check (`.github/workflows/validate.yml`)."

**Rationale**

The word "exactly" makes this an actionable promise, not a summary. A contributor who edits a tracked `character-bibles/*/bible.yaml` — a duplicate `character_id`, a dangling `alias_of`, a display-name collision, a missing required identity field, a referenced image that no longer exists — gets green ruff and green pytest locally and a red CI. That is precisely the failure the doc claims to prevent. Fix by listing all six CI steps, or by adding a real-repo test for the bible validator so the claim becomes true.

**Risk if this disposition is acted on and the analysis is wrong**

None from editing prose. The only risk is over-correction: if someone instead deletes the CI-only steps to make CONTRIBUTING literally true, the repo loses the canon-integrity gate on character bibles, which is the stated reason that step exists ("so a malformed bible or an identity collision can no longer reach main with CI green").

**Skeptic's verdict**

Independently verified; every factual assertion holds. CONTRIBUTING.md:22 literally says "CI (`.github/workflows/validate.yml`) runs exactly these; run them first:" over a block containing only `ruff check .` (:25) and `pytest` (:26), with ":29 Both must be green." The workflow has six run-steps: ruff (:36), pytest (:40), `python character-bibles/_schema/validate-character-bibles.py --root character-bibles --workspace-root .` (:49), `python 00_SYSTEM/scripts/validate_ledger.py 00_SYSTEM/continuity_ledger.md` (:57), an inline root-relative-asset scan (:61-82), and `python docs/verify_static_site.py docs` (:90). The coverage analysis also checks out: test_validate_ledger.py:89-95 exercises the real committed ledger (REAL_LEDGER, :25) and test_verify_static_site.py:121-122 asserts `vss.verify_static_site(vss.DOCS) == []`, while all eight tests in character-bibles/_schema/tests/test_validate_bibles.py take tmp_path and run only synthesised fixtures. I hunted for the missed reference and it does not exist: `git grep "validate-character-bibles"` hits only the workflow, _qa/system-audit.md:61, the tmp_path test, and scripts/workflow_engine.py:689 — which is generated audit-plan prose ("- Action: run `python character-bibles/_schema/validate-character-bibles.py ...`"), not execution (workflow_engine's only subprocess call is `git rev-parse` at :628). No .ps1, Makefile, or pre-commit runs the gate. I also refuted the best accidental-coverage candidate: test_character_media.py:23 loads the real tree and :51 asserts character_id uniqueness, but bible_store.load_all returns `(path.name, ...)` (bible_store.py:165) and character_summary sets `"character_id": character_id` from the folder name (:222), so a duplicate declared character_id can never trip it, and bible_dirs (:135-143) skips alias_of folders entirely. If anything the sweep understated: the inline static-asset root-relative scan has no pytest equivalent either (no test reads real docs/index.html, styles.css, app.js for `"/static/`), so two gates lack local equivalents. Severity corrected High -> Medium: the validator currently passes (I ran it read-only: "Validated 12 Character Bible file(s). PASSED with 0 warning(s."), so nothing is broken today, and the worst outcome is a red CI on an explicitly named step after a green local run — self-diagnosing, non-destructive, no canon or data corruption. Repair is the right disposition and is non-breaking (list all six steps in CONTRIBUTING.md:22-30 and fix the same undercount at CONTRIBUTING.md:73 "CI must be green (ruff + pytest)" and README.md:82-83 "CI runs the same suite plus a static-asset check", and/or add a real-repo test for the bible validator).

---

### U12 — Genesis scripts silently ignore unknown flags; `genesis_release.py --help` performs a destructive release rebuild instead of printing help

- **Location:** `00_SYSTEM/scripts/genesis/genesis_release.py:158`
- **Lens:** doc-reality  |  **Category:** config
- **Severity:** Medium  |  **Disposition:** Repair

**Evidence**

.claude/skills/mz-package/SKILL.md:20-25 documents this as a pre-mint safety check: "verify its integrity + provenance BEFORE distributing or minting: `python 00_SYSTEM/scripts/genesis/genesis_release.py --verify <genesis-dir>` — re-hashes every SHA256SUMS.txt file and cross-checks the release manifest's per-artifact sha256/bytes (the values CHIP-0015 mints with)." The `--verify` path itself is correctly implemented (genesis_release.py:107-155, :162-169). The hazard is the argv handling around it: :159 `positional = [a for a in sys.argv[1:] if not a.startswith("--")]`, :160 `genesis_dir = Path(positional[0]) if positional else FACTORY / "GENESIS"`, :162 `if "--verify" in sys.argv:` … else :171 `r = package(genesis_dir)`. There is no argparse, so every flag except `--verify` is discarded and execution falls through to `package()`, which rewrites the CBZ, the PDF, `release_manifest.json` and `SHA256SUMS.txt` (:103 `(rel / "SHA256SUMS.txt").write_text(...)`). I hit this directly while auditing: `python 00_SYSTEM/scripts/genesis/genesis_release.py --help` printed "Genesis release: 24 images (22 pages + 2 covers) … manifest + SHA256SUMS written" and left `M GENESIS/release/MonkeyZoo_Genesis.pdf`, `M GENESIS/release/SHA256SUMS.txt`, `M GENESIS/release/release_manifest.json` in `git status` (mtimes 13:30:35-36 matching the invocation). I restored all three with `git checkout --`; `git status -- GENESIS/` is clean. Eleven of the twelve genesis scripts share the no-argparse pattern (`grep -c argparse` returns 0 for genesis_build, genesis_crop_audit, genesis_dupes, genesis_editorial, genesis_layout, genesis_matrix, genesis_plan, genesis_qa, genesis_release, genesis_report, genesis_specs; only genesis_charart.py uses argparse).

**Rationale**

A command documented as read-only verification is one typo away from rewriting the release artifacts whose hashes CHIP-0015 mints with. `--help` is the single most likely thing an operator types against an unfamiliar script, and it is the exact input that triggers the rebuild. Switching main() to argparse makes `--help` print help and unknown flags exit 2, at zero behavioural cost to the two documented invocations (`genesis_release.py` and `genesis_release.py --verify <dir>`).

**Risk if this disposition is acted on and the analysis is wrong**

An argparse conversion must keep the bare no-argument invocation meaning "package GENESIS/", or any runbook or CI step that calls the script with no arguments breaks. Verify no caller passes flags that are currently being silently absorbed before tightening.

**Skeptic's verdict**

UPHELD — independently confirmed by reading the code and by empirical reproduction; every cited fact is accurate and the hazard is worse than reported.

CODE VERIFIED VERBATIM (00_SYSTEM/scripts/genesis/genesis_release.py): :158 `def main() -> None:`; :159 `positional = [a for a in sys.argv[1:] if not a.startswith("--")]`; :160 `genesis_dir = Path(positional[0]) if positional else FACTORY / "GENESIS"`; :162 `if "--verify" in sys.argv:`; :171 `r = package(genesis_dir)`. package() rewrites artifacts at :97 (release_manifest.json) and :103 `(rel / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")`. No argparse import. Their argparse census is exact: `grep -c argparse` = 0 for all 11 named scripts, 2 only for genesis_charart.py.

DOC CLAIM VERIFIED: .claude/skills/mz-package/SKILL.md:22 documents `python 00_SYSTEM/scripts/genesis/genesis_release.py --verify <genesis-dir>` as a pre-mint check for "the values CHIP-0015 mints with."

EMPIRICAL REPRODUCTION (isolated scratch genesis dir): `--help <dir>` printed "Genesis release: 24 images (22 pages + 2 covers) ... manifest + SHA256SUMS written", exit 0, wrote all four release files. No help text. `--verify-only <dir>` (near-miss typo) did the same, because :162 is list membership, not prefix matching.

TWO FINDINGS STRONGER THAN THE ORIGINAL CLAIM:
(1) `--verify=<dir>` — the equals-form of the DOCUMENTED command — is strictly worse than --help. Starting with "--", it is filtered from `positional`, so the directory argument is discarded AND `genesis_dir` falls back to `FACTORY / "GENESIS"`. It repackaged the REAL production release (output "CBZ: 12868 KB / PDF: 9524 KB" matching the tracked artifacts). A one-character typo on the documented invocation silently retargets the write to the live release. Restored via `git checkout -- GENESIS/`; on-disk hashes now match the committed manifest exactly (cbz 52dfb91f…, pdf 9b582790…), `git status -- GENESIS/` clean.
(2) The drift is invisible to the tool meant to detect it. CBZ is deterministic (identical hash across runs) but PDF is not (a03cb439… -> 7429e01f…, PIL embeds a creation date); package() then rewrites manifest+SHA256SUMS to match the NEW pdf, so `--verify` reports OK afterward while the minting hash has changed. Only git catches it.

REFUTATION ATTEMPTS THAT FAILED: no CI reference (`git grep genesis -- .github/` empty); no .ps1/.bat/.sh wrapper invokes any genesis script; no external Python caller (`git grep "genesis_" -- "*.py"` outside the genesis dir returns nothing). Only callers are the two documented forms plus tests.

DISPOSITION SAFETY: test_genesis_release.py:150,156 call `["genesis_release.py", str(genesis), "--verify"]` (positional then flag) — argparse handles interspersed args natively. Bare invocation (genesis_report.py:153, project_direction.json:687) works with an optional positional. argparse with `--verify` store_true + optional genesis_dir breaks nothing.

SEVERITY: Medium confirmed, not inflated and not deflated. Not High — artifacts are git-tracked and regenerable, so damage is detectable and fully recoverable, no network/credential exposure. Not Low — this is the command the skill advertises as the pre-mint provenance gate, and the failure silently alters the bytes CHIP-0015 mints with.

---

### U13 — scripts/compose_issue01_draft_panels.py is orphaned and mutates a published issue's workflow state

- **Location:** `scripts/compose_issue01_draft_panels.py:221`
- **Lens:** dead-python  |  **Category:** dead-code
- **Severity:** Low  |  **Disposition:** Deprecate

**Evidence**

`git grep -n compose_issue01_draft_panels` returns only: `00_SYSTEM/project_direction.json:593,597` (+ `docs/static/` mirror) inside a `"docs"` array on a task whose instructions read `"DONE 2026-07-15. Built queue; composed draft panels ... (scripts/compose_issue01_draft_panels.py) ..."`; `00_SYSTEM/integration_upgrade/ARCHITECTURE_FINDINGS.md:11` naming its `compose()` as the rejected card-cutout technique; and auto-generated `docs/audit/silent_failure_report.md` rows. No skill, CI, runbook, `*.ps1`, test, or Python import references it. It nonetheless runs unconditionally against a live Studio: `ISSUE = "MZ-2026-08-01"`, `BASE = "http://127.0.0.1:8765"`, `if __name__ == "__main__": raise SystemExit(main())`, and issues POSTs including `req_json("POST", f"/api/issues/{ISSUE}/art-queue/build", {})` (line 193) and `req_json("POST", f"/api/issues/{ISSUE}/advance", {"stage": "art_production"})` (line 221) against an issue already in `05_RELEASE_ARCHIVE/2026/2026-08_Issue_01`.

**Rationale**

Unreachable and superseded: the repo's own ARCHITECTURE_FINDINGS.md documents its compositing approach as what the integration pipeline replaced, and its target issue is published. Lower severity than the two above only because its POSTs rebuild a queue and advance a stage rather than overwrite a release archive.

**Risk if this disposition is acted on and the analysis is wrong**

The draft composites currently shipping in `02_MONTHLY_ISSUES/2026-08_Issue_01/generated_art/selected_panels/` were produced by this script; the same project_direction entry notes they must be "replace[d] with final illustrated panels before public release quality claim", so deleting it before that replacement lands removes the only way to regenerate what is on the shelf today.

**Skeptic's verdict**

PARTIALLY UPHELD — the orphan half is confirmed; the harm half ("mutates a published issue's workflow state") is REFUTED, so severity drops to Low.

CONFIRMED BY READING THE CODE:
- File is git-tracked: `git ls-files` -> `scripts/compose_issue01_draft_panels.py`.
- Exhaustive tracked-tree grep yields 11 hits, all accounted for and all non-invoking: `00_SYSTEM/project_direction.json` JSON path `/tracks/4/tasks/8/instructions` (a "DONE 2026-07-15" provenance record) and `/tracks/4/tasks/8/docs/2` (a provenance array), `00_SYSTEM/integration_upgrade/ARCHITECTURE_FINDINGS.md:11`, auto-generated `docs/audit/silent_failure_report.md` rows, and the `docs/static/` mirror.
- No invocation path exists. All four `.claude/skills/*/SKILL.md` reference only `00_SYSTEM/scripts/*` (e.g. `python 00_SYSTEM/scripts/run_art_batch.py`), never root `scripts/`. `.github/workflows/validate.yml` never names it (it is only swept by `ruff check .`). All 13 tracked `*.ps1` return zero matches for "compose"; the only dynamic-looking dispatch, `scripts/improvement_loop.ps1:9`, hard-codes `Join-Path $PSScriptRoot "workflow_engine.py"`. No `import compose`, runpy, or importlib dispatch anywhere.
- Their code quotes are exact: line 17 `ISSUE = "MZ-2026-08-01"`, line 19 `BASE = "http://127.0.0.1:8765"`, line 193 `req_json("POST", f"/api/issues/{ISSUE}/art-queue/build", {})`, line 221 `req_json("POST", f"/api/issues/{ISSUE}/advance", {"stage": "art_production"})`, lines 228-229 `if __name__ == "__main__": raise SystemExit(main())`.
- The issue really is published: `02_MONTHLY_ISSUES/2026-08_Issue_01/.workflow-status.json` -> `active_stage: published`, last transition `release` -> `published` at 2026-07-16.

REFUTED — BOTH CITED POSTs ARE NON-MUTATING AGAINST THIS TARGET:
(a) Line 193 reaches `art_queue_workspace.build_queue`, whose first statement (art_queue_workspace.py:85) is `_stage(folder,root,{"art_prompts","art_production"})`; `_stage` (line 45) raises `ArtQueueError(f"Art Queue requires workflow stage {' or '.join(sorted(allowed))}; current stage is {active}",409)`. Stage is `published`, so it 409s and `if persist:_write_json(_workspace(folder)/"queue.json",queue)` (line 97) is NEVER reached. No queue is rebuilt.
(b) Line 221 — the claim's own LOCATION — is UNREACHABLE. Every `multipart_import` hits `import_attempt` (art_queue_workspace.py:116), which also opens with `_stage(folder,root,{"art_production"})` -> 409, so all 24 panels land in `fail` (line 204), and lines 217-218 `if fail:\n        return 1` return before line 221 ever executes.
(c) Even if reached, `issue_workflow.record_advance:276` raises `IssueWorkflowError("Stage mismatch; stage skipping is not allowed")` because `"art_production" != "published"`. No state write.
So the severity rationale ("its POSTs rebuild a queue and advance a stage") is wrong on both counts.

ALSO OVERSTATED: they call ARCHITECTURE_FINDINGS.md:11 "the rejected card-cutout technique." That row actually reads `| Card-cutout paste compositing | **Real** — ...` under the heading "What's real vs. aspirational" — i.e. the baseline that shipped. The literal phrase `**Rejected with evidence**` belongs to a different row, line 51 `| Edge unification (img2img ring) | **Rejected with evidence** (Cycle 16) ... |`. Superseded: yes (the 2026-07-17 status table shows true-alpha layers, ground-plane placement, contact shadows built). Labeled "rejected": no.

THE ONE REAL (SMALL) HAZARD THEY MISSED: the unguarded effect is local, not API. `compose()` lines 128-130 run before any 409: `STAGING.mkdir(parents=True, exist_ok=True)` then `canvas.save(out, "PNG")` into `02_MONTHLY_ISSUES/2026-08_Issue_01/generated_art/draft_composites/{pid}.png`. Those 24 PNGs ARE git-tracked (`git ls-files | grep draft_composites` -> 24 under 2026-08_Issue_01, 24 under 2026-09_Issue_02) and `generated_art/` is not gitignored, so a stray run overwrites tracked release-evidence images. Git-recoverable, non-canonical, requires deliberately running an obviously issue-specific script -> Low.

DISPOSITION HOLDS AT DEPRECATE: it is one of a family of hard-coded one-off drivers (`drive_issue_01_neonblue_story.py`, `drive_issue_02_pipeline.py`, `drive_issue_03_scarline_scaffold.py`, `prepare_issue01_release_assets.py`, `rc_real_issue_run.py`) with no live caller. Removal would be wrong — `project_direction.json` and `ARCHITECTURE_FINDINGS.md:11` cite it by path/function name as the provenance trail for a completed task and for the baseline compositing technique. Deprecating (neutralizing the `__main__` entry point / adding an active-stage precondition) preserves those citations and breaks nothing.

---

### U14 — Three launcher/runbook surfaces hardcode a four-package install list, contradicting CONTRIBUTING.md's "single source of truth" claim

- **Location:** `Start-BananaLab.ps1:83`
- **Lens:** deps  |  **Category:** doc-mismatch
- **Severity:** Low  |  **Disposition:** Consolidate

**Evidence**

`Start-BananaLab.ps1:81-99` embeds both a probe list and an install list:

```powershell
    Write-Step "Checking Python dependencies (flask, pillow, pyyaml, jsonschema)"
    $code = @'
import importlib.util, sys
missing = [n for n in ("flask", "PIL", "yaml", "jsonschema") if importlib.util.find_spec(n) is None]
```

```powershell
    & $PythonExe -m pip install flask pillow pyyaml jsonschema
```

Repeated a third time in the same file's recovery hint, `Start-BananaLab.ps1:161`:

```powershell
    Write-Host "  3. .\.venv\Scripts\python.exe -m pip install flask pillow pyyaml jsonschema"
```

Same literal list at `start-banana-lab.sh:28` and `docs/OPERATOR_RUNBOOK.md:18`. That is five copies across three files.

Directly contradicted by `CONTRIBUTING.md:17`:

> "`requirements-dev.txt` is the single source of truth for dependencies, shared by CI"

and by `requirements-dev.txt:2-3`, which claims the same: "This is the single source of truth shared by CI (.github/workflows/validate.yml) and the README quickstart."

The list is currently *correct for the Studio alone* — I computed the transitive closure of `character-bibles/_review_app/app.py` across 13 local modules: `['PIL', 'flask', 'jsonschema', 'werkzeug', 'yaml']`, and werkzeug arrives with flask. So this is latent drift, not a live break for `app.py`.

**Rationale**

The claim in CONTRIBUTING.md is false as written, and the falseness is what makes it dangerous: a maintainer who adds an import to the review app will update `requirements-dev.txt`, watch CI go green, and never learn that five hardcoded copies in the launcher path still need editing. The probe at line 83 makes it worse than a stale comment — it actively reports "Dependencies present" and skips installation when the four legacy names resolve, so a genuinely missing fifth package produces a confident green check followed by an ImportError at app start. Consolidate all five copies to `pip install -r requirements-dev.txt` (or, if the launcher deliberately wants a lean runtime venv without pytest/ruff/numpy/scipy, split out a `requirements.txt` and have both the launcher and requirements-dev.txt reference it via `-r`).

**Risk if this disposition is acted on and the analysis is wrong**

Pointing the launchers at `requirements-dev.txt` grows the operator venv from 4 packages to 10 — pulling in numpy, scipy, pytest, pytest-asyncio, anyio, and ruff. On the Windows bootstrap path that is a materially slower and larger first run (scipy alone is ~40MB), and a scipy wheel resolution failure would newly break `Start-BananaLab.ps1` for a user who only wanted to open the Studio UI. That argues for the `-r requirements.txt` split rather than the blunt substitution; either way the current five-copy duplication should not survive.

**Skeptic's verdict**

Facts confirmed by direct reading; severity corrected down. VERIFIED VERBATIM: Start-BananaLab.ps1:81 `Write-Step "Checking Python dependencies (flask, pillow, pyyaml, jsonschema)"`, :84 `missing = [n for n in ("flask", "PIL", "yaml", "jsonschema") if importlib.util.find_spec(n) is None]`, :98 `& $PythonExe -m pip install flask pillow pyyaml jsonschema`, :161 `Write-Host "  3. .\.venv\Scripts\python.exe -m pip install flask pillow pyyaml jsonschema"`; start-banana-lab.sh:25 `if ! "$PYTHON" -c "import flask, PIL, yaml, jsonschema"`, :26, :28; docs/OPERATOR_RUNBOOK.md:18. CONTRIBUTING.md:17 and requirements-dev.txt:2-3 say what is claimed. The skip-on-green behavior is real (Start-BananaLab.ps1:90-94 returns after "Dependencies present" without installing), so a future fifth runtime dep would yield a green check then an ImportError at app start. INDEPENDENTLY RECONFIRMED CLOSURE: third-party imports across app.py plus its 11 sibling modules plus 00_SYSTEM/scripts/new_issue.py (reached via `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00_SYSTEM" / "scripts"))` at app.py:28) are exactly flask, werkzeug, jsonschema, PIL, yaml -- no numpy/scipy, no subprocess, no importlib/getattr dispatch. The four-name list is currently sufficient; this is latent drift, not a live break. MISSED-REFERENCE SEARCH EMPTY: no test, CI step, skill, or .ps1 wrapper keeps the lists in sync; .github/workflows/validate.yml:32 uses `pip install -r requirements-dev.txt` only; no fourth surface duplicates the list. CORRECTIONS AGAINST THEM: (1) count is wrong -- 8 literal occurrences across 3 files (ps1 x4, sh x3, runbook x1), not "five copies"; the undercount does not change the three-surface headline. (2) The "contradiction" is overstated: both SSoT sentences are scope-qualified -- CONTRIBUTING.md:17 reads "single source of truth for dependencies, shared by CI and this guide" and requirements-dev.txt:3 "shared by CI (.github/workflows/validate.yml) and the README quickstart" -- neither asserts the launchers consume it, so this is an unstated-scope gap rather than a false statement about the launcher path. SEVERITY LOWERED to Low: nothing is broken today, no correctness/security/user-facing impact, and the failure mode requires a future maintainer to add a fifth runtime dependency. Not Informational, because the probe actively reports success and skips install rather than being a merely stale comment. DISPOSITION Consolidate retained, but with a constraint their primary remedy gets wrong: `pip install -r requirements-dev.txt` in the launcher would install numpy, scipy, pytest, pytest-asyncio, anyio, and ruff into an operator's runtime venv (a real behavior change and extra failure surface on a Windows/AMD operator box). Their secondary option is the correct one: split a lean `requirements.txt` and have both the launcher/runbook and requirements-dev.txt reference it via `-r`, and drive the ps1/sh probe from that file instead of a hardcoded tuple.

---

### U15 — Four tracked pipeline scripts hard-code `I:\ai\nft\...` as a module-level constant with no env-var or config override

- **Location:** `00_SYSTEM/scripts/genesis/genesis_charart.py:36`
- **Lens:** config-drift  |  **Category:** config
- **Severity:** Low  |  **Disposition:** Repair

**Evidence**

Four independent hard-codings of this machine's ComfyUI I/O root, all module-level and all unconditional:
- 00_SYSTEM/scripts/genesis/genesis_charart.py:36 — `OUT_DIR = Path(r"I:\ai\nft\output")`
- 00_SYSTEM/scripts/integration/edge_unify.py:48-49 — `COMFY_INPUT = Path(r"I:\ai\nft\input")` / `COMFY_OUTPUT = Path(r"I:\ai\nft\output")`
- 00_SYSTEM/scripts/integration/gen_scene_pose.py:23 — `OUT_DIR = Path(r"I:\ai\nft\output")`
- 00_SYSTEM/scripts/integration/smoke_render.py:17 — `OUT_DIR = Path(r"I:\ai\nft\output")`

They are consumed for real work, not just documentation: genesis_charart.py:94 `sorted((OUT_DIR / prefix).glob(...))`, edge_unify.py:87-88 `comp.save(COMFY_INPUT / comp_name)`, smoke_render.py:40 `OUT_DIR.glob(f"{PREFIX}*.png")`.

All four are live, not dead: .claude/skills/mz-art-run/SKILL.md:72 invokes `gen_scene_pose.py`; 00_SYSTEM/automation_rules.md:110 documents `gen_scene_pose.py`; 00_SYSTEM/integration_upgrade/CYCLE_LEDGER.md:522 records `smoke_render.py` as "reusable"; genesis_charart.py has a tracked test module (00_SYSTEM/scripts/genesis/tests/test_genesis_charart.py).

No override mechanism exists anywhere: grepping `getenv|environ` across all tracked Python returns only `MZ_STUDIO_LOG_DIR`, `MZ_STUDIO_DEBUG`, and `PORT` (character-bibles/_review_app/app.py:527,620,625). config/production_config.yaml has a `source_of_truth`/`production` section but no ComfyUI path key.

By contrast the two scripts that were written portably do not hard-code anything: 00_SYSTEM/scripts/run_art_batch.py:11-12 documents "Output filename prefix: <issue_id>/<panel_id>_seed<seed> under ComfyUI's output directory" and lets the server resolve it; 00_SYSTEM/scripts/gen_char_refs.py:10 does the same.

**Rationale**

CLAUDE.md scopes `I:\ai\ComfyUI` under "Local rig facts (this machine)", which is fine for prose. Baking the same assumption into module-level constants in tracked code makes four scripts unrunnable on any other machine, and makes them fail by silent no-op rather than by error: smoke_render.py:40/50 globs a non-existent `OUT_DIR`, gets an empty set, and returns TIMEOUT after 900s rather than reporting a bad path; genesis_charart.py:94's existence-based resume sees zero files. The portable pattern already exists in the same tree (run_art_batch.py, gen_char_refs.py), so this is inconsistency, not an unavoidable constraint.

**Risk if this disposition is acted on and the analysis is wrong**

Routing these through an env var / config key with the current literal as the default preserves behaviour byte-for-byte on this rig. The risk of changing them is a typo'd default silently redirecting art output; mitigate by keeping the literal as the fallback and failing loudly when the resolved directory does not exist.

**Skeptic's verdict**

CORE CLAIM CONFIRMED, RATIONALE PARTLY REFUTED, SEVERITY INFLATED.

WHAT I VERIFIED AS TRUE (read every file, all quotes exact):
1. All five hard-codings exist verbatim at the cited lines: `00_SYSTEM/scripts/genesis/genesis_charart.py:36` `OUT_DIR = Path(r"I:\ai\nft\output")`; `00_SYSTEM/scripts/integration/edge_unify.py:48-49` `COMFY_INPUT = Path(r"I:\ai\nft\input")` / `COMFY_OUTPUT = Path(r"I:\ai\nft\output")`; `00_SYSTEM/scripts/integration/gen_scene_pose.py:23`; `00_SYSTEM/scripts/integration/smoke_render.py:17`.
2. The count is right. `git grep -n -E "I:[\\/]" -- '*.py'` over tracked files returns exactly these four scripts plus review-app tests that merely assert `"I:\\" not in` responses (leakage guards, not path constants).
3. Consumed for real work — confirmed, and the sweep UNDERCOUNTED. Beyond their three cited sites there are four more: `genesis_charart.py:115` and `:125` (`return OUT_DIR / im["subfolder"] / im["filename"]`), `edge_unify.py:119`, `gen_scene_pose.py:56`.
4. No override of any kind. `git grep -n -E "getenv|environ" -- '*.py'` over tracked files yields only `MZ_STUDIO_LOG_DIR`, `MZ_STUDIO_DEBUG`, `PORT` at `character-bibles/_review_app/app.py:527,620,625`. `config/production_config.yaml` has `source_of_truth:` and `production:` but no ComfyUI key (`output_root: "runs"` is the workflow-engine run dir, unrelated). No `--out-dir` flag in any of the four; notably `gen_scene_pose.py:71` exposes `--host` but not the output dir, so you can point at a different ComfyUI and still read from I:\.
5. Doc references check out: `.claude/skills/mz-art-run/SKILL.md:72`, `00_SYSTEM/automation_rules.md:110`, `CYCLE_LEDGER.md:522`, and the `run_art_batch.py:11-12` / `gen_char_refs.py:10` quotes are verbatim.

WHAT I REFUTE:
A. "Four tracked PIPELINE scripts" / "All four are live, not dead" is wrong for one. `edge_unify.py:1-3` says of itself: "Localized img2img edge unification -- EVALUATED AND REJECTED as a default pipeline stage (Cycle 16, 2026-07-17). Kept for reference/manual experiments only." Nothing imports it (`git grep` for importers returns only `test_genesis_charart.py:23: import genesis_charart as ca`); its sole entry is `__main__`. The sweep's four liveness citations actually cover gen_scene_pose (x2), smoke_render and genesis_charart — none covers edge_unify. Three live, one explicitly retired.
B. "makes them fail by silent no-op rather than by error" is false for three of the four. `edge_unify.py:87` `comp.save(COMFY_INPUT / comp_name)` raises FileNotFoundError on a missing dir. `gen_scene_pose.py:63` `raise TimeoutError(f"only {len(found)} of {len(seeds)} renders after {timeout_s}s")`. `genesis_charart.py:131` `raise TimeoutError(f"render {pid} timed out")`, and `:125` hands back a nonexistent path the caller then opens. The cited `genesis_charart.py:94` miss is the safest case of all — its own docstring calls it a resume cache ("delete the render file to force a fresh render"), so a miss regenerates rather than corrupts. Only `smoke_render.py` matches the described behaviour, and even it prints "TIMEOUT: render did not complete" and returns 1 — and only in the narrow case where ComfyUI IS reachable at 127.0.0.1:8188 but writes elsewhere, since `urlopen` at `:44` raises first otherwise.
C. "The portable pattern already exists in the same tree (run_art_batch.py, gen_char_refs.py)" is not apples-to-apples. Those two only queue prompts and exit; they never read a rendered PNG back. The four flagged scripts must locate the output on disk afterward — a requirement the "portable" pair never had. A real fix does exist (ComfyUI's `/view` endpoint; `genesis_charart.py:123-125` already parses `/history` for `subfolder`+`filename`, exactly `/view`'s inputs), but the sweep didn't cite it and its stated comparison overstates the case.

WHY High IS INFLATED (High -> Low):
- CI cannot be affected. `.github/workflows/validate.yml` runs `ruff check .` + `pytest` on `ubuntu-latest` and never invokes any of the four; `Path(r"I:\ai\nft\output")` just constructs a PosixPath on Linux. The only importing test states at lines 1-3 "Generation itself needs ComfyUI and is not unit-tested here."
- No user-facing surface: the Flask Studio app and docs/ site do not import these.
- This is a declared single-rig repo. `CLAUDE.md:33-35`: "## Local rig facts (this machine) - ComfyUI portable at `I:\ai\ComfyUI` ... Output: `I:\ai\nft\output\`." The same literal is in the operator runbooks the sweep itself cites (`mz-art-run/SKILL.md:43`, `mz-char-refs/SKILL.md:27,41`), so the constants AGREE with the documented environment — this is duplication, not drift-from-truth.
- No corruption, no data loss, no canon risk, no silent-wrong output. Worst case is a loud crash, or one 900s timeout with a misleading message, on a machine that does not yet exist.

Repair remains the right disposition — five copies of one machine fact across four files (plus three more in docs) with no single source of truth is a genuine, cheap-to-fix consolidation (one shared constant + env fallback). But it is Low-priority housekeeping on a single-operator rig, not a High-severity defect, and any repair should treat edge_unify.py as retired code rather than a pipeline stage.

---

### U16 — $env:PORT is documented in three places as a way to set the Studio port, but Start-BananaLab.ps1 unconditionally overwrites it

- **Location:** `README.md:22`
- **Lens:** doc-reality  |  **Category:** doc-mismatch
- **Severity:** Low  |  **Disposition:** Repair

**Evidence**

Three docs attribute `$env:PORT` to the launcher. README.md:22 (directly under the `.\Start-BananaLab.ps1` block): "Opens `http://127.0.0.1:8765` (loopback only, configurable via `-Port` or `$env:PORT`)." CONTRIBUTING.md:46: ".\Start-BananaLab.ps1            # http://127.0.0.1:8765  (or -Port / $env:PORT)". docs/OPERATOR_RUNBOOK.md:11 (directly under its `.\Start-BananaLab.ps1` block): "Opens `http://127.0.0.1:8765` (or custom port via `-Port <port>` or `$env:PORT`)." The launcher contradicts this. Start-BananaLab.ps1:15 declares `[int]$Port = 8765`; :135 gates on `if (-not (Test-PortFree $Port))`; :139 prints `$url = "http://127.0.0.1:$Port/"`; and :151, immediately before launching, does `$env:PORT = $Port` — an unconditional assignment that clobbers whatever the caller exported. app.py:625 then reads `port = int(os.environ.get("PORT", "8765"))`. So `$env:PORT = 9000; .\Start-BananaLab.ps1` free-port-tests 8765, prints 8765, sets PORT back to 8765, and serves on 8765. `$env:PORT` only works on the manual fallback path the runbook gives at OPERATOR_RUNBOOK.md:19 (`.\.venv\Scripts\python.exe character-bibles\_review_app\app.py`).

**Rationale**

The documented escape hatch for a port conflict silently does nothing. The launcher's own error text at :136 gives the working advice — "Stop the other process or re-run with -Port <free-port>" — so the code already knows `-Port` is the only launcher-side control. Either scope the docs to say `$env:PORT` applies when running app.py directly, or change :151 to honour a pre-set PORT when `-Port` was not passed explicitly (`$PSBoundParameters.ContainsKey('Port')`).

**Risk if this disposition is acted on and the analysis is wrong**

If the code is changed rather than the docs, honouring a stale exported `$env:PORT` could start the Studio on an unexpected port while the console still prints the URL the operator expects — worse than the current always-8765 behaviour. Prefer the doc fix unless the param-bound check is used.

**Skeptic's verdict**

Independently confirmed every citation. Start-BananaLab.ps1:15 `[int]$Port = 8765`, :135 `if (-not (Test-PortFree $Port))`, :136 throw naming `-Port <free-port>`, :139 `$url = "http://127.0.0.1:$Port/"`, and :151 `$env:PORT = $Port` — unconditional, no $PSBoundParameters guard exists anywhere in the file. app.py:625 `port = int(os.environ.get("PORT", "8765"))` is the repo's only PORT consumer. `git grep "env:PORT"` over tracked files returns exactly four hits: README.md:22, CONTRIBUTING.md:46, docs/OPERATOR_RUNBOOK.md:11, and the launcher line — nothing in .github/, scripts/tests/, .claude/skills/, or Backup-BananaLab.ps1 injects -Port from the environment, and PowerShell param defaults never consult env vars. Attribution to the launcher is fair, not a strawman: README.md contains zero occurrences of "app.py" and line 22 sits directly beneath the two `.\Start-BananaLab.ps1` code lines; OPERATOR_RUNBOOK.md:11 precedes its manual fallback at :19. Undersold detail: a dot-invoked .ps1 shares the caller's process, so the assignment also persists in the operator's shell after exit, poisoning a later manual app.py run. CORRECTIONS: (1) Severity Medium is inflated to Low — "silently does nothing" overstates it, since :142 prints `Open: http://127.0.0.1:8765/` and :148 `Start-Process $url` opens that same URL, so the operator is never misdirected, and the one scenario motivating a custom port (8765 occupied) hard-fails at :135/:136 with the correct remedy named; this is a loopback-only single-owner dev launcher per docs/LOCAL_SHIP.md:6, with no data, security, or pipeline impact. (2) Repair stands, but their code-side suggestion is unsafe as written: editing only :151 to honour a pre-set PORT would leave :135 free-port-testing 8765 and :139 printing 8765 while Flask binds elsewhere — worse than the status quo. Any code fix must resolve $Port before :135; the low-risk repair is doc-side, scoping $env:PORT to the direct-app.py path in all three docs.

---

### U17 — automation_rules §6A documents an `alpha_matte.py --inset` mode that the CLI does not expose

- **Location:** `00_SYSTEM/automation_rules.md:109`
- **Lens:** doc-reality  |  **Category:** doc-mismatch
- **Severity:** Low  |  **Disposition:** Repair

**Evidence**

00_SYSTEM/automation_rules.md:107-109 describes the integration script as: "alpha_matte.py     -- chroma-key a ref into a true-alpha layer (border-connected flood fill; baked-ground-shadow stripper; --inset mode for card-style refs like Clever's set)". The capability exists only as a Python keyword parameter. 00_SYSTEM/scripts/integration/alpha_matte.py:99-100 `def extract(src: Path, dst: Path, threshold: float = COLOR_DIST_THRESHOLD, inset: int = 0) -> dict:` with :109-110 `if inset: img = img.crop((inset, inset, img.width - inset, img.height - inset))`. But the CLI at :145-151 is `def main(): ap = argparse.ArgumentParser(); ap.add_argument("src", type=Path); ap.add_argument("dst", type=Path); ap.add_argument("--threshold", type=float, default=COLOR_DIST_THRESHOLD); args = ap.parse_args(); report = extract(args.src, args.dst, args.threshold)` — no `--inset` argument is registered and `inset` is never forwarded, so it is always 0. `python alpha_matte.py ref.png out.png --inset 12` exits 2 with "unrecognized arguments". `git grep -- "--inset" -- "*.md"` returns only automation_rules.md:109.

**Rationale**

This is the operator-facing recipe for exactly the case the docstring at :101-107 says the default algorithm fails on — card-style refs where "the flood fill from the outer corners stops at the card outline and removes nothing (found in Cycle 29: 0.97 opaque)". An operator following §6A gets an argparse error, and the obvious workaround (drop the flag) silently produces a 0.97-opaque matte that then fails the downstream integration gate. Two-line fix in argparse, or correct the doc to say `inset` is import-only.

**Risk if this disposition is acted on and the analysis is wrong**

Adding the flag is additive and cannot change existing invocations, since `inset` already defaults to 0. Editing the doc instead loses a documented capability that the code genuinely implements.

**Skeptic's verdict**

Core claim independently confirmed, severity corrected down. VERIFIED: automation_rules.md:107-109 reads "alpha_matte.py -- chroma-key a ref into a true-alpha layer (border-connected flood fill; baked-ground-shadow stripper; --inset mode for card-style refs like Clever's set)". alpha_matte.py:99-100 `def extract(src: Path, dst: Path, threshold: float = COLOR_DIST_THRESHOLD, inset: int = 0) -> dict:` and :109-110 `if inset: img = img.crop((inset, inset, img.width - inset, img.height - inset))`. main() at :145-153 registers only src, dst, --threshold and calls `extract(args.src, args.dst, args.threshold)` — inset is never forwarded. I ran it: `alpha_matte.py: error: unrecognized arguments: --inset 95`, exit 2. The strongest available refutation fails: the same fenced block also lists `validate_issue.py --integration`, which IS a genuine flag (validate_issue.py:166 `if "--integration" in sys.argv:`), so `--x` in this block reliably means CLI flag, and an operator would type it. No missed reference: git grep "inset" over tracked files shows no .ps1, no .claude/skills/*, no .github/workflows, no test, and NO caller anywhere passes inset= — batch_matte.py:31 and tests/test_integration_pipeline.py:55 both call `extract(src, dst)` with the default. Other docs are accurate because they omit the dashes (CYCLE_LEDGER.md:1191 "a new `inset` mode in `alpha_matte.extract`"). Provenance confirms drift: commit 66cdb86 (Cycle 29) added the kwarg without touching the CLI, and commit 1c57ef0 ("Cycle 30: docs truth sweep") later introduced the `--inset` prose. SEVERITY CORRECTED Medium -> Low: their rationale overstates the consequence. Dropping the flag is not silent — main() prints `corners_fully_transparent: False` and `opaque_frac: 0.97` from the returned report (:130-141), the argparse error is self-describing, the working call form is documented in the function docstring at :101-107, and validate_integration.py:103-116 (KNOWN_REF_COLORS incl. minted_card_border_cyan / minted_card_fill_pink) plus find_flat_card_regions catch a pasted card downstream. Blast radius is one rarely-exercised card-format path (a single supporting-cast character), with no data corruption and a loud failure. DISPOSITION Repair retained and safe: either add `ap.add_argument("--inset", type=int, default=0)` and forward it (backward-compatible, default 0 preserves every existing caller and the pinned test expectations), or amend the doc line to say inset is import-only. Neither breaks anything.

---

## Refuted (do NOT act on these)

Recorded so a later pass does not re-raise them.

### `00_SYSTEM/scripts/new_issue.py:176` — Duplicate-issue-id detection (new_issue) and issue lookup (issue_workflow) scan different folder sets, so two folders can claim the same issue_id

Refuted on its load-bearing fact. The claim rests on "two briefs have no `Issue ID:` line at all, so the substring test cannot match them even when globbed." False for the only folder that mattered: 02_MONTHLY_ISSUES/2026-10_Issue_02/issue_brief.md begins b'\xef\xbb\xbfIssue ID: MZ-2026-10-' — a UTF-8 BOM followed by the exact line. The creation-side check is a SUBSTRING test (`f"Issue ID: {n['issue_id']}" in path.read_text(...)`), not line-anchored, so a leading BOM does not defeat it. Running that exact expression over the live tree matches all 7 globbed briefs including 2026-10_Issue_02 -> MZ-2026-10-02. Their stated exploit (POST issue_id MZ-2026-10-02 with edition_number 7) is therefore rejected at new_issue.py:183 `raise IssueCreationError("Issue ID already exists")`. Their detector evidently used the anchored `^Issue ID:` form from _read_issue_id (issue_workflow.py:78), which the BOM does break — but that path reads metadata.json first and never reaches the regex.

The other "invisible" folder is un-collidable, not a hole: 2026-07_Mango_Pier's id is MZ-2026-07-MANGO, which fails ISSUE_ID_RE (new_issue.py:19) so create_issue can never mint a colliding id, and fails _safe_issue_id (issue_workflow.py:45-49) so find_issue can never be asked for it.

Missed reference: the invariant is deliberate and test-pinned. character-bibles/_review_app/tests/test_issue_creation.py:61-67 (test_duplicate_id_and_edition_are_distinct) renames 2027-01_Issue_01 -> 2027-01_Issue_02 to break folder-name/NN correspondence exactly as they describe, then asserts create with edition_number=3 and the same id raises "Issue ID". .claude/skills/mz-new-issue/SKILL.md:22-23 documents it: "Studio aborts if the edition folder or issue ID already exists — that's your month-collision check." Because create_issue always writes `Issue ID: <id>` to the brief (:154), issue_id to metadata.json (:147-151), and names folders {period}_Issue_{NN} (:112), every pipeline-produced folder is visible to both readers. app.py:267-277 adds no guard and needs none.

Accurate but non-defective in their evidence: the two enumerators do differ (glob "*_Issue_*/issue_brief.md" vs iterdir + metadata-first _read_issue_id); _ISSUE_PATH_CACHE at issue_workflow.py:52,57-60,66 is real and sticky; folder_name (:112) and expected_prefix (:88) are quoted verbatim and correct.

Residual worth investigating, but NOT the claimed defect and not currently reachable: the two readers disagree on tolerance rather than folder set. _read_issue_id uses `^Issue ID:\s*(\S+)` and prefers metadata.json, while the create side demands the byte-exact substring in the brief — so a hand-edit adding a second space after the colon, or reworking the brief while metadata.json keeps the id, would open the gap. Briefs here do get hand-edited (2026-10_Issue_02 acquired a BOM). Separately, that same BOM already defeats _read_issue_id's brief fallback, masked only because metadata.json is present — note 2026-07_Issue_05 and 2026-08_Issue_06 have metadata.json with NO issue_id and depend entirely on the brief regex. Low severity latent divergence; the proposed Repair (call _read_issue_id over iterdir on the create side) is reasonable hardening but fixes no demonstrated live defect.

### `00_SYSTEM/scripts/validate_issue.py:176` — `validate_issue.py --integration` — a documented Gate A pre-check — needs numpy+scipy, which the operator setup path never installs

Code facts confirmed, central inference refuted. CONFIRMED: validate_issue.py:176-177 is verbatim as quoted ("sys.path.insert(0, str(SYSTEM / \"scripts\" / \"integration\"))" / "from validate_integration import run_gate  # noqa: E402"), unguarded; validate_integration.py:29-31 is verbatim ("import numpy as np" / "from PIL import Image" / "from scipy import ndimage"); the asymmetry vs. the guarded jsonschema import at :77-81 setting SCHEMA_CHECKS_SKIPPED is real; all five gate citations exist (qa_checklist.md:49, mz-art-run/SKILL.md:88, mz-package/SKILL.md:35, README.md:200, automation_rules.md:136); the path is reachable (45 tracked files under 02_MONTHLY_ISSUES/2026-09_Issue_02/generated_art/integration_preview/).

REFUTED — five independent grounds:

(1) MISSED REFERENCE, in a file they already cited. "The operator install path never installs numpy or scipy" is false. README.md:74: "pip install -r requirements-dev.txt  # Studio + validators + test suite" — the word "validators" is explicit. CONTRIBUTING.md:14 repeats it and :17 states "`requirements-dev.txt` is the single source of truth for dependencies, shared by CI and this guide." requirements-dev.txt:18-19 lists numpy and scipy, and its header (line 1-3) declares it covers "the pipeline validators/tooling". They cited README:200 (the command) but not README:74 (the install for it), 126 lines up the same file, and never cite CONTRIBUTING.md.

(2) WRONG INSTALL PATH. The three lists cited are the Studio Flask bootstrap, not a validator install. Start-BananaLab.ps1:4 ".SYNOPSIS  One-command local startup for The Banana Lab (MonkeyZoo Studio)"; its probe at :84 is `("flask", "PIL", "yaml", "jsonschema")`; it terminates at :153 with `& $pythonExe "app.py"`. start-banana-lab.sh:1 carries the same comment and :37 is `exec "$PYTHON" "$ROOT/character-bibles/_review_app/app.py"`. OPERATOR_RUNBOOK.md:14 labels its block "Manual fallback:" and :19 runs `character-bibles\_review_app\app.py`. Decisively: grep for "validate_issue" in docs/OPERATOR_RUNBOOK.md returns nothing — the runbook does not own this gate, so "an operator who follows the repo's own runbook" is never sent to this command.

(3) WRONG ENVIRONMENT. The venv is not where the gate runs. README:200 and OPERATOR_RUNBOOK:155/203/228 invoke pipeline scripts as bare `python 00_SYSTEM/scripts/...`; CLAUDE.md states "Python scripts in `00_SYSTEM/scripts/` run with system `python`". Neither launcher activates .venv into the operator's shell (both invoke $pythonExe/$PYTHON directly and exec app.py). Empirically on this machine: system python has numpy 2.3.5 / scipy 1.17.1, and `.venv/` does not exist at all.

(4) INVERTED FAILURE FRAMING. An uncaught ModuleNotFoundError exits non-zero printing "No module named 'numpy'" — the loud, self-diagnosing failure the report itself argues is correct. There is no false PASS and no silently-skipped canon gate. "It looks like a broken script, not a missing package" does not survive reading the actual exception text. Plain and --art runs need only stdlib (jsonschema is guarded), so nothing else is affected.

(5) THE "MISLABEL" IS INERT, AND THE PROPOSED FIX REGRESSES. requirements-dev.txt:9 marks the block "Grouping (informational only)"; lines 18-19 install numpy+scipy unconditionally regardless of the comment, so the comment cannot cause a missing package. Their preferred repair (b) — replacing all three lists with `pip install -r requirements-dev.txt` — would pull scipy, pytest, pytest-asyncio, anyio and ruff into a one-command Studio start, contradicting the launcher's deliberately narrow 4-module probe; repair (a) does the same to the Studio venv.

RESIDUAL (why Low, not Informational): docs/OPERATOR_RUNBOOK.md is self-contained about the Studio and never cross-references requirements-dev.txt, so a reader who only ever opens the runbook has no pointer to the declared source of truth. That is a one-line docs cross-reference at most. The located artifact, validate_issue.py:176, requires no change — Retain.

### `00_SYSTEM/scripts/integration/tests/test_integration_pipeline.py:23` — 22% of the test suite is behind `pytest.importorskip` while requirements-dev.txt declares zero version pins — a dependency install failure yields green CI

REFUTED as stated. I reproduced each failure mode empirically (fake package on PYTHONPATH raising ImportError, full suite run) rather than reasoning about it.

WHAT IS TRUE: the 12 cited modules do use pytest.importorskip at the cited lines; my AST count gives 135/610 test functions = 22.1% (their 133/608 is trivially close); requirements-dev.txt has zero specifiers and lines 5-7 are quoted verbatim; there is no tracked conftest.py; validate.yml does not surface skips.

REFUTATION 1 - the headline is false. "A dependency install failure yields green CI" is wrong twice over. (a) A real `pip install -r requirements-dev.txt` failure fails the CI step under GitHub Actions' `bash -e`; the job is red before pytest runs. Their own rationale concedes this ("fails loudly") after the claim asserts the opposite. (b) Even installed-but-unimportable is loud for Pillow: with a broken PIL the suite gives `!!! Interrupted: 14 errors during collection !!!` / `12 skipped, 12 warnings, 14 errors` / EXIT=2. Fourteen tracked modules import PIL unguarded at module level, e.g. `character-bibles/_review_app/tests/test_canon_catalog.py:6: from PIL import Image` and `character-bibles/_review_app/tests/test_release_workspace.py:4: from PIL import Image`. The finding missed these entirely.

REFUTATION 2 - magnitude inflated ~2.3x. PIL is the ONLY guard in 8 of the 12 modules (76 of the 135 counted tests), and PIL absence is red, not green. Measured silent cases: broken numpy -> `706 passed, 4 skipped`, EXIT=0; broken scipy -> `711 passed, 3 skipped`, EXIT=0. Real silent surface = 4 modules / 59 functions = 9.7% of 610, not 22%.

REFUTATION 3 - the proposed repair would break the repo. A root conftest.py that hard-fails on any unimportable requirements-dev entry converts a 10% silent gap into a 100% hard stop for any contributor lacking scipy - exactly the failure the guards exist to prevent. The comment at test_integration_pipeline.py:18-22 ("an uncaught collection error interrupts pytest for the ENTIRE repo") is factually CORRECT: I confirmed one collection error interrupts the session with zero tests run. The guards are a sound, documented design decision.

REFUTATION 4 - already self-healing. pytest 8.4.2 emits in exactly this scenario: "PytestDeprecationWarning: Module 'numpy' was found, but when imported by pytest it raised: ImportError(...) In pytest 9.1 this warning will become an error by default." pytest is unpinned, so CI adopts that automatically - the unpinned-deps fact the finding cites as aggravating is actually what closes the gap.

RESIDUAL (small, why Low not Informational): the summary line understates the loss - 59 test functions vanish but the human-scanned number reads "4 skipped". That does diverge from the repo's own convention at 00_SYSTEM/scripts/validate_issue.py:216-218 ("PASS - built-in checks only (jsonschema not installed: JSON Schema validation SKIPPED).") enforced by 00_SYSTEM/scripts/tests/test_validate_issue.py:279. If anything is ever done here it is that disclosure pattern, not a hard-fail conftest. Not worth a change today: trigger is unlikely, exposure is 10%, and pytest 9.1 resolves it. Disposition Retain - the importorskip guards should stay exactly as written.

---

## Not verified (low severity or Retain)

Raised by a lens but below the bar for spending a refutation pass. Treat as
unproven leads, not findings.

| Sev | Disposition | Location | Lead |
|---|---|---|---|
| Low | Investigate Further | `00_SYSTEM/scripts/integration/batch_matte.py` | Three integration tools reachable only from a historical dev log |
| Low | Retain | `00_SYSTEM/scripts/integration/edge_unify.py:1` | edge_unify.py is self-documented dead code — an evaluated-and-rejected pipeline stage |
| Low | Repair | `00_SYSTEM/scripts/genesis/genesis_specs.py` | Three genesis CLI tools are kept alive only by their own tests and are absent from the GENESIS runbook |
| Low | Investigate Further | `02_MONTHLY_ISSUES/2026-07_Mango_Pier/_build_plan.py` | 02_MONTHLY_ISSUES/2026-07_Mango_Pier/_build_plan.py is an unreferenced issue-local script outside every test root |
| Low | Consolidate | `00_SYSTEM/scripts/new_issue.py:83` | Page-count limits differ across the three implementations that accept one: 64 in intake, 64 in story setup, 32 in the plan schema |
| Low | Remove | `requirements-dev.txt:19` | `pytest-asyncio` and `anyio` are declared but never imported and cannot be reached — no async code exists in the repo |
| Low | Repair | `character-bibles/_review_app/app.py:15` | `werkzeug` is a direct import declared nowhere, relying on flask's transitive pin |
| Low | Repair | `scripts/rc_real_issue_run.py:68` | Undeclared `reportlab` silently downgrades the RC probe's PDF output with no log line |
| Low | Repair | `requirements-dev.txt:17` | No Pillow version floor declared, while the code requires Pillow ≥ 9.1 and Stage 8 is documented to run on a second, unmanaged Pillow |
| Low | Repair | `README.md:79-81` | README.md names the wrong mechanism as the bare-`pytest` guard, contradicting pytest.ini's own comment |
| Low | Consolidate | `.github/workflows/validate.yml:64` | Two different "required static files" lists in the same CI job — the inline workflow list has drifted two entries behind docs/verify_static_site.py, and the root-relative-path check runs against only the shorter one |
| Low | Repair | `CONTRIBUTING.md:70` | Documented git conventions (stage-gate commit messages, `issue-##` release tags) do not match repository history |
| Low | Repair | `docs/HOSTING_PLAN.md:75` | HOSTING_PLAN lists a health endpoint as Phase-1 work still required; /api/health already exists and is documented in CONTRIBUTING |
| Low | Repair | `docs/OPERATOR_RUNBOOK.md:70` | OPERATOR_RUNBOOK quotes `POST /art-prompts/variants`; the registered route is `/api/issues/<issue_id>/art-prompts/variants` |
| Low | Investigate Further | `.github/REPOSITORY_WORKFLOW.md:24` | REPOSITORY_WORKFLOW mandates a `.ai-handoff/` evidence package and an `APPROVED TO MERGE` gate with no presence in the repo or CI |
| Informational | Retain | `scripts/package_issue.py` | scripts/package_issue.py, rc_real_issue_run.py, workflow_engine.py and backup_production.py are all still wired in — do NOT remove |
| Informational | Retain | `character-bibles/_review_app/bible_store.py:14` | __all__ audit: no lying entries, but seven names are exported without any external consumer |
| Informational | Investigate Further | `ruff.toml:11` | ruff.toml claims its excludes mirror pytest.ini's norecursedirs; they do not |
| Informational | Retain | `.gitignore:16-19` | Heavy-binary policy is inconsistent between trees: .gitignore excludes packaged exports under 02_MONTHLY_ISSUES while GENESIS/release ships a 13 MB CBZ and 9.7 MB PDF in git |
| Informational | Repair | `character-bibles/_review_app/app.py:620` | MZ_STUDIO_DEBUG and MZ_STUDIO_LOG_DIR are read at runtime but documented in no operator doc |
| Informational | Repair | `CONTRIBUTING.md:49` | CONTRIBUTING describes the health probe as covering one data root; it probes three and reports "degraded", not "ok", when any is missing |
