#!/usr/bin/env python3
"""Create a timestamped offline backup of MonkeyZoo production evidence.

Git is not sufficient for untracked art, PDF/CBZ packages, release archives,
or owner-managed assets. This script copies the critical trees into a single
backup folder with a manifest of SHA-256 hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TARGETS = [
    "02_MONTHLY_ISSUES",
    "03_APPROVED_CANON",
    "05_RELEASE_ARCHIVE",
    "character-bibles",
    "01_IDEAS_INBOX",
    "story-bibles",
    "04_REJECTED_OUTPUTS",
]


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def backup(destination_root: Path, targets: list[str], dry_run: bool = False) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = destination_root / f"monkeyzoo-backup-{stamp}"
    if destination.exists():
        raise SystemExit(f"Backup destination already exists: {destination}")
    if not dry_run:
        destination.mkdir(parents=True)
    copied: list[dict[str, object]] = []
    skipped: list[str] = []
    for rel in targets:
        source = ROOT / rel
        if not source.exists():
            skipped.append(rel)
            continue
        target = destination / rel
        print(f"BACKUP {rel} -> {target.relative_to(destination_root) if not dry_run else target}")
        if dry_run:
            continue
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
            )
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for path in sorted(target.rglob("*")):
            if path.is_file():
                copied.append(
                    {
                        "path": str(path.relative_to(destination)).replace("\\", "/"),
                        "size": path.stat().st_size,
                        "sha256": _hash_file(path),
                    }
                )
    if dry_run:
        print("Dry run complete; no files written.")
        return destination
    manifest = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_root": str(ROOT),
        "targets": targets,
        "skipped_missing": skipped,
        "file_count": len(copied),
        "files": copied,
    }
    (destination / "BACKUP_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (destination / "BACKUP_README.md").write_text(
        "# MonkeyZoo production backup\n\n"
        f"- Created: {manifest['created_at']}\n"
        f"- Source: `{ROOT}`\n"
        f"- Files: {len(copied)}\n"
        f"- Skipped missing targets: {', '.join(skipped) or 'none'}\n\n"
        "Restore by copying trees back into a MonkeyZoo workspace root, then "
        "run `python -m pytest character-bibles/_review_app/tests -q`.\n",
        encoding="utf-8",
    )
    print(f"Wrote {destination / 'BACKUP_MANIFEST.json'} ({len(copied)} files)")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        default=str(ROOT / "06_BACKUPS"),
        help="Directory that will contain the timestamped backup folder",
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Relative paths under the workspace root to include",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    destination_root = Path(args.dest)
    if not args.dry_run:
        destination_root.mkdir(parents=True, exist_ok=True)
    path = backup(destination_root, list(args.targets), dry_run=args.dry_run)
    print(f"Backup complete: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
