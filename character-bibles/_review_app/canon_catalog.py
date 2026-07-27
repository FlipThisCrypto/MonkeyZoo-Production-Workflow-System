"""Read-only catalog for approved locations, props, and expression sheets."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SAFE_ID = re.compile(r"^MZ-(LOC|PROP)-[A-Z0-9-]+$")
SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_EXPR_SLUG = re.compile(r"^[a-z0-9][a-z0-9 _-]*$", re.IGNORECASE)
SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
PRIMARY_NAME = "primary-reference.png"


__all__ = ["list_locations", "list_props", "get_location", "get_prop", "CanonCatalogError"]


class CanonCatalogError(ValueError):

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _canon_root(workspace: Path) -> Path:
    return workspace / "03_APPROVED_CANON"


_JSON_CACHE: dict[str, tuple[float, int, dict[str, Any]]] = {}


def _read_json(path: Path) -> dict[str, Any]:
    key = str(path.resolve())
    try:
        st = path.stat()
        mtime, size = st.st_mtime, st.st_size
    except OSError:
        mtime, size = 0.0, 0
    if key in _JSON_CACHE:
        cached_mtime, cached_size, cached_data = _JSON_CACHE[key]
        if cached_mtime == mtime and cached_size == size:
            return cached_data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CanonCatalogError(f"Malformed catalog inventory: {path.name}", 500) from exc
    if not isinstance(data, dict):
        raise CanonCatalogError(f"Catalog inventory must be an object: {path.name}", 500)
    _JSON_CACHE[key] = (mtime, size, data)
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


def _has_primary(folder: Path) -> bool:
    return (folder / PRIMARY_NAME).is_file()


def location_media_url(slug: str) -> str:
    return f"/media/locations/{slug}/{PRIMARY_NAME}"


def prop_media_url(slug: str) -> str:
    return f"/media/props/{slug}/{PRIMARY_NAME}"


def expression_media_url(slug: str, filename: str) -> str:
    # Keep spaces in slug path; clients should encodeURIComponent each segment.
    return f"/media/expressions/{slug}/{filename}"


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
        has_primary = _has_primary(folder)
        entry["has_bible"] = (folder / "bible.md").is_file()
        entry["has_primary_image"] = has_primary
        entry["folder"] = f"03_APPROVED_CANON/approved_locations/{slug}"
        entry["primary_image_url"] = location_media_url(slug) if has_primary else None
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
        has_primary = _has_primary(folder)
        entry["has_bible"] = (folder / "bible.md").is_file()
        entry["has_primary_image"] = has_primary
        entry["folder"] = f"03_APPROVED_CANON/approved_props/{slug}"
        entry["primary_image_url"] = prop_media_url(slug) if has_primary else None
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
            has_primary = _has_primary(folder)
            return {
                "summary": item,
                "bible_markdown": _bible_text(folder),
                "has_primary_image": has_primary,
                "primary_image_url": location_media_url(slug) if has_primary else None,
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
            has_primary = _has_primary(folder)
            return {
                "summary": item,
                "bible_markdown": _bible_text(folder),
                "has_primary_image": has_primary,
                "primary_image_url": prop_media_url(slug) if has_primary else None,
            }
    raise CanonCatalogError("Unknown prop", 404)


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def resolve_location_ref(workspace: Path, raw: str | None) -> dict[str, Any] | None:
    """Match panel location text to an approved location by id, slug, or display name."""
    if not raw or not str(raw).strip():
        return None
    key = _normalize_key(raw)
    for item in list_locations(workspace):
        candidates = [
            item.get("location_id"),
            item.get("slug"),
            item.get("display_name"),
            item.get("folder"),
        ]
        if any(_normalize_key(str(c)) == key for c in candidates if c):
            # softer contains match for free-text panel locations
            return {
                "reference_kind": "location",
                "location_id": item.get("location_id"),
                "display_name": item.get("display_name"),
                "slug": item.get("slug"),
                "primary_reference": PRIMARY_NAME if item.get("has_primary_image") else None,
                "primary_image_url": item.get("primary_image_url"),
                **(
                    {}
                    if item.get("has_primary_image")
                    else {"error": "Approved location primary reference unavailable"}
                ),
            }
    # Partial match on display name / season role phrasing
    for item in list_locations(workspace):
        name = _normalize_key(str(item.get("display_name") or ""))
        if name and (name in key or key in name):
            return {
                "reference_kind": "location",
                "location_id": item.get("location_id"),
                "display_name": item.get("display_name"),
                "slug": item.get("slug"),
                "primary_reference": PRIMARY_NAME if item.get("has_primary_image") else None,
                "primary_image_url": item.get("primary_image_url"),
                **(
                    {}
                    if item.get("has_primary_image")
                    else {"error": "Approved location primary reference unavailable"}
                ),
            }
    return {
        "reference_kind": "location",
        "display_name": str(raw),
        "error": "Location not found in approved canon",
    }


def resolve_prop_refs(workspace: Path, raw_props: list[Any] | None) -> list[dict[str, Any]]:
    """Match panel prop labels to approved props."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_props or []:
        if not raw:
            continue
        key = _normalize_key(str(raw))
        matched = None
        for item in list_props(workspace):
            candidates = [item.get("prop_id"), item.get("display_name"), _slug_for_prop(item)]
            if any(_normalize_key(str(c)) == key for c in candidates if c):
                matched = item
                break
        if not matched:
            for item in list_props(workspace):
                name = _normalize_key(str(item.get("display_name") or ""))
                if name and (name in key or key in name):
                    matched = item
                    break
        if matched:
            pid = str(matched.get("prop_id"))
            if pid in seen:
                continue
            seen.add(pid)
            result.append(
                {
                    "reference_kind": "prop",
                    "prop_id": matched.get("prop_id"),
                    "display_name": matched.get("display_name"),
                    "slug": _slug_for_prop(matched),
                    "primary_reference": PRIMARY_NAME if matched.get("has_primary_image") else None,
                    "primary_image_url": matched.get("primary_image_url"),
                    **(
                        {}
                        if matched.get("has_primary_image")
                        else {"error": "Approved prop primary reference unavailable"}
                    ),
                }
            )
        else:
            result.append(
                {
                    "reference_kind": "prop",
                    "display_name": str(raw),
                    "error": "Prop not found in approved canon",
                }
            )
    return result


def list_expression_sets(workspace: Path) -> list[dict[str, Any]]:
    """Inventory expression sheets under approved_expressions (local owner-managed assets)."""
    root = _canon_root(workspace) / "approved_expressions"
    if not root.is_dir():
        return []
    sets: list[dict[str, Any]] = []
    for folder in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if not SAFE_EXPR_SLUG.fullmatch(folder.name):
            continue
        pngs = sorted(p.name for p in folder.glob("*.png") if SAFE_FILENAME.fullmatch(p.name))
        if not pngs:
            continue
        base = next((n for n in pngs if "_00_clean_base" in n or n.endswith("_00_clean_base.png")), pngs[0])
        sets.append(
            {
                "slug": folder.name,
                "display_name": folder.name.replace("-", " ").replace("_", " ").title(),
                "image_count": len(pngs),
                "base_image": base,
                "base_image_url": expression_media_url(folder.name, base),
                "folder": f"03_APPROVED_CANON/approved_expressions/{folder.name}",
                "images": [
                    {"filename": name, "url": expression_media_url(folder.name, name)} for name in pngs
                ],
            }
        )
    return sets


def get_expression_set(workspace: Path, slug: str) -> dict[str, Any]:
    slug = str(slug or "")
    if not SAFE_EXPR_SLUG.fullmatch(slug):
        raise CanonCatalogError("Invalid expression set slug")
    for item in list_expression_sets(workspace):
        if item["slug"] == slug:
            return item
    raise CanonCatalogError("Unknown expression set", 404)


def resolve_canon_media(workspace: Path, kind: str, slug: str, filename: str) -> Path:
    """Resolve a safe filesystem path for a canon media file."""
    kind = str(kind or "")
    slug = str(slug or "")
    filename = str(filename or "")
    if not SAFE_FILENAME.fullmatch(filename):
        raise CanonCatalogError("Invalid media filename")
    if ".." in filename or "/" in filename or "\\" in filename:
        raise CanonCatalogError("Invalid media filename")

    if kind == "locations":
        if not SAFE_SLUG.fullmatch(slug):
            raise CanonCatalogError("Invalid location slug")
        folder = _canon_root(workspace) / "approved_locations" / slug
    elif kind == "props":
        if not SAFE_SLUG.fullmatch(slug):
            raise CanonCatalogError("Invalid prop slug")
        folder = _canon_root(workspace) / "approved_props" / slug
    elif kind == "expressions":
        if not SAFE_EXPR_SLUG.fullmatch(slug):
            raise CanonCatalogError("Invalid expression set slug")
        folder = _canon_root(workspace) / "approved_expressions" / slug
    else:
        raise CanonCatalogError("Unknown media kind")

    path = (folder / filename).resolve()
    try:
        path.relative_to(folder.resolve())
    except ValueError as exc:
        raise CanonCatalogError("Invalid media path") from exc
    if not path.is_file():
        raise CanonCatalogError("Media file not found", 404)
    return path


def catalog_summary(workspace: Path) -> dict[str, Any]:
    locations = list_locations(workspace)
    props = list_props(workspace)
    expressions = list_expression_sets(workspace)
    return {
        "locations_count": len(locations),
        "props_count": len(props),
        "locations_proposed": sum(1 for x in locations if x.get("status") == "proposed_story_canon"),
        "props_proposed": sum(1 for x in props if x.get("status") == "proposed_story_canon"),
        "locations_with_primary": sum(1 for x in locations if x.get("has_primary_image")),
        "props_with_primary": sum(1 for x in props if x.get("has_primary_image")),
        "expression_sets_count": len(expressions),
        "expression_images_count": sum(int(x.get("image_count") or 0) for x in expressions),
        "season": "2026-emo-monkeys-the-signal-between-us",
    }
