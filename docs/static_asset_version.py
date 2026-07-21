"""Deterministic cache-busting tokens for generated static assets."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


def version_token(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def versioned_script_url(path: Path, prefix: str = "/static/app.js") -> str:
    return f"{prefix}?v={version_token(path)}"


def replace_script_version(html: str, token: str, script_path: str = "./static/app.js") -> str:
    """Replace one or more existing query tokens with exactly one deployed hash."""
    return replace_asset_version(html, token, script_path)


def replace_asset_version(html: str, token: str, asset_path: str) -> str:
    """Replace existing query tokens for any asset path with deployed SHA256 hash."""
    pattern = re.escape(asset_path) + r"(?:\?v=[^\"'<>\s]*)?"
    return re.sub(pattern, f"{asset_path}?v={token}", html)



def update_html_for_deployed_bundle(html_path: Path, bundle_path: Path) -> str:
    """Version static HTML from the exact bytes that will be deployed."""
    token = version_token(bundle_path)
    html = html_path.read_text(encoding="utf-8")
    html_path.write_text(replace_script_version(html, token), encoding="utf-8", newline="")
    return token


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--update-html":
        print(update_html_for_deployed_bundle(Path(sys.argv[2]), Path(sys.argv[3])))
    else:
        print(version_token(Path(sys.argv[1])))
