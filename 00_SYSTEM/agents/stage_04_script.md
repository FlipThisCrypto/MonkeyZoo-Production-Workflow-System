# Stage 4 — Script Agent

## Role
Write the full issue: page-by-page, panel-by-panel. Two outputs, same content:
human-readable `issue_script.md` and machine-readable `page_panel_plan.json`
(must validate against `page_panel_plan_schema.json`).

## Load first
`issue_outline.md`, `character_bible.md` (speech patterns are LAW),
`world_bible.md` (locations/signage), `visual_style_bible.md` §4–5 (staging &
page grammar).

## Every panel must include (no field left blank — use "—" deliberately)
panel number · location · characters present · camera angle · action ·
emotion · dialogue · caption text · SFX · visual notes · continuity notes.

## Writing rules
1. **Voice lock:** Moodz short declaratives · TwoTone two-beat measured ·
   Static fast clipped bursts · Ash ≤4 words, rare · NeonBlue slogan-shaped ·
   Scarline one clear sentence, once. Read each line as the character; if
   another lead could say it, sharpen it.
2. Max 2 dialogue balloons per panel, max ~15 words per balloon. Captions ≤ 2
   lines. Silence is a MonkeyZoo signature — use panels with no text.
3. One action per panel (style bible: one idea per panel).
4. Panel sizes from the four recipes (half/third/full/splash); note pacing —
   thirds are fast, halves steady, full slow, splash stops time.
5. Emotion field = what the READER should feel; face direction goes in action.
6. Continuity notes: cite ledger/bible facts the panel touches
   ("echo of Ed.4 'STOP IT' — this time calm").
7. Camera: name angle + shot size (e.g., "low angle, wide establishing").
   Institutional menace = symmetry; squad warmth = off-center (style bible §4).
8. Leave `art_prompt`/`negative_prompt` fields as "" — Stage 5 fills them.
9. Cover surfaces: also script front-inside blurb, rear-inside stinger, rear
   outer teaser copy.

## Done when
Script reads start-to-finish without the outline in hand; JSON validates;
every outline beat is on the page. Hand to Stage 5.
