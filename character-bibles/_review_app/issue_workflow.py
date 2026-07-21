"""Repository-backed production status for MonkeyZoo issue folders."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import os
import tempfile
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
STATE_FILE = ".workflow-status.json"
APPROVAL_GATES = {"canon_review", "script", "art_production", "qa", "release"}


class IssueWorkflowError(ValueError):
    pass


def _safe_issue_id(value: str) -> str:
    value = str(value or "")
    if not ISSUE_ID.fullmatch(value):
        raise IssueWorkflowError("Issue ID must match MZ-YYYY-MM-NN")
    return value


_ISSUE_PATH_CACHE: dict[tuple[str, str], Path] = {}


def find_issue(issue_id: str, root: Path) -> Path:
    issue_id = _safe_issue_id(issue_id)
    cache_key = (issue_id, str(root.resolve()))
    if cache_key in _ISSUE_PATH_CACHE:
        cached_path = _ISSUE_PATH_CACHE[cache_key]
        if cached_path.is_dir():
            return cached_path
    for folder in (root / "02_MONTHLY_ISSUES").iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if _read_issue_id(folder) == issue_id:
            _ISSUE_PATH_CACHE[cache_key] = folder
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
    if verdict == "PASS":
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
        if verdict != "passed": messages.append(f"QA verdict is {verdict}; exact PASS is required")
    elif stage_id == "release":
        exports = folder / "exports"
        has_pdf = exports.exists() and any(path.is_file() and path.stat().st_size > 0 for path in exports.glob("*.pdf"))
        has_package = exports.exists() and any(
            path.is_file() and path.stat().st_size > 0
            for path in list(exports.glob("*.zip")) + list(exports.glob("*.cbz"))
        )
        if not has_pdf or not has_package:
            messages.append("Release requires real PDF and CBZ/ZIP exports")
    elif stage_id == "published":
        year = folder.name[:4]
        primary = root / "05_RELEASE_ARCHIVE" / year / folder.name
        number = folder.name.split("_Issue_")[-1] if "_Issue_" in folder.name else ""
        legacy = root / "05_RELEASE_ARCHIVE" / year / f"Issue_{number}"
        if not primary.exists() and not legacy.exists():
            messages.append("Published status requires release archive evidence")
    return {"status": "passed" if not messages else "failed", "messages": messages, "missing_files": missing}


def _load_state(folder: Path) -> tuple[dict[str, Any], bool]:
    path = folder / STATE_FILE
    if not path.exists():
        return {"schema_version": "1.0", "active_stage": "intake", "transitions": [], "approvals": {}}, True
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise IssueWorkflowError("Malformed workflow state; history was not modified") from exc
    if not isinstance(state, dict) or state.get("schema_version") != "1.0" or state.get("active_stage") not in {s[0] for s in STAGES} or not isinstance(state.get("transitions"), list) or not isinstance(state.get("approvals"), dict):
        raise IssueWorkflowError("Malformed workflow state; history was not modified")
    return state, False


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try: os.unlink(temporary)
        except OSError: pass
        raise


def _approval(stage_id: str, state: dict[str, Any], artifact_hash: str) -> dict[str, Any]:
    required = stage_id in APPROVAL_GATES
    record = state["approvals"].get(stage_id)
    stale = bool(record and record.get("artifact_hash") != artifact_hash)
    approved = bool(record and record.get("approved") is True and not stale)
    return {"required": required, "approved": approved, "stale": stale, "record": record}


def workflow_status(folder: Path, root: Path) -> dict[str, Any]:
    issue_id = _read_issue_id(folder)
    if not issue_id:
        raise IssueWorkflowError("Issue has no valid issue ID")
    state, inferred = _load_state(folder)
    active_index = next(i for i, stage in enumerate(STAGES) if stage[0] == state["active_stage"])
    artifact_hash = _issue_hash(folder)
    stages = []
    for index, (sid, label, required) in enumerate(STAGES):
        validation = _stage_validation(sid, folder, root) if index == active_index else {"status": "not_run", "messages": [], "missing_files": []}
        approval = _approval(sid, state, artifact_hash)
        if index < active_index: stage_state = "complete"
        elif index > active_index: stage_state = "not_started"
        elif validation["status"] != "passed": stage_state = "current_blocked"
        elif approval["required"] and not approval["approved"]: stage_state = "awaiting_approval"
        else: stage_state = "current_ready"
        stages.append({"id": sid, "number": index + 1, "label": label, "state": stage_state, "required_files": required, "missing_files": validation["missing_files"], "validation": validation, "approval": approval})
    current = stages[active_index]
    blockers = list(current["validation"]["messages"])
    if current["approval"]["required"] and not current["approval"]["approved"]:
        blockers.append("Owner approval is stale" if current["approval"]["stale"] else "Owner approval is required")
    return {"issue_id": issue_id, "active_stage": current["id"], "current_stage": {k: current[k] for k in ("id", "number", "label", "state")}, "stages": stages, "blockers": blockers, "next_action": {"id": "advance", "label": f"Advance {current['label']}"}, "owner_approval_required": current["approval"]["required"], "approval": current["approval"], "state_source": "inferred", "state_notice": "Inferred from repository evidence; active stage defaults to Intake and no approval is inferred."} if inferred else {"issue_id": issue_id, "active_stage": current["id"], "current_stage": {k: current[k] for k in ("id", "number", "label", "state")}, "stages": stages, "blockers": blockers, "next_action": {"id": "advance", "label": f"Advance {current['label']}"}, "owner_approval_required": current["approval"]["required"], "approval": current["approval"], "state_source": "recorded", "state_notice": None}


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
    state, _ = _load_state(folder)
    current_id = state["active_stage"]
    if requested_stage not in {s[0] for s in STAGES}: raise IssueWorkflowError("Unknown stage")
    if requested_stage != current_id: raise IssueWorkflowError("Stage mismatch; stage skipping is not allowed")
    index = next(i for i, stage in enumerate(STAGES) if stage[0] == current_id)
    if index == len(STAGES) - 1: raise IssueWorkflowError("Published is terminal and cannot be advanced")
    validation = _stage_validation(current_id, folder, root)
    if validation["status"] != "passed": raise IssueWorkflowError("Advancement blocked: " + "; ".join(validation["messages"]))
    artifact_hash = _issue_hash(folder)
    approval = _approval(current_id, state, artifact_hash)
    if approval["required"] and not approval["approved"]: raise IssueWorkflowError("Owner approval is stale" if approval["stale"] else "Owner approval is required")
    next_id = STAGES[index + 1][0]
    record = {"completed_stage": current_id, "from_stage": current_id, "to_stage": next_id, "validated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "artifact_hash": artifact_hash, "approval": {"required": approval["required"], "record_stage": current_id if approval["required"] else None}}
    state["transitions"].append(record)
    state["active_stage"] = next_id
    _atomic_write(folder / STATE_FILE, state)
    return workflow_status(folder, root)


def record_approval(folder: Path, root: Path, requested_stage: str | None, approved: Any, note: Any = None) -> dict[str, Any]:
    state, _ = _load_state(folder)
    stage = state["active_stage"]
    if requested_stage not in {s[0] for s in STAGES}: raise IssueWorkflowError("Unknown stage")
    if requested_stage != stage: raise IssueWorkflowError("Stage mismatch; approval applies only to the active stage")
    if stage not in APPROVAL_GATES: raise IssueWorkflowError("Active stage does not require owner approval")
    if approved is not True: raise IssueWorkflowError("Approval request must explicitly set approved to true")
    validation = _stage_validation(stage, folder, root)
    if validation["status"] != "passed": raise IssueWorkflowError("Approval blocked: " + "; ".join(validation["messages"]))
    state["approvals"][stage] = {"stage": stage, "approved": True, "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "artifact_hash": _issue_hash(folder), "note": str(note)[:500] if note else None, "actor": "project_owner"}
    _atomic_write(folder / STATE_FILE, state)
    return workflow_status(folder, root)


def _issue_hash(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file() and p.name != STATE_FILE and not p.name.endswith(".tmp")):
        digest.update(str(path.relative_to(folder)).encode()); digest.update(path.read_bytes())
    return digest.hexdigest()
