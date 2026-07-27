# Character Integration Upgrade — Final Report (Rounds 1 + 2, 30 cycles)

Branch: `character-integration-upgrade-20260716` → [PR #29](https://github.com/FlipThisCrypto/MonkeyZoo-Production-Workflow-System/pull/29).
Round 1 = Cycles 1–10 (2026-07-16, ComfyUI offline). Round 2 = Cycles
11–31 (2026-07-16/17, ComfyUI restored, 20 more One Things requested and
delivered). Full per-cycle evidence: `CYCLE_LEDGER.md`.

**Score: 30 counted PASS cycles across both rounds** (Round 1: 10;
Round 2: 20 — Cycles 11–15, 17–31, with Cycle 16 recorded as an honest
HOLD that does not count). Every cycle has implementation + tests +
inspected evidence + rollback in its ledger entry.

## Executive Summary

Before this branch, a "character in a scene" was either a monolithic
one-prompt render or a literal minted NFT card pasted as an opaque
rectangle. The branch delivers a complete, tested, deterministic
character-integration pipeline: true-alpha extraction (including
card-format supporting-cast refs), bespoke text2img scene poses,
measured ground-plane calibration for all five Issue-02 environments,
depth-sorted multi-character staging, per-position relighting, ground-
adaptive contact shadows, surface-clipped reflections, plate-sampled
depth haze, behind-geometry occlusion, foreground weather — plus an
automated QA stack (plate-baselined pixel gate, plate-diff grounding
check, canon-palette identity drift detection, `validate_issue
--integration`, and a v1.1 human Gate A checklist section). Six Issue-02
panels spanning all five environments and seven characters are staged as
integration previews with before/after comparison sheets for the owner's
Gate A decision.

## What Round 2 added (over Round 1's foundation)

| Cycle | One Thing | Verdict |
|---|---|---|
| 11 | ComfyUI restored + verified (VRAM check + smoke render, reusable script) | PASS |
| 12 | Puddle/wet-surface reflections (surface-clipped, deterministic) | PASS |
| 13 | Bespoke freeze-pose for the POC — 9 renders, img2img identity-drift root-caused, **text2img recipe established**; satchel canon error fixed pre-generation | PASS |
| 14 | Multi-character staging (depth-sort, per-character lighting, gaze-aware blocking) | PASS |
| 15 | POC re-composited with the bespoke pose — **all 14 applicable acceptance criteria PASS**; baked-ground-shadow matte stripper added | PASS |
| 16 | Masked-ring img2img edge unification — **rejected with visual evidence** (cfg-1.0 hallucination; scipy iterations=0 pitfall found and fixed) | HOLD (not counted) |
| 17 | Horizon MEASURED from the plate's own lamps (205→330) + calibrate_check overlay tool | PASS |
| 18 | 4 plates calibrated via agent fan-out; 3 verifier agents died on a session limit so **all overlays re-verified by direct inspection**; light-color fallbacks fixed | PASS |
| 19 | Identity drift QA — calibrated on the real beige renders; v1 caught scoring drift=canon by its own negative control; limitation (not a classifier) measured and documented | PASS |
| 20 | Depth haze (plate-sampled color; zero effect at near field — validated renders untouched) | PASS |
| 21 | Behind-geometry occlusion (traced occluders; half-behind staging lesson) | PASS |
| 22 | Integration previews + before/after sheets staged into the issue workspace (never touches selected_panels) | PASS |
| 23 | First panel on an agent-calibrated plate (Transit Hub) + gate plate-baseline subtraction (two false-positive classes root-caused) | PASS |
| 24 | `validate_issue.py --integration` (factory's own validator gates staged previews) | PASS |
| 25 | Gate A "Integration" section in qa_checklist v1.1 + mz-package Stage 9 hook | PASS |
| 26 | School hallway panel + bright-regime fixes (ground-adaptive shadow opacity; depth-fair metric) | PASS |
| 27 | Storm street panel (3 characters, lamp-matched lighting) — **initial ledger entry falsely claimed gate PASS; corrected on the record** | PASS (after correction) |
| 28 | Plate-diff grounding check (replaces the confounded lateral metric; floating control fails correctly) + per-character grounding boosts | PASS |
| 29 | Relay junction panel + first supporting-cast character (Clever): card-format inset mattes, calib-to-character height factor (principled 2.25 → art-directed 3.2, both recorded) | PASS |
| 30 | Docs truth sweep (rules/skill/findings/project_direction) — self-caught a panel-count overclaim, corrected against disk | PASS |
| 31 | Ship: 6/6 panels pass the full `--integration` gate, 21/21 regression tests, report + PR + memory updated | PASS |

## Integrity notes (what went wrong and was said out loud)

- **Cycle 27's first ledger entry claimed a gate PASS that was actually a
  FAIL** — I wrote the entry before reading the output. An append-only
  CORRECTION was committed before any fix work, and the underlying
  failure became Cycle 28's honest diagnosis (three confounders in the
  old shadow metric).
- **Cycle 16 is a rejection, not a success**, and is excluded from the
  count per the loop's own rules.
- **Cycle 30 self-caught a "7 panels" overclaim** (actual: 6, verified by
  directory listing) before it shipped.
- 3 of 4 calibration verifier agents died on a session limit in Cycle 18;
  rather than counting unverified work, every overlay was re-verified
  directly and that substitution is recorded.

## Validation results (final state)

```
python 00_SYSTEM/scripts/validate_issue.py 2026-09_Issue_02 --integration
  6/6 staged previews pass the pixel gate (all plate-baselined)  -> PASS exit 0

python -m pytest 00_SYSTEM/scripts/integration/tests -q
  21 passed

Grounding gate: 11 anchors + 3 relay anchors across 6 panels -- all PASS
Floating negative control (plate vs itself): FAIL (correct)
Known-bad pasted-card image: FAIL (correct, still caught)
```

## Epilogue — full-issue integration (2026-07-17, after this report's 31 cycles)

Two owner directives followed the 31-cycle work above and are now done:

1. **Format change**: Issue 02 was rewritten from 24 panels to the new
   house standard — **16 pages, 96 panels, + 1-panel front cover + 1-panel
   back cover teasing Issue 03** (each locked beat decompressed into a
   4-panel acting sequence; original events/dialogue preserved verbatim in
   each sequence's core panel).
2. **Integrate everything**: **all 96 panels + both covers are now
   integrated and staged**, 96/96 passing `validate_issue --integration`.
   Built via a 14-agent-per-page workflow over a new `build_panel.py` CLI
   and a 137-layer pre-matted pose menu, with an independent adversarial
   QA agent per page — which caught a close-up matte-edge halo the pixel
   gate structurally can't see (fixed in `closeup.py`). Full flip-through:
   `generated_art/integration_preview/pages_preview/ISSUE_02_full_preview.png`.

Also this session: fixed the GitHub CI (`validate.yml` lacked numpy/scipy,
which broke the whole test suite's collection) — CI green, 225 passed.

## Owner decisions still open

1. **The Gate A promotion call**: the assembled preview pages + per-panel
   previews sit in `generated_art/integration_preview/` — decide whether
   these integrated panels replace the shipped draft composites (promotion
   into `selected_panels/` is human-only; nothing has been promoted).
2. Merge PR #29 (branch-protected main; CI green, MERGEABLE/CLEAN).

## Recommended next One Thing

**Bespoke ComfyUI portrait renders for the close-up panels.** Every panel
is integrated, but the ~23 close-ups use the deterministic head-crop
builder (`closeup.py`) rather than purpose-drawn portraits — the single
biggest remaining quality lift, and the pipeline (`gen_scene_pose.py` with
a portrait clause → matte → `build_panel.py closeup`) is already in place
to do it once GPU time is allotted.
