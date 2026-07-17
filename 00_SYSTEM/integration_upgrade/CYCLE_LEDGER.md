# Character Integration Upgrade — Cycle Ledger

Branch: `character-integration-upgrade-20260716`. Goal: characters look
illustrated into scenes (pose, scale, ground contact, lighting, occlusion)
instead of pasted as flat NFT-card cutouts. See
`00_SYSTEM/integration_upgrade/ARCHITECTURE_FINDINGS.md` for the baseline
diagnosis this ledger works against.

Constraint discovered before Cycle 1: ComfyUI (127.0.0.1:8188) is not
running on this rig and has a history of ZLUDA hangs on this machine
(per `pxpipe`/generation-log lessons). Cycles are sequenced to front-load
everything achievable with deterministic PIL/numpy/scipy tooling against
*existing* approved art, and only reach for new GPU generation once/if the
server is confirmed stable — so the loop isn't blocked end-to-end by one
piece of infra.

---

## Cycle 1 — Chroma-key alpha extraction tool for character refs

**Selected because**: every downstream integration capability (masking,
scale placement, shadows, occlusion) requires a transparent character
layer, and none exists anywhere in the repo (confirmed by architecture
scan — `gen_char_refs.py` only ever emits opaque PNGs on a flat solid
background). This is the single narrowest unblock for the whole track.

**Scoped for one cycle**: yes — one script, one algorithm, testable on a
single reference image with a numeric+visual pass/fail.

**Files inspected**: `00_SYSTEM/scripts/gen_char_refs.py` (confirmed solid
per-character backdrop colors), sample ref
`03_APPROVED_CANON/approved_characters/static/static_00_clean_base.png`
(pixel-sampled: backdrop ~[221,69,128], std ≈1 — diffusion noise, not a
flat exact color, so a naive exact-match key would fail).

**Files created**:
- `00_SYSTEM/scripts/integration/alpha_matte.py` — border-connected
  flood-fill chroma-key (scipy.ndimage.label, keeps only background
  components touching the image border, so an interior patch that happens
  to share the backdrop hue is never clipped), gaussian-feathered alpha
  edge, and a 2px edge-band defringe (unmixes backdrop-color bleed out of
  the RGB channels using the alpha as the unmix weight).

**Test**: ran on `static_00_clean_base.png` (880×1184).
```
backdrop_color_est: [220.0, 71.0, 129.0]
transparent_frac: 0.645
opaque_frac: 0.3302
edge_frac: 0.0248
corner_alpha: [0, 0, 0, 0]
corners_fully_transparent: True
```

**Visual inspection**: composited the output over solid green and dark
test backgrounds and inspected the PNG directly (not just the numeric
report). No magenta/pink halo ring at the silhouette edge; the character's
own pink pouch-lining detail (interior, never touches the border) is
correctly preserved rather than keyed out — confirms the border-connected
flood fill is doing the right thing instead of a global-threshold false
positive.

**Defects found during testing**: none on this image. Known limitation
recorded for Cycle 2: threshold/feather constants were tuned on one image
and need validation across a few more characters/poses before treating the
tool as generally reliable.

**Verdict**: **PASS**. Rollback: purely additive new file, no existing
asset touched; safe to delete the module without side effects.

---

## Cycle 2 — Batch-validate alpha matte across all 6 leads + build a transparent layer library

**Selected because**: Cycle 1 proved the algorithm on one image; the six
leads use six different backdrop colors (orange/purple/hot-pink/teal/
spring-green/light-grey per `gen_char_refs.py`), and Scarline's own fur is
light-grey — the single hardest case for a color-distance key (backdrop
color nearly matches a real character color). Needed to know if the tool
generalizes before anything downstream depends on it.

**Scoped for one cycle**: yes.

**Files created**: `00_SYSTEM/scripts/integration/batch_matte.py` (runs
`alpha_matte.extract` across a sample ref per character, verdicts PASS
only if all corners are transparent AND opaque fraction is in a plausible
15–60% silhouette range) and
`00_SYSTEM/integration_upgrade/character_layers/<char>/*.png` (the
resulting transparent layers — a small seed library, not a full batch of
all refs yet).

**Test**: ran across Moodz, TwoTone, Static, Ash, NeonBlue, Scarline
primary refs — **6/6 PASS** (all corners fully transparent, opaque
fractions 0.31–0.36, tight and consistent).

**Visual inspection**: composited Scarline and Ash over a dark test
background and inspected the PNGs directly. Scarline (light-grey backdrop
+ light-grey fur, the adversarial case) came through clean — fur
preserved, backdrop gone, no halo. This is direct evidence the
border-connected flood-fill approach (not a naive global threshold) is
doing real work, not just getting lucky on easy cases.

**Defects found**: none. Algorithm confirmed to generalize without
per-character tuning.

**Verdict**: **PASS**.

---

## Cycle 3 — scene_blocking/pose_spec schema + ground-plane geometry placement (POC)

**Selected because**: with transparent layers in hand, the next blocker is
*where and how big* to place a character so it isn't floating/mis-scaled —
the literal #1 symptom in the brief (NFT card floating in front of the
background, screenshotted as the "before" evidence below). Chose the
brief's own POC target panel, `MZ-2026-09-02_P01_PANEL01` (rainy Zoo City
street, single character Static) — confirmed via `art_prompt_pack.json`
this is exactly the panel matching the brief's description.

**Before (baseline evidence)**: inspected the current shipped image,
`generated_art/selected_panels/MZ-2026-09-02_P01_PANEL01.png` — it is
literally Static's minted NFT card (#1199, magenta card background, blue
border, "MonkeyZoo" signature) pasted in a small framed box near the
bottom of the plate, with a debug caption strip overlay. This is the exact
failure mode described in the brief, now captured as before/after evidence
rather than taken on faith.

**Files inspected**: `art_prompt_pack.json` (panel's pose/environment/
lighting text), `03_APPROVED_CANON/approved_locations/zoo-city-streets/
primary-reference.png` (the clean 1280×720 plate, no card/no caption —
confirmed the real background asset already exists and is high quality;
the problem is purely how the character gets added to it).

**Files created**:
- `00_SYSTEM/scripts/integration/perspective.py` — single-point
  ground-plane height-line scaling (`scale(y_foot) = calib_height_px *
  (y_foot - horizon_y) / (calib_y - horizon_y)`), the standard matte-
  painting technique for consistent character scale vs. depth.
- `00_SYSTEM/integration_upgrade/poc/MZ-2026-09-02_P01_PANEL01/
  scene_blocking.json` — horizon/calibration (against the visible trash
  can, chosen over the doorway because its scale is closer to Static's
  chibi proportions) and three light sources (streetlamp key, magenta
  sign fill, green sign fill) read off the plate. Documents explicitly
  that these are visually-estimated art-direction values, not
  camera-calibrated measurements — no vanishing-point detection tool
  exists in this repo.
- `00_SYSTEM/integration_upgrade/poc/MZ-2026-09-02_P01_PANEL01/
  pose_spec.json` — full acting-direction spec (orientation, eye target,
  stance, hands, ground contact, lighting assignment, occlusion plan) per
  the brief's character-instance schema, adapted to this scene. Honestly
  flags a real limitation: ComfyUI is offline this session, so this uses
  Static's existing clean-base reference pose rather than a bespoke
  freeze-mid-step render — recorded as follow-up work, not hidden.
- `00_SYSTEM/scripts/integration/compositor.py` — `place_character()`:
  crops the character layer to its opaque bbox, scales it to the ground
  plane's computed height at the foot anchor, and alpha-composites it so
  the bbox's bottom-center lands exactly on the anchor pixel.

**Test**: ran `compositor.py` on the POC panel — target height 106.8px at
foot anchor (300, 640), scale factor 0.1211, output saved to
`01_geometry_placement.png`.

**Visual inspection**: opened the output directly. Card/border/number/
signature are completely gone (replaced by the real alpha layer). Scale
reads correctly next to the trash can it was calibrated against. Feet land
at the intended pavement point. However — as expected, since this cycle is
geometry-only — the character still reads as pasted: too bright/saturated
against the dark moody plate, no contact shadow, no relighting. This is
the exact remaining gap the brief describes and is the explicit scope of
Cycles 4–5, not a defect in this cycle's own deliverable.

**Defects found**: none in the geometry math itself (anchor/scale both
verified correct by inspection). Noted limitation: horizon/calibration
values are estimated, not measured — acceptable for a POC, flagged for a
future precision pass if the technique is productionized.

**Verdict**: **PASS** (scoped to geometry only; integration is not yet
complete — continues in Cycles 4–5).

---

## Cycle 4 — Procedural contact shadow generator

**Selected because**: Cycle 3's own inspection notes named the exact next
gap — geometry alone still reads as pasted because nothing grounds the
character to the surface. "Missing cast shadows and contact shadows" is
also an explicit QA-gate failure condition in the brief.

**Scoped for one cycle**: yes.

**Files created**: `00_SYSTEM/scripts/integration/shadow.py` —
`draw_contact_shadow()`: a blurred, directionally-offset ellipse under the
foot anchor (flattened footprint, not a circle; offset driven by a
shadow-direction angle so it reads as cast light, not a generic drop
shadow). Wired into `compositor.py`: `place_character()` now takes a
`shadow_direction` string (matches the plain-English values already used
in `pose_spec.json`'s `lighting.shadow_direction`), draws the shadow on
the canvas *before* pasting the character so it sits correctly underneath.

**Test**: re-ran `compositor.py` on the POC panel — `contact_shadow_applied:
true`, output `02_geometry_plus_shadow.png`.

**Visual inspection**: cropped and 3×-upscaled the foot area and looked
directly at the pixels (not just the full-frame thumbnail, where a subtle
night-scene shadow is easy to miss) — a real soft dark patch is visible
under and slightly screen-left of his feet.

**Numeric verification** (not just eyeballing): sampled mean RGB luminance
in the shadow's actual bounding box, before vs. after —
`42.16 → 34.23` (a 7.93-point / ~19% darkening). Confirms the shadow is
real and not a no-op that happened to look plausible in a dark scene.

**Defects found**: none blocking. Noted limitation: opacity (0.42) was
tuned by eye for this one dark, low-contrast night scene — a bright
daylight panel would need a different default; flagged as a follow-up
tuning pass once more panel types are tested.

**Verdict**: **PASS**.

---

## Cycle 5 — Environmental relighting pass for character layer

**Selected because**: the geometry+shadow render (Cycle 4) still looked
too bright/flat compared to the moody dark plate — "Missing neon or
environmental light on the characters" is a named brief symptom and a
named QA-gate failure condition, and it's the last big visual gap before
the POC can plausibly pass the acceptance checklist.

**Scoped for one cycle**: yes.

**Files created**: `00_SYSTEM/scripts/integration/relight.py` —
`relight()`: (1) ambient exposure match (moves the character's own mean
brightness halfway toward the sampled scene-ambient brightness near its
foot position — halfway, not all the way, so it stays readable as a
foreground subject), (2) a directional key/fill color gradient across the
silhouette (screen-blend toward the key-light color on the key side,
multiply-blend toward the fill-light color on the fill side), (3) a thin
rim-light highlight on the alpha edge facing the key light. Explicitly
does not touch alpha or redraw linework — recolors existing opaque pixels
only, so identity/line-art stays canon-locked per `character_bible.md`.
Wired into `compositor.py`: `run()` now reads `scene_blocking.json`'s key/
fill light source positions, decides which side of the character is the
"key side" from their x-position relative to the foot anchor, and passes a
`relight_spec` into `place_character()`.

**Test**: re-ran `compositor.py` — `relit: true`, output
`03_geometry_shadow_relight.png`.

**Visual inspection**: cropped/upscaled the character again. Immediately
reads as belonging to the scene's low-key mood rather than a bright
flat-lit cutout; a cool cast is visible on the key-light side.

**Numeric verification**: sampled mean RGB in the character bbox,
before/after — overall luma `86.6 → 73.4` (moved toward the dark scene
ambient). Left (fill/magenta) half: G channel dropped 26% (consistent
with a magenta multiply-tint, which suppresses green). Right (key/cyan)
half: overall brightness dropped only 11% vs. the left's ~20%+ (consistent
with the screen-blend key tint partially offsetting the ambient
darkening). This is the intended asymmetric-lighting signature, not
measurement noise — confirms the directional logic is actually
discriminating sides, not just applying a flat filter.

**Defects found**: none blocking. Noted limitation: this is a 2D
gradient-based approximation, not real per-pixel normal-based lighting —
correct for this flat cel-shaded house style, but would need a different
approach (e.g. a hand-painted light-direction mask) if the art style ever
adds real form-shading.

**Verdict**: **PASS**.

---

## Cycle 6 — Foreground rain occlusion layer

**Selected because**: the brief explicitly calls out "Environmental
Occlusion" and lists rain-across-the-character as its first example, and
this is the last acceptance-checklist gap the POC pose_spec had already
flagged (`occlusion: ["rain layer in front of the character", ...]`) but
not yet implemented.

**Scoped for one cycle**: yes.

**Files created**: `00_SYSTEM/scripts/integration/occlusion.py` —
`add_foreground_rain()`: deterministic (fixed-seed) streak generator drawn
on a top layer over an expanded character bbox, angle matched to the
plate's own rain lean (visual estimate, same honesty caveat as the
ground-plane values — flagged, not measured). Wired into `compositor.py`
as the final stage, gated on the `pose_spec.json` occlusion list actually
requesting it (so panels that don't call for rain-in-front don't get it by
default).

**Test**: re-ran `compositor.py` — `foreground_rain_applied: true`, final
output `04_final_integrated.png`.

**Visual inspection**: cropped/upscaled the character region — rain
streaks are now visibly crossing his head and torso, reading as falling
between camera and character rather than only behind him.

**Numeric verification**: diffed the character-bbox region between the
pre-occlusion (`03_...`) and final (`04_...`) renders — 4.3% of pixels
inside the character's own bounding box changed by more than a
noise-level threshold, confirming streaks genuinely cross the silhouette
rather than only appearing in the surrounding background.

**Defects found**: none blocking.

**Verdict**: **PASS**. This closes the last acceptance-checklist gap
identified for the POC panel — see the acceptance-checklist run below.

---

### POC acceptance-checklist run — `MZ-2026-09-02_P01_PANEL01`, final render `04_final_integrated.png`

| # | Criterion | Result |
|---|---|---|
| 1 | No card background/border/number/signature | **PASS** — alpha layer has none |
| 2 | Pose expresses the scripted action | **PARTIAL** — orientation/placement match the beat, but this is Static's existing clean-base pose, not a bespoke freeze-mid-step render (no GPU available this session; documented in `pose_spec.json`'s `asset_limitation`) |
| 3 | Character identity remains canonical | **PASS** — no linework/alpha touched, only recolored via relight |
| 4 | Scale fits the environment | **PASS** — calibrated against the plate's own trash can |
| 5 | Perspective fits the camera | **PASS** for this single-figure, standing-on-flat-ground case; not yet tested against a non-eye-level camera |
| 6 | Believable ground contact | **PASS** — foot anchor + contact shadow |
| 7 | Lighting matches actual position | **PASS** — directional key/fill tint + exposure match, verified numerically |
| 8 | Plausible contact shadow | **PASS** — verified numerically (Cycle 4) |
| 9 | Reflections where required | **NOT IMPLEMENTED** — character stands beside, not in, the puddle per the pose spec, so no reflection was required for this specific pose; puddle-reflection compositing itself remains unbuilt |
| 10 | Environmental effects behind/in front | **PASS** — plate rain behind, new foreground rain layer in front |
| 11 | Eye lines/body direction support story | **PARTIAL** — same caveat as #2 |
| 12 | Multiple characters share one spatial system | **N/A** — single-character panel |
| 13 | Line treatment/color fit the environment | **PASS** — relight brings exposure/tint in line |
| 14 | Looks intentionally illustrated as one composition | **PASS** on direct visual inspection |
| 15 | Visually inspected, not just generated | **PASS** — every stage in this ledger was opened and looked at, several also numerically diffed |

**Overall POC verdict: PASS with two known, disclosed gaps** (bespoke pose
render blocked on ComfyUI being offline; puddle-reflection compositing not
yet built). Both are named as explicit follow-up work, not hidden.

---

## Cycle 7 — Automated integration QA gate script

**Selected because**: everything through Cycle 6 was verified by hand
(visual inspection + one-off numeric spot checks). The brief explicitly
wants integration-aware QA gates, and `validate_issue.py` has no pixel
checks at all (confirmed in the architecture scan) — without an automated
gate, every future panel needs the same manual inspection effort redone,
and there's nothing to stop a regression to the pasted-card look from
silently shipping again.

**Scoped for one cycle**: yes.

**Files created**: `00_SYSTEM/scripts/integration/validate_integration.py`
with three checks: `find_flat_card_regions()` (large flat-color rectangles
— debug overlays, un-alpha'd backdrops), `known_reference_color_regions()`
(color-distance match against the six `gen_char_refs.py` backdrop colors
plus the minted-card pink/cyan sampled directly from the real draft
composite), `check_contact_shadow()` (local-contrast test at a declared
foot anchor).

**Test — negative control, not just a happy-path run**: ran the gate
against two known cases: the real shipped `before` image (literal pasted
NFT card) and the Cycle 6 `after` render. This is the important test,
because a QA gate that only ever runs against art it already knows is
good proves nothing.

**Defects found during testing (this is the substantive part of the
cycle)**:
1. First version of `find_flat_card_regions` missed the actual card
   entirely — the character artwork drawn on top of the card's flat pink
   backdrop fragments it into ~984 small disconnected slivers, each too
   small/thin to pass the area+aspect filters. Confirmed by direct
   inspection of the label map, not assumed.
2. Attempted fix (morphological closing to re-merge the slivers) made it
   worse: at any closing strength able to bridge the character-sized gaps,
   it also engulfed the plate's own dark night sky (flat by the same
   metric) into one giant false-positive blob covering most of the frame.
   Reverted — recorded as a wrong turn, not silently dropped.
3. Real fix: added a second, independent check — direct color-distance
   matching against the known bad-color palette (sampled from the actual
   file, not guessed) — which correctly caught the card (29,899px pink +
   3,584px cyan border) that the flat-region detector missed.
4. That color-match check then false-positived on the `after` image's own
   MonkeyZoo neon sign glow (legitimate scene content), because saturated
   magenta neon and the minted-card pink sit within the same color-
   distance threshold. Fixed by requiring the matched pixels also be
   locally flat (gradient/bloom neon glow isn't; a pasted flat card is) —
   re-verified clean on both control images afterward.

**Final validation** (after both fixes): `before` → **FAIL** (3 flat
debug-overlay regions, 4 known-bad-color regions totaling the real card,
no contact shadow). `after` → **PASS** (zero flat regions, zero
color-match regions, contact shadow present). Correct on both directions
of the control test.

**Verdict**: **PASS**. The two documented false-negative/false-positive
rounds during testing are the point of running a negative control at all
— recorded here instead of only reporting the final clean result, per the
instruction that generating a file without inspecting it doesn't count as
validation.

---

## Cycle 8 — Regression test suite

**Selected because**: every prior cycle was validated manually. Without
pinned tests, a future edit (e.g. re-tuning `alpha_matte`'s threshold, or
touching `validate_integration`'s color palette) could silently
reintroduce either bug found in Cycle 7 with no signal. Repo already has
an established pytest convention (`character-bibles/_review_app/tests/`),
so this follows existing project format rather than inventing a new one.

**Scoped for one cycle**: yes.

**Files created**:
`00_SYSTEM/scripts/integration/tests/test_integration_pipeline.py` — 10
tests covering: alpha-matte corner transparency across 3 characters
(parametrized), the Scarline adversarial enclosed-color case, ground-plane
height/depth monotonicity + round-trip + horizon-guard, contact-shadow
darkening, and the two Cycle-7 negative-control images pinned as automated
assertions (before → FAIL with a caught bad-color region, after → PASS).

**Test**: `python -m pytest 00_SYSTEM/scripts/integration/tests -v` —
**10/10 PASSED** in 7.18s.

**Defects found**: none — this cycle formalized existing verified
behavior into regression coverage rather than finding new bugs.

**Verdict**: **PASS**.

---

## Cycle 9 — Document integration pipeline in operational docs

**Selected because**: "Studio workflow integration" is explicitly named in
the brief's prioritization list, and everything built in Cycles 1-8 was an
orphaned side project until this cycle — invisible to `automation_rules.md`
(the tool-roles/pipeline-gates source of truth) and to the `mz-art-run`
skill an operator or future session would actually reach for.

**Scoped for one cycle**: yes.

**Files changed**:
- `00_SYSTEM/automation_rules.md` — new §6A "Character Integration
  Pipeline (optional Stage 6.5)": documents the four scripts, states
  explicitly it does NOT replace Stage 6 generation and still requires
  human Gate A/B sign-off (no gate was weakened), and names current
  limitations honestly (no bespoke pose generation, no puddle reflection,
  no multi-character staging).
- `.claude/skills/mz-art-run/SKILL.md` — new subsection pointing at the
  compositor + QA gate as an alternative to monolithic generation for
  plate+character panels, with the exact QA-gate invocation.

**Test**: re-read both files after editing to confirm the insertions
landed in the right section and didn't corrupt surrounding structure
(pipeline gates table, engine-facts section) — both intact.

**Defects found**: none.

**Verdict**: **PASS**.

---

## Cycle 10 — Register character-integration track in project_direction.json

**Selected because**: `project_direction.json` is the file every session
is instructed to read first (per its own file and per this repo's memory
notes) and the authoritative priority source for the Studio platform.
Cycles 1-9 were invisible to it until this cycle — the brief's item 13
("Update project direction... when applicable") calls for exactly this.

**Scoped for one cycle**: yes.

**Files changed**: `00_SYSTEM/project_direction.json` — added task
`character-integration-pipeline` under the `canon-assets` track
(status `next`, priority P2, full instructions + doc pointers), updated
`issue-01-final-art-upgrade`'s instructions to point at the new tooling
instead of hand re-pasting, and inserted the new task into
`recommended_order` directly before `issue-01-final-art-upgrade` (the task
it most directly unblocks).

**Test**: `python -m pytest character-bibles/_review_app/tests/test_project_direction.py -v`
— this is the Studio platform's own loader/schema test suite, run against
the edited file (not a self-authored check) — **4/4 PASSED**. Also
independently re-parsed the file with `json.load` and confirmed the new
task id appears and `recommended_order` is well-formed.

**Defects found**: none.

**Verdict**: **PASS**.

---

# ROUND 2 — Cycles 11–30 (2026-07-16, second sweep)

Round 1 (Cycles 1–10) ended with three disclosed gaps: bespoke pose
generation (blocked on ComfyUI being offline), puddle reflection, and
multi-character staging. Round 2 starts by clearing the infra blocker.

---

## Cycle 11 — ComfyUI restored + verified stable render

**Selected because**: the single named blocker from Round 1's final
report. Every generation-dependent improvement (bespoke poses, img2img
edge unification, new plates) is gated behind a *verified-stable* server —
and this rig's history (Issue 06 generation log, mz-art-run skill) shows
"server responds" is not the same as "server renders" (VRAM-leak trap).

**Scoped for one cycle**: yes — launch, verify, smoke-render, confirm.

**Procedure followed** (per mz-art-run's hang-recovery/VRAM rules):
1. Checked for stale ComfyUI python processes first — none found.
2. Launched `I:\ai\ComfyUI\run_zluda.bat` minimized; 2 processes spawned
   (launcher loop + server).
3. Polled `/system_stats` — up after ~45s (warm relaunch, not the ~7min
   cold path). `vram_free` = 15.85 GB ✔ (matches the skill's ≈15.8 GB
   healthy threshold).
4. Queued a minimal Z-Image graph (new `smoke_render.py`, reusable for
   future recoveries) — **render completed in 50s**.
5. Verified the output is real content, not a black/corrupt frame:
   512×512, mean 208.1, std 80.5, 914 unique sampled colors.
6. Re-checked VRAM after render: 15.61 GB free — no leak.

**Files created**: `00_SYSTEM/scripts/integration/smoke_render.py` — the
verification step as a reusable script (queue minimal graph, poll for the
output file, exit code = verdict), so future hang recoveries don't
re-improvise this check.

**Verdict**: **PASS**. Generation-dependent cycles are unblocked.

---

## Cycle 12 — Puddle reflection compositing module

**Selected because**: the one acceptance-checklist item marked NOT
IMPLEMENTED in Round 1 (criterion 9), and a named brief requirement
("Reflections on wet surfaces"). Doable deterministically without GPU, so
it ran while ComfyUI booted.

**Scoped for one cycle**: yes.

**Files created/changed**:
- `00_SYSTEM/scripts/integration/reflection.py` — `add_puddle_reflection()`:
  mirrors the already-scaled/relit sprite across the ground contact line,
  squashes (0.80), fades vertically from the contact line, applies a
  deterministic per-row sine ripple, tints toward water color, clips to a
  declared reflective-surface polygon. Zero randomness.
- `scene_blocking.json` — new `reflective_surfaces` array; the polygon was
  traced visually then **verified by rendering an overlay against the
  plate and inspecting it** (`_test/puddle_poly_check.png`) before use.
- `pose_spec.json` — `reflection` opt-in block (surface reference +
  physical-plausibility note).
- `compositor.py` — reflection drawn after shadow, before character paste
  (never overlaps the sprite); raises a clear error if a pose requests a
  surface the scene doesn't declare.

**Test**: full compositor re-run — `reflection_visible_px: 4542`. QA gate
on the new final render: PASS. Regression suite: 10/10.

**Visual + numeric verification**: the reflection is deliberately
restrained (dark outfit over dark water), so visual inspection alone was
inconclusive — instead diffed the new render against the git-committed
pre-reflection render (byte-identical pipeline otherwise, since the rain
layer is fixed-seed): **3,565 changed pixels, ALL confined to x 262–339 /
y 640–719** — exactly the mirror region below the contact line, nothing
else in the frame touched. The 6×-amplified diff image shows the mirrored
boot soles at the contact line fading downward — correct orientation,
correct falloff. (Side benefit: this diff also proves the occlusion rain
layer is fully deterministic, as claimed in Cycle 6.)

**Defects found**: none. Noted judgment call: reflection strength tuned to
match the plate's own diffuse neon reflections rather than a mirror-sharp
look that would break the flat cel style.

**Verdict**: **PASS**.

---

## Cycle 14 — Multi-character staging (completed while Cycle 13's renders were queued)

**Selected because**: one of the two remaining Round-1 gaps ("multi-
character staging is unbuilt"), and the brief's Multi-Character Scenes
requirements (shared perspective/scale/ground plane, depth positions,
meaningful interaction, no sticker-row lineups). Ran during Cycle 13's GPU
wait — the ledger records completion order honestly.

**Target panel**: `MZ-2026-09-02_P06_PANEL02` — "Team gives Static space
instead of ordering silence" (Moodz, Scarline, Static) on the same
zoo-city-streets plate whose ground plane was already calibrated.

**Files created/changed**:
- `compositor.py` — new `run_scene()`: `characters_spec.json` array, all
  characters share one ground plane and light set; composited far-to-near
  (sorted by foot-anchor y) so near figures overlap far ones; per-character
  relight with the key side decided per character position (factored
  `derive_relight_spec()` out of `run()`); foreground rain applied once
  over the union region at the end. CLI auto-detects multi vs single spec.
- `poc/MZ-2026-09-02_P06_PANEL02/scene_blocking.json` — inherited verbatim
  from the P01 calibration (same plate/camera), retagged.
- `poc/MZ-2026-09-02_P06_PANEL02/characters_spec.json` — full staging spec.
  Blocking uses the two characters' natural gaze directions (Moodz glances
  viewer-right → placed screen-left; Scarline glances viewer-left → placed
  screen-right) so both eye-lines land on Static WITHOUT mirroring any
  sprite — mirroring is forbidden for asymmetric identity marks (Scarline's
  stripe is canon viewer-left).
- Asset prep: matted `*_16_worried` for all three (PASS: opaque 0.29–0.34).

**Defects found during testing**:
1. First matte attempt used the `_02_threeqtr` variants — FAILED (opaque
   0.96): those refs don't have flat backdrops. Led to a full 12-character
   scan of which approved refs are matte-able; also exposed that the
   corner-std pre-filter false-positives on dark-cornered busy refs, so
   the matte's own corner+opaque verdict stays the authoritative gate.
   Bad outputs deleted, not left in the layer library.
2. First composite gave Moodz (standing IN the water sheet) a shadow only
   — read as floating on water. Fixed by enabling his reflection on the
   declared surface (the physically correct grounding cue); re-ran and
   verified 1,493 visible reflection pixels + visual zoom inspection.

**Test**: composite ran with correct depth order (static → scarline →
moodz, far-to-near); regression suite still 10/10; single-character path
re-verified byte-identical behavior (same reflection px count).

**Visual verdict**: three characters at three depths, ground-plane-correct
scales, individual lighting, rain crossing all figures, no sticker-row —
the spatial gap between the flankers and Static carries the story beat.

**Verdict**: **PASS**.

---

## Cycle 13 — Bespoke scene-specific pose render (Static freeze-mid-step)

**Selected because**: the single largest disclosed gap from Round 1 — the
POC used Static's generic reference pose instead of the scripted beat.
Round 1's final report named this the recommended next One Thing.

**Canon fix first**: while re-reading `pose_spec.json` before generating,
caught that "gripping satchel strap" had leaked into the spec from the
direction brief's *example prose* — Static has no satchel in any approved
ref or in `character_bible.md`. Corrected to canon mitten-fist acting
BEFORE generation, so the error never reached rendered art (documented in
the spec's `hands_canon_note`).

**Three generation attempts, evidence-driven** (9 renders total):
1. **img2img @ denoise 0.85** from the minted frame-0 PNG (the documented
   pose-tier recipe), 3 seeds — poses usable, but ALL drifted identity:
   beige face instead of canon porcelain white [222,222,222], weakened
   black hair cap. Measured, not eyeballed: face sampled at [249,233,218].
2. **img2img @ denoise 0.80 + "reinforced" prompt**, 3 seeds — worse, and
   diagnosing it exposed a self-inflicted cfg-1.0 trap: the reinforcement
   said "never beige, never tan" — but at cfg 1.0 negatives are inert, so
   naming "beige" PROMOTES it (same failure class as the documented
   balloon-clause hazard in run_art_batch.py). A lesson re-learned and now
   re-recorded.
3. **text2img (no init) with the calibrated BASE prompt + pure-positive
   pose clause**, 3 seeds — root cause confirmed: the init image itself
   was dragging colors warm at every denoise; without it, all 3 seeds
   render canon colors. Winner seed 777021: porcelain-white face, glossy
   jet-black cap, separated grey eye rings, chest stitch, o-mouth, raised
   mitten fist, three-quarter-right with head tilted up — the scripted
   freeze-and-notice beat.

**Also fixed during this cycle**: `gen_scene_pose.py`'s wait loop
originally globbed `{name}_scene_seed*` and returned instantly when a
previous batch's files matched — found live on attempt 2, fixed to
seed-exact matching (comment documents the failure).

**Deliverables**: `gen_scene_pose.py` (reusable scene-pose generator that
imports the canonical identity descriptors from gen_char_refs.py instead
of duplicating them); 9 candidate renders under
`I:\ai\nft\output\MZ-SCENE-POSE\`; winner matted into
`character_layers/static/static_scene_freeze.png` (matte PASS: corners
transparent, opaque 0.51 — higher than the 0.31-0.36 typical because the
pose fills more frame; within the 0.15-0.60 gate).

**Knowledge captured**: img2img from minted cards = identity-color drift
at any pose-changing denoise on this engine; bespoke poses should be
text2img from BASE + pose clause, with img2img reserved for
close-to-init variants. This inverts the Round-1 assumption and is now
the documented default for scene poses.

**Verdict**: **PASS**.

---

## Cycle 15 — POC re-composite with the bespoke pose + acceptance re-run

**Selected because**: closes the loop Cycle 13 opened — the bespoke asset
existed but the flagship POC still showed the generic pose.

**Defect found and fixed (the substantive part)**: first re-composite
showed a **pink ellipse under the character** — Z-Image had baked a
backdrop-tinted drop-shadow into the winning render, and it survived the
matte because it's backdrop-*family* but outside the strict key threshold
(also explaining the suspicious 0.51 opaque fraction noted at matte time —
a warning sign initially misread as "pose fills more frame"). Fixed
generally, not as a one-off: new `strip_baked_ground_shadow()` in
`alpha_matte.py` re-keys the bottom 30% of the opaque bbox with a relaxed
threshold (62) — the baked ellipse is always near the backdrop color
there, while boots/legs are far from it. Re-matte: opaque 0.478, ellipse
gone (verified visually), boots intact.

**Files changed**: `alpha_matte.py` (+`strip_baked_ground_shadow`),
`pose_spec.json` (asset swap + `asset_history` provenance),
`character_layers/static/static_scene_freeze.png` (re-matted).

**Tests**: regression suite 10/10 after the matte change (including the
three parametrized corner/opaque assertions — proving the new stripper
doesn't damage normal refs). QA gate on the new final render: **PASS**,
contact shadow delta 38.6 luma.

**Acceptance checklist re-score** (vs. the Cycle 6 run): criteria 2 (pose
expresses scripted action) and 11 (eye lines/body direction) move
**PARTIAL → PASS** — the freeze-and-notice beat is now in the asset
itself: three-quarter-right stance, head tilted up toward the signage,
raised mitten fist, o-mouth alarm. Criterion 9 (reflections) moved
NOT IMPLEMENTED → PASS in Cycle 12. **All 14 applicable criteria now
PASS** (criterion 12 remains N/A — single-character panel; the
multi-character system is separately proven in Cycle 14).

**Verdict**: **PASS**.

---

## Cycle 16 — Localized img2img edge unification — **HOLD (rejected with evidence; does NOT count toward the 20)**

**Selected because**: the brief's preferred-pipeline step 12 ("localized
inpainting or image-to-image integration around the character boundary")
was the only unimplemented stage of the preferred hybrid workflow.

**Built**: `edge_unify.py` — dilate-minus-erode ring mask around the
composited silhouette, masked img2img via SetLatentNoiseMask at low
denoise, plus a pixel-space clamp making background-preservation outside
the ring a mathematical guarantee (output = ring*sampled + (1-ring)*orig).

**Attempt 1** (ring 4px in / 22px out, denoise 0.35): metrics fine
(12,929 ring px re-imagined, zero change outside after clamp) but visual
inspection failed it hard — hallucinated foreign blobs at the seam
(brown mass behind the head, white blob at the hip), the character's thin
tail destroyed (it fits inside the erosion band), muddy boot contact.

**Attempt 2** (character fully protected, 10px outer ring, denoise 0.18):
worse — and diagnosing it found a real scipy pitfall: `binary_erosion(...,
iterations=0)` means "erode until CONVERGENCE" (erases everything), not
"no erosion" — so the entire character was silently repaintable and got
repainted (studded pants replaced with plain legs, face flattened). Bug
fixed in the module with a warning comment.

**Verdict rationale**: at cfg 1.0 (negatives inert, weak guidance) this
engine re-imagines masked regions rather than harmonizing them, while the
deterministic compositor's feathered/defringed edges already pass all
acceptance criteria — so the stage adds hallucination risk with no
measured benefit. Module retained with a REJECTED banner for future
engines with real guidance; not wired into any pipeline path.

**Verdict**: **HOLD** — investigation complete and valuable (one scipy
bug fixed, one engine limitation established with before/after evidence),
but no shipped improvement, so per the loop's own rules it does not count
toward the 20.

---

## Cycle 17 — Ground-plane calibration measured, corrected, and tooled

**Selected because**: while verifying calibrations with the new overlay
renderer (built this cycle), the horizon estimate from Cycle 3 (y=205)
looked wrong against the plate's receding structure — and horizon error
grows with distance from the calibration point, which matters exactly
when panels start using far-field placements (the multi-char panel
already spans y=545–688).

**Tool built**: `calibrate_check.py` — renders horizon line, calibration
marker (now with `calib_x`), light-source positions, and reflective
polygons over the plate. Every calibration now gets a look-at-it
verification artifact, same discipline as the puddle polygon in Cycle 12.

**Measurement (not eyeball)**: the plate's two same-height streetlamps
give simultaneous equations for the horizon: near lamp (base y=470,
340px tall) and left lamp (base y=437, 242px tall) → H≈355. Receding
awning/fence lines converge ≈320. Adopted **330 (±25)**, documented in
`scene_blocking.json`'s new `horizon_derivation` field.

**Empirical confirmation before committing**: rendered the POC character
at both horizons side-by-side (H=205 → 107px vs H=330 → 136px at the same
foot anchor) — the corrected scale reads clearly better against the
trash can and doorway (`_test/horizon_compare.png`).

**Applied**: both POC scene_blocking files updated; both panels
re-composited (P01: 135.6px; P06: static 94.1 / scarline 147.9 / moodz
156.6 — foreground flankers now have proper near-camera presence);
QA gate re-run PASS on both; regression suite 10/10.

**Honest caveat**: the plate is itself AI-generated art, and its internal
perspective is not perfectly consistent (lamp math says 355, structure
lines say 320). 330 is the best single value the plate supports; the
uncertainty band is recorded in the spec rather than hidden.

**Verdict**: **PASS**.

---
