# MonkeyZoo Automation Rules
**Version:** 1.0

Who does what, and what may run without a human.

---

## 1. Tool Roles

| Tool | Role |
|---|---|
| Claude Fable 5 | Showrunner, pipeline architect, continuity manager, script writer, prompt-pack generator, automation planner, QA checklist generator (Stages 1–5, 7*, 9*, 10 — * = report writing; approval clicks stay human) |
| Claude Code | Create folders, run `scripts/*.py`, validate JSON, rename files, package exports, append ledger entries, git commits |
| ComfyUI | Panel/cover/reference/background generation, upscaling, inpainting; workflows saved per shot-type and reused |
| Kohya SS | Train/update character LoRAs (trigger: 20+ approved refs per character, or identity QA failure rate >30%) |
| ControlNet | openpose (poses), depth (staging), canny/lineart (layout matching) |
| IPAdapter | Character identity lock + style lock from approved refs |
| Krita / Photoshop / CSP / Affinity / GIMP | Cleanup, lettering, bubbles, panel edits, final page corrections |
| Python | `new_issue.py` (scaffold), `validate_issue.py` (schemas + completeness), `build_release.py` (CBZ/renames/archive staging) |
| Git | Version control of the whole factory; canon history; rollback |

## 2. Automation Levels

- **AUTO (no approval needed):** folder scaffolding, JSON validation, file
  renaming to conventions, CBZ packaging, checksum computation, archive
  copying, ledger APPEND (drafted by agent, committed by script).
- **DRAFT (agent produces, human approves):** briefs, outlines, scripts,
  prompt packs, covers, social posts, metadata, QA reports.
- **HUMAN-ONLY:** canon approval (moving anything into 03_APPROVED_CANON),
  panel approve/reject final click, RELEASE decision, minting/publishing,
  any edit to a LOCKED bible section, character redesigns.

## 3. File & Naming Conventions (scripts enforce)

- Issue folder: `YYYY-MM_Issue_##` · Issue ID: `MZ-YYYY-MM-##`
- Panel ID: `MZ-YYYY-MM-##_P<page 2-digit>_PANEL<2-digit>`
- Raw art: `<panel_id>_seed<seed>_v<n>.png` in `raw_panels/`
- Selected: `<panel_id>.png` in `selected_panels/` (exactly one per panel)
- Upscaled: `<panel_id>_print.png` · Edited: `<panel_id>_final.png`
- Exports: `MonkeyZoo_Issue_##_Print.pdf`, `_Web.pdf`, `_CBZ.zip`, `cover.png`

## 4. Pipeline Gates (a stage may not start until the previous gate passes)

```
G0 idea file exists            → Stage 1 Intake
G1 brief approved              → Stage 2 Continuity
G2 no unresolved conflicts     → Stage 3 Showrunner
G3 outline approved            → Stage 4 Script
G4 plan JSON validates         → Stage 5 Art Director
G5 pack JSON validates         → Stage 6 Generation (ComfyUI)
G6 batch complete              → Stage 7 Art QA
G7 every panel approved        → Stage 8 Layout & Lettering
G8 pages assembled             → Stage 9 Final QA
G9 RELEASE verdict             → Stage 10 Release + archive + git tag
```

## 5. Git Discipline

- Commit after every stage gate with message `MZ-YYYY-MM-##: <stage> done`.
- Tag releases `issue-##`. Bibles/ledger changes always in their own commit
  (`canon: <what changed>`), never mixed with issue files.
- Generated art is committed only from `selected_panels/` onward; `raw_panels/`
  is gitignored (bulk).

## 6. Byte-Exact Value Rule

Any byte-exact value written into a release file — sha256 hashes, IPFS CIDs,
the MonkeyZoo DID, seeds — must be produced by a disk/command read at the
moment of writing (`Get-FileHash`, reading the source file), NEVER transcribed
from conversation context or memory. Rationale + background: `tooling_pxpipe.md`
(context-compression tooling can silently confabulate hex). Stage 9 verifies
hashes by recomputation only.

## 7. Failure / Rollback Rules

- Schema validation failure → block gate, report exact field, never hand-fix
  JSON silently: fix the producing stage's output.
- Art QA failure rate >50% in a batch → stop generating; check identity stack
  (LoRA weight, refs loaded, ControlNet map) before burning more compute.
- Continuity conflict found after Stage 4 → return to Stage 2, do not patch
  dialogue locally.
- Anything canon-breaking discovered post-release → next issue addresses it or
  ledger records the erratum; never silently edit released files.
