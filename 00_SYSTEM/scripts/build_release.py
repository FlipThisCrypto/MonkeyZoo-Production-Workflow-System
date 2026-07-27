#!/usr/bin/env python3
"""Package MonkeyZoo issue exports and archive released issues.

Usage:
    python build_release.py 2026-07_Issue_05            # build CBZ from web layout
    python build_release.py 2026-07_Issue_05 --archive  # copy to 05_RELEASE_ARCHIVE

CBZ = zip of layout/web_layout pages in reading order plus cover.png.
PDFs are produced by the layout tool (Krita/Affinity export); this script
verifies they exist and reports what's missing rather than faking them.
"""
import os
import shutil
import sys
import zipfile
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import issue_cover  # noqa: E402  the one canonical cover-location contract

__all__ = ["build_cbz", "check_exports", "archive"]


FACTORY = Path(__file__).resolve().parents[2]



def _find_cover(issue_dir: Path) -> Path | None:
    """Resolve the final cover through the shared contract.

    This used to prefer ``exports/cover.png`` and then fall back to a fuzzy
    ``*cover*.png`` sweep of ``generated_art/`` -- a search order the Studio
    release gate did not share, so the two surfaces could disagree about
    whether an issue had a cover at all. The order now lives in one place
    (``issue_cover``), and the fuzzy sweep is gone: it let a preview render
    stand in for the deliverable and made the result depend on filesystem case
    rules.

    A legacy-located cover is still accepted, but it announces itself rather
    than passing silently, so the deprecation is visible where the packaging
    actually happens.
    """
    resolved = issue_cover.resolve_final_cover(issue_dir)
    if resolved.warning:
        print(f"  WARN: {resolved.warning}")
    return resolved.path


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
    ]
    for name in expected:
        status = "OK " if (issue_dir / "exports" / name).exists() else "MISSING"
        print(f"  [{status}] exports/{name}")

    # The cover is reported through the shared contract rather than listed as
    # `exports/cover.png`. Listing it there was one of the two sources that
    # taught operators the deprecated location in the first place.
    resolved = issue_cover.resolve_final_cover(issue_dir)
    if resolved.source == "canonical":
        print(f"  [OK ] {issue_cover.CANONICAL_RELPATH}")
    elif resolved.source == "legacy":
        print(f"  [OK ] {issue_cover.LEGACY_RELPATH}  (DEPRECATED)")
        print(f"        {resolved.warning}")
    else:
        print(f"  [MISSING] {issue_cover.CANONICAL_RELPATH}")
        print(f"        {resolved.blocker}")


def archive(issue_dir: Path, number: str) -> None:
    year = issue_dir.name[:4]
    # Unique destination: year/full-folder (legacy year/Issue_NN collides across months).
    dest = FACTORY / "05_RELEASE_ARCHIVE" / year / issue_dir.name
    if dest.exists():
        sys.exit(f"ABORT: archive already exists at {dest}")
    # Copy into a temp sibling and rename into place only on success, so an
    # interrupted copy (Ctrl-C, disk full, per-file error) cannot leave a
    # partial archive that the exists() guard then permanently refuses to retry.
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.partial-{os.getpid()}")
    if tmp.exists():
        shutil.rmtree(tmp)
    try:
        shutil.copytree(issue_dir, tmp, ignore=shutil.ignore_patterns("raw_panels"))
        os.replace(tmp, dest)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
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
