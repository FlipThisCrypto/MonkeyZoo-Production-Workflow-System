from __future__ import annotations

import copy
import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

__all__ = ["load_bible", "save_bible", "resolve_character_id", "character_summary", "load_all", "BibleStoreError"]


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"
VALID_STATUSES = {
    "canon",
    "established",
    "experimental",
    "optional",
    "dormant",
    "retired",
    "contradicted",
    "unknown",
    "reserved",
}
VALID_STRENGTHS = {"defining", "strong", "moderate", "subtle", "background"}
VALID_FREQUENCIES = {
    "almost always",
    "often",
    "sometimes",
    "rarely",
    "special circumstances only",
    "never",
}


class BibleStoreError(ValueError):
    pass


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text via a temp file + fsync + os.replace so a crash or full disk
    mid-write cannot truncate/corrupt a canon bible.yaml or its history log
    (mirrors issue_workflow._atomic_write). The final bytes are identical to a
    plain write_text, so serialization/canon content is unchanged."""
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _load_yaml(path: Path) -> Any:
    """Parse a bible.yaml, turning a malformed file into a clean BibleStoreError
    (HTTP 400) instead of an uncaught yaml.YAMLError that 500s character
    resolution app-wide because one bible is corrupt."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BibleStoreError(f"Malformed bible: {path}") from exc


_IDENTITY_INDEXES: dict[str, dict[str, str]] = {}


def _identity_index(root: Path) -> dict[str, str]:
    key = str(root.resolve())
    if key in _IDENTITY_INDEXES:
        return _IDENTITY_INDEXES[key]
    index: dict[str, str] = {}
    aliases: list[tuple[list[str], str]] = []
    for path in sorted(root.glob("MZ-CHAR-*/bible.yaml")):
        data = _load_yaml(path) or {}
        ident = data.get("identification") or {}
        names = [path.parent.name, ident.get("character_id"), ident.get("current_display_name"), ident.get("personal_name"), ident.get("legacy_label"), ident.get("series_name"), *(ident.get("nicknames") or [])]
        target = ident.get("alias_of") or path.parent.name
        entry = ([str(name).strip().casefold() for name in names if name], target)
        if ident.get("alias_of"):
            aliases.append(entry)
        for token in entry[0]:
            index.setdefault(token, target)
    for names, target in aliases:
        for token in names:
            index[token] = target
    _IDENTITY_INDEXES[key] = index
    return index


def resolve_character_id(value: str, root: Path = BIBLES_ROOT) -> str:
    """Resolve stable IDs and human-facing aliases to one canonical character ID."""
    token = str(value or "").strip().casefold()
    if not token:
        raise BibleStoreError("Character identity is required")
    target = _identity_index(root).get(token)
    if not target:
        raise BibleStoreError(f"Unknown character: {value}")
    return target


def bible_dirs(root: Path = BIBLES_ROOT) -> list[Path]:
    result = []
    for path in sorted(root.glob("MZ-CHAR-*")):
        if not (path / "bible.yaml").exists():
            continue
        data = _load_yaml(path / "bible.yaml") or {}
        if not (data.get("identification") or {}).get("alias_of"):
            result.append(path)
    return result


def load_bible(character_id: str, root: Path = BIBLES_ROOT) -> dict[str, Any]:
    character_id = resolve_character_id(character_id, root)
    path = root / character_id / "bible.yaml"
    if not path.exists():
        raise BibleStoreError(f"Unknown character: {character_id}")
    return _load_yaml(path)


def save_bible(character_id: str, data: dict[str, Any], root: Path = BIBLES_ROOT) -> None:
    character_id = resolve_character_id(character_id, root)
    path = root / character_id / "bible.yaml"
    if not path.exists():
        raise BibleStoreError(f"Unknown character: {character_id}")
    _atomic_write_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110))
    _IDENTITY_INDEXES.pop(str(root.resolve()), None)



def load_all(root: Path = BIBLES_ROOT) -> list[tuple[str, dict[str, Any]]]:
    return [(path.name, _load_yaml(path / "bible.yaml")) for path in bible_dirs(root)]


def trait_count(data: Any, status: str | None = None) -> int:
    count = 0
    for _, trait in walk_traits(data):
        if status is None or trait.get("status") == status:
            count += 1
    return count


def unresolved_count(data: Any) -> int:
    if data is None or data == "":
        return 1
    if isinstance(data, list):
        if not data:
            return 1
        return sum(unresolved_count(item) for item in data)
    if isinstance(data, dict):
        if {"name", "status", "strength", "usage_frequency"}.issubset(data):
            return 1 if data.get("status") in {"unknown", "reserved"} else 0
        return sum(unresolved_count(value) for value in data.values())
    return 0


def last_appearance(data: dict[str, Any]) -> str:
    appearances = data.get("growth_and_continuity", {}).get("published_appearances", []) or []
    return appearances[-1] if appearances else "Unresolved"


def continuity_warnings(data: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    ident = data.get("identification", {})
    visual = data.get("visual_canon", {})
    if ident.get("naming_status") in {"unresolved", "personal_name_unresolved", "reserved"}:
        warnings.append("Naming unresolved")
    if not visual.get("primary_reference_image"):
        warnings.append("No primary reference image")
    if trait_count(data, "contradicted"):
        warnings.append("Contradicted trait needs review")
    if trait_count(data, "experimental"):
        warnings.append("Experimental traits pending")
    if visual.get("glasses_status") == "ambiguous":
        warnings.append("Glasses/eyewear ambiguity")
    return warnings


def image_url(character_id: str, rel_path: str | None) -> str | None:
    if not rel_path:
        return None
    return f"/media/{character_id}/{rel_path.replace(os.sep, '/')}"


def character_summary(character_id: str, data: dict[str, Any]) -> dict[str, Any]:
    ident = data.get("identification", {})
    visual = data.get("visual_canon", {})
    return {
        "character_id": character_id,
        "display_name": ident.get("current_display_name"),
        "series_name": ident.get("series_name"),
        "personal_name": ident.get("personal_name"),
        "legacy_label": ident.get("legacy_label") or ident.get("series_name"),
        "nationality": ident.get("nationality"),
        "country_of_origin": ident.get("country_of_origin"),
        "naming_status": ident.get("naming_status"),
        "development_level": ident.get("development_level"),
        "canon_traits": trait_count(data, "canon"),
        "experimental_traits": trait_count(data, "experimental"),
        "unresolved_fields": unresolved_count(data),
        "last_comic_appearance": last_appearance(data),
        "continuity_warnings": continuity_warnings(data),
        "primary_image": image_url(character_id, visual.get("primary_reference_image")),
        "image_status": "approved" if visual.get("primary_reference_image") else "unavailable",
    }


def walk_traits(data: Any, path: str = ""):
    if isinstance(data, dict):
        if {"name", "status", "strength", "usage_frequency"}.issubset(data):
            yield path, data
        for key, value in data.items():
            next_path = f"{path}.{key}" if path else key
            yield from walk_traits(value, next_path)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            yield from walk_traits(value, f"{path}.{index}" if path else str(index))


def visible_sections(data: dict[str, Any]) -> dict[str, Any]:
    ident = data.get("identification", {})
    visual = data.get("visual_canon", {})
    source_map = load_source_map(ident.get("character_id"))
    return {
        "identification": ident,
        "visual_canon": visual,
        "character_core": data.get("character_core", {}),
        "voice_and_dialogue": data.get("voice_and_dialogue", {}),
        "behavior": data.get("behavior", {}),
        "skills_and_limitations": data.get("skills_and_limitations", {}),
        "relationships": data.get("relationships", []),
        "story_use": data.get("story_use", {}),
        "running_elements": data.get("running_elements", {}),
        "growth_and_continuity": data.get("growth_and_continuity", {}),
        "issue_level_usage": data.get("issue_level_usage", {}),
        "source_map": source_map,
        "history": load_history(ident.get("character_id")),
    }


def get_path(data: Any, path: str) -> Any:
    cursor = data
    for part in path.split("."):
        if isinstance(cursor, list):
            try:
                cursor = cursor[int(part)]
            except (ValueError, IndexError) as exc:
                raise BibleStoreError(f"Cannot follow path: {path}") from exc
        elif isinstance(cursor, dict):
            try:
                cursor = cursor[part]
            except KeyError as exc:
                raise BibleStoreError(f"Cannot follow path: {path}") from exc
        else:
            raise BibleStoreError(f"Cannot follow path: {path}")
    return cursor


def set_path(data: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    cursor = data
    try:
        for part in parts[:-1]:
            cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
        last = parts[-1]
        if isinstance(cursor, list):
            cursor[int(last)] = value
        else:
            cursor[last] = value
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise BibleStoreError(f"Cannot follow path: {path}") from exc


def history_path(character_id: str, root: Path = BIBLES_ROOT) -> Path:
    return root / character_id / "approval-history.json"


def load_history(character_id: str | None, root: Path = BIBLES_ROOT) -> list[dict[str, Any]]:
    if not character_id:
        return []
    path = history_path(character_id, root)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BibleStoreError(f"Malformed approval history: {path}") from exc


def append_history(character_id: str, entry: dict[str, Any], root: Path = BIBLES_ROOT) -> None:
    path = history_path(character_id, root)
    history = load_history(character_id, root)
    history.append(entry)
    _atomic_write_text(path, json.dumps(history, indent=2, ensure_ascii=False))


def audit_entry(action: str, field_path: str, previous: Any, new: Any, note: str | None = None) -> dict[str, Any]:
    return {
        "date": dt.datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "field_path": field_path,
        "previous_value": previous,
        "new_value": new,
        "approval_status": action,
        "note": note,
    }


def update_trait(character_id: str, trait_path: str, updates: dict[str, Any], note: str | None = None,
                 root: Path = BIBLES_ROOT) -> dict[str, Any]:
    data = load_bible(character_id, root)
    trait = get_path(data, trait_path)
    if not isinstance(trait, dict) or "status" not in trait:
        raise BibleStoreError("Selected path is not a trait")
    previous = copy.deepcopy(trait)
    normalized = normalize_trait_updates(updates)
    review_action = normalized.pop("_review_action", "edit_trait")
    trait.update(normalized)
    save_bible(character_id, data, root)
    append_history(character_id, audit_entry(review_action, trait_path, previous, copy.deepcopy(trait), note), root)
    return trait


def normalize_trait_updates(updates: dict[str, Any]) -> dict[str, Any]:
    updates = dict(updates)
    action = updates.pop("action", None)
    if action == "approve_canon":
        updates["status"] = "canon"
        updates["_review_action"] = "approve_as_canon"
    elif action == "approve_established":
        updates["status"] = "established"
        updates["_review_action"] = "approve_as_established"
    elif action == "keep_experimental":
        updates["status"] = "experimental"
        updates["_review_action"] = "keep_experimental"
    elif action == "mark_optional":
        updates["status"] = "optional"
        updates["_review_action"] = "mark_optional"
    elif action == "mark_dormant":
        updates["status"] = "dormant"
        updates["_review_action"] = "mark_dormant"
    elif action == "retire":
        updates["status"] = "retired"
        updates["usage_frequency"] = "never"
        updates["_review_action"] = "retire"
    elif action == "reject":
        updates["status"] = "retired"
        updates["usage_frequency"] = "never"
        updates["notes"] = ("REJECTED: " + updates.get("notes", "")).strip()
        updates["_review_action"] = "reject"
    else:
        updates["_review_action"] = "edit_trait"
    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise BibleStoreError(f"Unsupported status: {updates['status']}")
    if "strength" in updates and updates["strength"] not in VALID_STRENGTHS:
        raise BibleStoreError(f"Unsupported strength: {updates['strength']}")
    if "usage_frequency" in updates and updates["usage_frequency"] not in VALID_FREQUENCIES:
        raise BibleStoreError(f"Unsupported frequency: {updates['usage_frequency']}")
    return updates


def update_field(character_id: str, field_path: str, value: Any, action: str = "edit_field",
                 note: str | None = None, root: Path = BIBLES_ROOT) -> Any:
    data = load_bible(character_id, root)
    previous = copy.deepcopy(get_path(data, field_path))
    set_path(data, field_path, value)
    save_bible(character_id, data, root)
    append_history(character_id, audit_entry(action, field_path, previous, value, note), root)
    return value


def undo_last(character_id: str, root: Path = BIBLES_ROOT) -> dict[str, Any]:
    history = load_history(character_id, root)
    if not history:
        raise BibleStoreError("No history to undo")
    last = history.pop()
    data = load_bible(character_id, root)
    set_path(data, last["field_path"], last["previous_value"])
    save_bible(character_id, data, root)
    _atomic_write_text(history_path(character_id, root), json.dumps(history, indent=2, ensure_ascii=False))
    return last


def load_source_map(character_id: str | None, root: Path = BIBLES_ROOT) -> dict[str, Any]:
    if not character_id:
        return {"sources": []}
    path = root / character_id / "references" / "source-map.json"
    if not path.exists():
        return {"sources": []}
    return json.loads(path.read_text(encoding="utf-8"))


def comparison(character_ids: list[str], root: Path = BIBLES_ROOT) -> dict[str, Any]:
    items = []
    for character_id in character_ids:
        data = load_bible(character_id, root)
        summary = character_summary(character_id, data)
        traits = [{"path": path, **trait} for path, trait in walk_traits(data)]
        items.append({"summary": summary, "traits": traits})
    return {"characters": items, "overlap": compute_overlap(items)}


def compute_overlap(items: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "personality": ["character_core.dominant_traits"],
        "speech": ["voice_and_dialogue"],
        "story_role": ["character_core.team_role", "story_use"],
        "visual": ["visual_canon"],
        "relationships": ["relationships"],
        "shared_quirks": ["behavior.quirks", "running_elements"],
    }
    result = {}
    for name, prefixes in buckets.items():
        seen: dict[str, list[str]] = {}
        for item in items:
            cid = item["summary"]["character_id"]
            for trait in item["traits"]:
                if any(trait["path"].startswith(prefix) for prefix in prefixes):
                    key = overlap_key(trait)
                    if key:
                        seen.setdefault(key, [])
                        if cid not in seen[key]:
                            seen[key].append(cid)
        result[name] = {key: ids for key, ids in seen.items() if len(ids) > 1}
    result["missing_differentiators"] = [
        item["summary"]["character_id"]
        for item in items
        if item["summary"]["experimental_traits"] == 0 and item["summary"]["canon_traits"] < 3
    ]
    return result


def overlap_key(trait: dict[str, Any]) -> str:
    name = (trait.get("name") or "").strip().lower()
    value = str(trait.get("value") or "").strip().lower()
    generic_names = {
        "team role",
        "story function",
        "best adventure role",
        "plot contribution",
        "humor function",
        "archetype",
        "anti-caricature",
        "avoid caricature",
        "do not caricature voice",
        "humor style",
        "growth seed",
        "future growth",
        "unresolved naming or future work",
    }
    if name == "monkey form":
        return ""
    ignored_values = {
        "use the speech trait only when it supports the scene.",
        "do not reduce the character to the easiest visual joke or single trait.",
        "let the character have scene purpose beyond one quirk.",
    }
    if value in ignored_values:
        return ""
    if name in generic_names and value:
        return value
    return value or name
