"""Issue-local, approval-gated story variant workspace."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

import bible_store
import issue_workflow

VARIANT_ID = re.compile(r"^(outline|script)-\d{8}T\d{6}Z-[0-9a-f]{6}$")
OUTLINE_SECTIONS = ["Logline:", "Theme:", "Page count:", "Emotional arc:", "Conflict:", "Ending:", "## Page map"]
SCRIPT_FIELDS = ["- Location:", "- Characters:", "- Action:", "- Dialogue:", "- Continuity notes:"]


class StoryWorkspaceError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_text(text: str) -> str:
    return _hash_bytes(text.encode("utf-8"))


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc: raise StoryWorkspaceError(f"Malformed story workspace record: {path.name}") from exc


def _atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try: os.unlink(temp)
        except OSError: pass
        raise


def _write_json(path: Path, data: Any) -> None:
    _atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _workspace(folder: Path) -> Path:
    return folder / ".story-workspace"


def _safe_variant(value: str, kind: str) -> str:
    if not VARIANT_ID.fullmatch(str(value or "")) or not value.startswith(kind + "-"):
        raise StoryWorkspaceError("Invalid variant ID")
    return value


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _variant_id(kind: str, content: str) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{kind}-{stamp}-{_hash_text(content + str(time.time_ns()))[:6]}"


def _brief(folder: Path) -> dict[str, Any]:
    meta = _read_json(folder / "metadata.json", {}) or {}
    brief = issue_workflow._brief_fields(folder)
    return {"issue_id": issue_workflow._read_issue_id(folder), "title": meta.get("title") or brief.get("Working Title"), "page_count": int(meta.get("page_count") or brief.get("Page Count") or 8), "panel_count": int(meta.get("panel_count") or brief.get("Panel Count") or 24), "primary_character": meta.get("primary_character") or brief.get("Main Character"), "guest_character": meta.get("guest_character") or brief.get("Supporting Characters"), "month": meta.get("issue_month") or brief.get("Issue Month"), "required_canon": meta.get("required_canon_references") or brief.get("Required Canon References"), "prohibited": meta.get("prohibited_story_elements") or brief.get("Prohibited Changes")}


def _split_balanced(value: str) -> list[str]:
    parts, current, depth = [], [], 0
    for char in value.replace("\r", " ").replace("\n", " "):
        if char == "(": depth += 1
        elif char == ")" and depth: depth -= 1
        if char == "," and depth == 0:
            token = "".join(current).strip()
            if token: parts.append(token)
            current = []
        else: current.append(char)
    token = "".join(current).strip()
    if token: parts.append(token)
    return parts


def _clean_cast_reference(value: str, role: str) -> dict[str, str]:
    raw = re.sub(r"\s+", " ", str(value or "")).strip()
    name = raw.split("(", 1)[0].strip()
    name = re.split(r"\s+(?:—|â€”|-)\s+", name, maxsplit=1)[0].strip()
    annotation = raw[len(name):].strip(" \t—-")
    return {"reference": name, "role": role, "annotation": annotation, "source": raw}


def _multiline_brief_field(text: str, label: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(label)}:\s*(.*)$", text)
    if not match: return None
    lines = [match.group(1)]
    for line in text[match.end():].splitlines():
        if re.match(r"^[A-Z][A-Za-z0-9 /]+:\s*", line): break
        if line.strip(): lines.append(line.strip())
    return "\n".join(lines).strip()


def cast_references(folder: Path) -> list[dict[str, str]]:
    """Prefer structured stable IDs, with balanced prose parsing as compatibility fallback."""
    meta = _read_json(folder / "metadata.json", {}) or {}
    structured = meta.get("character_ids") or meta.get("cast")
    if isinstance(structured, list) and structured:
        result = []
        for index, item in enumerate(structured):
            if isinstance(item, dict):
                value = item.get("character_id") or item.get("id") or item.get("name")
                role = item.get("role") or ("primary" if index == 0 else "guest")
            else: value, role = item, "primary" if index == 0 else "guest"
            if value: result.append(_clean_cast_reference(str(value), str(role)))
        return result
    if meta.get("primary_character") or meta.get("guest_character"):
        result = []
        if meta.get("primary_character"): result.append(_clean_cast_reference(meta["primary_character"], "primary"))
        for token in _split_balanced(str(meta.get("guest_character") or "")):
            result.append(_clean_cast_reference(token, "guest"))
        return result
    text = (folder / "issue_brief.md").read_text(encoding="utf-8", errors="replace") if (folder / "issue_brief.md").exists() else ""
    result = []
    main = _multiline_brief_field(text, "Main Character")
    if main: result.append(_clean_cast_reference(main, "primary"))
    supporting = _multiline_brief_field(text, "Supporting Characters")
    for token in _split_balanced(supporting or ""):
        result.append(_clean_cast_reference(token, "guest"))
    return result


_FILE_HASH_CACHE: dict[str, tuple[float, int, str]] = {}


def _cached_file_hash(path: Path) -> str:
    key = str(path.resolve())
    try:
        st = path.stat()
        mtime, size = st.st_mtime, st.st_size
    except OSError:
        return _hash_bytes(path.read_bytes())
    if key in _FILE_HASH_CACHE:
        cached_mtime, cached_size, cached_hash = _FILE_HASH_CACHE[key]
        if cached_mtime == mtime and cached_size == size:
            return cached_hash
    digest = _hash_bytes(path.read_bytes())
    _FILE_HASH_CACHE[key] = (mtime, size, digest)
    return digest


def canon_snapshot(folder: Path, root: Path, generation_type: str, persist: bool = False) -> dict[str, Any]:
    brief = _brief(folder)
    sources, characters, aliases, warnings, excluded = [], [], {}, [], []
    references = cast_references(folder)
    for reference in references:
        token = reference["reference"]
        if token:
            try:
                canonical = bible_store.resolve_character_id(token, root / "character-bibles")
                if canonical in [c["character_id"] for c in characters]: continue
                data = bible_store.load_bible(canonical, root / "character-bibles")
                ident = data.get("identification", {})
                path = root / "character-bibles" / canonical / "bible.yaml"
                aliases[token] = canonical
                sources.append({"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": _cached_file_hash(path)})
                characters.append({"character_id": canonical, "display_name": ident.get("current_display_name"), "personal_name": ident.get("personal_name"), "legacy_labels": ident.get("legacy_labels") or [], "nationality": ident.get("nationality"), "origin": ident.get("origin"), "canon_status": ident.get("canon_status"), "role": reference["role"], "source_annotation": reference["annotation"], "voice": data.get("voice_and_dialogue", {}), "relationships": data.get("relationships", []), "constraints": data.get("personality_and_behavior", {}), "visual_constraints": data.get("visual_canon", {}).get("features_that_must_never_change", [])})
            except ValueError:
                warnings.append(f"Unsupported character reference: {token}")
                excluded.append({"source": reference["source"], "reference": token, "reason": "missing reliable approved identity"})
    for rel in ["00_SYSTEM/monkeyzoo_master_bible.md", "00_SYSTEM/world_bible.md", "00_SYSTEM/continuity_ledger.md"]:
        path = root / rel
        if path.exists(): sources.append({"path": rel, "sha256": _cached_file_hash(path)})
    season = next(iter(sorted((root / "story-bibles" / "seasons").glob("*/SEASON-BIBLE.md"))), None) if (root / "story-bibles" / "seasons").exists() else None
    if season: sources.append({"path": str(season.relative_to(root)).replace("\\", "/"), "sha256": _cached_file_hash(season)})
    brief_path = folder / "issue_brief.md"
    snapshot = {"schema_version":"1.0", "issue_id":brief["issue_id"], "generation_type":generation_type, "created_at":_now() if persist else None, "canon_sources":sources, "character_ids":[c["character_id"] for c in characters], "characters":characters, "cast_references":references, "alias_resolutions":aliases, "issue_brief_hash":_cached_file_hash(brief_path) if brief_path.exists() else None, "season_plan_hash": next((s["sha256"] for s in sources if "SEASON-BIBLE" in s["path"]), None), "previous_issue_references":[], "warnings":warnings, "excluded":excluded}
    snapshot["snapshot_hash"] = _hash_text(json.dumps({k:v for k,v in snapshot.items() if k not in {"created_at","snapshot_hash"}}, sort_keys=True))
    if persist: _write_json(_workspace(folder) / "canon-snapshots" / f"{snapshot['snapshot_hash']}.json", snapshot)
    return snapshot



def _current_snapshot_hash(folder: Path, root: Path, kind: str) -> str:
    return canon_snapshot(folder, root, kind)["snapshot_hash"]


def _validation(kind: str, content: str, brief: dict[str, Any]) -> dict[str, Any]:
    findings = []
    required = OUTLINE_SECTIONS if kind == "outline" else SCRIPT_FIELDS
    for field in required:
        if field.lower() not in content.lower(): findings.append({"level":"error", "message":f"Missing required section: {field}"})
    if brief["issue_id"] not in content: findings.append({"level":"error", "message":"Issue ID is missing or does not match"})
    if re.search(r"<(?:[^>]+)>|\b(?:TBD|TODO|PLACEHOLDER)\b", content, re.I): findings.append({"level":"error", "message":"Unresolved placeholder text detected"})
    if kind == "script":
        panels = re.findall(r"\*\*Panel\s+([0-9]+\.[0-9]+)", content, re.I)
        if len(panels) != len(set(panels)): findings.append({"level":"error", "message":"Duplicate panel IDs detected"})
        if not panels: findings.append({"level":"error", "message":"No script panels detected"})
    if brief.get("prohibited") and str(brief["prohibited"]).lower() in content.lower(): findings.append({"level":"warning", "message":"Heuristic match to prohibited material; owner review required"})
    errors = sum(f["level"] == "error" for f in findings)
    return {"status":"failed" if errors else "passed", "errors":errors, "findings":findings, "heuristic":True}


def _variant_path(folder: Path, kind: str, variant_id: str) -> Path:
    return _workspace(folder) / f"{kind}s" / "variants" / f"{_safe_variant(variant_id, kind)}.json"


def _load_variant(folder: Path, kind: str, variant_id: str) -> dict[str, Any]:
    data = _read_json(_variant_path(folder, kind, variant_id))
    if not isinstance(data, dict): raise StoryWorkspaceError("Unknown variant")
    return data


def _workflow_stage(folder: Path, root: Path, expected: str) -> None:
    actual = issue_workflow.workflow_status(folder, root)["active_stage"]
    if actual != expected: raise StoryWorkspaceError(f"{expected.title()} workspace requires active workflow stage {expected}; current stage is {actual}", 409)


def prompt_package(folder: Path, root: Path, kind: str) -> dict[str, Any]:
    if kind not in {"outline","script"}: raise StoryWorkspaceError("Unknown generation type")
    _workflow_stage(folder, root, kind)
    brief, snapshot = _brief(folder), canon_snapshot(folder, root, kind, persist=True)
    approved_outline = current_approval(folder, root, "outline") if kind == "script" else None
    if kind == "script" and not approved_outline: raise StoryWorkspaceError("Script generation requires an approved outline", 409)
    generation_id = _variant_id(kind, brief["issue_id"])
    contract = "Use the repository issue outline template." if kind == "outline" else "Use the repository per-page, per-panel script template."
    text = f"# Manual {kind.title()} Prompt Package\nGeneration ID: {generation_id}\nIssue ID: {brief['issue_id']}\n\n## Task\nCreate one canon-safe {kind} variant. Do not invent approval or unsupported canon.\n\n## Issue brief\n{json.dumps(brief, indent=2)}\n\n## Frozen canon context\n{json.dumps(snapshot, indent=2)}\n\n## Output contract\n{contract}\n\n## Validation\nReturn complete Markdown with no placeholders.\n"
    path = _workspace(folder) / "prompts" / f"{generation_id}.md"
    _atomic(path, text)
    return {"generation_id":generation_id, "provider":"manual_prompt", "model":"External/manual", "execution_mode":"manual", "prompt":text, "prompt_hash":_hash_text(text), "canon_snapshot_hash":snapshot["snapshot_hash"]}


def import_variant(folder: Path, root: Path, kind: str, body: dict[str, Any]) -> dict[str, Any]:
    _workflow_stage(folder, root, kind)
    content = body.get("content")
    if not isinstance(content, str) or not content.strip() or len(content) > 500_000: raise StoryWorkspaceError("content must be non-empty Markdown")
    approved_outline = current_approval(folder, root, "outline") if kind == "script" else None
    if kind == "script" and not approved_outline: raise StoryWorkspaceError("Script import requires a current approved outline", 409)
    snapshot = canon_snapshot(folder, root, kind, persist=True)
    variant_id = _variant_id(kind, content)
    record = {"schema_version":"1.0", "variant_id":variant_id, "issue_id":_brief(folder)["issue_id"], "kind":kind, "created_at":_now(), "source_type":"manual_import", "provider":str(body.get("provider") or "manual"), "model":str(body.get("model") or "user supplied"), "execution_mode":"manual", "content":content, "content_hash":_hash_text(content), "canon_snapshot_hash":snapshot["snapshot_hash"], "issue_brief_hash":snapshot["issue_brief_hash"], "approved_outline":approved_outline, "prompt_hash":body.get("prompt_hash"), "validation":_validation(kind, content, _brief(folder)), "approval":None, "superseded":False, "owner_note":None}
    _write_json(_variant_path(folder, kind, variant_id), record)
    _log(folder, {"event_id":_variant_id(kind, variant_id), "issue_id":record["issue_id"], "type":f"{kind}_import", "variant_id":variant_id, "provider":record["provider"], "model":record["model"], "execution_mode":"manual", "start_time":record["created_at"], "end_time":record["created_at"], "success":True, "prompt_hash":record["prompt_hash"], "canon_snapshot_hash":record["canon_snapshot_hash"], "output_hash":record["content_hash"], "validation_status":record["validation"]["status"], "error_summary":None})
    return decorate_variant(record, folder, root)


def _log(folder: Path, event: dict[str, Any]) -> None:
    path = _workspace(folder) / "generation-log.json"
    events = _read_json(path, [])
    if not isinstance(events, list): raise StoryWorkspaceError("Malformed generation log")
    events.append(event); _write_json(path, events)


def decorate_variant(record: dict[str, Any], folder: Path, root: Path) -> dict[str, Any]:
    result = dict(record)
    result["canon_stale"] = record["canon_snapshot_hash"] != _current_snapshot_hash(folder, root, record["kind"])
    approval_record = record.get("approval")
    outline_current = True
    if record["kind"] == "script":
        current_outline = current_approval(folder, root, "outline")
        outline_current = bool(current_outline and record.get("approved_outline", {}).get("variant_id") == current_outline.get("variant_id") and record.get("approved_outline", {}).get("content_hash") == current_outline.get("content_hash"))
    result["outline_approval_current"] = outline_current
    result["approval_current"] = bool(approval_record and approval_record.get("content_hash") == record["content_hash"] and approval_record.get("canon_snapshot_hash") == record["canon_snapshot_hash"] and not result["canon_stale"] and outline_current)
    return result


def variants(folder: Path, root: Path, kind: str) -> list[dict[str, Any]]:
    base = _workspace(folder) / f"{kind}s" / "variants"
    return [decorate_variant(_read_json(path), folder, root) for path in sorted(base.glob("*.json"))] if base.exists() else []


def approve(folder: Path, root: Path, kind: str, variant_id: str, note: Any = None) -> dict[str, Any]:
    _workflow_stage(folder, root, kind)
    record = _load_variant(folder, kind, variant_id)
    if record["validation"]["status"] != "passed": raise StoryWorkspaceError("Variant has validation errors", 409)
    if record["canon_snapshot_hash"] != _current_snapshot_hash(folder, root, kind): raise StoryWorkspaceError("Canon changed since generation", 409)
    if record.get("approval"): raise StoryWorkspaceError("Variant is already approved and immutable", 409)
    current = approval(folder, kind)
    if current:
        prior = _load_variant(folder, kind, current["variant_id"]); prior["superseded"] = True; _write_json(_variant_path(folder, kind, prior["variant_id"]), prior)
    record["approval"] = {"variant_id":variant_id, "issue_id":record["issue_id"], "timestamp":_now(), "content_hash":record["content_hash"], "canon_snapshot_hash":record["canon_snapshot_hash"], "owner_note":str(note)[:1000] if note else None, "actor":"project_owner"}
    _write_json(_variant_path(folder, kind, variant_id), record)
    _write_json(_workspace(folder) / f"{kind}s" / "approvals" / "current.json", record["approval"])
    return decorate_variant(record, folder, root)


def approval(folder: Path, kind: str) -> dict[str, Any] | None:
    data = _read_json(_workspace(folder) / f"{kind}s" / "approvals" / "current.json")
    return data if isinstance(data, dict) else None


def current_approval(folder: Path, root: Path, kind: str) -> dict[str, Any] | None:
    record = approval(folder, kind)
    if not record: return None
    try: variant = _load_variant(folder, kind, record["variant_id"])
    except (KeyError, StoryWorkspaceError): return None
    if variant.get("content_hash") != record.get("content_hash"): return None
    if variant.get("canon_snapshot_hash") != _current_snapshot_hash(folder, root, kind): return None
    return record


def promote(folder: Path, root: Path, kind: str, variant_id: str, replace: bool = False) -> dict[str, Any]:
    _workflow_stage(folder, root, kind)
    record = decorate_variant(_load_variant(folder, kind, variant_id), folder, root)
    if not record["approval_current"]: raise StoryWorkspaceError("A current approved variant is required", 409)
    if kind == "script":
        outline_approval = current_approval(folder, root, "outline")
        if not outline_approval: raise StoryWorkspaceError("Approved outline is no longer current", 409)
    destination = folder / f"issue_{kind}.md"
    history_dir = _workspace(folder) / f"{kind}s" / "promotions"
    existing = list(history_dir.glob("*.json")) if history_dir.exists() else []
    if any((_read_json(p, {}) or {}).get("variant_id") == variant_id for p in existing): raise StoryWorkspaceError("Variant was already promoted", 409)
    if destination.exists() and not replace: raise StoryWorkspaceError(f"{destination.name} already exists; explicit replacement confirmation is required", 409)
    backup = None
    if destination.exists():
        backup = history_dir / f"backup-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
        _atomic(backup, destination.read_text(encoding="utf-8"))
    _atomic(destination, record["content"])
    validation = _validation(kind, destination.read_text(encoding="utf-8"), _brief(folder))
    if validation["status"] != "passed": raise StoryWorkspaceError("Post-promotion validation failed", 409)
    provenance = {"variant_id":variant_id, "promoted_at":_now(), "content_hash":record["content_hash"], "canon_snapshot_hash":record["canon_snapshot_hash"], "destination":destination.name, "backup":str(backup.relative_to(folder)).replace("\\", "/") if backup else None, "actor":"project_owner"}
    _write_json(history_dir / f"{variant_id}.json", provenance)
    return {"ok":True, "promotion":provenance, "workflow":issue_workflow.workflow_status(folder, root)}


def summary(folder: Path, root: Path) -> dict[str, Any]:
    workflow = issue_workflow.workflow_status(folder, root); brief = _brief(folder)
    outlines, scripts = variants(folder, root, "outline"), variants(folder, root, "script")
    return {"issue":brief, "workflow":workflow, "provider":{"available":True,"type":"manual_prompt","model_label":"External/manual","execution_mode":"manual"}, "canon":canon_snapshot(folder, root, "outline"), "outlines":outlines, "scripts":scripts, "outline_approval":approval(folder,"outline"), "script_approval":approval(folder,"script"), "existing_files":{"issue_outline.md":(folder/"issue_outline.md").exists(),"issue_script.md":(folder/"issue_script.md").exists()}, "draft_counts":{"outlines":len(outlines),"scripts":len(scripts)}}
