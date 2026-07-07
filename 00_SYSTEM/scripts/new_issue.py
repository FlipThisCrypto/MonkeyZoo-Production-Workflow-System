#!/usr/bin/env python3
"""Scaffold a new MonkeyZoo monthly issue folder.

Usage:
    python new_issue.py 2026-08 6 "Working Title"

Creates /02_MONTHLY_ISSUES/YYYY-MM_Issue_##/ with all required stubs and
subfolders, plus the matching /01_IDEAS_INBOX/YYYY-MM-idea.md if missing.
"""
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]

SUBDIRS = [
    "references/character_refs", "references/background_refs",
    "references/pose_refs", "references/previous_issue_refs",
    "generated_art/raw_panels", "generated_art/selected_panels",
    "generated_art/upscaled", "generated_art/edited",
    "layout/print_layout", "layout/web_layout", "layout/social_crops",
    "exports/promo_images",
]

BRIEF_FIELDS = [
    "Issue ID", "Issue Month", "Issue Number", "Working Title", "Core Idea",
    "Theme", "Satire Target", "Emotional Core", "Main Character",
    "Supporting Characters", "Conflict", "Antagonist or Problem", "Setting",
    "Running Joke", "Ending", "Next Issue Teaser", "Required Visuals",
    "Forbidden Changes", "Continuity Risks", "Release Assets Needed",
]


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    month, number = sys.argv[1], int(sys.argv[2])
    title = sys.argv[3] if len(sys.argv) > 3 else "Untitled"
    issue_id = f"MZ-{month}-{number:02d}"
    folder = FACTORY / "02_MONTHLY_ISSUES" / f"{month}_Issue_{number:02d}"

    if folder.exists():
        sys.exit(f"ABORT: {folder} already exists.")

    for sub in SUBDIRS:
        (folder / sub).mkdir(parents=True, exist_ok=True)

    brief = [f"{f}: " for f in BRIEF_FIELDS]
    brief[0] = f"Issue ID: {issue_id}"
    brief[1] = f"Issue Month: {month}"
    brief[2] = f"Issue Number: {number}"
    brief[3] = f"Working Title: {title}"
    (folder / "issue_brief.md").write_text("\n".join(brief) + "\n", encoding="utf-8")

    stubs = {
        "issue_outline.md": f"# {issue_id} — {title}\n\n(Stage 3 output)\n",
        "issue_script.md": f"# {issue_id} — {title} — Script\n\n(Stage 4 output)\n",
        "cover_prompt.md": "# Main cover\n\n# Variant cover\n",
        "social_posts.md": "## Launch post\n\n## Twitter/X\n\n## Facebook\n\n"
                           "## Discord\n\n## Newsletter blurb\n\n## Issue summary\n\n"
                           "## Alt text\n\n## Teaser post\n",
        "qa_report.md": f"# {issue_id} QA Report\n\n## Art QA\n\n## Final QA\nVERDICT: PENDING\n",
        "final_export_checklist.md": f"# {issue_id} Final Export Checklist\n\n(Stage 9 output)\n",
        "page_panel_plan.json": '{\n  "issue_id": "%s",\n  "issue_title": "%s",\n'
                                '  "page_count": 8,\n  "pages": []\n}\n' % (issue_id, title),
        "art_prompt_pack.json": '{\n  "issue_id": "%s",\n  "style_lock_phrase": "",\n'
                                '  "base_negative_prompt": "",\n  "panels": []\n}\n' % issue_id,
        "metadata.json": "{}\n",
        "generation_log.md": f"# {issue_id} Generation Log\n",
    }
    for name, content in stubs.items():
        (folder / name).write_text(content, encoding="utf-8")

    idea = FACTORY / "01_IDEAS_INBOX" / f"{month}-idea.md"
    if not idea.exists():
        idea.write_text(f"# Idea for {issue_id} — drop rough idea here\n", encoding="utf-8")

    print(f"Scaffolded {folder}")


if __name__ == "__main__":
    main()
