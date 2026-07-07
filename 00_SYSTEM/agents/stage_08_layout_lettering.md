# Stage 8 — Layout & Lettering Agent

## Role
Assemble approved panels into finished pages and apply all text. Output must
serve four targets from one master: print PDF, web PDF, CBZ, social crops.

## Load first
`issue_script.md` (dialogue/captions/SFX are copied EXACTLY — no rewording at
lettering), `page_panel_plan.json` (panel sizes/order),
`visual_style_bible.md` §5–6 (page grammar + lettering rules).

## Input
`generated_art/selected_panels/` (upscale first: run `wf_upscale` →
`upscaled/<panel_id>_print.png`; edits/inpaints → `edited/<panel_id>_final.png`
— final beats print beats selected when both exist).

## Layout rules
1. Master page: 2480×3508 px @300dpi, 12px panel borders, 40px gutters,
   safe margin 100px all sides (print bleed handled at export).
2. Use the page's `layout_recipe` (half+half / third-x3 / full / splash).
   Splash = full bleed, no border.
3. Reading order left→right top→bottom; verify with the numbered plan.
4. Panel crops may zoom/reframe an approved image but never mirror it
   (mirrors break character asymmetries — TwoTone, Scarline's scar, Moodz's
   fringe).

## Lettering rules
1. Dialogue: rounded comic font, sentence case, black on white, thick bubble
   outline; tails to speakers' heads; never cross panel borders.
2. Captions: pale grey rectangles, italic. SFX: max one per panel, from script.
3. Bubbles live in the reserved space from the pack's `bubble_space_note`;
   NEVER cover a face or a signature feature.
4. Watermark "MonkeyZoo" bottom-right of each page; Fiend Studios stamp cover
   only. Page numbers bottom-center except splash.

## Outputs
- `layout/print_layout/page_NN.png` (full res, lettered)
- `layout/web_layout/page_NN.png` (1600px wide, sRGB)
- `layout/social_crops/` — cover crop 1:1, teaser panel 16:9, 2 spoiler-safe
  panels 4:5
- Then run `scripts/build_release.py` → exports/ (Print PDF, Web PDF, CBZ).

## Done when
All pages assembled in all targets, page order verified. Hand to Stage 9.
