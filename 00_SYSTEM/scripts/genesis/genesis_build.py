#!/usr/bin/env python3
"""Genesis page + cover assembler.

Renders the 22-page Genesis issue from GENESIS_LAYOUT_PLAN.json and the 96
integrated source panels, with full lettering (dialogue / caption / SFX). Panel
geometry comes from per-page layout templates so pages vary in density and shape
instead of a fixed six-panel grid. Front and back covers are rendered as
independent full-page images.

Reuses the proven, Linux-safe, blank-marker-aware lettering from
00_SYSTEM/scripts/assemble_pages.py (draw_bubble / draw_caption / draw_sfx).

Usage: python genesis_build.py [GENESIS_DIR]   (default: <factory>/GENESIS)
Source panels are 1280x720 (web tier); print pages are upscaled and documented
as source-limited, not native print resolution.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FACTORY = Path(__file__).resolve().parents[3]
SCRIPTS = FACTORY / "00_SYSTEM" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import assemble_pages as ap  # noqa: E402  (fonts, lettering helpers, page constants)

PAGE_W, PAGE_H = ap.PAGE_W, ap.PAGE_H        # 2480 x 3508
MARGIN, GUTTER, BORDER = ap.MARGIN, ap.GUTTER, ap.BORDER
WEB_W = 1600                                 # web downscale width
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN - 90          # leave a strip for footer / page number

# Normalized slot rectangles (x, y, w, h) in [0,1] within the content box, per
# template. Slot 0 is the emphasis/feature slot where the template has one.
TEMPLATES: dict[str, list[tuple[float, float, float, float]]] = {
    "splash": [(0, 0, 1, 1)],
    "stack2": [(0, 0, 1, 0.5), (0, 0.5, 1, 0.5)],
    "feature_top1": [(0, 0, 1, 0.62), (0, 0.62, 1, 0.38)],
    "feature_top2": [(0, 0, 1, 0.55), (0, 0.55, 0.5, 0.45), (0.5, 0.55, 0.5, 0.45)],
    "row3": [(0, 0, 1, 1 / 3), (0, 1 / 3, 1, 1 / 3), (0, 2 / 3, 1, 1 / 3)],
    "feature_left2": [(0, 0, 0.58, 1), (0.58, 0, 0.42, 0.5), (0.58, 0.5, 0.42, 0.5)],
    "grid4": [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)],
    "feature_top3": [(0, 0, 1, 0.5), (0, 0.5, 1 / 3, 0.5), (1 / 3, 0.5, 1 / 3, 0.5), (2 / 3, 0.5, 1 / 3, 0.5)],
    "feature_left3": [(0, 0, 0.55, 1), (0.55, 0, 0.45, 1 / 3), (0.55, 1 / 3, 0.45, 1 / 3), (0.55, 2 / 3, 0.45, 1 / 3)],
    "feature_top4": [(0, 0, 1, 0.4), (0, 0.4, 0.5, 0.3), (0.5, 0.4, 0.5, 0.3), (0, 0.7, 0.5, 0.3), (0.5, 0.7, 0.5, 0.3)],
    "grid5": [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 1 / 3, 0.5), (1 / 3, 0.5, 1 / 3, 0.5), (2 / 3, 0.5, 1 / 3, 0.5)],
    "left_feature4": [(0, 0, 0.5, 1), (0.5, 0, 0.5, 0.25), (0.5, 0.25, 0.5, 0.25), (0.5, 0.5, 0.5, 0.25), (0.5, 0.75, 0.5, 0.25)],
    "grid6": [(0, 0, 0.5, 1 / 3), (0.5, 0, 0.5, 1 / 3), (0, 1 / 3, 0.5, 1 / 3), (0.5, 1 / 3, 0.5, 1 / 3), (0, 2 / 3, 0.5, 1 / 3), (0.5, 2 / 3, 0.5, 1 / 3)],
    "feature_top5": [(0, 0, 1, 0.38), (0, 0.38, 0.5, 0.31), (0.5, 0.38, 0.5, 0.31), (0, 0.69, 1 / 3, 0.31), (1 / 3, 0.69, 1 / 3, 0.31), (2 / 3, 0.69, 1 / 3, 0.31)],
}


def template_rects(template: str, count: int) -> list[tuple[int, int, int, int]]:
    """Pixel (x, y, w, h) slots for a template, with gutters inset. Falls back to
    an even vertical stack if the template is unknown or the count mismatches."""
    norm = TEMPLATES.get(template)
    if not norm or len(norm) != count:
        norm = [(0, i / count, 1, 1 / count) for i in range(count)]
    g = GUTTER
    rects = []
    for (nx, ny, nw, nh) in norm:
        x = MARGIN + nx * CONTENT_W
        y = MARGIN + ny * CONTENT_H
        w = nw * CONTENT_W
        h = nh * CONTENT_H
        # inset by half a gutter on interior edges
        ix = x + (g / 2 if nx > 0.001 else 0)
        iy = y + (g / 2 if ny > 0.001 else 0)
        iw = w - (g / 2 if nx > 0.001 else 0) - (g / 2 if nx + nw < 0.999 else 0)
        ih = h - (g / 2 if ny > 0.001 else 0) - (g / 2 if ny + nh < 0.999 else 0)
        rects.append((int(ix), int(iy), int(iw), int(ih)))
    return rects


import re

_SPEAKER = re.compile(r"^\s*([A-Z][A-Za-z0-9 .'&-]{0,22})(\([^)]*\))?\s*:\s*(.+)$")


def split_dialogue(s: str) -> list[tuple[str, str]]:
    """Split 'NEONBLUE: text' / 'STATIC (small): text' into (speaker, text) so the
    speaker becomes a tag above the balloon instead of sitting inside it. Handles
    multiple balloons separated by ' / ' and drops blank markers."""
    if ap._is_blank(s):
        return []
    out = []
    for part in [p for p in str(s).split(" / ") if p.strip() and not ap._is_blank(p)]:
        m = _SPEAKER.match(part)
        if m:
            spk = re.sub(r"\s*\([^)]*\)", "", m.group(1)).strip()
            txt = m.group(3).strip().strip('"')
            out.append((spk, txt))
        else:
            out.append(("", part.strip().strip('"')))
    return out


def _letter_panel(d: ImageDraw.ImageDraw, rect, panel: dict, splash: bool) -> list[str]:
    """Draw dialogue/caption/SFX for one panel; return lettering warnings."""
    sx, sy, sw, sh = rect
    warns = []
    balloons = split_dialogue(panel.get("dialogue", ""))
    if balloons:
        max_w = min(560, int(sw * 0.8))
        step = sw / (len(balloons) + 1)
        for i, (spk, txt) in enumerate(balloons, 1):
            bx = sx + step * i
            by = sy + 0.17 * sh
            ap.draw_bubble(d, bx, by, txt, spk, max_w=max_w)
            if len(txt.split()) > 35:
                warns.append(f"balloon >35 words: {panel['source_panel_id']}")
    cap = panel.get("caption", "")
    if not ap._is_blank(cap):
        for part in [p for p in cap.split(" / ") if not ap._is_blank(p)]:
            cy = sy + 0.80 * sh
            cx = sx + 0.03 * sw
            ap.draw_caption(d, cx, cy, part.strip(), max_w=int(sw * 0.9))
    sfx = panel.get("sfx", "")
    if not ap._is_blank(sfx):
        sfx_y = 0.66 if balloons else 0.12   # keep SFX clear of top-anchored balloons
        ap.draw_sfx(d, sx + 0.60 * sw, sy + sfx_y * sh, sfx, small=("bmp" in sfx.lower()))
    return warns


def render_page(page: dict, panel_dir: Path) -> tuple[Image.Image, list[str]]:
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(canvas)
    template = page["layout_template"]
    count = page["panel_count"]
    rects = template_rects(template, count)
    warns = []
    splash = template == "splash"
    for panel, rect in zip(page["panels"], rects):
        sx, sy, sw, sh = rect
        pid = panel["source_panel_id"]
        art_path = panel_dir / f"{pid}.png"
        if art_path.exists():
            art = ap.fit_cover(Image.open(art_path).convert("RGB"), sw, sh)
            canvas.paste(art, (sx, sy))
        else:
            d.rectangle([sx, sy, sx + sw, sy + sh], fill=(210, 210, 210))
            d.text((sx + 40, sy + 40), f"MISSING {pid}", font=ap.F_CAPTION, fill="red")
            warns.append(f"missing art: {pid}")
        d.rectangle([sx, sy, sx + sw, sy + sh], outline="black", width=BORDER)
        warns += _letter_panel(d, rect, panel, splash)
    # footer: series/issue + page number
    d.text((PAGE_W - 360, PAGE_H - 74), "MonkeyZoo · GENESIS", font=ap.F_PAGENO, fill=(90, 90, 90))
    d.text((MARGIN, PAGE_H - 74), f"{page['page_number']}", font=ap.F_PAGENO, fill=(90, 90, 90))
    return canvas, warns


def _fit_fullbleed(img: Image.Image, w: int, h: int) -> Image.Image:
    s = max(w / img.width, h / img.height)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def _band(d, y0, y1, alpha=150):
    overlay = Image.new("RGBA", (PAGE_W, y1 - y0), (10, 10, 15, alpha))
    return overlay


def render_front_cover(src: Path, plan: dict) -> Image.Image:
    # The source cover art already carries the MONKEYZOO wordmark and the
    # "Signals in the Silence" board, so the overlay adds ONLY the issue title
    # treatment (GENESIS + ISSUE 01) in a bottom band -- no duplicate logo/subtitle.
    base = _fit_fullbleed(Image.open(src).convert("RGB"), PAGE_W, PAGE_H).convert("RGBA")
    ov = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, PAGE_H - 620, PAGE_W, PAGE_H], fill=(8, 8, 14, 175))
    base = Image.alpha_composite(base, ov)
    d = ImageDraw.Draw(base)
    title = ap._font("impact.ttf", 300)
    issue = ap._font("comicbd.ttf", 100)
    _centered(d, "GENESIS", PAGE_H - 560, title, "white")
    _centered(d, "ISSUE 01", PAGE_H - 210, issue, (250, 210, 70))
    return base.convert("RGB")


def render_back_cover(src: Path, plan: dict) -> Image.Image:
    base = _fit_fullbleed(Image.open(src).convert("RGB"), PAGE_W, PAGE_H).convert("RGBA")
    ov = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, 0, PAGE_W, 560], fill=(8, 8, 14, 160))
    od.rectangle([0, PAGE_H - 520, PAGE_W, PAGE_H], fill=(8, 8, 14, 175))
    base = Image.alpha_composite(base, ov)
    d = ImageDraw.Draw(base)
    nxt = ap._font("impact.ttf", 140)
    teaser = ap._font("comicbd.ttf", 92)
    credit = ap._font("arial.ttf", 60)
    _centered(d, "NEXT ISSUE", 150, nxt, (250, 210, 70))
    _centered(d, "The Signal Answers Back", 330, teaser, "white")
    _centered(d, "MonkeyZoo · The Banana Lab Studio", PAGE_H - 430, credit, (215, 215, 220))
    _centered(d, "MonkeyZoo: Genesis — Production Issue 08 / Published Issue 01", PAGE_H - 330, credit, (180, 180, 185))
    _centered(d, "© MonkeyZoo / Fusion Squad. All rights reserved.", PAGE_H - 230, credit, (150, 150, 155))
    return base.convert("RGB")


def _centered(d: ImageDraw.ImageDraw, text: str, y: int, font, fill) -> None:
    w = d.textbbox((0, 0), text, font=font)[2]
    d.text(((PAGE_W - w) / 2, y), text, font=font, fill=fill)


def _save_web(img: Image.Image, path: Path) -> Path:
    """Web edition: optimized JPG at WEB_W wide (git-friendly, web-appropriate)."""
    h = round(PAGE_H * WEB_W / PAGE_W)
    web = img.resize((WEB_W, h), Image.LANCZOS).convert("RGB")
    path = path.with_suffix(".jpg")
    web.save(path, "JPEG", quality=88, optimize=True)
    return path


def build(genesis_dir: Path) -> dict:
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    panel_dir = FACTORY / plan["source_panel_dir"]
    covers = genesis_dir / "covers"
    story = genesis_dir / "story_pages"
    web_c = genesis_dir / "web" / "covers"
    web_s = genesis_dir / "web" / "story_pages"
    for p in (covers, story, web_c, web_s, genesis_dir / "previews"):
        p.mkdir(parents=True, exist_ok=True)
        # scoped cleanup: remove only rendered image files in GENESIS's own output
        # subdirs so stale renders (e.g. old .png web pages) don't accumulate.
        for ext in ("*.png", "*.jpg"):
            for stale in p.glob(ext):
                stale.unlink()

    all_warns = []
    # covers (independent full-page images)
    front = render_front_cover(FACTORY / plan["front_cover"], plan)
    back = render_back_cover(FACTORY / plan["back_cover"], plan)
    front.save(covers / "01_FRONT_COVER.png"); _save_web(front, web_c / "01_FRONT_COVER.png")
    back.save(covers / "24_BACK_COVER.png"); _save_web(back, web_c / "24_BACK_COVER.png")

    # story pages -> numbered 02..23 (01=front, 24=back)
    page_imgs = []
    for pg in plan["pages"]:
        img, warns = render_page(pg, panel_dir)
        all_warns += warns
        seq = pg["page_number"] + 1                 # page 1 -> file index 02
        name = f"{seq:02d}_PAGE_{pg['page_number']:02d}.png"
        img.save(story / name)
        _save_web(img, web_s / name)
        page_imgs.append(img)
        print(f"page {pg['page_number']:02d} -> {name} ({pg['panel_count']} panels, {pg['layout_template']})")

    # full-issue contact sheet (front + pages + back thumbnails)
    _contact_sheet([front] + page_imgs + [back], genesis_dir / "previews" / "full_issue_contact_sheet.png")

    return {"pages": len(page_imgs), "warnings": all_warns,
            "front_cover": str(covers / "01_FRONT_COVER.png"),
            "back_cover": str(covers / "24_BACK_COVER.png")}


def _contact_sheet(images: list[Image.Image], path: Path, cols: int = 6, thumb_w: int = 300) -> None:
    th = round(PAGE_H * thumb_w / PAGE_W)
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (thumb_w + 12) + 12, rows * (th + 12) + 12), (30, 30, 34))
    for i, im in enumerate(images):
        t = im.resize((thumb_w, th), Image.LANCZOS)
        r, c = divmod(i, cols)
        sheet.paste(t, (12 + c * (thumb_w + 12), 12 + r * (th + 12)))
    sheet.convert("RGB").save(path.with_suffix(".jpg"), "JPEG", quality=85, optimize=True)


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    result = build(genesis_dir)
    print(f"\nGenesis assembled: {result['pages']} story pages + 2 covers")
    if result["warnings"]:
        print(f"lettering/render warnings: {len(result['warnings'])}")
        for w in result["warnings"][:20]:
            print("  -", w)


if __name__ == "__main__":
    main()
