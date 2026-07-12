"""Export the canonical Studio character inventory and primary portraits only."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import bible_store


def export(root: Path = ROOT) -> list[dict]:
    bibles = root / "character-bibles"
    media = root / "docs" / "media"
    if media.exists():
        shutil.rmtree(media)
    media.mkdir(parents=True)
    records = []
    for character_id, data in bible_store.load_all(bibles):
        summary = bible_store.character_summary(character_id, data)
        relative = (data.get("visual_canon") or {}).get("primary_reference_image")
        source = bibles / character_id / relative if relative else None
        if source and source.is_file():
            target_dir = media / character_id
            target_dir.mkdir()
            target = target_dir / f"portrait{source.suffix.lower()}"
            shutil.copy2(source, target)
            summary["primary_image"] = f"./media/{character_id}/{target.name}"
            summary["image_status"] = "approved"
        else:
            summary["primary_image"] = None
            summary["image_status"] = "unavailable"
        records.append(summary)
    output = root / "docs" / "static" / "characters.json"
    output.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return records


if __name__ == "__main__":
    export()
