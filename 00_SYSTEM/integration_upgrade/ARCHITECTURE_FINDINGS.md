# Character Integration — Baseline Architecture Findings (2026-07-16)

Repo-evidence diagnosis before any changes in this track. See
`CYCLE_LEDGER.md` for what was built in response.

## What's real vs. aspirational

| Capability | Status |
|---|---|
| Single monolithic panel generation (bg+character in one prompt) | **Real** — `run_art_batch.py`, one ComfyUI graph per panel, no img2img/inpaint/ControlNet nodes despite `controlnet` fields existing in the JSON schema (always `{"required": false, "type": "none"}` in every issue pack) |
| Card-cutout paste compositing | **Real** — `compose()` in `compose_issue01_draft_panels.py` / `drive_issue_02_pipeline.py`: pastes each character's whole 220×220 opaque square ref onto a darkened background plate in a fixed row near the bottom, framed with a solid color box. Self-labeled `"DRAFT COMPOSITE"` in its own output. This is what actually ships in Issue 01/02 `selected_panels/`. |
| ControlNet / OpenPose / depth | **Not implemented** — doc-only intention in `automation_rules.md` and agent stage docs |
| Alpha transparency on character refs | **Not implemented** until Cycle 1 of this track |
| Perspective/scale-to-depth placement | **Not implemented** — fixed-position equal-size row |
| Contact shadows / relighting | **Not implemented** anywhere (zero repo hits before this track) |
| Integration-aware QA | **Not implemented** — `validate_issue.py` and `qa_checklist.md` check schema/identity/anatomy/style/readability only; nothing about scale, shadow, perspective |
| Character identity | Text description (hair + card color) + optional untrained IPAdapter refs. LoRA training hasn't run yet despite refs being "LoRA-ready." |

## Proof-of-concept target

`MZ-2026-09-02_P01_PANEL01` — Zoo City Streets, single character (Static,
MZ-CHAR-003), action "freezes on a sidewalk as a transit board clicks
off-rhythm," wet pavement / neon reflections / night rain per world bible.
Matches the brief's requested POC shape (single character, strong ground
plane + rain + neon).

## Infra constraint

ComfyUI (127.0.0.1:8188) is down as of this session and has a documented
hang history on this rig (see `pxpipe-token-proxy` memory and Issue 06
generation log). Cycles in this track are sequenced to not depend on new
GPU generation where deterministic PIL/numpy/scipy compositing can solve
the same problem against already-approved reference art.


## Status update (2026-07-17, after Cycles 11-30)

The "what needs building" table above described the 2026-07-16 baseline.
Current state:

| Capability | Status now |
|---|---|
| True-alpha character layers | **Built** — incl. card-format refs (inset mode) and baked-shadow stripping; 7 characters in the layer library |
| Bespoke scene poses | **Built** — text2img recipe (img2img rejected with measured identity-drift evidence) |
| Ground-plane placement | **Built** — 5 plates calibrated with measured horizons; character-height factor for odd calib objects |
| Contact shadows | **Built** — ground-adaptive opacity, per-character boost overrides |
| Reflections | **Built** — per declared surface (soft gloss vs hard puddle) |
| Relight / haze | **Built** — key/fill per position; plate-sampled depth haze |
| Geometry occlusion | **Built** — traced solid occluders (behind-object placement) |
| Multi-character staging | **Built** — depth-sorted, per-character lighting, gaze-aware blocking |
| Edge unification (img2img ring) | **Rejected with evidence** (Cycle 16) — engine hallucinates at cfg 1.0 |
| Integration QA | **Built** — pixel gate (plate-baselined colors/overlays + plate-diff grounding), layer identity check, `validate_issue --integration`, Gate A checklist v1.1 |
| Integrated panels staged | 6 of Issue 02's 24 (P01_P01, P01_P02, P02_P01, P02_P03, P06_P02, P07_P02) with before/after sheets |
