#!/usr/bin/env python3
"""Atomically initialize a MonkeyZoo monthly issue intake package."""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

FACTORY = Path(__file__).resolve().parents[2]
ISSUE_ID_RE = re.compile(r"^MZ-\d{4}-\d{2}-\d{2}$")
CHARACTER_ID_RE = re.compile(r"^MZ-CHAR-[A-Z0-9-]+$")
OUTPUT_REQUIREMENTS = {"cover", "metadata", "social copy", "QA"}
SUBDIRS = [
    "references/character_refs", "references/background_refs", "references/pose_refs",
    "references/previous_issue_refs", "generated_art/raw_panels", "generated_art/selected_panels",
    "generated_art/upscaled", "generated_art/edited", "layout/print_layout",
    "layout/web_layout", "layout/social_crops", "exports/promo_images",
]
BRIEF_FIELDS = [
    "Issue ID", "Issue Month", "Issue Number", "Working Title", "Issue Type", "Core Idea",
    "Opening Situation", "Theme", "Satire Target", "Emotional Core", "Main Character",
    "Supporting Characters", "Conflict", "Antagonist or Problem", "Setting", "Running Joke",
    "Ending", "Next Issue Teaser", "Required Visuals", "Required Canon References",
    "Forbidden Changes", "Continuity Risks", "Page Count", "Panel Count", "Release Assets Needed",
]


class IssueCreationError(ValueError):
    pass


def _text(data: dict[str, Any], name: str, *, required: bool = False) -> str:
    value = data.get(name)
    if value is None or value == "":
        if required:
            raise IssueCreationError(f"Missing required field: {name}")
        return ""
    if not isinstance(value, str):
        raise IssueCreationError(f"{name} must be text")
    value = value.strip()
    if required and not value:
        raise IssueCreationError(f"Missing required field: {name}")
    return value


def _integer(data: dict[str, Any], name: str, minimum: int, maximum: int, default: int | None = None) -> int:
    value = data.get(name, default)
    if isinstance(value, bool) or value is None:
        raise IssueCreationError(f"{name} must be an integer between {minimum} and {maximum}")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise IssueCreationError(f"{name} must be an integer between {minimum} and {maximum}") from None
    if isinstance(value, float) and not value.is_integer() or isinstance(value, str) and not re.fullmatch(r"[+-]?\d+", value.strip()):
        raise IssueCreationError(f"{name} must be an integer between {minimum} and {maximum}")
    if not minimum <= number <= maximum:
        raise IssueCreationError(f"{name} must be between {minimum} and {maximum}")
    return number


def normalize_request(data: Any, factory: Path = FACTORY) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise IssueCreationError("Request body must be a JSON object")
    normalized = {name: _text(data, name, required=True) for name in (
        "issue_id", "title", "primary_character", "core_premise", "main_conflict",
        "emotional_goal", "opening_situation", "ending_direction",
    )}
    for name in ("issue_type", "guest_character", "required_canon_references", "prohibited_story_elements"):
        normalized[name] = _text(data, name)
    normalized["issue_type"] = normalized["issue_type"] or "Monthly"
    for name, limits, default in (
        ("year", (2000, 2100), None), ("month", (1, 12), None),
        ("edition_number", (1, 999), None), ("page_count", (1, 64), 8),
        ("panel_count", (1, 300), 20),
    ):
        normalized[name] = _integer(data, name, *limits, default)
    if not ISSUE_ID_RE.fullmatch(normalized["issue_id"]):
        raise IssueCreationError("issue_id must match MZ-YYYY-MM-NN and contain no traversal or unsafe characters")
    expected_prefix = f"MZ-{normalized['year']:04d}-{normalized['month']:02d}-"
    if not normalized["issue_id"].startswith(expected_prefix):
        raise IssueCreationError("issue_id year and month must match the submitted year and month")
    if any(ch in normalized["title"] for ch in '<>:"/\\|?*') or ".." in normalized["title"]:
        raise IssueCreationError("title contains unsafe path characters")
    for field in ("primary_character", "guest_character"):
        cid = normalized[field]
        if not cid:
            continue
        if not CHARACTER_ID_RE.fullmatch(cid):
            raise IssueCreationError(f"{field} is malformed")
        if not (factory / "character-bibles" / cid / "bible.yaml").is_file():
            raise IssueCreationError(f"Unknown character or missing bible: {cid}")
    if normalized["guest_character"] and normalized["guest_character"] == normalized["primary_character"]:
        raise IssueCreationError("guest_character must differ from primary_character")
    requirements = data.get("output_requirements", sorted(OUTPUT_REQUIREMENTS))
    if not isinstance(requirements, list) or any(not isinstance(item, str) or item not in OUTPUT_REQUIREMENTS for item in requirements):
        raise IssueCreationError("output_requirements must be a list containing only: cover, metadata, social copy, QA")
    normalized["output_requirements"] = sorted(set(requirements))
    normalized["period"] = f"{normalized['year']:04d}-{normalized['month']:02d}"
    normalized["folder_name"] = f"{normalized['period']}_Issue_{normalized['edition_number']:02d}"
    return normalized


def _character_name(character_id: str, factory: Path) -> str:
    import yaml
    data = yaml.safe_load((factory / "character-bibles" / character_id / "bible.yaml").read_text(encoding="utf-8")) or {}
    return str((data.get("identification") or {}).get("current_display_name") or character_id)


def _contents(n: dict[str, Any], factory: Path) -> dict[str, str]:
    primary_name = _character_name(n["primary_character"], factory)
    guest_names = [_character_name(n["guest_character"], factory)] if n["guest_character"] else []
    values = {
        "Issue ID": n["issue_id"], "Issue Month": n["period"], "Issue Number": n["edition_number"],
        "Working Title": n["title"], "Issue Type": n["issue_type"], "Core Idea": n["core_premise"],
        "Opening Situation": n["opening_situation"], "Theme": n["emotional_goal"], "Emotional Core": n["emotional_goal"],
        "Main Character": n["primary_character"], "Supporting Characters": n["guest_character"],
        "Conflict": n["main_conflict"], "Antagonist or Problem": n["main_conflict"], "Ending": n["ending_direction"],
        "Required Canon References": n["required_canon_references"], "Forbidden Changes": n["prohibited_story_elements"],
        "Continuity Risks": n["required_canon_references"], "Page Count": n["page_count"], "Panel Count": n["panel_count"],
        "Release Assets Needed": ", ".join(n["output_requirements"]),
    }
    brief_json = {
        "issue_id": n["issue_id"], "issue_month": n["period"], "issue_number": n["edition_number"],
        "working_title": n["title"], "core_idea": n["core_premise"], "theme": n["emotional_goal"],
        "satire_target": "To be established during concept stage", "emotional_core": n["emotional_goal"],
        "main_character": primary_name, "supporting_characters": guest_names, "conflict": n["main_conflict"],
        "antagonist_or_problem": n["main_conflict"], "setting": n["opening_situation"],
        "running_joke": "To be established during concept stage", "ending": n["ending_direction"],
        "next_issue_teaser": "To be established during concept stage", "required_visuals": [],
        "forbidden_changes": [n["prohibited_story_elements"]] if n["prohibited_story_elements"] else [],
        "continuity_risks": [n["required_canon_references"]] if n["required_canon_references"] else [],
        "release_assets_needed": n["output_requirements"],
    }
    metadata = {key: n[key] for key in (
        "issue_id", "title", "issue_type", "year", "month", "edition_number", "page_count", "panel_count",
        "primary_character", "guest_character", "opening_situation", "required_canon_references",
        "prohibited_story_elements", "output_requirements",
    )}
    metadata.update({"status": "intake", "workflow_stage": "1. Intake"})
    return {
        "issue_brief.md": "\n".join(f"{field}: {values.get(field, '')}" for field in BRIEF_FIELDS) + "\n",
        "issue_brief.json": json.dumps(brief_json, indent=2, ensure_ascii=False) + "\n",
        "issue_outline.md": f"# {n['issue_id']} — {n['title']}\n\n(Stage 3 output)\n",
        "issue_script.md": f"# {n['issue_id']} — {n['title']} — Script\n\n(Stage 4 output)\n",
        "cover_prompt.md": "# Main cover\n\n# Variant cover\n",
        "social_posts.md": "## Launch post\n\n## Twitter/X\n\n## Facebook\n\n## Discord\n\n## Newsletter blurb\n\n## Issue summary\n\n## Alt text\n\n## Teaser post\n",
        "qa_report.md": f"# {n['issue_id']} QA Report\n\n## Art QA\n\n## Final QA\nVERDICT: PENDING\n",
        "final_export_checklist.md": f"# {n['issue_id']} Final Export Checklist\n\n(Stage 9 output)\n",
        "metadata.json": json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        "generation_log.md": f"# {n['issue_id']} Generation Log\n",
    }


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def create_issue(data: Any, factory: Path = FACTORY) -> dict[str, Any]:
    n = normalize_request(data, factory)
    contents = _contents(n, factory)
    issues_root = factory / "02_MONTHLY_ISSUES"
    final = issues_root / n["folder_name"]
    existing_id = any(
        f"Issue ID: {n['issue_id']}" in path.read_text(encoding="utf-8", errors="ignore")
        for path in issues_root.glob("*_Issue_*/issue_brief.md")
    )
    if final.exists():
        raise IssueCreationError("Edition folder already exists")
    if existing_id:
        raise IssueCreationError("Issue ID already exists")
    temp = issues_root / f".{n['folder_name']}.creating-{uuid.uuid4().hex}"
    idea = factory / "01_IDEAS_INBOX" / f"{n['period']}-idea.md"
    idea_temp = idea.with_name(f".{idea.name}.creating-{uuid.uuid4().hex}") if not idea.exists() else None
    finalized = False
    try:
        temp.mkdir(parents=False)
        for subdir in SUBDIRS:
            (temp / subdir).mkdir(parents=True)
        for name, content in contents.items():
            _write_text(temp / name, content)
        for name in contents:
            if not (temp / name).is_file():
                raise OSError(f"Required issue file was not written: {name}")
        if idea_temp:
            _write_text(idea_temp, f"# Idea for {n['issue_id']}\n\nOpening situation: {n['opening_situation']}\n")
        os.rename(temp, final)
        finalized = True
        if idea_temp:
            os.rename(idea_temp, idea)
    except IssueCreationError:
        raise
    except Exception as exc:
        if finalized and final.exists():
            shutil.rmtree(final)
        raise IssueCreationError("Issue creation failed; no files were committed") from exc
    finally:
        if temp.exists():
            shutil.rmtree(temp, ignore_errors=True)
        if idea_temp and idea_temp.exists():
            idea_temp.unlink(missing_ok=True)
    return {"ok": True, "issue_id": n["issue_id"], "location": str(final.relative_to(factory)), "files_created": sorted(contents), "stage": "1. Intake", "validation_status": "initialized"}


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python new_issue.py YYYY-MM NUMBER [TITLE]")
    year, month = map(int, sys.argv[1].split("-"))
    number = int(sys.argv[2])
    raise SystemExit("The CLI now requires the complete guided intake payload; use MonkeyZoo Studio.")


if __name__ == "__main__":
    main()
