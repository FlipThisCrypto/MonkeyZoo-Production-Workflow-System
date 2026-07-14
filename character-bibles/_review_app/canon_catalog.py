"""Read-only catalog for approved locations and props inventories."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SAFE_ID = re.compile(r"^MZ-(LOC|PROP)-[A-Z0-9-]+$")


class CanonCatalogError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _canon_root(workspace: Path) -> Path:
    return workspace / "03_APPROVED_CANON"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CanonCatalogError(f"Malformed catalog inventory: {path.name}", 500) from exc
    if not isinstance(data, dict):
        raise CanonCatalogError(f"Catalog inventory must be an object: {path.name}", 500)
    return data


def _slug_for_location(item: dict[str, Any]) -> str:
    return str(item.get("slug") or item.get("location_id", "").lower())


def _slug_for_prop(item: dict[str, Any]) -> str:
    prop_id = str(item.get("prop_id") or "")
    return prop_id.lower().replace("mz-prop-", "") if prop_id else ""


def _bible_text(folder: Path) -> str | None:
    path = folder / "bible.md"
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _primary_image(folder: Path) -> str | None:
    primary = folder / "primary-reference.png"
    if primary.is_file():
        return str(primary.relative_to(folder.parents[2] if "approved_" in str(folder) else folder)).replace("\\", "/")
    # Prefer relative from workspace when possible
    return "primary-reference.png" if primary.is_file() else None


def list_locations(workspace: Path) -> list[dict[str, Any]]:
    inv_path = _canon_root(workspace) / "approved_locations" / "locations-inventory.json"
    if not inv_path.is_file():
        return []
    data = _read_json(inv_path)
    items = data.get("locations") or []
    result = []
    base = _canon_root(workspace) / "approved_locations"
    for item in items:
        if not isinstance(item, dict):
            continue
        slug = _slug_for_location(item)
        folder = base / slug
        entry = dict(item)
        entry["has_bible"] = (folder / "bible.md").is_file()
        entry["has_primary_image"] = (folder / "primary-reference.png").is_file()
        entry["folder"] = f"03_APPROVED_CANON/approved_locations/{slug}"
        result.append(entry)
    return result


def list_props(workspace: Path) -> list[dict[str, Any]]:
    inv_path = _canon_root(workspace) / "approved_props" / "props-inventory.json"
    if not inv_path.is_file():
        return []
    data = _read_json(inv_path)
    items = data.get("props") or []
    result = []
    base = _canon_root(workspace) / "approved_props"
    for item in items:
        if not isinstance(item, dict):
            continue
        slug = _slug_for_prop(item)
        folder = base / slug
        entry = dict(item)
        entry["has_bible"] = (folder / "bible.md").is_file()
        entry["has_primary_image"] = (folder / "primary-reference.png").is_file()
        entry["folder"] = f"03_APPROVED_CANON/approved_props/{slug}"
        result.append(entry)
    return result


def get_location(workspace: Path, location_id: str) -> dict[str, Any]:
    location_id = str(location_id or "")
    if not SAFE_ID.fullmatch(location_id) or not location_id.startswith("MZ-LOC-"):
        raise CanonCatalogError("Invalid location ID")
    for item in list_locations(workspace):
        if item.get("location_id") == location_id:
            slug = _slug_for_location(item)
            folder = _canon_root(workspace) / "approved_locations" / slug
            return {
                "summary": item,
                "bible_markdown": _bible_text(folder),
                "has_primary_image": (folder / "primary-reference.png").is_file(),
            }
    raise CanonCatalogError("Unknown location", 404)


def get_prop(workspace: Path, prop_id: str) -> dict[str, Any]:
    prop_id = str(prop_id or "")
    if not SAFE_ID.fullmatch(prop_id) or not prop_id.startswith("MZ-PROP-"):
        raise CanonCatalogError("Invalid prop ID")
    for item in list_props(workspace):
        if item.get("prop_id") == prop_id:
            slug = _slug_for_prop(item)
            folder = _canon_root(workspace) / "approved_props" / slug
            return {
                "summary": item,
                "bible_markdown": _bible_text(folder),
                "has_primary_image": (folder / "primary-reference.png").is_file(),
            }
    raise CanonCatalogError("Unknown prop", 404)


def catalog_summary(workspace: Path) -> dict[str, Any]:
    locations = list_locations(workspace)
    props = list_props(workspace)
    return {
        "locations_count": len(locations),
        "props_count": len(props),
        "locations_proposed": sum(1 for x in locations if x.get("status") == "proposed_story_canon"),
        "props_proposed": sum(1 for x in props if x.get("status") == "proposed_story_canon"),
        "season": "2026-emo-monkeys-the-signal-between-us",
    }
