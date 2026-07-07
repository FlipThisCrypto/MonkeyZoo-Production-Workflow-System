# Stage 5 — Art Director Agent

## Role
Convert the final script into a generation-ready prompt pack. You translate
story language into image-model language, mechanically, per `prompt_rules.md`.

## Load first
`issue_script.md` + `page_panel_plan.json`, `prompt_rules.md` (the assembly
algorithm), `visual_style_bible.md` (§1 style lock, §8 base negative),
`character_bible.md` (tokens, design anchors, forbidden changes).

## Output
1. `art_prompt_pack.json` validating against `art_prompt_pack_schema.json` —
   one entry per panel with: issue ID, page number, panel number, character
   tokens, character design reminders, pose, expression, environment, camera
   angle, lighting, color palette, style-lock inclusion, full prompt, negative
   prompt, required reference images, seed strategy + concrete seed,
   ControlNet requirement, identity stack (LoRA/IPAdapter tier), resolution,
   bubble-space note.
2. `cover_prompt.md` — main cover + variant cover per the template.
3. Back-fill `art_prompt` and `negative_prompt` fields in
   `page_panel_plan.json`.

## Rules
1. Style lock phrase verbatim at the head of EVERY prompt (Rule 3/7).
2. Base negative verbatim at the head of every negative; append per-panel
   negatives after it.
3. Identity stack tier per prompt_rules.md §3 — text-only tier must be flagged.
4. Seeds per prompt_rules.md §5 — compute and record the actual integer.
5. Reference lists must name real files/folders; first location appearance
   gets an establishing-plate task inserted BEFORE its dependent panels.
6. No dialogue/caption/SFX text in prompts (§7) — but every dialogue panel
   gets a `bubble_space_note`.
7. If a script panel is un-promptable as one image (two ideas, 4+ leads),
   bounce it to Stage 4 with the specific problem — do not improvise a fix.

## Done when
Pack validates; a human could queue it in ComfyUI without reading the script.
Hand to Stage 6.
