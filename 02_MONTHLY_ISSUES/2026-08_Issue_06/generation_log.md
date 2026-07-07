# MZ-2026-08-06 Generation Log

**Hardware:** AMD Radeon RX 6800 (16GB) via ZLUDA · Ryzen 7 3800X · 128GB RAM
**Server:** ComfyUI 0.19.3 portable (`run_zluda.bat`), API-driven via
`00_SYSTEM/scripts/run_art_batch.py`
**Output root:** `I:\ai\nft\output\MZ-2026-08-06\`

## Engine selection (2026-07-03)

| Attempt | Engine | Result |
|---|---|---|
| 1 | RealVisXL V4.0 (SDXL, on disk) | HARD FAIL — photorealism checkpoint steamrolled the style lock; produced a photo-real street. RealVis was installed for the pixel-art→3D restyle pipeline (`I:\ai\nft\workflows\production.json`), not comic generation. 1 test image → rejected. |
| 2 | Animagine XL 4.0 (SDXL, downloaded 6.46GB) | FAIL for characters — tag-trained model can't parse the pack's long prose prompts: character panels collapsed into sticker-sheet grids of heads; "no characters" plates collapsed into pattern wallpaper (contradiction with the character-describing style lock). Backgrounds-only were passable. ~14 images → rejected. Kept on disk as a background/pin-up fallback. |
| 3 | **Z-Image Turbo bf16 (DiT)** | **PASS** — model was already on disk (root of portable install); added `qwen_3_4b.safetensors` text encoder (7.49GB) + `ae.safetensors` VAE (as `z_image_ae.safetensors`) from Comfy-Org/z_image_turbo. Strong prose adherence: clean single-character chibi with thick outlines + flat color on first try. |

## Production settings (engine: zimage)

- Graph: UNETLoader(z_image_turbo_bf16) → ModelSamplingAuraFlow(shift 3.0) →
  KSampler(steps 8, cfg 1.0, res_multistep, simple) · CLIPLoader(qwen_3_4b,
  type lumina2) · VAE z_image_ae · per-panel resolution from pack
- **cfg 1.0 ⇒ negative prompts are INERT** (ConditioningZeroOut per official
  template). All guard-language must live in the positive prompt — Z-Image
  adapter note for prompt_rules.
- Plates (page 0) use `--plate-style`: the character-describing style lock is
  replaced at send time with a scenery lock ("flat color cartoon background
  art… EMPTY scenery, no characters") — with cfg 1 the model happily draws a
  monkey if the prompt opens by describing one (confirmed pre-fix).
- Throughput: ~90s/image after warmup (first gen ~7 min: 19GB model+TE load
  + ZLUDA kernel compile).
- Seeds per prompt_rules §5: per-panel seeds from the pack; variant v = seed+v.

## Batch 1 (full issue, 2 variants/panel)

- Queued: 44 generations (3 plates + 19 panels × 2 variants), batch order:
  plates → characterless → solo → two-shots → groups → splash.
- Identity tier: TEXT-ONLY for all six leads (no approved refs exist yet, no
  LoRAs — flagged in pack; extra QA scrutiny required). Patch identity from
  prose description of faction ref #1997.
- ControlNet/IPAdapter: NOT wired this batch (SDXL-only control models on disk
  are incompatible with Z-Image DiT). Composition adherence relies on Z-Image
  prose-following; pose-critical panels get extra variants on reroll.
  → Follow-up: `ZImageFunControlnet` node exists in this build — evaluate a
  Z-Image Fun ControlNet download for Issue 07.

## Deviations from spec (waivers)

1. `automation_rules` requires ≥4 variants/panel; first pass ran 2 to conserve
   wall-clock. Panels failing QA at 2 variants get rerolled per §5 policy.
2. `prompt_rules` §3 requires LoRA/IPAdapter tier for recurring characters —
   impossible this run (no trained LoRAs, no Z-Image IPAdapter). Mitigation:
   text anchors + QA strictness; this batch's approved panels seed
   `03_APPROVED_CANON/approved_characters/` so Issue 07 can move up the
   identity-stack tiers.

## Batch 2 (reroll, 11 panels × 2 variants, 2026-07-03)

Runner fixes applied before queueing (all in `run_art_batch.py` zimage path):
1. Clause filter strips lettering notes ("clear for two balloons" → drawn as
   literal balloons in batch 1) and SFX mentions.
2. "MonkeyZoo house style:" brand words stripped (rendered as ZOZO/MOZOZO
   logo text in batch 1); style description retained.
3. Characterless panels auto-get plate-style treatment (fixes P01_PANEL02 and
   P08_PANEL02 drawing the style-lock's monkey).
4. Positive-phrased no-text instruction appended (negatives inert at cfg 1).

Result: zero balloon/logo artifacts in 22 images. All 11 panels resolved.

## Per-panel results

Batch 1: 44 images → 11 panel-groups selected, 11 rejected.
Batch 2: 22 images → remaining 11 resolved (3 with layout-crop instructions).
Full verdict table: qa_report.md §Art QA. Selected files:
`generated_art/selected_panels/<panel_id>.png` (22/22, validator PASS).

Recommended next actions for identity quality (Issue 07):
- Human-approve the best character images from selected_panels into
  `03_APPROVED_CANON/approved_characters/<name>/` (canon approval is
  HUMAN-ONLY per automation_rules §2 — not done automatically).
- Wire IPAdapter for Z-Image or evaluate Z-Image Fun ControlNet.
- Kohya LoRA training once any lead crosses 20 approved refs.
