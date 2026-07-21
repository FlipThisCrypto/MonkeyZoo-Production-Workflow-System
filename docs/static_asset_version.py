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
    """Stamp ``asset_path`` with ``?v=<token>``, replacing any existing token.

    The match is right-anchored: the asset path must be followed by its optional
    ``?v=...`` query and then an attribute delimiter (quote / whitespace / ``>``)
    or end-of-string. Without that anchor a path that is a *prefix* of another
    token — e.g. stamping ``app.js`` while the page also references ``app.json`` —
    would be rewritten into ``app.js?v=...on``, corrupting the longer reference.
    """
    pattern = re.escape(asset_path) + r"(?:\?v=[^\"'<>\s]*)?(?=[\"'\s>]|$)"
    # Escape backslashes in the replacement so a Windows-style path can't be read
    # as a regex group reference; asset refs are POSIX-relative in practice.
    replacement = (asset_path + f"?v={token}").replace("\\", "\\\\")
    return re.sub(pattern, replacement, html)


def update_html_for_deployed_asset(html_path: Path, asset_ref: str, file_path: Path) -> str:
    """Version one asset reference in ``html_path`` from the exact deployed bytes."""
    token = version_token(Path(file_path))
    html = html_path.read_text(encoding="utf-8")
    html_path.write_text(replace_asset_version(html, token, asset_ref), encoding="utf-8", newline="")
    return token


def update_html_for_deployed_bundle(html_path: Path, bundle_path: Path) -> str:
    """Version static HTML's app.js reference from the exact deployed bytes."""
    return update_html_for_deployed_asset(html_path, "./static/app.js", bundle_path)


def _usage() -> None:
    print(
        "usage:\n"
        "  static_asset_version.py <file>                       # print sha256 token\n"
        "  static_asset_version.py --update-html <html> <bundle>  # version ./static/app.js\n"
        "  static_asset_version.py --update-asset <html> <ref> <file>  # version any asset ref",
        file=sys.stderr,
    )


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--update-html":
        print(update_html_for_deployed_bundle(Path(sys.argv[2]), Path(sys.argv[3])))
    elif len(sys.argv) == 5 and sys.argv[1] == "--update-asset":
        print(update_html_for_deployed_asset(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])))
    elif len(sys.argv) == 2 and not sys.argv[1].startswith("--"):
        print(version_token(Path(sys.argv[1])))
    else:
        _usage()
        sys.exit(2)
