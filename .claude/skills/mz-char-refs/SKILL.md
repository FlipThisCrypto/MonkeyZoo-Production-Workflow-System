---
name: mz-char-refs
description: Generate or extend standardized MonkeyZoo character reference variant sets (poses, expressions, angles) from the minted canon cards, and manage approved canon toward the LoRA-training threshold. Use when the user asks for character variants, reference sheets, more refs for a character, or LoRA prep.
---

# MonkeyZoo: Character Reference Variants

Standardized identity refs are generated **img2img from each character's
minted canon card** — never text-only (identity drifts).

## Canon sources (the trait system)
`03_APPROVED_CANON/approved_characters/factions/<name>.webp` — one identical
base monkey (pale stitched chest, brown arms, studded cuffs/pants, grey tread
boots, grey eye rings, droopy lid); identity = HAIR + card color:

| Lead | Card | Hair trait | Card color |
|---|---|---|---|
| Moodz | #1136 | black bowl hair + blue beanie | orange |
| TwoTone | #1195 | half-black/half-white split | purple |
| Ash | #1173 | silver-white fringe over one eye | teal |
| Static | #1199 | glossy black slicked cap | hot pink |
| NeonBlue | #99-4 | white spike crown + cyan streaks | green |
| Scarline | #1028 | white helmet hair + red stripe (viewer-left) | grey |

## Generate
1. Ensure inits staged as **flat PNG frame-0 extracts** at ComfyUI input
   `I:\ai\nft\input\mz-canon\<name>.png` (912×1216 lanczos scale in-graph).
   **NEVER feed the raw minted webps to LoadImage:** NeonBlue's card is a
   25-frame ANIMATED webp — LoadImage expands it to a 25-image batch and the
   25× img2img wedges ZLUDA hard (root cause of the 2026-07-06/07 stalls;
   masqueraded as a VRAM leak). Check any new minted asset with PIL
   `n_frames` before use; extract frame 0 to PNG.
2. `python 00_SYSTEM/scripts/gen_char_refs.py --img2img [--only ash,moodz]
   [--variants-only angry,walking]`
   - 14-variant matrix: 4 angles + portrait + 4 expressions + 5 poses.
   - **Denoise tiers are calibrated — don't change casually:** 0.70 angles/
     portrait (identity max), 0.80 expressions, 0.85 poses. Ladder-tested
     2026-07-06: identity holds through 0.85 with flat-color inits.
   - True back views are impossible (Z-Image refuses); the matrix uses
     over-shoulder rear three-quarter instead.
3. Outputs land in `I:\ai\nft\output\MZ-REFS/`.

## QA & placement
- Contact-sheet triage, then per-image check: correct hair trait, card color,
  monkey face (watch for human-child drift at high denoise), studded gear,
  tail present, no text.
- Winners → `03_APPROVED_CANON/approved_characters/<name>/` named
  `<name>_<variant>.png` (e.g. `ash_06_angry.png`). Rejects → requeue with
  seed+1 (edit seed in script call or accept the variant gap).
- Track counts: **20+ approved refs per character unlocks Kohya LoRA
  training** (`MZ_<Name>_v1.safetensors`), which permanently fixes panel
  identity drift. Update the character bible ref-folder notes when counts
  change materially.

## ZLUDA hang note
Long batches can wedge the GPU (queue frozen >15 min). `/interrupt` won't
help: kill the ComfyUI python process, the launcher loop relaunches, requeue
only the missing variants with `--only`/`--variants-only`. After ANY
kill-relaunch, verify `vram_free` ≈ 15.8GB AND watch one render complete
before walking away — a leaked-VRAM relaunch stalls silently at 0%
(full procedure: mz-art-run §3).
