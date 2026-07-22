#!/usr/bin/env python3
"""Deployed static-site consistency gate for the public GitHub Pages export.

The exported catalog JSON references media by relative URL (raw/unencoded, per
the mediaUrl client contract). Nothing verified that those files actually exist
in the shipped docs/ tree, so a stale or buggy export could publish dangling
image references that 404 on the live site. This re-derives every media URL the
export declares and confirms it resolves to a real file, and that each data JSON
parses -- a deployment gate, run in CI, that fails before a broken site ships.

Checks:
  * required files exist (index.html, static/{styles.css,app.js,canon-catalog.json,characters.json})
  * each static/*.json data file is valid JSON
  * every media URL in canon-catalog.json (locations/props primary_image_url,
    expression base_image_url + images[].url) resolves to a file under docs/
  * every non-null characters.json primary_image resolves to a file under docs/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

DOCS = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "index.html",
    "static/styles.css",
    "static/app.js",
    "static/canon-catalog.json",
    "static/characters.json",
]
DATA_JSON = ["canon-catalog.json", "characters.json", "issue-workflows.json", "project-direction.json"]


def _resolve(url: str) -> str:
    """Map a stored media URL to a docs-relative filesystem path: drop any query,
    URL-decode, and strip a leading ./ or /."""
    path = unquote(urlsplit(url).path)
    if path.startswith("./"):
        path = path[2:]
    elif path.startswith("/"):
        path = path[1:]
    return path


def verify_static_site(docs: Path) -> list[str]:
    problems: list[str] = []

    for rel in REQUIRED_FILES:
        if not (docs / rel).is_file():
            problems.append(f"missing required file: {rel}")

    data: dict[str, object] = {}
    for name in DATA_JSON:
        path = docs / "static" / name
        if not path.is_file():
            continue
        try:
            data[name] = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"invalid JSON in static/{name}: {exc}")

    def check(url: object, where: str) -> None:
        if not url or not isinstance(url, str):
            return
        target = docs / _resolve(url)
        if not target.is_file():
            problems.append(f"dangling media reference ({where}): {url}")

    catalog = data.get("canon-catalog.json")
    if isinstance(catalog, dict):
        for loc in catalog.get("locations", []) or []:
            check(loc.get("primary_image_url"), f"location {loc.get('slug') or loc.get('location_id')}")
        for prop in catalog.get("props", []) or []:
            check(prop.get("primary_image_url"), f"prop {prop.get('slug') or prop.get('prop_id')}")
        for expr in catalog.get("expressions", []) or []:
            slug = expr.get("slug")
            check(expr.get("base_image_url"), f"expression {slug} base")
            for img in expr.get("images", []) or []:
                check(img.get("url"), f"expression {slug}/{img.get('filename')}")

    characters = data.get("characters.json")
    if isinstance(characters, list):
        for char in characters:
            if isinstance(char, dict):
                check(char.get("primary_image"), f"character {char.get('character_id')}")

    return problems


def main() -> None:
    docs = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCS
    if not docs.is_dir():
        print(f"docs/ not found: {docs} (nothing to verify)")
        return
    problems = verify_static_site(docs)
    if problems:
        print(f"Static site consistency FAILED with {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print(f"Static site consistency PASSED: {docs} references resolve, data JSON valid.")


if __name__ == "__main__":
    main()
