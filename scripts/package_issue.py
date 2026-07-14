#!/usr/bin/env python3
"""Operator helper: assemble pages (optional) and build CBZ/export checklist.

Usage:
  python scripts/package_issue.py 2026-08_Issue_06
  python scripts/package_issue.py 2026-08_Issue_06 --assemble
  python scripts/package_issue.py 2026-08_Issue_06 --archive

Does not invent PDF lettering quality. Uses existing Stage 8/10 scripts:
  - 00_SYSTEM/scripts/assemble_pages.py  (optional --assemble)
  - 00_SYSTEM/scripts/build_release.py
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_SCRIPTS = ROOT / "00_SYSTEM" / "scripts"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_folder", help="Folder name under 02_MONTHLY_ISSUES, e.g. 2026-08_Issue_06")
    parser.add_argument("--assemble", action="store_true", help="Run assemble_pages.py before build_release")
    parser.add_argument("--archive", action="store_true", help="Pass --archive to build_release (legacy full-tree copy)")
    args = parser.parse_args()

    issue_dir = ROOT / "02_MONTHLY_ISSUES" / args.issue_folder
    if not issue_dir.is_dir():
        print(f"ERROR: missing issue folder {issue_dir}", file=sys.stderr)
        return 1

    if args.assemble:
        assemble = SYSTEM_SCRIPTS / "assemble_pages.py"
        print(f"==> assemble_pages {args.issue_folder}")
        result = subprocess.run([sys.executable, str(assemble), args.issue_folder], cwd=str(ROOT))
        if result.returncode != 0:
            return result.returncode

    build = SYSTEM_SCRIPTS / "build_release.py"
    cmd = [sys.executable, str(build), args.issue_folder]
    if args.archive:
        cmd.append("--archive")
    print(f"==> build_release {' '.join(cmd[2:])}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        return result.returncode

    print()
    print("Next (formal Banana Lab release gates):")
    print("  1. Ensure QA PASS is promoted and current")
    print("  2. Complete CHIP-0015 metadata without TODO placeholders")
    print("  3. Studio Release workspace: Approve → Promote manifest → Publish archive")
    print("  4. Advance workflow to Published")
    print("  5. .\\Backup-BananaLab.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
