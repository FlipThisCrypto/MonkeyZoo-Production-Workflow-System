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


def _find_cover(issue_dir: Path) -> Path | None:
    candidates = [
        issue_dir / "exports" / "cover.png",
        issue_dir / "generated_art" / "covers" / "main_cover.png",
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return path
    generated = issue_dir / "generated_art"
    if generated.exists():
        matches = sorted(p for p in generated.rglob("*cover*.png") if p.is_file() and p.stat().st_size > 0)
        if matches:
            return matches[0]
    return None


def build_cbz(issue_dir: Path, number: str) -> None:
    web = issue_dir / "layout" / "web_layout"
    pages = sorted(web.glob("page_*.png"))
    cover = _find_cover(issue_dir)
    if not pages:
        print(f"  SKIP CBZ: no pages in {web}")
        return
    exports = issue_dir / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    out = exports / f"MonkeyZoo_Issue_{number}_CBZ.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        if cover is not None:
            z.write(cover, "000_cover.png")
        for i, p in enumerate(pages, 1):
            z.write(p, f"{i:03d}_{p.name}")
    print(f"  Built {out.name} ({len(pages)} pages{' + cover' if cover is not None else ''})")


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
    # Unique destination: year/full-folder (legacy year/Issue_NN collides across months).
    dest = FACTORY / "05_RELEASE_ARCHIVE" / year / issue_dir.name
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
