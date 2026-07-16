"""Export read-only locations/props catalogs for GitHub Pages."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import canon_catalog  # noqa: E402

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
    # Expression image URLs are local-only; export inventory metadata without full image lists for Pages.
    expressions = [
        {
            "slug": item["slug"],
            "display_name": item["display_name"],
            "image_count": item["image_count"],
            "base_image": item.get("base_image"),
            "folder": item.get("folder"),
        }
        for item in canon_catalog.list_expression_sets(ROOT)
    ]
    payload = {
        "summary": canon_catalog.catalog_summary(ROOT),
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
