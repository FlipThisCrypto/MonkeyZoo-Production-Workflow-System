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


def verify(genesis_dir: Path) -> dict:
    """Re-verify a packaged release before distribution/minting. Every file listed
    in SHA256SUMS.txt must exist and match its recorded hash (detects post-package
    corruption or a swapped file), and the release manifest's per-artifact sha256
    and byte size -- the provenance the CBZ/PDF are distributed and CHIP-0015
    minted with -- must match the actual files (detects manifest/file drift).
    Returns {'verified', 'problems'}; problems is empty for an intact release."""
    rel = genesis_dir / "release"
    sums_path = rel / "SHA256SUMS.txt"
    if not sums_path.is_file():
        raise SystemExit(f"No SHA256SUMS.txt found in {rel} (nothing to verify).")

    problems: list[str] = []
    verified = 0
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("  ", 1)  # sha256sum format: "<64-hex>  <path>"
        if len(parts) != 2 or len(parts[0]) != 64:
            problems.append(f"malformed SHA256SUMS entry: {line[:70]}")
            continue
        expected, relpath = parts[0].strip(), parts[1].strip()
        target = genesis_dir / relpath
        if not target.is_file():
            problems.append(f"MISSING: {relpath}")
        elif _sha256(target) != expected:
            problems.append(f"HASH MISMATCH (corrupted): {relpath}")
        else:
            verified += 1

    manifest_path = rel / "release_manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"unreadable release_manifest.json: {exc}")
            manifest = {}
        for kind, art in (manifest.get("artifacts") or {}).items():
            fname = art.get("file", "")
            target = rel / fname
            if not target.is_file():
                problems.append(f"manifest artifact missing: {fname}")
                continue
            if _sha256(target) != art.get("sha256"):
                problems.append(f"manifest {kind} sha256 mismatch for {fname} (provenance drift)")
            if target.stat().st_size != art.get("bytes"):
                problems.append(f"manifest {kind} byte size mismatch for {fname}")
    return {"release": str(rel), "verified": verified, "problems": problems}


def main() -> None:
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    genesis_dir = Path(positional[0]) if positional else FACTORY / "GENESIS"

    if "--verify" in sys.argv:
        result = verify(genesis_dir)
        for problem in result["problems"]:
            print(f"  FAIL {problem}")
        status = "FAILED" if result["problems"] else "OK"
        print(f"Release verify {status}: {result['verified']} checksummed file(s) intact, "
              f"{len(result['problems'])} problem(s) in {result['release']}")
        raise SystemExit(1 if result["problems"] else 0)

    r = package(genesis_dir)
    m = r["manifest"]
    print(f"Genesis release: {r['pages']} images ({m['story_pages']} pages + 2 covers)")
    print(f"  CBZ: {m['artifacts']['cbz']['file']}  {m['artifacts']['cbz']['bytes']//1024} KB")
    print(f"  PDF: {m['artifacts']['pdf']['file']}  {m['artifacts']['pdf']['bytes']//1024} KB")
    print("  reading order verified 01..24; manifest + SHA256SUMS written")


if __name__ == "__main__":
    main()
