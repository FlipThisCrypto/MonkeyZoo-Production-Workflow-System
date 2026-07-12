#!/usr/bin/env python3
"""Scaffold a new MonkeyZoo monthly issue folder.

Usage:
    python new_issue.py 2026-08 6 "Working Title"

Creates /02_MONTHLY_ISSUES/YYYY-MM_Issue_##/ with all required stubs and
subfolders, plus the matching /01_IDEAS_INBOX/YYYY-MM-idea.md if missing.
"""
import json
import re
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

class IssueCreationError(ValueError):
    pass

def create_issue(data: dict, factory: Path = FACTORY) -> dict:
    required = ["issue_id", "title", "month", "year", "edition_number", "primary_character", "core_premise", "main_conflict", "emotional_goal", "opening_situation", "ending_direction"]
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise IssueCreationError("Missing required fields: " + ", ".join(missing))
    issue_id = str(data["issue_id"]).strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}", issue_id):
        raise IssueCreationError("Issue ID must use only letters, numbers, hyphens, and underscores")
    year, month = int(data["year"]), int(data["month"])
    number = int(data["edition_number"])
    if not (2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= number <= 999):
        raise IssueCreationError("Year, month, or edition number is out of range")
    title = str(data["title"]).strip()
    if any(ch in title for ch in '<>:"/\\|?*'):
        raise IssueCreationError("Title contains invalid path characters")
    character_id = str(data["primary_character"])
    if not (factory / "character-bibles" / character_id / "bible.yaml").is_file():
        raise IssueCreationError(f"Unknown character or missing bible: {character_id}")
    guest = str(data.get("guest_character") or "").strip()
    if guest and not (factory / "character-bibles" / guest / "bible.yaml").is_file():
        raise IssueCreationError(f"Unknown guest character or missing bible: {guest}")
    period = f"{year:04d}-{month:02d}"
    folder = factory / "02_MONTHLY_ISSUES" / f"{period}_Issue_{number:02d}"
    existing_ids = [p for p in (factory / "02_MONTHLY_ISSUES").glob("*/issue_brief.md") if f"Issue ID: {issue_id}" in p.read_text(encoding="utf-8", errors="ignore")]
    if folder.exists() or existing_ids:
        raise IssueCreationError("Issue ID or edition folder already exists")
    for sub in SUBDIRS:
        (folder / sub).mkdir(parents=True, exist_ok=False)
    values = {
        "Issue ID": issue_id, "Issue Month": period, "Issue Number": number,
        "Working Title": title, "Core Idea": data["core_premise"],
        "Theme": data["emotional_goal"], "Emotional Core": data["emotional_goal"],
        "Main Character": character_id, "Supporting Characters": guest,
        "Conflict": data["main_conflict"], "Antagonist or Problem": data["main_conflict"],
        "Ending": data["ending_direction"], "Forbidden Changes": data.get("prohibited_story_elements", ""),
        "Continuity Risks": data.get("required_canon_references", ""),
        "Release Assets Needed": ", ".join(data.get("output_requirements", ["cover", "metadata", "social copy", "QA"])),
    }
    (folder / "issue_brief.md").write_text("\n".join(f"{f}: {values.get(f, '')}" for f in BRIEF_FIELDS) + "\n", encoding="utf-8")
    page_count, panel_count = int(data.get("page_count", 8)), int(data.get("panel_count", 20))
    stubs = _stub_files(issue_id, title, page_count, panel_count)
    for name, content in stubs.items():
        (folder / name).write_text(content, encoding="utf-8")
    idea = factory / "01_IDEAS_INBOX" / f"{period}-idea.md"
    if not idea.exists():
        idea.write_text(f"# Idea for {issue_id} — {data['opening_situation']}\n", encoding="utf-8")
    return {"ok": True, "issue_id": issue_id, "location": str(folder.relative_to(factory)), "files_created": sorted(["issue_brief.md", *stubs]), "stage": "1. Intake", "validation_status": "initialized"}

def _stub_files(issue_id: str, title: str, page_count: int = 8, panel_count: int = 20) -> dict:
    return {
        "issue_outline.md": f"# {issue_id} — {title}\n\n(Stage 3 output)\n",
        "issue_script.md": f"# {issue_id} — {title} — Script\n\n(Stage 4 output)\n",
        "cover_prompt.md": "# Main cover\n\n# Variant cover\n",
        "social_posts.md": "## Launch post\n\n## Twitter/X\n\n## Facebook\n\n## Discord\n\n## Newsletter blurb\n\n## Issue summary\n\n## Alt text\n\n## Teaser post\n",
        "qa_report.md": f"# {issue_id} QA Report\n\n## Art QA\n\n## Final QA\nVERDICT: PENDING\n",
        "final_export_checklist.md": f"# {issue_id} Final Export Checklist\n\n(Stage 9 output)\n",
        "page_panel_plan.json": json.dumps({"issue_id": issue_id, "issue_title": title, "page_count": page_count, "panel_count": panel_count, "pages": []}, indent=2) + "\n",
        "art_prompt_pack.json": json.dumps({"issue_id": issue_id, "style_lock_phrase": "", "base_negative_prompt": "", "panels": []}, indent=2) + "\n",
        "metadata.json": json.dumps({"issue_id": issue_id, "title": title, "status": "intake", "page_count": page_count, "panel_count": panel_count}, indent=2) + "\n",
        "generation_log.md": f"# {issue_id} Generation Log\n",
    }


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
