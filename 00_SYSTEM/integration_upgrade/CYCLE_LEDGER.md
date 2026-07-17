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
