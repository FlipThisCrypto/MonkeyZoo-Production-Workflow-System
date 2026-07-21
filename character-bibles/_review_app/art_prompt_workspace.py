"""Evidence-backed Art Prompt Pack generation from the canonical page plan."""
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

import issue_workflow

VARIANT_ID = re.compile(r"^pack-\d{8}T\d{6}Z-[0-9a-f]{6}$")

DEFAULT_STYLE_LOCK = (
    "MonkeyZoo house style: chibi cartoon monkey with oversized round head, "
    "huge white oval eyes with tiny black dot pupils, two small dot nostrils, "
    "thick uniform black outlines, flat color fills with soft cel shading, "
    "simplified plush body with visible stitch seams, mitten hands, curled tail, "
    "clean vector cartoon look, dark cartoon sci-fi cyberpunk backdrop"
)

DEFAULT_NEGATIVE = (
    "photorealistic, horror gore, extra limbs, fingers, watermark, logo text, "
    "speech balloons, low contrast mush, identity drift, unapproved costume changes"
)


__all__ = ["build_pack", "validate_pack", "create_variant", "ArtPromptError"]


class ArtPromptError(ValueError):

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_json(data: Any) -> str:
    return _hash_bytes(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def _workspace(folder: Path) -> Path:
    return folder / ".art-prompt-workspace"


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def _write_json(path: Path, data: Any) -> None:
    _atomic(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ArtPromptError(f"Malformed art prompt workspace record: {path.name}") from exc


@contextmanager
def _promotion_lock(folder: Path):
    path = _workspace(folder) / ".promotion.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ArtPromptError("Art prompt pack promotion is already in progress", 409) from exc
    try:
        os.write(fd, _now().encode())
        os.fsync(fd)
        os.close(fd)
        yield
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def _require_stage(folder: Path, root: Path) -> None:
    active = issue_workflow.workflow_status(folder, root)["active_stage"]
    if active != "art_prompts":
        raise ArtPromptError(
            f"Art Prompt Pack workspace requires active workflow stage art_prompts; current stage is {active}",
            409,
        )


def _plan(folder: Path) -> dict[str, Any]:
    data = issue_workflow._json(folder / "page_panel_plan.json")
    if not data:
        raise ArtPromptError("Canonical page_panel_plan.json is missing or malformed", 409)
    return data


def _plan_hash(folder: Path) -> str:
    return _hash_bytes((folder / "page_panel_plan.json").read_bytes())


def _style_lock(root: Path) -> str:
    path = root / "00_SYSTEM" / "visual_style_bible.md"
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r">\s*\*\*\"([^\"]+)\"\*\*", text)
        if match and len(match.group(1).strip()) >= 20:
            return match.group(1).strip()
    return DEFAULT_STYLE_LOCK


def _panel_number(panel_id: str, fallback: int) -> int:
    match = re.search(r"PANEL(\d+)$", str(panel_id or ""))
    return int(match.group(1)) if match else fallback


def _ensure_min(text: str, minimum: int, filler: str) -> str:
    value = str(text or "").strip()
    if len(value) >= minimum:
        return value
    joined = f"{value} {filler}".strip()
    if len(joined) >= minimum:
        return joined
    return (joined + " " + filler * 3).strip()[: max(minimum, len(joined))]


def build_pack(folder: Path, root: Path) -> dict[str, Any]:
    """Build a schema-oriented art prompt pack from the canonical page plan."""
    plan = _plan(folder)
    style = _style_lock(root)
    issue_id = plan.get("issue_id") or issue_workflow._read_issue_id(folder)
    panels: list[dict[str, Any]] = []
    for page in plan.get("pages", []):
        page_number = int(page.get("page_number") or 0)
        for index, panel in enumerate(page.get("panels", []), start=1):
            panel_id = panel.get("panel_id") or f"{issue_id}_P{page_number:02d}_PANEL{index:02d}"
            characters = list(panel.get("characters") or [])
            action = panel.get("action") or "character action"
            location = panel.get("location") or "scene location"
            camera = panel.get("camera_angle") or "medium shot"
            emotion = panel.get("emotion") or "neutral"
            visual = panel.get("visual_notes") or action
            base_prompt = panel.get("art_prompt") or (
                f"{style}. {action}. Location: {location}. Camera: {camera}. "
                f"Emotion: {emotion}. Notes: {visual}."
            )
            negative = panel.get("negative_prompt") or DEFAULT_NEGATIVE
            panels.append(
                {
                    "issue_id": issue_id,
                    "page_number": page_number,
                    "panel_number": _panel_number(panel_id, index),
                    "panel_id": panel_id,
                    "character_tokens": characters,
                    "character_design_reminders": [
                        "preserve approved identity markers",
                        "mitten hands only",
                    ],
                    "pose": _ensure_min(action, 1, "standing"),
                    "expression": _ensure_min(emotion, 1, "neutral"),
                    "environment": _ensure_min(location, 1, "scene"),
                    "camera_angle": _ensure_min(camera, 1, "medium"),
                    "lighting": "soft key light with readable silhouette",
                    "color_palette": "flat cel colors with one soft shade pass",
                    "style_lock_phrase_included": True,
                    "prompt": _ensure_min(base_prompt, 40, style),
                    "negative_prompt": _ensure_min(negative, 20, DEFAULT_NEGATIVE),
                    "references_required": list(panel.get("references_required") or characters),
                    "seed_strategy": "per_panel",
                    "seed": 100000 + page_number * 100 + index,
                    "controlnet": {
                        "required": False,
                        "type": "none",
                        "reference": "",
                    },
                    "identity_stack": {
                        "tier": "text-only",
                        "lora": [],
                        "ipadapter_refs": [],
                    },
                }
            )
    if not panels:
        raise ArtPromptError("Canonical page plan has no panels", 409)
    return {
        "issue_id": issue_id,
        "style_lock_phrase": style,
        "base_negative_prompt": DEFAULT_NEGATIVE,
        "panels": panels,
    }


_PACK_SCHEMA_CACHE: dict[str, dict] = {}


def _get_pack_schema(schema_path: Path) -> dict[str, Any]:
    key = str(schema_path.resolve())
    if key not in _PACK_SCHEMA_CACHE:
        _PACK_SCHEMA_CACHE[key] = json.loads(schema_path.read_text(encoding="utf-8"))
    return _PACK_SCHEMA_CACHE[key]


def validate_pack(pack: dict[str, Any], root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    schema_path = root / "00_SYSTEM" / "art_prompt_pack_schema.json"
    if not schema_path.exists():
        raise ArtPromptError("art_prompt_pack_schema.json is missing", 500)
    schema = _get_pack_schema(schema_path)
    for error in Draft202012Validator(schema).iter_errors(pack):
        findings.append({"level": "error", "message": error.message})

    if not pack.get("panels"):
        findings.append({"level": "error", "message": "Pack has no panels"})
    ids = [panel.get("panel_id") for panel in pack.get("panels", [])]
    if len(ids) != len(set(ids)):
        findings.append({"level": "error", "message": "Duplicate panel IDs in pack"})
    return {
        "status": "failed" if findings else "passed",
        "findings": findings,
        "errors": len(findings),
    }


def _variant_id(pack: dict[str, Any]) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = _hash_bytes((json.dumps(pack, sort_keys=True) + str(time.time_ns())).encode())[:6]
    return f"pack-{stamp}-{digest}"


def create_variant(folder: Path, root: Path) -> dict[str, Any]:
    _require_stage(folder, root)
    pack = build_pack(folder, root)
    variant_id = _variant_id(pack)
    record = {
        "schema_version": "1.0",
        "variant_id": variant_id,
        "issue_id": pack["issue_id"],
        "created_at": _now(),
        "source": "canonical_page_plan",
        "plan_hash": _plan_hash(folder),
        "pack": pack,
        "pack_hash": _hash_json(pack),
        "validation": validate_pack(pack, root),
        "approval": None,
        "superseded": False,
    }
    _write_json(_workspace(folder) / "variants" / f"{variant_id}.json", record)
    return decorate(record, folder)


def _safe_variant(variant_id: str) -> str:
    if not VARIANT_ID.fullmatch(str(variant_id or "")):
        raise ArtPromptError("Invalid art prompt pack variant ID")
    return variant_id


def _load(folder: Path, variant_id: str) -> dict[str, Any]:
    data = _read_json(_workspace(folder) / "variants" / f"{_safe_variant(variant_id)}.json")
    if not isinstance(data, dict):
        raise ArtPromptError("Unknown art prompt pack variant")
    return data


def decorate(record: dict[str, Any], folder: Path) -> dict[str, Any]:
    result = dict(record)
    plan_path = folder / "page_panel_plan.json"
    result["plan_stale"] = not plan_path.exists() or record.get("plan_hash") != _hash_bytes(plan_path.read_bytes())
    approval = record.get("approval")
    result["approval_current"] = bool(
        approval
        and approval.get("pack_hash") == record.get("pack_hash")
        and approval.get("plan_hash") == record.get("plan_hash")
        and not result["plan_stale"]
    )
    return result


def variants(folder: Path) -> list[dict[str, Any]]:
    base = _workspace(folder) / "variants"
    if not base.exists():
        return []
    return [decorate(_read_json(path), folder) for path in sorted(base.glob("*.json"))]


def approve(folder: Path, root: Path, variant_id: str, note: Any = None) -> dict[str, Any]:
    _require_stage(folder, root)
    record = decorate(_load(folder, variant_id), folder)
    if record["validation"]["status"] != "passed":
        raise ArtPromptError("Art prompt pack has validation errors", 409)
    if record["plan_stale"]:
        raise ArtPromptError("Canonical page plan changed since pack generation", 409)
    if record.get("approval"):
        raise ArtPromptError("Art prompt pack variant is already approved and immutable", 409)
    current = _read_json(_workspace(folder) / "approvals" / "current.json")
    if current:
        prior = _load(folder, current["variant_id"])
        prior["superseded"] = True
        _write_json(_workspace(folder) / "variants" / f"{prior['variant_id']}.json", prior)
    record["approval"] = {
        "variant_id": variant_id,
        "approved_at": _now(),
        "pack_hash": record["pack_hash"],
        "plan_hash": record["plan_hash"],
        "actor": "project_owner",
        "note": str(note)[:1000] if note else None,
    }
    stored = {k: v for k, v in record.items() if k not in {"plan_stale", "approval_current"}}
    _write_json(_workspace(folder) / "variants" / f"{variant_id}.json", stored)
    _write_json(_workspace(folder) / "approvals" / "current.json", record["approval"])
    return decorate(_load(folder, variant_id), folder)


def promote(folder: Path, root: Path, variant_id: str, replace: bool = False) -> dict[str, Any]:
    _require_stage(folder, root)
    with _promotion_lock(folder):
        record = decorate(_load(folder, variant_id), folder)
        if not record["approval_current"]:
            raise ArtPromptError("A current approved art prompt pack variant is required", 409)
        destination = folder / "art_prompt_pack.json"
        promotion = _workspace(folder) / "promotions" / f"{variant_id}.json"
        if promotion.exists():
            raise ArtPromptError("Art prompt pack variant was already promoted", 409)
        if destination.exists() and not replace:
            raise ArtPromptError(
                "art_prompt_pack.json already exists; explicit replacement confirmation is required",
                409,
            )
        pack = record["pack"]
        validation = validate_pack(pack, root)
        if validation["status"] != "passed" or _hash_json(pack) != record.get("pack_hash"):
            raise ArtPromptError("Final art prompt pack validation failed before promotion", 409)
        destination_existed = destination.exists()
        original = destination.read_bytes() if destination_existed else None
        backup = None
        if destination_existed:
            backup = _workspace(folder) / "promotions" / f"backup-{variant_id}.json"
            if backup.exists():
                raise ArtPromptError("Replacement backup already exists for this pack variant", 409)
            _atomic_bytes(backup, original)
        try:
            _write_json(destination, pack)
            written = _read_json(destination)
            written_validation = validate_pack(written, root)
            if written_validation["status"] != "passed" or _hash_json(written) != record["pack_hash"]:
                raise ArtPromptError("Post-promotion validation failed", 409)
            provenance = {
                "variant_id": variant_id,
                "promoted_at": _now(),
                "pack_hash": record["pack_hash"],
                "plan_hash": record["plan_hash"],
                "destination": "art_prompt_pack.json",
                "backup": str(backup.relative_to(folder)).replace("\\", "/") if backup else None,
                "actor": "project_owner",
            }
            _write_json(promotion, provenance)
            return {
                "ok": True,
                "promotion": provenance,
                "workflow": issue_workflow.workflow_status(folder, root),
            }
        except Exception:
            if promotion.exists():
                promotion.unlink()
            if destination_existed and original is not None:
                _atomic_bytes(destination, original)
            elif destination.exists():
                destination.unlink()
            raise


def summary(folder: Path, root: Path) -> dict[str, Any]:
    workflow = issue_workflow.workflow_status(folder, root)
    plan_path = folder / "page_panel_plan.json"
    return {
        "issue_id": issue_workflow._read_issue_id(folder),
        "workflow": workflow,
        "plan": {
            "exists": plan_path.exists(),
            "sha256": _hash_bytes(plan_path.read_bytes()) if plan_path.exists() else None,
        },
        "variants": variants(folder),
        "canonical_pack_exists": (folder / "art_prompt_pack.json").exists(),
    }
