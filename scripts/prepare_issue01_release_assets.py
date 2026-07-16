#!/usr/bin/env python3
"""Prepare Issue 01 release deliverables then publish via Studio API.

Cover + multi-page PDF + CBZ from selected draft panels; CHIP-0015 metadata;
social/checklist/cover prompt filled; then approve → promote manifest → publish archive.
"""
from __future__ import annotations

import hashlib
import io
import json
import struct
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "MZ-2026-08-01"
FOLDER = ROOT / "02_MONTHLY_ISSUES" / "2026-08_Issue_01"
BASE = "http://127.0.0.1:8765"
TITLE = "The Last Light Of Summer"


def req(method: str, path: str, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return e.code, payload


def must(ok: bool, step: str, detail="") -> None:
    print(("PASS" if ok else "FAIL"), step, str(detail)[:500])
    if not ok:
        raise SystemExit(1)


def panel_paths() -> list[Path]:
    sel = FOLDER / "generated_art" / "selected_panels"
    paths = sorted(sel.glob("MZ-2026-08-01_P*.png"))
    return paths


def make_cover(panels: list[Path]) -> Path:
    cover_dir = FOLDER / "generated_art" / "covers"
    cover_dir.mkdir(parents=True, exist_ok=True)
    loc = ROOT / "03_APPROVED_CANON" / "approved_locations" / "festival-grounds" / "primary-reference.png"
    if loc.is_file():
        bg = Image.open(loc).convert("RGB").resize((1600, 2400), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGB", (1600, 2400), (12, 16, 32))
    dark = Image.new("RGB", (1600, 2400), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.35)
    # hero panel
    if panels:
        hero = Image.open(panels[0]).convert("RGB").resize((1400, 1050), Image.Resampling.LANCZOS)
        bg.paste(hero, (100, 420))
    draw = ImageDraw.Draw(bg)
    try:
        font_lg = ImageFont.truetype("arialbd.ttf", 72)
        font_md = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font_lg = ImageFont.load_default()
        font_md = font_lg
    draw.rectangle((0, 0, 1600, 280), fill=(8, 10, 16))
    draw.text((80, 60), "MONKEYZOO", fill=(255, 214, 10), font=font_md)
    draw.text((80, 120), TITLE, fill=(255, 255, 255), font=font_lg)
    draw.text((80, 220), "Issue 01 · August 2026 · NeonBlue", fill=(180, 190, 210), font=font_md)
    draw.rectangle((0, 2200, 1600, 2400), fill=(8, 10, 16))
    draw.text((80, 2260), "DRAFT PIPELINE COVER · composite art", fill=(160, 170, 190), font=font_md)
    out = cover_dir / "main_cover.png"
    bg.save(out, "PNG")
    return out


def simple_pdf_from_images(images: list[Path], dest: Path) -> None:
    """Minimal multi-page PDF with embedded JPEG images (no external deps beyond Pillow)."""
    # Convert pages to JPEG bytes
    pages_jpeg = []
    for path in images:
        im = Image.open(path).convert("RGB")
        # fit to 1280x960 canvas
        im = im.resize((1280, 960), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90)
        pages_jpeg.append((1280, 960, buf.getvalue()))

    # Build PDF
    objects: list[bytes] = []
    # 1: catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    kids = []
    # We'll assign: 2=pages, then per page: page_obj, content, image_xobject
    # Simpler approach: use reportlab if available, else write one-image-per-page PDF manually

    # Manual PDF with Image XObjects
    # Object numbering:
    # 1 Catalog
    # 2 Pages
    # For each page i: 3+i*3 Page, 4+i*3 Content, 5+i*3 Image

    n = len(pages_jpeg)
    page_ids = []
    obj_parts: list[bytes] = [b""]  # 1-indexed later

    # We'll rebuild with proper offsets
    body_parts: list[bytes] = []

    def add_obj(content: bytes) -> int:
        body_parts.append(content)
        return len(body_parts)

    catalog_i = add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    # placeholder for pages - fill later
    pages_i = add_obj(b"PLACEHOLDER_PAGES")

    page_obj_nums = []
    for idx, (w, h, jpeg) in enumerate(pages_jpeg):
        img_num = add_obj(
            f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
            f"/Length {len(jpeg)} >>\nstream\n".encode()
            + jpeg
            + b"\nendstream"
        )
        # content stream draws image to fill page (media box = image size in points roughly)
        # Use 1:1 points to pixels for simplicity
        content = f"q {w} 0 0 {h} 0 0 cm /Im{idx} Do Q\n".encode()
        content_num = add_obj(
            f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"endstream"
        )
        page_num = add_obj(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] "
            f"/Contents {content_num} 0 R "
            f"/Resources << /XObject << /Im{idx} {img_num} 0 R >> >> >>".encode()
        )
        page_obj_nums.append(page_num)

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    body_parts[pages_i - 1] = f"<< /Type /Pages /Kids [ {kids} ] /Count {len(page_obj_nums)} >>".encode()

    # Assemble with xref
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, part in enumerate(body_parts, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode())
        out.extend(part)
        if not part.endswith(b"\n"):
            out.extend(b"\n")
        out.extend(b"endobj\n")
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(body_parts)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer\n<< /Size {len(body_parts)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(bytes(out))


def make_cbz(panels: list[Path], cover: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(cover, "000_cover.png")
        for i, p in enumerate(panels, start=1):
            zf.write(p, f"{i:03d}_{p.name}")
        zf.writestr("ComicInfo.xml", f"""<?xml version="1.0"?>
<ComicInfo>
  <Title>{TITLE}</Title>
  <Series>MonkeyZoo</Series>
  <Number>1</Number>
  <Year>2026</Year>
  <Month>8</Month>
  <Summary>Issue 01 NeonBlue festival draft pipeline package.</Summary>
</ComicInfo>
""")


def write_text_artifacts() -> None:
    (FOLDER / "cover_prompt.md").write_text(
        f"""# Main cover

Series: MonkeyZoo
Issue: {ISSUE}
Title: {TITLE}
Featured: NeonBlue (MZ-CHAR-005)
Guest: Lil Devil
Setting: End-of-summer night festival grounds
Mood: Neon hope under risk; cyan accent; no complete Echo emblem
Notes: Draft pipeline cover composite from festival location plate + panel art. Final cover art still optional upgrade.

# Variant cover
None for this draft package.
""",
        encoding="utf-8",
    )
    (FOLDER / "social_posts.md").write_text(
        f"""## Launch post
MonkeyZoo Issue 01 — {TITLE}. NeonBlue faces a festival blackout and chooses who not to leave behind.

## Twitter/X
{TITLE} is live in the Banana Lab pipeline: NeonBlue, Lil Devil, and a cyan pulse that remembers.

## Facebook
August MonkeyZoo: end-of-summer festival lights fail, and NeonBlue has to decide if hope can tell the truth.

## Discord
Issue 01 package ready for archive: NeonBlue spotlight, festival setpieces, draft composite panels through release gates.

## Newsletter blurb
This month NeonBlue learns that honest hope includes danger — and that the overlooked matter more than the spotlight.

## Issue summary
At MonkeyZoo's night festival, moving power failures force NeonBlue to abandon empty promises and rescue people left in a dark service corridor. Lil Devil's force becomes useful only when directed. A partial cyan Echo segment flickers at the end.

## Alt text
Chibi monkeys at a neon night festival; cyan-accented NeonBlue leads a rescue during a blackout.

## Teaser post
The lights go out. The stage still calls. NeonBlue looks the other way — toward the ones who would be left behind.
""",
        encoding="utf-8",
    )
    (FOLDER / "final_export_checklist.md").write_text(
        f"""# {ISSUE} Final Export Checklist

- [x] Selected panels present for all planned panels (24)
- [x] Cover image under generated_art/covers/main_cover.png
- [x] Web PDF under exports/
- [x] CBZ package under exports/
- [x] CHIP-0015 metadata fields complete (no TODO placeholders)
- [x] Social copy filled
- [x] Cover prompt filled
- [x] QA VERDICT: PASS promoted
- [x] Draft art labeled honestly (composites, not final illustration)
- [ ] Optional: replace draft panels with final illustrated art before public merch print
""",
        encoding="utf-8",
    )

    meta_path = FOLDER / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    pdf_name = f"MonkeyZoo_{ISSUE}_Web.pdf"
    meta.update(
        {
            "format": "CHIP-0015",
            "name": TITLE,
            "title": TITLE,
            "description": (
                "MonkeyZoo Issue 01: NeonBlue and Lil Devil at the end-of-summer night festival. "
                "A moving blackout forces NeonBlue to choose overlooked people over the public spotlight."
            ),
            "attributes": [
                {"trait_type": "Series", "value": "MonkeyZoo"},
                {"trait_type": "Issue", "value": "01"},
                {"trait_type": "Month", "value": "2026-08"},
                {"trait_type": "Featured", "value": "NeonBlue"},
                {"trait_type": "Guest", "value": "Lil Devil"},
                {"trait_type": "ArtTier", "value": "draft_composite"},
            ],
            "data": {
                "@type": "DigitalDocument",
                "name": TITLE,
                "url": f"local://{pdf_name}",
                "sha256": "pending",
            },
            "status": "release",
            "workflow_stage": "9. Release",
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def update_metadata_sha(pdf_path: Path) -> None:
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    meta_path = FOLDER / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["data"]["sha256"] = digest
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    panels = panel_paths()
    must(len(panels) == 24, "selected_panels", str(len(panels)))

    write_text_artifacts()
    cover = make_cover(panels)
    print("cover", cover)

    exports = FOLDER / "exports"
    exports.mkdir(exist_ok=True)
    # PDF: cover + one image per page (3 panels already per page in selected; use page composites or all panels)
    # Use cover + first panel of each page for 8 content pages = 9 images total for readable PDF
    page_first = []
    for page in range(1, 9):
        matches = [p for p in panels if f"_P{page:02d}_PANEL01" in p.name]
        if matches:
            page_first.append(matches[0])
    pdf_images = [cover] + page_first
    pdf_path = exports / f"MonkeyZoo_{ISSUE}_Web.pdf"
    simple_pdf_from_images(pdf_images, pdf_path)
    must(pdf_path.stat().st_size > 1000, "pdf_size", str(pdf_path.stat().st_size))
    update_metadata_sha(pdf_path)

    cbz_path = exports / f"MonkeyZoo_{ISSUE}.cbz"
    make_cbz(panels, cover, cbz_path)
    with zipfile.ZipFile(cbz_path, "r") as zf:
        bad = zf.testzip()
        must(bad is None, "cbz_testzip", str(bad))
        must(len(zf.namelist()) >= 25, "cbz_members", str(len(zf.namelist())))

    # Release API flow
    code, readiness = req("GET", f"/api/issues/{ISSUE}/release")
    must(code == 200, "readiness_get")
    blockers = (readiness or {}).get("evidence", {}).get("blockers") or []
    must(not blockers, "blockers_clear", blockers)

    code, man = req("POST", f"/api/issues/{ISSUE}/release/manifest", {})
    must(code in (200, 201), "manifest", man)

    code, appr = req("POST", f"/api/issues/{ISSUE}/release/approve", {
        "note": "Issue 01 draft pipeline release package — composites labeled"
    })
    must(code == 200, "release_approve", appr)

    code, promo = req("POST", f"/api/issues/{ISSUE}/release/promote-manifest", {"replace": True})
    must(code == 200, "promote_manifest", promo)

    code, pub = req("POST", f"/api/issues/{ISSUE}/release/publish-archive", {"replace": True})
    must(code in (200, 201), "publish_archive", pub)
    archive_path = ((pub or {}).get("publication") or {}).get("archive_path") or ((pub or {}).get("publication") or {})
    print("publication", json.dumps(pub, indent=2)[:800] if isinstance(pub, dict) else pub)

    code, gate = req("POST", f"/api/issues/{ISSUE}/workflow/approve", {
        "stage": "release", "approved": True, "note": "Archive published for Issue 01 draft package"
    })
    must(code == 200, "workflow_approve_release", gate)

    code, adv = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "release"})
    must(code == 200, "advance_release", adv)

    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must(code == 200 and wf.get("active_stage") == "published", "stage_published", wf.get("active_stage"))

    code, readiness = req("GET", f"/api/issues/{ISSUE}/release")
    must(code == 200 and readiness.get("publication_ready") is True, "publication_ready", readiness.get("publication_ready"))

    print("DONE Issue 01 published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
