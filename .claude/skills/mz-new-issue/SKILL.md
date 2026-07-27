---
name: mz-new-issue
description: Run the MonkeyZoo writing pipeline (Stages 1–5) for a new monthly issue — from a rough idea in 01_IDEAS_INBOX to a validated, generation-ready prompt pack. Use when the user drops a new issue idea, says "start the next issue", or asks for a brief/outline/script/prompt pack.
---

# MonkeyZoo: New Issue (Stages 1–5)

Turn a rough idea into a complete, canon-safe, generation-ready issue package.

## Pre-flight
1. Read `00_SYSTEM/monkeyzoo_master_bible.md` (canon hierarchy + hard rules).
2. Read `00_SYSTEM/continuity_ledger.md` — note the LAST issue's OPEN THREADS.
   The previous rear-cover teaser MUST be honored or explicitly deferred.
3. Read `00_SYSTEM/character_bible.md` (v1.1+): personalities are LOCKED;
   visual identity is hair-based; use each character's **Prompt descriptor**
   verbatim in art prompts.
4. If the script touches FusionZoo tech, pull facts from
   `00_SYSTEM/nft_fusion_reference.md` — never invent tech behavior.

## Steps
1. **Scaffold:** create the edition in MonkeyZoo Studio (guided intake; the
   positional `new_issue.py` CLI is retired). Studio aborts if the edition
   folder or issue ID already exists — that's your month-collision check.
2. **Stage 1 Intake** (`00_SYSTEM/agents/stage_01_intake.md`): idea →
   `issue_brief.md`. Never ask questions; infer and mark `(inferred)`.
   Map informal character names to canon leads (e.g. "Emo" → Moodz).
3. **Stage 2 Continuity** (`stage_02_continuity.md`): run all 7 checks,
   append `## Continuity Review` verdict to the brief, draft the ledger entry
   (marked DRAFT).
4. **Stage 3 Showrunner** (`stage_03_showrunner.md`): `issue_outline.md`.
   8 pages = hook / escalate ×2 / SPLASH peak / complicate / turn / land /
   door-to-next. One splash max. Endings land on choice, not victory.
5. **Stage 4 Script** (`stage_04_script.md`): `issue_script.md` +
   `page_panel_plan.json`. Voice lock: Ash ≤4 words; Scarline exactly one
   sentence per issue; Moodz short declaratives; NeonBlue slogan-shaped;
   Static fast bursts (danger-meter joke); TwoTone two-beat.
6. **Stage 5 Art Director** (`stage_05_art_director.md` + `prompt_rules.md`):
   `art_prompt_pack.json` + `cover_prompt.md`. Style lock phrase opens every
   prompt VERBATIM; base negative opens every negative. Compute real seeds
   (issue# ×10000 + page×100 + panel). Insert page-0 establishing plates for
   new locations.
7. **Validate:** `python 00_SYSTEM/scripts/validate_issue.py <folder>` must
   PASS (text-only identity warnings are expected until LoRAs exist).
8. Write release copy early while context is hot: `social_posts.md` (8
   sections), `metadata.json` (CHIP-0015 — copy the FlipThisComics collection
   block verbatim from the previous issue; leave TODO-IPFS markers).
9. Commit: `MZ-YYYY-MM-##: stages 1-5 + release copy`.

## Hard rules that bite
- Green glow is RESERVED for zombie/cracked-chamber content.
- Max 3 named characters per generated panel; groups compose in layers.
- No dialogue/caption/SFX text in art prompts — lettering applies text.
- Every new location/character/tech = ledger NEW LORE entry + world bible.
- Byte-exact values (sha256, IPFS CIDs, DID) come from disk commands only
  (`automation_rules.md` §6).
