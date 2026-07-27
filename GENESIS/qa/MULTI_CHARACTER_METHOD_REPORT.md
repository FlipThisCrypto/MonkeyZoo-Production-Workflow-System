# Multi-Character Staging — Method Report

79 of 96 panels are multi-character. Method used: **Option B — individual
panel-specific poses + deliberate compositor staging** (`genesis_charart.
make_multi_panel` / `compose_multi`). Shared full-panel generation (Option A)
was not used because Z-Image drifts/merges identities when two named designs
share one prompt; per-character generation keeps each identity exact.

## Pipeline
1. Per character: generate a panel-specific pose (facing derived from screen
   position; action/emotion from the beat), on the flat card-colour backdrop.
2. HSV hue-key matte per character (robust to the card colour).
3. Stage on the darkened location plate sharing a common ground line; back-to-
   front by scale so nearer characters overlap; contact shadow each; facing set
   so the pair reads as a conversation (eye-line).
4. Depth staging: 2-char = 0.27/0.71 x, 0.80/0.74 scale; 3-char = 0.20/0.50/0.80.

## QA per panel
matte corners clear · correct + distinct identities (no bleed) · shared ground
contact · overlapping order · common plate lighting · shared perspective.

## Proven
`MZ-2026-09-02_P05_PANEL02` (Static + Clever): both on-model, grounded, facing
each other, depth-staged, clean mattes. Integrated on page 6.
