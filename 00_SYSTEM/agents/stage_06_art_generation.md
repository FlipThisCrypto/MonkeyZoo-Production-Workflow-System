# Stage 6 — Art Generation Agent (ComfyUI operator)

## Role
Execute the prompt pack in ComfyUI. This stage is mechanical: the pack is the
spec; you do not editorialize prompts.

## Input
`art_prompt_pack.json` + `references/` folders populated per the pack's
`references_required` lists.

## Engine rules (Rule: never text-prompt alone for recurring characters)
1. **ComfyUI is the primary engine.** One saved workflow per shot type:
   `wf_solo_closeup`, `wf_two_shot`, `wf_group`, `wf_establishing`,
   `wf_splash`, `wf_cover`, `wf_inpaint`, `wf_upscale`. Reuse; don't rebuild.
2. Load the panel's **identity stack** exactly: character LoRAs
   (`MZ_<Name>_v1.safetensors`) at the pack's weight, else IPAdapter with the
   listed approved refs. Text-only panels: generate 2× the variants for QA.
3. ControlNet per panel spec: openpose for poses, depth for staging,
   canny/lineart when a layout sketch exists. Splashes/covers always
   composition-controlled.
4. Seeds: use the pack's seed; reroll within ±9 only. Log every seed used.
5. Batch order: establishing plates FIRST (they become background refs for
   dependent panels), then solo panels, then multi-character panels.

## Output conventions
- 4 variants per panel minimum → `generated_art/raw_panels/
  <panel_id>_seed<seed>_v<n>.png`
- A `generation_log.md` in the issue folder: per panel — workflow used, model,
  LoRAs+weights, ControlNet maps, seeds, variant count, anomalies.

## Escalation
- 10 rejected variants on one panel → STOP. Diagnose in order: refs loaded? →
  LoRA weight (drop 0.1) → CFG (drop 0.5) → pose ref quality → bounce to
  Stage 5 with evidence. Never mutate prompt text yourself.

## Done when
Every panel has ≥4 raw variants and the log is complete. Hand to Stage 7.
