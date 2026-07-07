# MonkeyZoo Visual Style Bible
**Version:** 1.0 · **Last updated:** 2026-07-02

The look is the brand. This file defines it; `prompt_rules.md` defines how to
ask an image model for it. Grounded in approved refs: `Fusion Squad.png`,
`emo.png` (#973), `zombie.png` (#1997), published editions 1–4.

---

## 1. STYLE LOCK PHRASE (never change — Rule 3)

Use verbatim, at the start of every art prompt:

> **"MonkeyZoo house style: chibi cartoon monkey with oversized round head,
> huge white oval eyes with tiny black dot pupils, two small dot nostrils,
> thick uniform black outlines, flat color fills with soft cel shading,
> simplified plush body with visible stitch seams, mitten hands, curled tail,
> clean vector cartoon look, dark cartoon sci-fi cyberpunk backdrop"**

Energy references (for humans, not prompts): Adult Swim / indie cartoon
attitude, Samurai Jack staging, Powerpuff Girls simplicity, Invader Zim
weirdness. Do NOT put artist/show names in prompts — describe, don't name.

## 2. Character Rendering Rules

- Head ≈ half of total height. Bodies stay simple; complexity lives in the face.
- Eyes are the acting instrument: size, lid position, and pupil placement carry
  emotion. Mouths are simple shapes (line, "o", wide grin, jagged distress).
- **Mitten hands only. Never fingers.** Feet are rounded or chunky boots.
- Stitch seams on chest/arms are always visible (living-toy identity).
- Outline weight is uniform and thick; no sketchy/broken lines, no hatching.
- Color: flat fills + ONE soft cel shade pass. No painterly texture, no
  full-body gradients, no photoreal fur.

## 3. Backgrounds

- Two modes, both canon:
  1. **Scene mode** — soft-focus cyberpunk environments, desaturated greys with
     neon accents (see #973: rainy monochrome street, glowing lamp).
  2. **Card mode** — flat saturated color field with rounded-rect frame (see
     #1997: orange card). Use for covers, pin-ups, character cards, NFT stills.
- Backgrounds are always simpler than characters. Characters pop via contrast
  and outline weight; backgrounds may drop outlines entirely.
- Environmental palette: charcoal, wet-asphalt grey, glass teal, neon signage
  colors (cyan/magenta/green). FusionZoo interiors: sterile white + glow lines.
- Green glow is RESERVED for zombie/cracked-chamber content. Don't use it as
  generic sci-fi dressing.

## 4. Staging & Composition (Samurai Jack rules)

- One idea per panel. If a panel needs two ideas, it's two panels.
- Big silhouettes, generous negative space, low or high angles for power
  dynamics, dead-center symmetry for institutional menace (FusionZoo loves
  symmetry; the squad breaks it).
- Quiet beats get wide shots and empty space. Panic beats get tight close-ups.
- Splash pages: max one per issue, reserved for the emotional/mechanical peak.

## 5. Panel & Page Grammar

- Page size: 2480×3508 px (A4 @300dpi) print master; panels generated
  individually then composed.
- Panel shapes: rectangular, thick black borders (12px @300dpi), white gutters
  (40px). Broken/borderless panels only for system-glitch moments.
- Reading order strictly left→right, top→bottom. No experimental flow.
- Standard page recipes: Half+Half · Third×3 · Full · Splash (bleed).
  These four cover 95% of pages (matches Editions 1–4 pacing).

## 6. Lettering

- Dialogue: clean rounded comic sans-serif (e.g., "Komika" class), sentence
  case, black on white bubbles, thick black bubble outline matching line weight.
- Narration: rectangular caption boxes, pale grey fill, italic.
- SFX: chunky display type, outlined, max one SFX per panel
  (canon set: WHRRRR, CRACKLE, THUD).
- Bubble tails point to speakers' heads, never cross panel borders.
- Reserve top 20% OR one side third of every dialogue panel for bubbles —
  the Art Director must note bubble space in every panel prompt.
- Watermark: "MonkeyZoo" script bottom-right of full pages; Fiend Studios
  stamp on covers only.

## 7. Color Discipline

- Each lead owns a palette (see character bible). Palettes never cross-bleed:
  if two leads share a panel, keep their signature colors separated by
  background neutrals.
- Scene lighting may TINT characters (night blue, chamber glow) but signature
  hues must stay identifiable. QA checks identity at a squint.

## 8. BASE NEGATIVE PROMPT (start of every negative prompt)

> "realistic anatomy, human hands, individual fingers, extra limbs, extra
> tails, small eyes, detailed fur texture, photorealism, 3d render, painterly
> brushwork, cross-hatching, thin sketchy lines, full-body gradient, watermark
> text, signature text, extra characters, duplicate character, redesigned
> costume, new accessories, jewelry, tattoos, extra scars, background characters
> with faces, deformed pupils, asymmetric eye sizes"

Per-panel negatives are APPENDED, never replace this base.

## 9. Style Drift Tripwires (Art QA hard-fails)

- Fingers. Any fingers.
- Missing stitch seams or missing curled tail.
- Outline weight varying inside one panel.
- A lead rendered off-palette (check against character bible swatches).
- Green glow appearing outside zombie/cracked-chamber contexts.
- More than one SFX per panel; bubble covering a face.
- Any costume/prop not in the character bible or approved_props.
