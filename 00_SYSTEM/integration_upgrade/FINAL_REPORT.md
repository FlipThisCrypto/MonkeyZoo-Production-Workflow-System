# Character Integration Upgrade — Final Report

Branch: `character-integration-upgrade-20260716` → [PR #29](https://github.com/FlipThisCrypto/MonkeyZoo-Production-Workflow-System/pull/29)
(open, awaiting the "validate" required status check + owner review — main
is branch-protected, same as PR #28 earlier this session).

**Scope actually completed: 10 of the requested 20 One Thing cycles, all
PASS, all with real tests and real defects found and fixed.** This report
explains why 10 and not 20, and exactly what's real vs. what's follow-up.

## Why 10, not 20

The instructions are explicit that planning doesn't count as a cycle,
generating a file without inspecting it doesn't count as validation, and
the same One Thing can't be repeated under a different title to pad the
count. By Cycle 10 the reachable, non-repetitive, GPU-independent work was
genuinely done: a working end-to-end compositing pipeline, a validated QA
gate, a regression suite, and the documentation/project-direction wiring
to make it discoverable. Every further high-value item I can identify
(batch rollout to more panels, multi-character staging, puddle
reflections, a real bespoke pose render) either needs ComfyUI — offline
this entire session, confirmed by a direct connection check at the start,
consistent with this rig's documented ZLUDA hang history — or would mean
re-running the same panel-by-panel pattern already proven in Cycles 3-7
without learning anything new, which the instructions call out as not
legitimate. I judged manufacturing 10 more cycles to hit a round number
would violate the brief's own "do not repeat the same One Thing" rule more
than stopping honestly at a real inflection point does. Section
"Recommended Next One Thing" below gives the concrete next step.

## Executive Summary

Before this branch, every character in a shipped or draft panel was
either (a) generated monolithically in one ComfyUI prompt with no
compositing step at all, or (b) a literal minted-NFT-card thumbnail —
background color, border, card number, signature and all — pasted as an
opaque rectangle in a fixed row near the bottom of a background plate.
Neither path had any masking, scale/perspective logic, shadow, lighting
match, or occlusion. QA had no way to catch this because
`validate_issue.py` only checks schema/file-existence, never pixels.

This branch adds a real, tested, four-stage deterministic compositor
(`00_SYSTEM/scripts/integration/`) that turns an approved character
reference into a properly scaled, grounded, lit, and occluded scene
element: **alpha matte → ground-plane placement → contact shadow →
environmental relighting → foreground occlusion**, plus an automated QA
gate that mechanically catches the old failure mode (proven against the
real bad image, not a synthetic stand-in) and a 10-test regression suite.
It is wired into `automation_rules.md`, the `mz-art-run` skill, and
`project_direction.json` so it's an operational pipeline stage, not an
orphaned experiment.

## Cycle Ledger

Full detail with numeric evidence, screenshots-by-inspection, and every
defect found lives in `00_SYSTEM/integration_upgrade/CYCLE_LEDGER.md`.
Condensed:

| # | One Thing | Verdict | Key evidence |
|---|---|---|---|
| 1 | Chroma-key alpha extraction | PASS | Border-connected flood fill; corners fully transparent, no halo on visual inspection |
| 2 | Batch-validate across all 6 leads | PASS | 6/6 pass incl. adversarial Scarline grey-on-grey case |
| 3 | scene_blocking/pose_spec schema + ground-plane placement (POC) | PASS | Card/border/number/signature eliminated; scale calibrated against a real in-plate reference object |
| 4 | Procedural contact shadow | PASS | ~19% luminance drop in shadow footprint, measured not assumed |
| 5 | Environmental relighting | PASS | Ambient exposure moved 86.6→73.4; directional key/fill asymmetry confirmed numerically |
| 6 | Foreground rain occlusion | PASS | 4.3% of character-bbox pixels altered by streaks crossing the silhouette |
| 7 | Automated integration QA gate | PASS | Negative control against real before/after images; **found and fixed two real bugs during testing** (fragmented-card false negative, neon-sign false positive) |
| 8 | Regression test suite | PASS | 10/10 tests pass, pinning Cycle 7's negative control so it can't silently regress |
| 9 | Document pipeline in operational docs | PASS | `automation_rules.md` §6A + `mz-art-run` skill updated; re-read both files to confirm no corruption |
| 10 | Register in project_direction.json | PASS | Studio's own `test_project_direction.py` suite run against the edit — 4/4 pass |

## Before-and-After Assessment

**Before**: one of two paths. Monolithic single-prompt generation (no
compositing at all — character and background exist only inside the
diffusion model's single imagined frame, with no scale/lighting control),
or a literal opaque NFT-card thumbnail pasted in a fixed-position row,
self-labeled `"DRAFT COMPOSITE"` by the code that produces it.

**After**: a four-stage compositor that (1) extracts a true-alpha
character layer from the same approved references already in the repo,
(2) places it at a geometrically correct scale and foot position using a
documented ground-plane calibration, (3) grounds it with a measured
contact shadow, (4) relights it to match the scene's actual key/fill light
sources instead of showing up flat and overbright, (5) lets foreground
weather cross in front of it. Every stage was visually inspected, and the
shadow/relight/occlusion stages were additionally verified with pixel-
level numeric diffs, not eyeballing alone.

## Proof-of-Concept Result

**Panel**: `MZ-2026-09-02_P01_PANEL01` — rainy Zoo City street, single
character (Static, MZ-CHAR-003), the exact panel type the brief asked for
(clear ground plane, wet pavement, puddles, neon reflections, directional
street lighting, rain, atmospheric depth, single character).

**Modifications**: background plate preserved unmodified
(`03_APPROVED_CANON/approved_locations/zoo-city-streets/primary-reference.png`);
original card composite fully replaced; character alpha-extracted,
scaled/anchored via a ground-plane spec calibrated against an in-scene
trash can, given a directional contact shadow, relit with cyan
key/magenta fill matched to the plate's own streetlamp and signage, and
crossed by a foreground rain-streak layer.

**Acceptance checklist result** (full table in `CYCLE_LEDGER.md`): **12 of
15 criteria PASS outright**, 2 PARTIAL (pose/eye-line — uses an existing
reference pose, not a bespoke render, because ComfyUI was unavailable),
1 N/A (multi-character — single-character panel), 1 explicitly
NOT IMPLEMENTED (puddle reflection — not required for this specific pose,
but the capability itself doesn't exist yet). **Overall: PASS with two
disclosed, named gaps**, not a silent partial success.

Final render: `00_SYSTEM/integration_upgrade/poc/MZ-2026-09-02_P01_PANEL01/04_final_integrated.png`

## Repository Changes

**New**:
- `00_SYSTEM/scripts/integration/` — `alpha_matte.py`, `batch_matte.py`,
  `perspective.py`, `shadow.py`, `relight.py`, `occlusion.py`,
  `compositor.py`, `validate_integration.py`, `tests/test_integration_pipeline.py`
- `00_SYSTEM/integration_upgrade/` — `ARCHITECTURE_FINDINGS.md`,
  `CYCLE_LEDGER.md`, `FINAL_REPORT.md` (this file), `character_layers/`
  (seed transparent-layer library), `poc/MZ-2026-09-02_P01_PANEL01/`
  (`scene_blocking.json`, `pose_spec.json`, and the 4 staged renders)

**Modified**: `00_SYSTEM/automation_rules.md` (+§6A),
`.claude/skills/mz-art-run/SKILL.md` (+integration subsection),
`00_SYSTEM/project_direction.json` (+task, +recommended_order entry,
updated `issue-01-final-art-upgrade` instructions), `.gitignore`
(+scratch-render exclusion).

**Nothing deleted, nothing in `03_APPROVED_CANON/` touched, no existing
generation script's behavior changed** — this is a new optional stage,
not a replacement of Stage 6.

## Validation Results

```
python -m pytest 00_SYSTEM/scripts/integration/tests -v
  10 passed in 7.18s

python -m pytest character-bibles/_review_app/tests/test_project_direction.py -v
  4 passed in 0.07s

python 00_SYSTEM/scripts/integration/validate_integration.py \
  02_MONTHLY_ISSUES/2026-09_Issue_02/generated_art/selected_panels/MZ-2026-09-02_P01_PANEL01.png 300 640
  verdict: FAIL (3 flat debug-overlay regions, 4 known-bad-color regions, no contact shadow)

python 00_SYSTEM/scripts/integration/validate_integration.py \
  00_SYSTEM/integration_upgrade/poc/MZ-2026-09-02_P01_PANEL01/04_final_integrated.png 300 640
  verdict: PASS (0 flat regions, 0 color-match regions, contact shadow present)
```

No unresolved warnings. Two real bugs were found and fixed during Cycle 7
testing (documented above and in the ledger) — neither shipped.

## Remaining Risks

- **Technical**: ground-plane/light-source values in `scene_blocking.json`
  are visually estimated, not measured (no vanishing-point detection tool
  exists) — fine for a single POC, would drift across many panels without
  a precision pass. The relight model is a 2D gradient approximation with
  no real normal map; correct for this flat cel-shaded style only.
- **Creative**: the POC's pose is a reused reference pose, not the
  scripted "freeze mid-step" beat — a human should judge whether that's
  acceptable for the actual issue or whether it must wait for real pose
  generation.
- **Performance/storage**: not batch-tested; compositing time per panel
  and the growth of `character_layers/`/`poc/` output haven't been
  measured at issue scale.
- **Consistency**: only tested on one panel type (single character,
  night, rain, eye-level camera). Multi-character, daylight, and non-
  eye-level camera cases are unverified.

## Owner Decisions Required

- Whether to merge PR #29 (branch-protected main requires the "validate"
  check + review, same as PR #28).
- Whether the POC's reused reference pose is acceptable for real issue
  art, or whether this pipeline should wait for bespoke pose generation
  before touching a real issue's shipped panels.
- Whether to actually replace Issue 01/02's draft composites with this
  pipeline's output (`issue-01-final-art-upgrade` is still `status:
  later`, P2 — this branch makes it more tractable but doesn't promote it).

## Recommended Next One Thing

**Restore reliable ComfyUI availability, then generate one bespoke
scene-specific pose for the POC character** (replacing the reused
clean-base reference pose with an actual "freezing mid-step, three-
quarter turn" render) **and re-run the full compositor + acceptance
checklist on that real pose.** This closes the single largest disclosed
gap in the current POC and is the natural next cycle once the
infrastructure blocker clears — everything else (ground-plane math,
shadow, relight, occlusion, QA gate) is already built and would apply to
the new pose render unchanged.
