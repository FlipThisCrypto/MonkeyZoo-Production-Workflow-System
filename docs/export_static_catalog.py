"""Export read-only locations/props/expressions catalogs for GitHub Pages."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import canon_catalog  # noqa: E402

EXPR_MAX_EDGE = 512
EXPR_QUALITY = 82
PRIMARY_MAX_EDGE = 768
PRIMARY_QUALITY = 82


def _export_primary_media(items: list[dict], kind: str) -> int:
    """Export each location/prop primary reference into docs/media/<kind> and
    rewrite its URL to a RAW RELATIVE path.

    canon_catalog emits the live app's absolute "/media/<kind>/<slug>/..." URL and
    never copies the file into docs/, so on GitHub Pages (served under a repo
    subpath) every locations/props thumbnail 404s. Mirror the expression export:
    resize the source primary-reference.png to a web-tier webp under
    docs/media/<kind>/<slug>/ and point the catalog at "./media/<kind>/<slug>/...".
    An item whose source image is missing/unreadable is marked has_primary_image
    False so the site never links a file that isn't there.
    """
    src_root = ROOT / "03_APPROVED_CANON" / f"approved_{kind}"
    dest_root = ROOT / "docs" / "media" / kind
    if dest_root.exists():
        shutil.rmtree(dest_root)
    exported = 0
    for entry in items:
        slug = (entry.get("folder") or "").rsplit("/", 1)[-1]
        source = src_root / slug / "primary-reference.png"
        if not (entry.get("has_primary_image") and slug and source.is_file()):
            entry["has_primary_image"] = False
            entry["primary_image_url"] = None
            continue
        try:
            img = Image.open(source).convert("RGB")
        except OSError:
            entry["has_primary_image"] = False
            entry["primary_image_url"] = None
            continue
        w, h = img.size
        scale = min(1.0, PRIMARY_MAX_EDGE / max(w, h))
        if scale < 1.0:
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        dest_dir = dest_root / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / "primary-reference.webp"
        try:
            img.save(out_path, "WEBP", quality=PRIMARY_QUALITY, method=4)
        except Exception:
            out_path = dest_dir / "primary-reference.jpg"
            img.save(out_path, "JPEG", quality=PRIMARY_QUALITY, optimize=True)
        entry["primary_image_url"] = f"./media/{kind}/{slug}/{out_path.name}".replace("\\", "/")
        exported += 1
    return exported


def _export_expression_assets() -> list[dict]:
    """Copy/resize expression plates into docs/media/expressions for Pages browsing."""
    src_root = ROOT / "03_APPROVED_CANON" / "approved_expressions"
    dest_root = ROOT / "docs" / "media" / "expressions"
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)

    exported: list[dict] = []
    if not src_root.is_dir():
        return exported

    for folder in sorted(src_root.iterdir(), key=lambda p: p.name.lower()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        slug = folder.name
        # URL-safe relative segment (keep readable names; encode at URL time)
        dest_dir = dest_root / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        images: list[dict] = []
        for png in sorted(folder.glob("*.png")):
            try:
                img = Image.open(png).convert("RGB")
            except OSError:
                continue
            w, h = img.size
            scale = min(1.0, EXPR_MAX_EDGE / max(w, h))
            if scale < 1.0:
                img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
            # Prefer webp for size; fall back to jpeg if webp unavailable
            out_name = png.stem + ".webp"
            out_path = dest_dir / out_name
            try:
                img.save(out_path, "WEBP", quality=EXPR_QUALITY, method=4)
            except Exception:
                out_name = png.stem + ".jpg"
                out_path = dest_dir / out_name
                img.save(out_path, "JPEG", quality=EXPR_QUALITY, optimize=True)
            # Relative URL from docs/index.html, emitted RAW (unencoded), matching
            # the contract of canon_catalog.expression_media_url and the
            # locations/props/character URLs: the single client-side mediaUrl()
            # percent-encodes each segment exactly once. Pre-encoding here caused a
            # double-encode (a spaced slug "lil devil" -> %20 -> client %2520) that
            # 404s every such expression plate on GitHub Pages.
            rel_url = f"./media/expressions/{slug}/{out_name}".replace("\\", "/")
            images.append({"filename": out_name, "url": rel_url, "source_png": png.name})

        if not images:
            continue
        base = next((i for i in images if "_00_clean_base" in i["filename"]), images[0])
        exported.append(
            {
                "slug": slug,
                "display_name": slug.replace("-", " ").replace("_", " ").title(),
                "image_count": len(images),
                "base_image": base["filename"],
                "base_image_url": base["url"],
                "folder": f"03_APPROVED_CANON/approved_expressions/{slug}",
                "images": [{"filename": i["filename"], "url": i["url"]} for i in images],
                "static_media": True,
            }
        )
        print(f"  expressions/{slug}: {len(images)} plates")
    return exported


if __name__ == "__main__":
    out = ROOT / "docs" / "static"
    out.mkdir(parents=True, exist_ok=True)
    # Project direction map for Project Map dashboard (Pages read-only)
    try:
        import project_direction  # noqa: E402

        direction = project_direction.enrich(project_direction.load_direction(ROOT))
        (out / "project-direction.json").write_text(
            json.dumps(direction, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Exported project direction ({direction.get('task_counts', {}).get('total', '?')} tasks)")
    except Exception as exc:  # pragma: no cover - export best-effort
        print(f"Project direction export skipped: {exc}")

    print("Exporting expression plates for GitHub Pages…")
    expressions = _export_expression_assets()

    # Prefer disk inventory when present; fall back to catalog list without media
    if not expressions:
        expressions = [
            {
                "slug": item["slug"],
                "display_name": item["display_name"],
                "image_count": item["image_count"],
                "base_image": item.get("base_image"),
                "base_image_url": item.get("base_image_url"),
                "folder": item.get("folder"),
                "images": item.get("images") or [],
                "static_media": False,
            }
            for item in canon_catalog.list_expression_sets(ROOT)
        ]

    summary = canon_catalog.catalog_summary(ROOT)
    # Override expression counts from exported static media when available
    if expressions:
        summary = dict(summary)
        summary["expression_sets_count"] = len(expressions)
        summary["expression_images_count"] = sum(int(x.get("image_count") or 0) for x in expressions)

    locations = canon_catalog.list_locations(ROOT)
    props = canon_catalog.list_props(ROOT)
    loc_media = _export_primary_media(locations, "locations")
    prop_media = _export_primary_media(props, "props")
    print(f"Exported {loc_media} location + {prop_media} prop primary images to docs/media")
    payload = {
        "summary": summary,
        "locations": locations,
        "props": props,
        "expressions": expressions,
    }
    (out / "canon-catalog.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Exported {payload['summary']['locations_count']} locations, "
        f"{payload['summary']['props_count']} props, "
        f"{len(expressions)} expression sets"
    )
