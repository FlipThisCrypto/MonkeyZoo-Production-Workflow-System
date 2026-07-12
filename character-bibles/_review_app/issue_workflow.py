"""Repository-backed production status for MonkeyZoo issue folders."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import bible_store

ISSUE_ID = re.compile(r"^MZ-\d{4}-\d{2}-\d{2}$")
STAGES = [
    ("intake", "Intake", ["issue_brief.md", "metadata.json"]),
    ("canon_review", "Canon Review", []),
    ("outline", "Outline", ["issue_outline.md"]),
    ("script", "Script", ["issue_script.md"]),
    ("page_plan", "Page & Panel Plan", ["page_panel_plan.json"]),
    ("art_prompts", "Art Prompt Pack", ["art_prompt_pack.json"]),
    ("art_production", "Art Production", []),
    ("qa", "Quality Assurance", ["qa_report.md"]),
    ("release", "Release Package", ["cover_prompt.md", "metadata.json", "social_posts.md", "final_export_checklist.md"]),
    ("published", "Published", []),
]
ARTIFACT_GROUPS = {
    "Intake": ["issue_brief.md", "metadata.json"], "Outline": ["issue_outline.md"],
    "Script": ["issue_script.md"], "Plans": ["page_panel_plan.json"],
    "Prompts": ["art_prompt_pack.json"], "QA": ["qa_report.md"],
    "Covers": ["cover_prompt.md"], "Social": ["social_posts.md"],
    "Release": ["final_export_checklist.md"],
}


class IssueWorkflowError(ValueError):
    pass


def _safe_issue_id(value: str) -> str:
    value = str(value or "")
    if not ISSUE_ID.fullmatch(value):
        raise IssueWorkflowError("Issue ID must match MZ-YYYY-MM-NN")
    return value


def find_issue(issue_id: str, root: Path) -> Path:
    issue_id = _safe_issue_id(issue_id)
    for folder in (root / "02_MONTHLY_ISSUES").iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if _read_issue_id(folder) == issue_id:
            return folder
    raise IssueWorkflowError(f"Unknown issue: {issue_id}")


def _read_issue_id(folder: Path) -> str | None:
    metadata = _json(folder / "metadata.json") or {}
    if metadata.get("issue_id"):
        return metadata["issue_id"]
    brief = folder / "issue_brief.md"
    if brief.exists():
        match = re.search(r"^Issue ID:\s*(\S+)", brief.read_text(encoding="utf-8", errors="replace"), re.M)
        if match:
            return match.group(1)
    for candidate in (folder / "page_panel_plan.json", folder / "art_prompt_pack.json"):
        data = _json(candidate) or {}
        if data.get("issue_id"):
            return data["issue_id"]
    return None


def _json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _brief_fields(folder: Path) -> dict[str, str]:
    path = folder / "issue_brief.md"
    result = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
    return result


def _schema_errors(path: Path, schema: Path) -> list[str]:
    data = _json(path)
    if data is None:
        return [f"{path.name} is missing or malformed"]
    spec = json.loads(schema.read_text(encoding="utf-8"))
    return [error.message for error in Draft202012Validator(spec).iter_errors(data)]


def _qa_verdict(folder: Path) -> str:
    path = folder / "qa_report.md"
    if not path.exists():
        return "missing"
    text = path.read_text(encoding="utf-8", errors="replace").upper()
    verdicts = re.findall(r"VERDICT:\s*([^\r\n]+)", text)
    verdict = verdicts[-1].strip() if verdicts else "MISSING"
    if verdict.startswith("RELEASE") or verdict.startswith("PASS"):
        return "passed"
    if verdict.startswith("HOLD") or verdict.startswith("FAIL"):
        return "failed"
    return "pending"


def _stage_validation(stage_id: str, folder: Path, root: Path) -> dict[str, Any]:
    required = dict((sid, files) for sid, _, files in STAGES)[stage_id]
    missing = [name for name in required if not (folder / name).is_file() or (folder / name).stat().st_size == 0]
    messages = [f"Missing required file: {name}" for name in missing]
    if stage_id == "canon_review":
        fields = _brief_fields(folder)
        ids = [fields.get("Main Character"), fields.get("Supporting Characters")]
        for raw in filter(None, ids):
            for value in [item.strip() for item in raw.split(",") if item.strip()]:
                try: bible_store.resolve_character_id(value, root / "character-bibles")
                except ValueError: messages.append(f"Character bible unavailable: {value}")
    elif stage_id == "page_plan" and not missing:
        messages += _schema_errors(folder / "page_panel_plan.json", root / "00_SYSTEM" / "page_panel_plan_schema.json")
    elif stage_id == "art_prompts" and not missing:
        messages += _schema_errors(folder / "art_prompt_pack.json", root / "00_SYSTEM" / "art_prompt_pack_schema.json")
    elif stage_id == "art_production":
        plan = _json(folder / "page_panel_plan.json") or {}
        planned = [panel.get("panel_id") for page in plan.get("pages", []) for panel in page.get("panels", []) if panel.get("panel_id")]
        selected = folder / "generated_art" / "selected_panels"
        missing_art = [pid for pid in planned if not (selected / f"{pid}.png").exists()]
        if not planned: messages.append("A valid page plan is required before art production")
        if missing_art: messages.append(f"Missing selected art for {len(missing_art)} planned panel(s)")
    elif stage_id == "qa":
        verdict = _qa_verdict(folder)
        if verdict != "passed": messages.append(f"QA verdict is {verdict}; RELEASE or PASS is required")
    elif stage_id == "release":
        exports = folder / "exports"
        if not exports.exists() or not any(exports.glob("*.pdf")) or not any(exports.glob("*.zip")):
            messages.append("Release requires real PDF and CBZ/ZIP exports")
    elif stage_id == "published":
        number = folder.name.split("_Issue_")[-1] if "_Issue_" in folder.name else ""
        archive = root / "05_RELEASE_ARCHIVE" / folder.name[:4] / f"Issue_{number}"
        if not archive.exists(): messages.append("Published status requires release archive evidence")
    return {"status": "passed" if not messages else "failed", "messages": messages, "missing_files": missing}


def workflow_status(folder: Path, root: Path) -> dict[str, Any]:
    issue_id = _read_issue_id(folder)
    if not issue_id:
        raise IssueWorkflowError("Issue has no valid issue ID")
    validations = [_stage_validation(sid, folder, root) for sid, _, _ in STAGES]
    first_failed = next((i for i, val in enumerate(validations) if val["status"] != "passed"), len(STAGES) - 1)
    stages = []
    for index, ((sid, label, required), validation) in enumerate(zip(STAGES, validations)):
        if index < first_failed: state = "complete"
        elif index == first_failed: state = "blocked" if validation["messages"] else "current"
        else: state = "not_started"
        stages.append({"id": sid, "number": index + 1, "label": label, "state": state, "required_files": required, "missing_files": validation["missing_files"], "validation": validation})
    current = stages[first_failed]
    return {"issue_id": issue_id, "current_stage": {k: current[k] for k in ("id", "number", "label", "state")}, "stages": stages, "blockers": current["validation"]["messages"], "next_action": {"id": "validate", "label": f"Validate {current['label']}"}, "owner_approval_required": current["id"] in {"canon_review", "qa", "release"}}


def issue_detail(folder: Path, root: Path) -> dict[str, Any]:
    metadata, brief = _json(folder / "metadata.json") or {}, _brief_fields(folder)
    workflow = workflow_status(folder, root)
    artifacts = []
    for group, names in ARTIFACT_GROUPS.items():
        for name in names:
            path = folder / name
            artifacts.append({"group": group, "name": name, "exists": path.is_file(), "modified": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None, "viewable": path.suffix.lower() in {".md", ".txt", ".json", ".png", ".webp"}})
    modified = max((p.stat().st_mtime for p in folder.rglob("*") if p.is_file()), default=folder.stat().st_mtime)
    return {"issue_id": workflow["issue_id"], "title": metadata.get("title") or metadata.get("name") or brief.get("Working Title") or "Title unavailable", "edition_number": metadata.get("edition_number") or brief.get("Issue Number"), "period": metadata.get("issue_month") or brief.get("Issue Month"), "primary_character": metadata.get("primary_character") or brief.get("Main Character"), "guest_character": metadata.get("guest_character") or brief.get("Supporting Characters"), "location": str(folder.relative_to(root)), "last_updated": dt.datetime.fromtimestamp(modified).isoformat(timespec="seconds"), "validation_state": "blocked" if workflow["blockers"] else "passed", "blocker_count": len(workflow["blockers"]), "workflow": workflow, "artifacts": artifacts, "degraded": False}


def list_issues(root: Path) -> list[dict[str, Any]]:
    result = []
    for folder in sorted((root / "02_MONTHLY_ISSUES").iterdir()):
        if not folder.is_dir() or folder.name.startswith("."): continue
        try: result.append(issue_detail(folder, root))
        except Exception as exc: result.append({"issue_id": _read_issue_id(folder) or folder.name, "title": "Malformed legacy issue", "degraded": True, "error": str(exc), "location": str(folder.relative_to(root)), "blocker_count": 1, "validation_state": "degraded"})
    return result


def view_artifact(folder: Path, relative: str) -> dict[str, Any]:
    if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise IssueWorkflowError("Unsafe artifact path")
    path = (folder / relative).resolve()
    try: path.relative_to(folder.resolve())
    except ValueError: raise IssueWorkflowError("Artifact path escapes issue folder") from None
    if not path.is_file(): raise IssueWorkflowError("Artifact does not exist")
    if path.suffix.lower() not in {".md", ".txt", ".json"}: raise IssueWorkflowError("Artifact is not text-viewable")
    return {"name": relative, "type": path.suffix.lower(), "content": path.read_text(encoding="utf-8", errors="replace")}


def record_advance(folder: Path, root: Path, requested_stage: str | None) -> dict[str, Any]:
    status = workflow_status(folder, root)
    current = status["current_stage"]
    if requested_stage and requested_stage != current["id"]: raise IssueWorkflowError("Stage skipping is not allowed")
    validation = _stage_validation(current["id"], folder, root)
    if validation["status"] != "passed": raise IssueWorkflowError("Advancement blocked: " + "; ".join(validation["messages"]))
    record = {"stage": current["id"], "validated_at": dt.datetime.now().isoformat(timespec="seconds"), "artifact_hash": _issue_hash(folder), "approved": False}
    path = folder / ".workflow-status.json"
    history = _json(path) or {"transitions": []}
    history["transitions"].append(record)
    path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    return workflow_status(folder, root)


def _issue_hash(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file() and p.name != ".workflow-status.json"):
        digest.update(str(path.relative_to(folder)).encode()); digest.update(path.read_bytes())
    return digest.hexdigest()
