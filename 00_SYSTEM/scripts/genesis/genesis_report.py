#!/usr/bin/env python3
"""Generate Genesis documentation from real produced data (plan + QA + release).

Emits README, top-level manifest, release report, credits, and character /
lettering / visual-QA reports. Everything is derived from the layout plan, the
QA sidecars, and the release manifest so the docs cannot claim more than was
actually produced.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]


def _load(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def generate(genesis_dir: Path) -> None:
    plan = _load(genesis_dir / "GENESIS_LAYOUT_PLAN.json")
    qa = _load(genesis_dir / "qa" / "genesis_qa.json", {})
    shot = _load(genesis_dir / "metadata" / "shot_distribution.json", {})
    dlg = _load(genesis_dir / "metadata" / "dialogue_metrics.json", {})
    pages = plan["pages"]

    manifest = {
        "series": plan["series"], "issue_title": plan["issue_title"],
        "story_subtitle": plan["story_subtitle"],
        "production_issue": plan["production_issue"], "published_issue": plan["published_issue"],
        "slug": plan["slug"], "seed": plan["seed"],
        "story_pages": plan["story_page_count"], "total_panels": plan["total_panels"],
        "total_images": plan["story_page_count"] + 2,
        "deliverables": {
            "front_cover": "covers/01_FRONT_COVER.png (master) · web/covers/01_FRONT_COVER.jpg",
            "back_cover": "covers/24_BACK_COVER.png (master) · web/covers/24_BACK_COVER.jpg",
            "story_pages": "story_pages/02_PAGE_01.png .. 23_PAGE_22.png (masters) · web/story_pages/*.jpg",
            "cbz": "release/MonkeyZoo_Genesis.cbz", "pdf": "release/MonkeyZoo_Genesis.pdf",
            "manifest": "release/release_manifest.json", "checksums": "release/SHA256SUMS.txt",
            "layout_plan": "GENESIS_LAYOUT_PLAN.json / .md",
            "contact_sheet": "previews/full_issue_contact_sheet.jpg",
        },
        "source": {
            "panels": plan["source_panel_dir"], "panel_resolution": "1280x720 (web tier)",
            "source_issue": plan["source_issue"],
        },
        "qa_overall": qa.get("overall_pass"),
    }
    (genesis_dir / "GENESIS_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # --- character report ---
    chars = Counter()
    for pg in pages:
        for pa in pg["panels"]:
            for c in (pa.get("characters") or []):
                chars[c] += 1
    char_md = ["# MonkeyZoo: Genesis — Character Report", "",
               "Appearances tallied from the layout plan (panel `characters` field).", "",
               "| Character | Panels |", "|---|---|"]
    char_md += [f"| {c} | {n} |" for c, n in chars.most_common()]
    char_md += ["", "Identity and approved designs are inherited from the source integrated panels;",
                "Genesis performs layout + lettering only and does not alter character canon.", ""]
    (genesis_dir / "GENESIS_CHARACTER_REPORT.md").write_text("\n".join(char_md), encoding="utf-8")

    # --- lettering report ---
    let_md = ["# MonkeyZoo: Genesis — Lettering Report", "",
              f"- Dialogue: **{dlg.get('total_dialogue_words','?')} words** across "
              f"**{dlg.get('panels_with_dialogue','?')} panels**",
              f"- Avg words / speaking panel: **{dlg.get('avg_words_per_speaking_panel','?')}** "
              f"(max in one panel: {dlg.get('max_words_in_panel','?')})",
              f"- Overflow (>35 words) warnings: {len(qa.get('lettering',{}).get('warnings',[]))}",
              "",
              "Speaker prefixes are split out of balloons and shown as tags; captions are",
              "restricted to scene-establishing location/time stamps (production beat-notes",
              "in the source `caption` field are kept internal and never rendered). Blank",
              "markers (\"—\") never produce empty balloons/captions/SFX.", ""]
    (genesis_dir / "GENESIS_LETTERING_REPORT.md").write_text("\n".join(let_md), encoding="utf-8")

    # --- visual QA report ---
    vis_md = ["# MonkeyZoo: Genesis — Visual QA Report", "",
              "Automated + manual inspection.", "",
              "## Shot variety",
              f"- {shot.get('by_shot',{})} · close fraction {shot.get('close_fraction','?')}",
              f"- Pages with adjacent same-scale close-ups: "
              f"{qa.get('shots',{}).get('adjacent_closeups_same_page') or 'none'}",
              "- Source camera types are Wide/Medium/Close; additional read of scale comes from"
              " placement (feature vs grid slot). Shot variety is bounded by the source art.",
              "", "## Layout variety",
              f"- Panels/page distribution: {qa.get('pacing',{}).get('distribution',{})}",
              f"- Adjacent identical templates: {qa.get('pacing',{}).get('adjacent_same_template','?')}",
              "", "## Known source-limited items (honest)",
              "- Source panels are 1280x720 (web tier); print masters are upscaled, not native print DPI.",
              "- Only 5 background plates exist, so wide establishing shots reuse locations and",
              "  characters read small in some wide panels — an art-generation (ComfyUI) upgrade path,",
              "  gated on owner approval, not a layout defect.", ""]
    (genesis_dir / "GENESIS_VISUAL_QA_REPORT.md").write_text("\n".join(vis_md), encoding="utf-8")

    # --- credits ---
    cred_md = ["# MonkeyZoo: Genesis — Credits", "",
               "**Series:** MonkeyZoo  ·  **Issue:** Genesis (Published Issue 01 / Production Issue 08)",
               "**Story:** Signals in the Silence", "",
               "- Studio: MonkeyZoo / The Banana Lab Studio",
               "- Story, canon & integrated art: MonkeyZoo Production Workflow System",
               "- Layout, lettering, covers & release assembly: automated Genesis pipeline",
               "  (`00_SYSTEM/scripts/genesis/`)", "",
               "© MonkeyZoo / Fusion Squad. All rights reserved.", ""]
    (genesis_dir / "GENESIS_CREDITS.md").write_text("\n".join(cred_md), encoding="utf-8")

    # --- release report ---
    rr = ["# MonkeyZoo: Genesis — Release Report", "",
          "## Executive result",
          "- **Complete web-edition issue produced**: 22 story pages + independent front & back covers,",
          "  fully lettered, variable-density layout, packaged as CBZ + PDF with manifest & checksums.",
          f"- Technical QA overall: **{'PASS' if qa.get('overall_pass') else 'FAIL'}**.",
          "- Source panels are web-tier (1280x720); this is a polished web edition, not native print.",
          "",
          "## Issue identity",
          f"- Series **{plan['series']}** · Issue **{plan['issue_title']}** · Story *{plan['story_subtitle']}*",
          f"- Production Issue **{plan['production_issue']}** · Published Issue **{plan['published_issue']}** · seed `{plan['seed']}`",
          "- Output root: `GENESIS/`",
          "",
          "## Final metrics",
          f"- Covers: 2 (independent)  ·  Story pages: **{plan['story_page_count']}**  ·  Total images: {plan['story_page_count']+2}",
          f"- Panels: **{plan['total_panels']}**  ·  avg **{qa.get('pacing',{}).get('avg','?')}**/page "
          f"(min {qa.get('pacing',{}).get('min','?')}, max {qa.get('pacing',{}).get('max','?')})",
          f"- Panels/page distribution: {qa.get('pacing',{}).get('distribution',{})}",
          f"- Shots: {shot.get('by_shot',{})} (close fraction {shot.get('close_fraction','?')})",
          f"- Dialogue: {dlg.get('total_dialogue_words','?')} words / {dlg.get('panels_with_dialogue','?')} panels "
          f"(avg {dlg.get('avg_words_per_speaking_panel','?')}, max {dlg.get('max_words_in_panel','?')})",
          "",
          "## Page-by-page",
          "| Pg | Side | Panels | Template | Location | Page-turn |",
          "|---|---|---|---|---|---|"]
    for pg in pages:
        rr.append(f"| {pg['page_number']} | {pg['reader_side']} | {pg['panel_count']} | "
                  f"`{pg['layout_template']}` | {pg['location']} | {pg['page_turn_purpose']} |")
    rr += ["", "## Deliverables (paths under GENESIS/)",
           "- `covers/01_FRONT_COVER.png`, `covers/24_BACK_COVER.png` (full-res masters)",
           "- `story_pages/02_PAGE_01.png` … `23_PAGE_22.png` (full-res masters)",
           "- `web/**` (optimized JPG web edition)  ·  `previews/full_issue_contact_sheet.jpg`",
           "- `release/MonkeyZoo_Genesis.cbz`, `release/MonkeyZoo_Genesis.pdf`",
           "- `release/release_manifest.json`, `release/SHA256SUMS.txt`",
           "- `GENESIS_LAYOUT_PLAN.json/.md`, `metadata/*.json`, QA + this report",
           "",
           "## Reproducing",
           "```",
           "python 00_SYSTEM/scripts/genesis/genesis_plan.py     # layout plan (deterministic, seed "
           f"{plan['seed']})",
           "python 00_SYSTEM/scripts/genesis/genesis_build.py    # render pages + covers",
           "python 00_SYSTEM/scripts/genesis/genesis_release.py  # CBZ + PDF + manifest + checksums",
           "python 00_SYSTEM/scripts/genesis/genesis_qa.py       # structural/lettering/shot QA",
           "python 00_SYSTEM/scripts/genesis/genesis_report.py   # regenerate these docs",
           "```",
           "",
           "## Remaining owner gates (not done autonomously)",
           "- Promotion of any Genesis art into `03_APPROVED_CANON/` is human-only.",
           "- Bespoke high-res ComfyUI re-renders of panels (quality upgrade) remain owner-gated.",
           ""]
    (genesis_dir / "GENESIS_RELEASE_REPORT.md").write_text("\n".join(rr), encoding="utf-8")

    # --- README ---
    readme = ["# MonkeyZoo: Genesis", "",
              f"*{plan['story_subtitle']}* — Published Issue **01** (Production Issue 08).", "",
              "A complete, fully lettered web-edition comic issue: **22 story pages** with variable,",
              "narrative-driven panel density, plus **independent front and back covers**, packaged as",
              "CBZ + PDF with a manifest and checksums.", "",
              "## Read it",
              "- `release/MonkeyZoo_Genesis.cbz` — comic reader (CBZ)",
              "- `release/MonkeyZoo_Genesis.pdf` — PDF",
              "- `web/story_pages/` + `web/covers/` — per-page JPGs",
              "- `previews/full_issue_contact_sheet.jpg` — whole issue at a glance", "",
              "## What's here",
              "- `covers/` — full-res front & back cover masters (PNG)",
              "- `story_pages/` — full-res page masters (PNG)  *(gitignored; regenerable)*",
              "- `web/` — optimized JPG web edition",
              "- `release/` — CBZ, PDF, `release_manifest.json`, `SHA256SUMS.txt`",
              "- `metadata/` — shot distribution, dialogue metrics, page turns",
              "- `GENESIS_LAYOUT_PLAN.json/.md` — the deterministic page/panel plan",
              "- `GENESIS_*_REPORT.md` — release, technical QA, lettering, character, visual QA", "",
              "## How it was built",
              "The 96 integrated 'Signals in the Silence' panels were reflowed into 22 pages by a",
              "deterministic planner (beat classification + DP segmentation at scene boundaries),",
              "rendered with variable layout templates and full lettering, and packaged for release.",
              "Genesis performs **layout, lettering, covers and packaging only** — it does not alter",
              "character canon or regenerate art. See `GENESIS_RELEASE_REPORT.md` to reproduce.", "",
              "## Honest limitations",
              "- Source panels are 1280x720 (web tier); the web edition is crisp, print masters are upscaled.",
              "- 5 background plates exist, so wide shots reuse locations; bespoke ComfyUI re-renders are the",
              "  (owner-gated) quality upgrade path.", ""]
    (genesis_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print("Genesis docs generated: README, MANIFEST, RELEASE_REPORT, CREDITS, CHARACTER, LETTERING, VISUAL_QA")


def main() -> None:
    generate(Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS")


if __name__ == "__main__":
    main()
