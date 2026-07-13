"""Deterministic cache-busting tokens for generated static assets."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def version_token(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def versioned_script_url(path: Path, prefix: str = "/static/app.js") -> str:
    return f"{prefix}?v={version_token(path)}"


if __name__ == "__main__":
    print(version_token(Path(sys.argv[1])))
