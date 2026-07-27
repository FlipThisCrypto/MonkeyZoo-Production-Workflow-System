"""Assemble the full 16-page issue preview from staged integration panels.

Builds:
  - one 2x3 preview page per plan page (dialogue strips under each panel)
  - a full-issue contact sheet (front cover, 16 pages as thumbnails, back cover)
All into generated_art/integration_preview/pages_preview/.
Missing panels render as a labeled PENDING placeholder so the sheet is
honest about coverage.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
ISSUE = ROOT / "02_MONTHLY_ISSUES" / "2026-09_Issue_02"
PREVIEW = ISSUE / "generated_art" / "integration_preview"
OUT = PREVIEW / "pages_preview"


def font(size, bold=False):
    for n in (["arialbd.ttf"] if bold else []) + ["arial.ttf"]:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{n}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def assemble_page(pg) -> tuple[Image.Image, int, int]:
    PW, PH, GUT, STRIP = 620, 349, 16, 44
    page_w = GUT * 3 + PW * 2
    page_h = 70 + (PH + STRIP + GUT) * 3
    canvas = Image.new("RGB", (page_w, page_h), (14, 14, 18))
    d = ImageDraw.Draw(canvas)
    d.text((GUT, 18), f"PAGE {pg['page_number']} — {pg['page_purpose']}", font=font(24, True), fill=(230, 230, 235))
    have = 0
    for i, pa in enumerate(pg["panels"]):
        col, row = i % 2, i // 2
        x = GUT + col * (PW + GUT)
        y = 70 + row * (PH + STRIP + GUT)
        img_p = PREVIEW / f"{pa['panel_id']}.png"
        if img_p.exists():
            canvas.paste(Image.open(img_p).convert("RGB").resize((PW, PH), Image.LANCZOS), (x, y))
            have += 1
        else:
            d.rectangle([x, y, x + PW, y + PH], outline=(90, 90, 100), width=2)
            d.text((x + PW // 2, y + PH // 2), "PENDING", font=font(22, True), fill=(120, 120, 130), anchor="mm")
        txt = pa["dialogue"] if pa["dialogue"] not in ("—", "") else (pa["caption"] if pa.get("caption", "—") not in ("—", "") else "")
        d.rectangle([x, y + PH, x + PW, y + PH + STRIP], fill=(26, 26, 32))
        d.text((x + 8, y + PH + STRIP // 2), txt[:90], font=font(15), fill=(215, 215, 225), anchor="lm")
    return canvas, have, len(pg["panels"])


def main():
    OUT.mkdir(exist_ok=True)
    plan = json.loads((ISSUE / "page_panel_plan.json").read_text(encoding="utf-8"))
    total_have = total = 0
    page_thumbs = []
    for pg in plan["pages"]:
        img, have, n = assemble_page(pg)
        img.save(OUT / f"page_{pg['page_number']:02d}_preview.png")
        total_have += have
        total += n
        page_thumbs.append((pg["page_number"], img))

    # full-issue contact sheet: covers + 16 page thumbnails, 4 columns
    TW = 300
    cols = 6
    def thumb(im):
        return im.resize((TW, round(im.height * TW / im.width)), Image.LANCZOS)
    tiles = []
    if (PREVIEW / "COVER_FRONT.png").exists():
        tiles.append(("FRONT", thumb(Image.open(PREVIEW / "COVER_FRONT.png").convert("RGB"))))
    for n, img in page_thumbs:
        tiles.append((f"p{n}", thumb(img)))
    if (PREVIEW / "COVER_BACK.png").exists():
        tiles.append(("BACK→ISSUE 03", thumb(Image.open(PREVIEW / "COVER_BACK.png").convert("RGB"))))
    th = max(t[1].height for t in tiles) + 24
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (TW + 12) + 12, rows * (th + 12) + 60), (10, 10, 14))
    d = ImageDraw.Draw(sheet)
    d.text((14, 16), f"MONKEYZOO — Signals In The Silence — full issue preview ({total_have}/{total} panels integrated)",
           font=font(24, True), fill=(255, 220, 60))
    for idx, (label, im) in enumerate(tiles):
        r, c = divmod(idx, cols)
        x = 12 + c * (TW + 12)
        y = 56 + r * (th + 12)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + im.height + 4), label, font=font(15, True), fill=(200, 200, 210))
    sheet.save(OUT / "ISSUE_02_full_preview.png")
    print(json.dumps({"pages": len(plan["pages"]), "panels_integrated": total_have,
                      "panels_total": total, "contact_sheet": str(OUT / "ISSUE_02_full_preview.png")}, indent=2))


if __name__ == "__main__":
    main()
