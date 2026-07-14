# Banana Lab Operator Runbook

Local writable runtime for MonkeyZoo production. GitHub Pages is public **read-only**.

## Start

```powershell
.\Start-BananaLab.ps1
```

Opens `http://127.0.0.1:8765`.

Manual fallback:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install flask pillow pyyaml jsonschema
.\.venv\Scripts\python.exe character-bibles\_review_app\app.py
```

## Stage meanings

| Stage | Required evidence | Owner approval? |
|---|---|---|
| Intake | `issue_brief.md`, `metadata.json` | No |
| Canon Review | Characters resolve to Character Bibles | Yes |
| Outline | `issue_outline.md` | No |
| Script | `issue_script.md` | Yes |
| Page & Panel Plan | schema-valid `page_panel_plan.json` | No |
| Art Prompt Pack | schema-valid `art_prompt_pack.json` | No |
| Art Production | selected PNG per planned panel | Yes |
| QA | promoted `qa_report.md` with exact `VERDICT: PASS` | Yes |
| Release | cover, CHIP-0015 metadata, social, checklist, PDF, CBZ/ZIP | Yes |
| Published | `05_RELEASE_ARCHIVE/YYYY/Issue_NN/` exists | No |

Workflow never invents completion from a button alone. Advancement requires current artifacts and, where configured, hash-bound owner approval.

## Issue creation

Use Studio **Create New Issue** or `new_issue.create_issue` with:

- `issue_id` matching `MZ-YYYY-MM-NN`
- year/month matching the ID
- known primary character (and optional different guest)
- title without path-unsafe characters (`<>:"/\|?*`)

## Story / Script

1. Advance to **outline**.
2. Generate manual prompt package, import Markdown variant, approve, promote (`issue_outline.md`).
3. Advance to **script**.
4. Import script variant (requires current approved outline), approve, promote (`issue_script.md`).
5. Owner-approve the script workflow gate, then advance.

Promotion refuses silent overwrite of existing finals unless `replace=true`.

## Layout

1. Active stage must be `page_plan`.
2. Create plan variant from canonical script.
3. Approve (hash-bound to script).
4. Promote to `page_panel_plan.json`.

## Art Prompt Pack

1. Advance to `art_prompts`.
2. Create pack variant from the canonical page plan (`POST /art-prompts/variants`).
3. Approve the variant (bound to plan hash + pack hash).
4. Promote to `art_prompt_pack.json` (schema-validated, atomic, backup/rollback).

See `docs/ART_PROMPT_PACK_WORKSPACE.md`.

## Art queue

1. Advance to `art_production`.
2. Build queue (one item per panel).
3. Export panel prompt packages (manual provider).
4. Import PNG/JPEG/WebP attempts.
5. Select preferred attempt (transactional; rolls back on failure).

Selected path:

`generated_art/selected_panels/<panel_id>.png`

## Visual QA

PASS is blocked by:

- missing / invalid / duplicate panel art
- dimension mismatches across selected panels
- empty `characters` on any planned panel
- unmapped selected images
- missing `issue_id` or `title` in metadata
- missing cover prompt, continuity notes, or final checklist

Cover image absence is advisory at QA. Release owns the final cover blocker.

Finalize with `pass|hold|fail`, then promote to `qa_report.md`. Promoted PASS must include:

```text
Evidence hash: <64-hex>
VERDICT: PASS
```

**Critical:** do not edit `metadata.json`, cover prompt, checklist, selected panels, or cover images after QA PASS without creating a new QA review. Those files participate in the QA evidence hash and will stale release approval.

## Release

Blockers include:

- QA not exact current PASS
- no cover under `generated_art/**/*cover*.png`
- missing/empty PDF
- invalid or empty CBZ/ZIP
- CHIP-0015 metadata missing fields
- any `TODO` placeholder in metadata
- missing social copy / checklist / cover prompt

Approve release (evidence-bound), promote `release_hash_manifest.json`, owner-approve the release stage, then advance to **published**.

## Publication archive

Formal API (preferred):

```http
POST /api/issues/<issue_id>/release/publish-archive
{"replace": false}
```

Requires:

- active stage `release` or `published`
- current release approval
- promoted `release_hash_manifest.json`
- non-empty PDF and valid CBZ/ZIP in `exports/`

Copies verified artifacts into:

```text
05_RELEASE_ARCHIVE/YYYY/Issue_NN/
```

Git ignores `05_RELEASE_ARCHIVE/` by design. After archive publication, advance to **published** and confirm `publication_ready=true`.

Legacy CLI still available:

```powershell
python 00_SYSTEM/scripts/build_release.py 2026-09_Issue_01 --archive
```

## Backups

```powershell
.\Backup-BananaLab.ps1
```

See `docs/BACKUPS.md` for targets, cadence, restore, and security notes.

Protect outside Git:

- `02_MONTHLY_ISSUES/**/generated_art/selected_panels`
- `02_MONTHLY_ISSUES/**/exports` (gitignored PDFs/ZIP/CBZ)
- `05_RELEASE_ARCHIVE`
- `03_APPROVED_CANON` (especially untracked owner assets)
- workspace state folders: `.story-workspace`, `.layout-workspace`, `.art-prompt-workspace`, `.art-workspace`, `.qa-workspace`, `.release-workspace`
- `.workflow-status.json` and approvals

Git is not sufficient for untracked art and package binaries.

## Common errors

| Symptom | Likely cause |
|---|---|
| 400 title contains unsafe path characters | Colon or other path-illegal character in title |
| 409 stage mismatch / stage skipping | Advance only the active stage |
| Trusted writable local runtime required | Static Pages or capability probe failed; use local app |
| QA PASS blocked | Evidence blockers; fix art/metadata, new review |
| Canonical QA evidence is missing or stale | Files changed after QA promote; re-QA before release |
| Invalid CBZ or ZIP | Empty zip, truncated zip, or non-zip bytes |
| Published requires release archive evidence | Create `05_RELEASE_ARCHIVE/YYYY/Issue_NN` |

## Art procedure (manual-provider)

- Engine: operator-chosen (ComfyUI/Z-Image or external)
- Dimensions: keep selected panels uniform (QA rejects dimension mismatches)
- Naming: `generated_art/selected_panels/<panel_id>.png`
- Import via Art Queue; keep rejected attempts under art-workspace history
- Cover: `generated_art/covers/main_cover.png` (name must contain `cover`)
- Lettering: production lettering is still operator-owned; do not rely on model balloons

## PDF / CBZ procedure

- Place final PDF under `exports/*.pdf` (non-empty)
- Place CBZ or ZIP under `exports/*.zip` or `exports/*.cbz` that opens as ZIP with at least one member and passes `testzip()`
- Workflow release stage currently requires `*.pdf` and `*.zip` in exports (CBZ-only is not enough for the stage validator)
- Reading order: zip member names sorted/readable by target reader
- Visual check: cover first, then page order

## RC proof issue

`MZ-2026-09-01` (`02_MONTHLY_ISSUES/2026-09_Issue_01`) completed intake through published archive via `scripts/rc_real_issue_run.py`.

See `02_MONTHLY_ISSUES/2026-09_Issue_01/RC_RUN_REPORT.md` for chronology and operator notes.

Replay (destructive if folder exists):

```powershell
# Remove prior RC folder only if you intend to rebuild it.
# Remove-Item -Recurse -Force 02_MONTHLY_ISSUES\2026-09_Issue_01
python scripts/rc_real_issue_run.py
```

The RC driver now uses the Art Prompt Pack workspace and `publish_archive` instead of free-form pack writes or ad-hoc archive copies.
