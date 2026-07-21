#!/usr/bin/env python3
"""Genesis release packager: CBZ + PDF + manifest + checksums.

Assembles the web-edition pages and covers (in reading order: front cover,
pages 1-22, back cover) into a CBZ archive and a PDF, then writes a release
manifest and a SHA256SUMS file. Refuses to package if any page is missing or
out of sequence.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

FACTORY = Path(__file__).resolve().parents[3]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def ordered_pages(genesis_dir: Path) -> list[Path]:
    """Reading order: 01 front cover, 02..23 story pages, 24 back cover."""
    web = genesis_dir / "web"
    files = list((web / "covers").glob("*.jpg")) + list((web / "story_pages").glob("*.jpg"))
    files.sort(key=lambda p: p.name)               # names are zero-padded 01..24
    return files


def _check_sequence(files: list[Path]) -> None:
    # Every release file must start with a two-digit page number. A stray/misnamed
    # jpg in the render dirs must trip the clean ABORT this packager promises, not
    # crash it with a ValueError (int('th')) mid-package.
    nums = []
    for p in files:
        prefix = p.name[:2]
        if not prefix.isdigit():
            raise SystemExit(f"ABORT: release file without a two-digit page prefix: {p.name}")
        nums.append(int(prefix))
    expected = list(range(1, 25))
    if nums != expected:
        raise SystemExit(f"ABORT: page sequence is not 01..24 in reading order: got {nums}")
    # exactly one front (01) and one back (24)
    if not files[0].name.startswith("01_") or not files[-1].name.startswith("24_"):
        raise SystemExit("ABORT: front cover must be 01 and back cover 24")


def build_cbz(files: list[Path], out: Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=p.name)


def build_pdf(files: list[Path], out: Path) -> None:
    imgs = [Image.open(p).convert("RGB") for p in files]
    try:
        imgs[0].save(out, "PDF", save_all=True, append_images=imgs[1:], resolution=150.0)
    finally:
        for img in imgs:
            img.close()



def package(genesis_dir: Path) -> dict:
    files = ordered_pages(genesis_dir)
    _check_sequence(files)
    rel = genesis_dir / "release"
    rel.mkdir(parents=True, exist_ok=True)
    cbz = rel / "MonkeyZoo_Genesis.cbz"
    pdf = rel / "MonkeyZoo_Genesis.pdf"
    build_cbz(files, cbz)
    build_pdf(files, pdf)

    manifest = {
        "series": "MonkeyZoo",
        "issue_title": "Genesis",
        "published_issue": 1,
        "production_issue": 8,
        "reading_order": [p.name for p in files],
        "page_count_total": len(files),
        "story_pages": len(files) - 2,
        "covers": {"front": files[0].name, "back": files[-1].name},
        "edition": "web (1600px wide, JPG q88) — source panels are 1280x720 web tier",
        "artifacts": {
            "cbz": {"file": cbz.name, "sha256": _sha256(cbz), "bytes": cbz.stat().st_size},
            "pdf": {"file": pdf.name, "sha256": _sha256(pdf), "bytes": pdf.stat().st_size},
        },
    }
    (rel / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # SHA256SUMS over the release artifacts + covers + web pages
    sums = []
    for p in [cbz, pdf] + files:
        sums.append(f"{_sha256(p)}  {p.relative_to(genesis_dir).as_posix()}")
    (rel / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return {"cbz": str(cbz), "pdf": str(pdf), "pages": len(files), "manifest": manifest}


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    r = package(genesis_dir)
    m = r["manifest"]
    print(f"Genesis release: {r['pages']} images ({m['story_pages']} pages + 2 covers)")
    print(f"  CBZ: {m['artifacts']['cbz']['file']}  {m['artifacts']['cbz']['bytes']//1024} KB")
    print(f"  PDF: {m['artifacts']['pdf']['file']}  {m['artifacts']['pdf']['bytes']//1024} KB")
    print("  reading order verified 01..24; manifest + SHA256SUMS written")


if __name__ == "__main__":
    main()
