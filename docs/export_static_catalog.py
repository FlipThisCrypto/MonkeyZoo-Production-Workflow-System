"""Export read-only locations/props/expressions catalogs for GitHub Pages."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import canon_catalog  # noqa: E402

EXPR_MAX_EDGE = 512
EXPR_QUALITY = 82


def _encode_media_url(rel: str) -> str:
    """Percent-encode each path segment of a relative media URL so expression
    slugs / filenames containing spaces or unicode resolve on GitHub Pages, while
    leaving "." / ".." navigation segments and the "/" structure intact. Getting
    this wrong silently breaks image links on the public site, so it is isolated
    here and unit-tested rather than inlined in the asset loop."""
    return "/".join(
        part if part in (".", "..") else quote(part, safe="._-")
        for part in rel.replace("\\", "/").split("/")
    )


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
            # Relative URL from docs/index.html (segments percent-encoded for browsers)
            rel_encoded = _encode_media_url(f"./media/expressions/{slug}/{out_name}")
            images.append({"filename": out_name, "url": rel_encoded, "source_png": png.name})

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

    payload = {
        "summary": summary,
        "locations": canon_catalog.list_locations(ROOT),
        "props": canon_catalog.list_props(ROOT),
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
