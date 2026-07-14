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
    payload = {
        "summary": canon_catalog.catalog_summary(ROOT),
        "locations": canon_catalog.list_locations(ROOT),
        "props": canon_catalog.list_props(ROOT),
    }
    (out / "canon-catalog.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {payload['summary']['locations_count']} locations, {payload['summary']['props_count']} props")
