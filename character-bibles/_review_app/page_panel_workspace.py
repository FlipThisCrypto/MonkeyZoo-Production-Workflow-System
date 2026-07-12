"""Stateful Page & Panel Planning workspace backed by canonical scripts."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

import bible_store
import issue_workflow

VARIANT_ID = re.compile(r"^plan-\d{8}T\d{6}Z-[0-9a-f]{6}$")
PAGE = re.compile(r"^###\s+Page\s+(\d+)\s*(?:[-—]\s*(.*))?$", re.I | re.M)
PANEL = re.compile(r"^\*\*Panel\s+(\d+)\.(\d+)\s*\(([^)]*)\)\*\*\s*$", re.I | re.M)
FIELDS = {"location":"location", "characters":"characters", "camera":"camera_angle", "action":"action", "emotion":"emotion", "dialogue":"dialogue", "caption":"caption", "sfx":"sfx", "visual notes":"visual_notes", "continuity notes":"continuity_notes", "props":"props"}


class PagePanelError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message); self.status = status


def _now() -> str: return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def _hash_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _hash_json(data: Any) -> str: return _hash_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try: os.unlink(temp)
        except OSError: pass
        raise


def _write_json(path: Path, data: Any) -> None: _atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc: raise PagePanelError(f"Malformed layout workspace record: {path.name}") from exc


def _workspace(folder: Path) -> Path: return folder / ".layout-workspace"
def _script_path(folder: Path) -> Path: return folder / "issue_script.md"


def _require_stage(folder: Path, root: Path) -> None:
    active = issue_workflow.workflow_status(folder, root)["active_stage"]
    if active != "page_plan": raise PagePanelError(f"Layout workspace requires active workflow stage page_plan; current stage is {active}", 409)


@contextmanager
def _promotion_lock(folder: Path):
    path = _workspace(folder) / ".promotion.lock"; path.parent.mkdir(parents=True, exist_ok=True)
    try: fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError: raise PagePanelError("Another plan promotion is already in progress", 409) from None
    try:
        os.write(fd, _now().encode()); os.fsync(fd); os.close(fd); yield
    finally:
        try: os.close(fd)
        except OSError: pass
        try: path.unlink()
        except OSError: pass


def _variant_id(plan: dict[str, Any]) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"plan-{stamp}-{_hash_bytes((_hash_json(plan)+str(time.time_ns())).encode())[:6]}"


def _safe_variant(value: str) -> str:
    if not VARIANT_ID.fullmatch(str(value or "")): raise PagePanelError("Invalid plan variant ID")
    return value


def _field_block(text: str) -> dict[str, str]:
    result = {}
    for line in text.splitlines():
        match = re.match(r"^-\s*([^:]+):\s*(.*)$", line.strip())
        if match and match.group(1).strip().lower() in FIELDS:
            result[FIELDS[match.group(1).strip().lower()]] = match.group(2).strip()
    return result


def parse_script(folder: Path, root: Path) -> dict[str, Any]:
    path = _script_path(folder)
    if not path.is_file() or not path.stat().st_size: raise PagePanelError("Canonical issue_script.md is missing", 409)
    text = path.read_text(encoding="utf-8", errors="replace")
    issue_id = issue_workflow._read_issue_id(folder)
    metadata = issue_workflow._json(folder / "metadata.json") or {}
    pages = []
    page_matches = list(PAGE.finditer(text))
    for page_index, page_match in enumerate(page_matches):
        start = page_match.end(); end = page_matches[page_index + 1].start() if page_index + 1 < len(page_matches) else len(text)
        page_text = text[start:end]; panels = []
        panel_matches = list(PANEL.finditer(page_text))
        for panel_index, panel_match in enumerate(panel_matches):
            block_end = panel_matches[panel_index + 1].start() if panel_index + 1 < len(panel_matches) else len(page_text)
            fields = _field_block(page_text[panel_match.end():block_end])
            raw_characters = [v.strip() for v in fields.get("characters", "").split(",") if v.strip() and v.strip() not in {"—", "-"}]
            characters, character_errors = [], []
            for value in raw_characters:
                try:
                    canonical = bible_store.resolve_character_id(value, root / "character-bibles")
                    if canonical not in characters: characters.append(canonical)
                except ValueError: character_errors.append(value)
            size_text = panel_match.group(3).lower()
            size = next((candidate for candidate in ("half","third","full","splash") if candidate in size_text), "full")
            page_number, panel_number = int(panel_match.group(1)), int(panel_match.group(2))
            panels.append({"panel_id":f"{issue_id}_P{page_number:02d}_PANEL{panel_number:02d}", "panel_size":size, "characters":characters, "location":fields.get("location", ""), "camera_angle":fields.get("camera_angle", ""), "action":fields.get("action", ""), "emotion":fields.get("emotion", ""), "dialogue":fields.get("dialogue", ""), "caption":fields.get("caption", ""), "sfx":fields.get("sfx", ""), "visual_notes":fields.get("visual_notes", ""), "continuity_notes":fields.get("continuity_notes", ""), "art_prompt":"", "negative_prompt":"", "references_required":characters, "lora_required":[], "controlnet_required":"", "seed_strategy":"deterministic per panel", "_source_number":f"{page_number}.{panel_number}", "_unknown_characters":character_errors, "_props":[v.strip() for v in fields.get("props", "").split(",") if v.strip()]})
        pages.append({"page_number":int(page_match.group(1)), "page_purpose":(page_match.group(2) or "Story page").strip(), "layout_recipe":"custom", "panels":panels})
    return {"issue_id":issue_id, "issue_title":metadata.get("title") or "Untitled issue", "page_count":len(pages), "pages":pages}


def _canonical_plan(plan: dict[str, Any]) -> dict[str, Any]:
    clean = json.loads(json.dumps(plan))
    for page in clean.get("pages", []):
        for panel in page.get("panels", []):
            panel.pop("_source_number", None); panel.pop("_unknown_characters", None); panel.pop("_props", None)
    return clean


def validate_plan(plan: dict[str, Any], root: Path) -> dict[str, Any]:
    findings = []
    pages = plan.get("pages", []) if isinstance(plan, dict) else []
    numbers = [p.get("page_number") for p in pages]
    if numbers != list(range(1, len(pages)+1)): findings.append({"level":"error","message":"Page numbers must be sequential starting at 1"})
    ids = []
    for page in pages:
        panels = page.get("panels", [])
        source_numbers = [p.get("_source_number") for p in panels]
        expected = [f"{page.get('page_number')}.{i}" for i in range(1, len(panels)+1)]
        if source_numbers != expected: findings.append({"level":"error","message":f"Page {page.get('page_number')} panel numbers must be sequential"})
        for panel in panels:
            ids.append(panel.get("panel_id"))
            if panel.get("_unknown_characters"): findings.append({"level":"error","message":f"Unknown characters in {panel.get('panel_id')}: {', '.join(panel['_unknown_characters'])}"})
            for field in ("location","action"):
                if not panel.get(field): findings.append({"level":"error","message":f"{panel.get('panel_id')} is missing {field}"})
    if len(ids) != len(set(ids)): findings.append({"level":"error","message":"Duplicate panel IDs detected"})
    schema = json.loads((root / "00_SYSTEM" / "page_panel_plan_schema.json").read_text(encoding="utf-8"))
    for error in Draft202012Validator(schema).iter_errors(_canonical_plan(plan)):
        findings.append({"level":"error","message":error.message})
    return {"status":"failed" if any(f["level"]=="error" for f in findings) else "passed", "findings":findings, "errors":sum(f["level"]=="error" for f in findings)}


def create_variant(folder: Path, root: Path) -> dict[str, Any]:
    _require_stage(folder, root)
    plan = parse_script(folder, root); variant_id = _variant_id(plan)
    script_hash = _hash_bytes(_script_path(folder).read_bytes())
    record = {"schema_version":"1.0", "variant_id":variant_id, "issue_id":plan["issue_id"], "created_at":_now(), "source":"canonical_script_parser", "script_hash":script_hash, "plan":plan, "plan_hash":_hash_json(_canonical_plan(plan)), "validation":validate_plan(plan, root), "approval":None, "superseded":False}
    _write_json(_workspace(folder) / "variants" / f"{variant_id}.json", record)
    return decorate(record, folder)


def _load(folder: Path, variant_id: str) -> dict[str, Any]:
    data = _read_json(_workspace(folder) / "variants" / f"{_safe_variant(variant_id)}.json")
    if not isinstance(data, dict): raise PagePanelError("Unknown plan variant")
    return data


def decorate(record: dict[str, Any], folder: Path) -> dict[str, Any]:
    result = dict(record); path = _script_path(folder)
    result["script_stale"] = not path.exists() or record.get("script_hash") != _hash_bytes(path.read_bytes())
    approval = record.get("approval")
    result["approval_current"] = bool(approval and approval.get("plan_hash") == record.get("plan_hash") and approval.get("script_hash") == record.get("script_hash") and not result["script_stale"])
    return result


def variants(folder: Path) -> list[dict[str, Any]]:
    base = _workspace(folder) / "variants"
    return [decorate(_read_json(path), folder) for path in sorted(base.glob("*.json"))] if base.exists() else []


def approve(folder: Path, root: Path, variant_id: str, note: Any = None) -> dict[str, Any]:
    _require_stage(folder, root); record = decorate(_load(folder, variant_id), folder)
    if record["validation"]["status"] != "passed": raise PagePanelError("Plan has validation errors", 409)
    if record["script_stale"]: raise PagePanelError("Canonical script changed since plan generation", 409)
    if record.get("approval"): raise PagePanelError("Plan variant is already approved and immutable", 409)
    current = _read_json(_workspace(folder) / "approvals" / "current.json")
    if current:
        prior = _load(folder, current["variant_id"]); prior["superseded"] = True; _write_json(_workspace(folder)/"variants"/f"{prior['variant_id']}.json", prior)
    record["approval"] = {"variant_id":variant_id,"approved_at":_now(),"plan_hash":record["plan_hash"],"script_hash":record["script_hash"],"actor":"project_owner","note":str(note)[:1000] if note else None}
    _write_json(_workspace(folder)/"variants"/f"{variant_id}.json", {k:v for k,v in record.items() if k not in {"script_stale","approval_current"}})
    _write_json(_workspace(folder)/"approvals"/"current.json", record["approval"])
    return decorate(_load(folder, variant_id), folder)


def promote(folder: Path, root: Path, variant_id: str, replace: bool = False) -> dict[str, Any]:
    _require_stage(folder, root)
    with _promotion_lock(folder):
        record = decorate(_load(folder, variant_id), folder)
        if not record["approval_current"]: raise PagePanelError("A current approved plan variant is required", 409)
        destination = folder / "page_panel_plan.json"; promotion = _workspace(folder)/"promotions"/f"{variant_id}.json"
        if promotion.exists(): raise PagePanelError("Plan variant was already promoted", 409)
        if destination.exists() and not replace: raise PagePanelError("page_panel_plan.json already exists; explicit replacement confirmation is required", 409)
        backup = None
        if destination.exists():
            backup = _workspace(folder)/"promotions"/f"backup-{variant_id}.json"
            if backup.exists(): raise PagePanelError("Replacement backup already exists for this plan variant", 409)
            _atomic(backup, destination.read_text(encoding="utf-8"))
        canonical = _canonical_plan(record["plan"]); _write_json(destination, canonical)
        validation = validate_plan(record["plan"], root)
        if validation["status"] != "passed": raise PagePanelError("Post-promotion validation failed", 409)
        provenance = {"variant_id":variant_id,"promoted_at":_now(),"plan_hash":record["plan_hash"],"script_hash":record["script_hash"],"destination":"page_panel_plan.json","backup":str(backup.relative_to(folder)).replace("\\","/") if backup else None,"actor":"project_owner"}
        _write_json(promotion, provenance)
        return {"ok":True,"promotion":provenance,"workflow":issue_workflow.workflow_status(folder, root)}


def summary(folder: Path, root: Path) -> dict[str, Any]:
    workflow = issue_workflow.workflow_status(folder, root); script = _script_path(folder)
    return {"issue_id":issue_workflow._read_issue_id(folder),"workflow":workflow,"script":{"exists":script.exists(),"sha256":_hash_bytes(script.read_bytes()) if script.exists() else None},"variants":variants(folder),"canonical_plan_exists":(folder/"page_panel_plan.json").exists()}
