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
