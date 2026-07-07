# MZ-2026-08-06 Final Export Checklist (Gate B evidence sheet)

Status legend: [x] done · [ ] pending · [~] drafted, needs final pass

## Completeness
- [x] Script complete (issue_script.md — 8 pages, 19 panels, 4 cover surfaces)
- [x] page_panel_plan.json written and validated
- [x] art_prompt_pack.json written (22 entries: 3 plates + 19 panels)
- [ ] Every scripted panel has approved, upscaled image
- [ ] Main cover generated + approved
- [ ] Variant cover generated + approved
- [~] metadata.json (CHIP-0015 complete except TODO-IPFS url/sha256 fields)

## Continuity
- [~] continuity_ledger.md entry appended (DRAFT — flip on release)
- [x] Previous teasers handled: Issue 05 threshold thread RESOLVED (Patch with
      squad); Issue 05 Super-watcher DEFERRED with P1.1 cameo, logged
- [ ] New lore final pass into world_bible §2/§4 on release (Old Quarter,
      Relay 1, the Signal, the Pending, the Keeper, Return Protocol)
- [x] No character redesigns (Pending look = declared issue-scoped exception)
- [x] Next-issue teaser present (rear outside cover "IT HEARD" + P08_PANEL02)

## Package
- [x] MonkeyZoo_Issue_06_Print.pdf (2480x3508 @300dpi, 8 pages, palette-PDF)
- [x] MonkeyZoo_Issue_06_Web.pdf (1600w)
- [x] MonkeyZoo_Issue_06_CBZ.zip (8 pages + cover)
- [x] cover.png (lettered) + promo_images/variant_cover.png + 4 social crops
- [x] Lettering pass — DRAFT TIER via assemble_pages.py (bubbles, captions,
      screen texts incl. RELAY 1 stencil / DAY 4,749 / RETURN PROTOCOL
      INITIATED, SFX, watermark, page numbers). Print-final manual polish in
      Krita/CSP still recommended before mint (see waiver below)
- [x] Page order verified (assembler emits in plan order; CBZ numerically sorted)
- [x] Social posts ready (all 8 sections)
- [x] Source files present (prompt pack, seeds, generation_log, layout_overrides.json)

**Stage 8 waivers:** (1) draft-tier programmatic lettering — margins and tails
functional, not polished; (2) model upscaling skipped (ESRGAN-on-ZLUDA ~5min/
panel) — Lanczos scaling used, visually adequate for flat-color art; revisit
for print masters; (3) minor balloon-string remnant visible in P08_PANEL01
top edge — inpaint before mint.

## Release hygiene
- [x] Alt text written (cover, variant, splash promo)
- [x] Metadata conventions match previous issues (CHIP-0015, collection block verbatim)
- [ ] Archive staged after RELEASE verdict

## VERDICT
HOLD — art pipeline (Stages 6–8) not yet run. Everything upstream of ComfyUI
is complete and validated. Same expected state as Issue 05's worked example.
