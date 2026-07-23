---
name: mz-package
description: Run MonkeyZoo layout, lettering, exports, and release gates (Stages 8–10) — assemble lettered pages, build PDFs/CBZ/covers/social crops, run Final QA, and prep CHIP-0015 metadata. Use when panels are selected and the user says "run stage 8", "package the issue", or "prep the release".
---

# MonkeyZoo: Package & Release (Stages 8–10)

## Stage 8 — Layout & Lettering
1. Author/refresh `layout/layout_overrides.json`: crop windows from QA edit
   notes (balloon remnants, conditional crops), `screen_text` entries (screen
   copy is NEVER generated — always lettered), bubble/caption/SFX positions.
2. Run the assembler with ComfyUI's embedded python (it has Pillow):
   `I:\ai\ComfyUI\python_embeded\python.exe 00_SYSTEM/scripts/assemble_pages.py <issue-folder>`
   → print_layout (2480×3508@300dpi), web_layout (1600w), Print/Web PDFs
   (palette-mode: this Pillow lacks JPEG), social crops per `_social` spec.
3. Covers: generate via Z-Image using `cover_prompt.md` (scene cover ~69001
   seed family, card-mode variant), letter title/stamps with Pillow, save
   `exports/cover.png` + `promo_images/variant_cover.png`.
4. CBZ + export check: `python 00_SYSTEM/scripts/build_release.py <issue-folder>`.
   For a Genesis-style packaged release, verify its integrity + provenance
   BEFORE distributing or minting:
   `python 00_SYSTEM/scripts/genesis/genesis_release.py --verify <genesis-dir>`
   — re-hashes every SHA256SUMS.txt file and cross-checks the release manifest's
   per-artifact sha256/bytes (the values CHIP-0015 mints with). Exit 1 lists any
   corruption or manifest/file provenance drift; never mint a release that fails.
5. Lanczos scaling is fine for flat-color art; ESRGAN upscale on ZLUDA is
   ~5min/panel — skip unless making print masters.
6. Programmatic lettering is DRAFT tier: recommend a Krita/CSP polish pass
   before minting.

## Stage 9 — Final QA (Gate B, `00_SYSTEM/qa_checklist.md`)
- `validate_issue.py <folder> --art` PASS.
- If any panel was composited via the integration pipeline (staged
  previews exist in `generated_art/integration_preview/`):
  `validate_issue.py <folder> --integration` PASS, plus the Gate A
  "Integration" checklist section judged by eye per panel.
- Ledger entry appended and consistent with the SHIPPED script; previous
  teaser honored/deferred; new lore copied into world/character bibles;
  next-issue teaser present.
- Exports exist and open; page order verified in all three formats.
- Verdict RELEASE or HOLD (with blocking list) at top of `qa_report.md` +
  `final_export_checklist.md` evidence sheet.

## Stage 10 — Release
- `social_posts.md`: all 8 sections (launch/X/Facebook/Discord/newsletter/
  summary/alt text/T-3 teaser). Voice = the captions' voice. Never spoil
  pages 6–8. Every post ends with the MintGarden link.
- `metadata.json` CHIP-0015: collection block copied VERBATIM from previous
  issue. **BYTE-EXACT RULE (`automation_rules.md` §6): sha256 via
  `Get-FileHash`, IPFS CIDs pasted from upload output — NEVER transcribed
  from conversation context.** Wallet/minting sessions: pxpipe OFF
  (`00_SYSTEM/tooling_pxpipe.md`).
- Archive: `build_release.py <issue-folder> --archive`, then git tag
  `issue-##`. Flip the ledger entry from DRAFT to released.
