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
