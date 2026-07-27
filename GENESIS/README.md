# MonkeyZoo: Genesis

*Signals in the Silence* — Published Issue **01** (Production Issue 08).

A complete, fully lettered web-edition comic issue: **22 story pages** with variable,
narrative-driven panel density, plus **independent front and back covers**, packaged as
CBZ + PDF with a manifest and checksums.

## Read it
- `release/MonkeyZoo_Genesis.cbz` — comic reader (CBZ)
- `release/MonkeyZoo_Genesis.pdf` — PDF
- `web/story_pages/` + `web/covers/` — per-page JPGs
- `previews/full_issue_contact_sheet.jpg` — whole issue at a glance

## What's here
- `covers/` — full-res front & back cover masters (PNG)
- `story_pages/` — full-res page masters (PNG)  *(gitignored; regenerable)*
- `web/` — optimized JPG web edition
- `release/` — CBZ, PDF, `release_manifest.json`, `SHA256SUMS.txt`
- `metadata/` — shot distribution, dialogue metrics, page turns
- `GENESIS_LAYOUT_PLAN.json/.md` — the deterministic page/panel plan
- `GENESIS_*_REPORT.md` — release, technical QA, lettering, character, visual QA

## How it was built
The 96 integrated 'Signals in the Silence' panels were reflowed into 22 pages by a
deterministic planner (beat classification + DP segmentation at scene boundaries),
rendered with variable layout templates and full lettering, and packaged for release.
Genesis performs **layout, lettering, covers and packaging only** — it does not alter
character canon or regenerate art. See `GENESIS_RELEASE_REPORT.md` to reproduce.

## Honest limitations
- Source panels are 1280x720 (web tier); the web edition is crisp, print masters are upscaled.
- 5 background plates exist, so wide shots reuse locations; bespoke ComfyUI re-renders are the
  (owner-gated) quality upgrade path.
