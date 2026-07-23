# MonkeyZoo: Genesis — Release Report

## Executive result
- **Complete web-edition issue produced**: 22 story pages + independent front & back covers,
  fully lettered, variable-density layout, packaged as CBZ + PDF with manifest & checksums.
- Technical QA overall: **PASS**.
- Source panels are web-tier (1280x720); this is a polished web edition, not native print.

## Issue identity
- Series **MonkeyZoo** · Issue **Genesis** · Story *Signals in the Silence*
- Production Issue **8** · Published Issue **1** · seed `20260718`
- Output root: `GENESIS/`

## Final metrics
- Covers: 2 (independent)  ·  Story pages: **22**  ·  Total images: 24
- Panels: **96**  ·  avg **4.36**/page (min 3, max 6)
- Panels/page distribution: {'4': 12, '6': 4, '3': 3, '5': 3}
- Shots: {'wide': 20, 'medium': 51, 'close': 25} (close fraction 0.26)
- Dialogue: 335 words / 60 panels (avg 5.58, max 13)

## Page-by-page
| Pg | Side | Panels | Template | Location | Page-turn |
|---|---|---|---|---|---|
| 1 | right | 4 | `band4` | Zoo City Streets | cold open — establish tone and the first anomaly |
| 2 | left | 4 | `hero4` | School / Public Address Zone | carry momentum into the next beat |
| 3 | right | 4 | `band4` | Zoo City Streets | carry momentum into the next beat |
| 4 | left | 4 | `hero4` | Early-Fall Storm Streets and Routine Nodes | carry momentum into the next beat |
| 5 | right | 6 | `band6` | Transit Announcement Hub | carry momentum into the next beat |
| 6 | left | 4 | `hero4` | Transit Announcement Hub | carry momentum into the next beat |
| 7 | right | 6 | `band6` | Transit Announcement Hub | carry momentum into the next beat |
| 8 | left | 4 | `hero4` | School / Public Address Zone | carry momentum into the next beat |
| 9 | right | 6 | `band6` | Transit Announcement Hub | carry momentum into the next beat |
| 10 | left | 6 | `hero6` | Transit Announcement Hub | carry momentum into the next beat |
| 11 | right | 4 | `hero4` | Early-Fall Storm Streets and Routine Nodes | carry momentum into the next beat |
| 12 | left | 4 | `band4` | School / Public Address Zone | carry momentum into the next beat |
| 13 | right | 4 | `hero4` | Transit Announcement Hub | carry momentum into the next beat |
| 14 | left | 4 | `band4` | Early-Fall Storm Streets and Routine Nodes | carry momentum into the next beat |
| 15 | right | 3 | `band3` | Zoo City Streets | carry momentum into the next beat |
| 16 | left | 5 | `hero5` | Zoo City Streets | carry momentum into the next beat |
| 17 | right | 4 | `hero4` | Transit Announcement Hub | carry momentum into the next beat |
| 18 | left | 3 | `hero3` | Old Relay Junction | hold on reaction before the turn |
| 19 | right | 5 | `band5` | Old Relay Junction | carry momentum into the next beat |
| 20 | left | 4 | `band4` | Zoo City Streets | carry momentum into the next beat |
| 21 | right | 5 | `band5` | Early-Fall Storm Streets and Routine Nodes | carry momentum into the next beat |
| 22 | left | 3 | `band3` | Zoo City Streets | final image / next-issue stinger |

## Deliverables (paths under GENESIS/)
- `covers/01_FRONT_COVER.png`, `covers/24_BACK_COVER.png` (full-res masters)
- `story_pages/02_PAGE_01.png` … `23_PAGE_22.png` (full-res masters)
- `web/**` (optimized JPG web edition)  ·  `previews/full_issue_contact_sheet.jpg`
- `release/MonkeyZoo_Genesis.cbz`, `release/MonkeyZoo_Genesis.pdf`
- `release/release_manifest.json`, `release/SHA256SUMS.txt`
- `GENESIS_LAYOUT_PLAN.json/.md`, `metadata/*.json`, QA + this report

## Reproducing
```
python 00_SYSTEM/scripts/genesis/genesis_plan.py     # layout plan (deterministic, seed 20260718)
python 00_SYSTEM/scripts/genesis/genesis_build.py    # render pages + covers
python 00_SYSTEM/scripts/genesis/genesis_release.py  # CBZ + PDF + manifest + checksums
python 00_SYSTEM/scripts/genesis/genesis_qa.py       # structural/lettering/shot QA
python 00_SYSTEM/scripts/genesis/genesis_report.py   # regenerate these docs
```

## Remaining owner gates (not done autonomously)
- Promotion of any Genesis art into `03_APPROVED_CANON/` is human-only.
- Bespoke high-res ComfyUI re-renders of panels (quality upgrade) remain owner-gated.
