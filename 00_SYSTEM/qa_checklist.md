# MonkeyZoo QA Checklist
**Version:** 1.0

Two gates. Gate A runs per generated panel batch (Stage 7). Gate B runs once
per issue before release (Stage 9). A panel/issue passes only with ZERO hard
fails. Soft fails need a written waiver in qa_report.md.

---

## GATE A — Art QA (per panel)

### Identity (HARD)
- [ ] Character is recognizably the bible design at a squint
- [ ] Signature colors correct (compare to character bible swatches)
- [ ] Fringe/split/spikes/hood/glow/scar — signature feature present & correct
- [ ] Outfit matches bible; NO invented costumes, props, tattoos, scars, jewelry
- [ ] Face consistent with the character's approved refs / base-seed portrait

### Anatomy (HARD)
- [ ] Mitten hands — zero fingers
- [ ] Correct limb count, one tail, curled tail shape
- [ ] Eyes: two, huge, white ovals, dot pupils, symmetrical
- [ ] Stitch seams visible

### Style (HARD)
- [ ] Thick uniform outlines, flat color + soft cel shade only
- [ ] No photorealism, painterly texture, hatching, or 3D-render look
- [ ] No accidental style drift vs previous approved panels in this issue

### Scene (HARD)
- [ ] Location matches the approved establishing plate for this issue
- [ ] Green glow only in zombie/cracked-chamber contexts
- [ ] Emotion on face matches script's emotion field
- [ ] No unintended text/watermarks in image

### Readability (SOFT unless unusable)
- [ ] One clear idea; silhouette reads at thumbnail size
- [ ] Action understandable without dialogue
- [ ] Bubble space clear where the prompt reserved it
- [ ] Panel-to-panel flow: eyeline/movement leads left→right

### Disposition
APPROVE → `generated_art/selected_panels/` · REJECT → `04_REJECTED_OUTPUTS/rejected_art/`
with one-line reason in qa_report.md. 10 rejects on same panel → escalate
(inpaint / new pose ref / re-prompt), never brute-force.

---

## GATE B — Final QA (per issue)

### Completeness (HARD)
- [ ] Script complete: every page, every panel, no TODOs
- [ ] Every scripted panel has an approved, upscaled image
- [ ] Main cover + variant cover approved
- [ ] All 4 cover surfaces written (front out/in, rear in/out)
- [ ] page_panel_plan.json + art_prompt_pack.json validate against schemas
- [ ] metadata.json complete (CHIP-0015; sha256 + urls filled after upload)

### Continuity (HARD)
- [ ] continuity_ledger.md entry appended for this issue
- [ ] Previous issue's teaser honored or explicitly deferred in ledger
- [ ] New lore written into world/character bibles
- [ ] No character redesign occurred (or explicit redesign issue declared)
- [ ] Next-issue teaser present on rear outside cover

### Package (HARD)
- [ ] Exports exist: Print PDF, Web PDF, CBZ, cover.png, promo images
- [ ] Lettering pass done: no bubble covers a face, margins ≥ safe area
- [ ] Page order verified in both PDFs and CBZ
- [ ] Social posts ready (all 8 sections of template)
- [ ] Source files present (prompts, seeds, refs list, layout files)

### Release hygiene (SOFT)
- [ ] Alt text written for cover + promo images
- [ ] Collector/NFT metadata spot-checked against previous issue conventions
- [ ] Archive copy staged for /05_RELEASE_ARCHIVE/YYYY/Issue_##

### Disposition
RELEASE / HOLD (list blocking items) — recorded at top of qa_report.md.
