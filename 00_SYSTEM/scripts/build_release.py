#!/usr/bin/env python3
"""Package MonkeyZoo issue exports and archive released issues.

Usage:
    python build_release.py 2026-07_Issue_05            # build CBZ from web layout
    python build_release.py 2026-07_Issue_05 --archive  # copy to 05_RELEASE_ARCHIVE

CBZ = zip of layout/web_layout pages in reading order plus cover.png.
PDFs are produced by the layout tool (Krita/Affinity export); this script
verifies they exist and reports what's missing rather than faking them.
"""
import shutil
import sys
import zipfile
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]


def build_cbz(issue_dir: Path, number: str) -> None:
    web = issue_dir / "layout" / "web_layout"
    pages = sorted(web.glob("page_*.png"))
    cover = issue_dir / "exports" / "cover.png"
    if not pages:
        print(f"  SKIP CBZ: no pages in {web}")
        return
    out = issue_dir / "exports" / f"MonkeyZoo_Issue_{number}_CBZ.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        if cover.exists():
            z.write(cover, "000_cover.png")
        for i, p in enumerate(pages, 1):
            z.write(p, f"{i:03d}_{p.name}")
    print(f"  Built {out.name} ({len(pages)} pages{' + cover' if cover.exists() else ''})")


def check_exports(issue_dir: Path, number: str) -> None:
    expected = [
        f"MonkeyZoo_Issue_{number}_Print.pdf",
        f"MonkeyZoo_Issue_{number}_Web.pdf",
        f"MonkeyZoo_Issue_{number}_CBZ.zip",
        "cover.png",
    ]
    for name in expected:
        status = "OK " if (issue_dir / "exports" / name).exists() else "MISSING"
        print(f"  [{status}] exports/{name}")


def archive(issue_dir: Path, number: str) -> None:
    year = issue_dir.name[:4]
    dest = FACTORY / "05_RELEASE_ARCHIVE" / year / f"Issue_{number}"
    if dest.exists():
        sys.exit(f"ABORT: archive already exists at {dest}")
    shutil.copytree(
        issue_dir, dest,
        ignore=shutil.ignore_patterns("raw_panels"),
    )
    print(f"  Archived to {dest} (raw_panels excluded)")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    issue_dir = FACTORY / "02_MONTHLY_ISSUES" / sys.argv[1]
    if not issue_dir.is_dir():
        sys.exit(f"No such issue folder: {issue_dir}")
    number = issue_dir.name.split("_Issue_")[1]

    if "--archive" in sys.argv:
        archive(issue_dir, number)
    else:
        build_cbz(issue_dir, number)
        check_exports(issue_dir, number)


if __name__ == "__main__":
    main()
