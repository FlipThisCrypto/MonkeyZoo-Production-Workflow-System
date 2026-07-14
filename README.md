# MonkeyZoo Production Workflow System

**Idea in → finished issue out.** A standardized monthly production system for
MonkeyZoo comics by Fiend Studios. Drop a rough idea in the inbox; the
pipeline turns it into a complete, canon-safe, QA'd, release-ready package.

Open source at
[FlipThisCrypto/MonkeyZoo-Production-Workflow-System](https://github.com/FlipThisCrypto/MonkeyZoo-Production-Workflow-System)
— see `LICENSE.pdf` (Flip This Comics Open Source License).

## Banana Lab Studio (local production UI)

The local writable production app lives at `character-bibles/_review_app/`.

```powershell
.\Start-BananaLab.ps1
```

Opens `http://127.0.0.1:8765`. GitHub Pages remains a public **read-only** preview.

| Doc | Contents |
|---|---|
| `docs/OPERATOR_RUNBOOK.md` | Stages, approvals, recovery, RC proof issue |
| `docs/ART_PROMPT_PACK_WORKSPACE.md` | Plan → schema-valid `art_prompt_pack.json` |
| `docs/ART_QUEUE_WORKSPACE.md` | Prompt export, import, preferred select |
| `docs/STORY_SCRIPT_WORKSPACE.md` | Outline/script variants |
| `docs/PAGE_PANEL_WORKSPACE.md` | Script → page plan |
| `docs/VISUAL_QA_WORKSPACE.md` | Evidence QA PASS/HOLD/FAIL |
| `docs/RELEASE_WORKSPACE.md` | Release approval, manifest, archive publish |
| `docs/BACKUPS.md` | Offline backup/restore |

```powershell
.\Backup-BananaLab.ps1
python scripts/rc_real_issue_run.py              # formal intake→published RC probe
python scripts/package_issue.py 2026-08_Issue_06 # CBZ/export helper (+ optional --assemble)
```

Studio workspaces now include Art Prompt Pack build/approve/promote inside **Art Queue**, and **Publish archive** on **Release**.

## Requirements

- **Writing/QA stages (1–5, 7, 9, 10):** a Claude agent (Claude Code) + the
  stage prompts in `00_SYSTEM/agents/`. Skills in `.claude/skills/` drive the
  whole pipeline.
- **Art stage (6):** [ComfyUI](https://github.com/comfyanonymous/ComfyUI) with
  Z-Image Turbo (`z_image_turbo_bf16.safetensors`, `qwen_3_4b.safetensors`
  text encoder, `ae.safetensors` VAE — all from Comfy-Org/z_image_turbo on
  Hugging Face). Works on NVIDIA natively or AMD via ZLUDA (this repo's
  recipes were calibrated on an RX 6800 through ZLUDA).
- **Layout stage (8):** Python 3 + Pillow (ComfyUI's embedded python works);
  Windows fonts referenced by `assemble_pages.py` (Comic Sans/Arial/Impact/
  Consolas) or substitute your own.
- **Optional:** Kohya SS for character LoRA training (20+ approved refs per
  character), Krita/CSP for print-final lettering polish.

## Claude skills (`.claude/skills/`)

| Skill | What it runs |
|---|---|
| `mz-new-issue` | Stages 1–5: idea → brief → outline → script → validated prompt pack |
| `mz-art-run` | Stages 6–7: Z-Image batch generation + adversarial Art QA (incl. ZLUDA hang recovery) |
| `mz-package` | Stages 8–10: lettered pages, PDFs/CBZ/covers, Final QA gate, release copy + CHIP-0015 metadata |
| `mz-char-refs` | Standardized character variant sets, img2img from the minted canon cards |

## What is NOT in the repo (by design)

Heavy generated art is gitignored and fully reproducible: every panel's
prompt, negative, seed, resolution, and engine settings live in each issue's
`art_prompt_pack.json` + `generation_log.md`. Tracked instead: QA-selected
panels, web layouts, social crops, covers, and every text/JSON artifact.
Rebuild exports with `assemble_pages.py` + `build_release.py`.

---

## The one-paragraph version

Everything flows from `00_SYSTEM/` (the source of truth: bibles, ledger,
schemas, rules, agent prompts, scripts). Each month a rough idea in
`01_IDEAS_INBOX/` is pushed through ten stages — intake, continuity check,
showrunning, scripting, art direction, ComfyUI generation, art QA, layout &
lettering, final QA, release — producing a full issue package in
`02_MONTHLY_ISSUES/`, updating the canon record, and archiving to
`05_RELEASE_ARCHIVE/`. Nothing becomes canon until it passes QA and is written
into the continuity ledger.

## Folder map

```
/MonkeyZoo_Comic_Factory
  /00_SYSTEM              ← source of truth. Read-only during production.
    monkeyzoo_master_bible.md   franchise overview + hard rules + canon hierarchy
    character_bible.md          the six leads + faction archetypes, full specs
    world_bible.md              Zoo City, FusionZoo tech rules, locations, factions
    visual_style_bible.md       style lock phrase, rendering/staging/lettering rules
    continuity_ledger.md        append-only record of everything that happened
    monthly_issue_template.md   all recurring file formats
    prompt_rules.md             mechanical prompt-assembly algorithm
    qa_checklist.md             Gate A (per panel) + Gate B (per issue)
    automation_rules.md         tool roles, automation levels, gates, git rules
    issue_brief_schema.json     ┐
    page_panel_plan_schema.json ├ machine-readable validation
    art_prompt_pack_schema.json ┘
    /agents                     stage_01…stage_10 prompt files (one per stage)
    /scripts                    new_issue.py · validate_issue.py · build_release.py
  /01_IDEAS_INBOX         ← you drop YYYY-MM-idea.md here. That's your whole job.
  /02_MONTHLY_ISSUES      ← one folder per issue, full working package
  /03_APPROVED_CANON      ← QA-approved reference images (characters/locations/…)
  /story-bibles           ← filed season plans and story-development bibles
  /04_REJECTED_OUTPUTS    ← rejected art/scripts/dialogue (kept for diagnosis)
  /05_RELEASE_ARCHIVE     ← immutable released issues, by year
```

## Current season and character references

The filed season plan for the active Emo Monkeys arc is:

`story-bibles/seasons/2026-emo-monkeys-the-signal-between-us/SEASON-BIBLE.md`

The production character/image index is:

`03_APPROVED_CANON/approved_characters/CHARACTER_IMAGE_INDEX.md`

Use that index when assembling prompt packs, LoRA/IPAdapter reference stacks,
or owner review pages. It marks the six Emo Monkey leads, guest characters,
generic faction references, and Patch's special issue-derived reference.

Patch note: Issue 05/06 production files identify `zombie.png (#1997 = Patch)`.
That reference is filed in the local Character Bible reference folder with
source-map notes. It is an issue-derived Patch reference, not permission to
turn every Zombie/Stayed image into Patch.

## Monthly workflow

| # | Stage | Agent file | In → Out |
|---|---|---|---|
| 0 | You | — | rough idea → `01_IDEAS_INBOX/YYYY-MM-idea.md`; run `scripts/new_issue.py YYYY-MM ## "Title"` |
| 1 | Intake | `agents/stage_01_intake.md` | idea → `issue_brief.md` |
| 2 | Continuity | `agents/stage_02_continuity.md` | brief + bibles → canon-safe brief + verdict |
| 3 | Showrunner | `agents/stage_03_showrunner.md` | brief → `issue_outline.md` (title, logline, arcs, page map, teaser) |
| 4 | Script | `agents/stage_04_script.md` | outline → `issue_script.md` + `page_panel_plan.json` |
| 5 | Art Director | `agents/stage_05_art_director.md` | script → `art_prompt_pack.json` + `cover_prompt.md` |
| 6 | Art Generation | `agents/stage_06_art_generation.md` | pack → ComfyUI → `generated_art/raw_panels/` |
| 7 | Art QA | `agents/stage_07_art_qa.md` | raw panels → `selected_panels/` + Art QA report |
| 8 | Layout & Lettering | `agents/stage_08_layout_lettering.md` | panels + script → lettered pages, all targets |
| 9 | Final QA | `agents/stage_09_final_qa.md` | package → RELEASE/HOLD + `final_export_checklist.md` |
| 10 | Release | `agents/stage_10_release.md` | package → `social_posts.md`, `metadata.json`, archive, git tag |

To run a stage with Claude: open the stage's agent file, give it the listed
inputs, save its outputs into the issue folder. Stages 1–5 and 7/9/10 are
Claude work; Stage 6 is ComfyUI; Stage 8 is layout tool + Claude for checks.
Gates between stages are defined in `automation_rules.md` §4 — a stage may not
start until the previous gate passes.

The local Character Bible review interface is used before script generation
when owner review is needed for names, trait approvals, visual references,
or continuity proposals. Generated story context must stay compact: selected
traits, visual requirements, role caps, cooldowns, and proposed updates only.
Do not paste full Character Bibles into script prompts.

## Scripts

```
python 00_SYSTEM/scripts/new_issue.py 2026-08 6 "Title"      # scaffold next issue
python 00_SYSTEM/scripts/validate_issue.py 2026-07_Issue_05  # schema + cross-checks
python 00_SYSTEM/scripts/validate_issue.py 2026-07_Issue_05 --art  # + panel files exist
python 00_SYSTEM/scripts/build_release.py 2026-07_Issue_05           # CBZ + export check
python 00_SYSTEM/scripts/build_release.py 2026-07_Issue_05 --archive # archive released issue
```

## Canon rules (the ten commandments — full text in master bible §6)

1. No redesigns without a redesign issue. 2. Core palettes never change.
3. The style lock phrase never changes. 4. New lore goes in the ledger.
5. Nothing generated is canon until QA passes. 6. The art model never invents
costumes/props/scars/features. 7. No one-off prompt language against the
visual bible. 8. Every panel references the character bible. 9. Every issue
updates the ledger. 10. Every package ships with sources, exports, prompts, QA.

## Consistency machinery (why the art stays on-model)

- **Style lock phrase** (visual_style_bible §1) opens every prompt, verbatim.
- **Identity stack** per character: LoRA → IPAdapter with approved refs →
  text-only (flagged). Recurring characters are never text-prompt-only.
- **Base seeds** per character for close-ups; deterministic per-panel seeds
  otherwise (prompt_rules §5) — reruns are reproducible.
- **Establishing plates**: first shot of each location is approved, then
  referenced by all later panels in that location.
- **Approved canon folders** feed IPAdapter and LoRA training (Kohya SS,
  trigger conditions in automation_rules §1).

## Growing the factory

The machine-readable plan + pack files are the expansion surface: daily strips
(reuse panels + new dialogue), short-form video (pan/zoom over upscaled
panels), character cards (card-mode renders + bible stats), NFT metadata
(CHIP-0015 generated from metadata.json), animated shorts (pose refs +
ControlNet sequences). Never fork the bibles for a spin-off — extend them.

## Sample issue

`02_MONTHLY_ISSUES/2026-07_Issue_05/` — *The Ones Who Stayed* — is a complete
worked example produced by running the whole pipeline on the idea in
`01_IDEAS_INBOX/2026-07-idea.md`. It honors Edition 4's rear-cover teaser
(Zombie Monkey, "Not everyone walks away"). Stages 6–8 outputs are specified
(prompt pack, seeds, workflows) but images aren't generated yet — that's the
ComfyUI session; everything it needs is in the pack.
