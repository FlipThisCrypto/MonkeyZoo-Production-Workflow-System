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
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import assemble_pages as ap  # noqa: E402  (fonts, lettering helpers, page constants)
from genesis_layout import synth_page_rects  # noqa: E402  scene/page-custom slot geometry

PAGE_W, PAGE_H = ap.PAGE_W, ap.PAGE_H        # 2480 x 3508
MARGIN, GUTTER, BORDER = ap.MARGIN, ap.GUTTER, ap.BORDER
WEB_W = 1600                                 # web downscale width
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN - 90          # leave a strip for footer / page number

# Normalized slot rectangles (x, y, w, h) in [0,1] within the content box, per
# template. Slot 0 is the emphasis/feature slot where the template has one.
# LANDSCAPE-BAND templates. The source panels are 16:9, so every slot is a
# full-width horizontal band (or, sparingly, a 2-up row) -- cover-cropping only
# trims sky top/bottom and never clips the characters at the sides. Tall columns
# and 3-across rows are deliberately absent; they were the accidental-crop cause.
# "hero_*" templates put a taller feature band first (slot 0).
_B = lambda ys: [(0, ys[i], 1, ys[i + 1] - ys[i]) for i in range(len(ys) - 1)]   # noqa: E731
TEMPLATES: dict[str, list[tuple[float, float, float, float]]] = {
    "splash": [(0, 0, 1, 1)],
    "band2": _B([0, 0.5, 1.0]),
    "hero2": _B([0, 0.6, 1.0]),
    "band3": _B([0, 1 / 3, 2 / 3, 1.0]),
    "hero3": _B([0, 0.46, 0.73, 1.0]),
    "band4": _B([0, 0.25, 0.5, 0.75, 1.0]),
    "hero4": _B([0, 0.4, 0.6, 0.8, 1.0]),
    "band5": _B([0, 0.2, 0.4, 0.6, 0.8, 1.0]),
    "hero5": _B([0, 0.32, 0.49, 0.66, 0.83, 1.0]),
    "band6": _B([0, 1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6, 1.0]),
    "hero6": _B([0, 0.30, 0.44, 0.58, 0.72, 0.86, 1.0]),
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


# Speakers that need an explicit label because a tail can't identify them
# (electronic / public-address / off-panel / on-screen). Ordinary cast speech
# drops the label and relies on the balloon tail, as in real comics.
# Only device/broadcast voices get a label (a tail can't point to a speaker);
# off-panel CAST speech reads fine as a plain balloon with the tail off-frame.
LABELLED_SPEAKERS = {"PA", "SCREEN", "RADIO", "RELAY", "SIGNAL",
                     "ANNOUNCE", "ANNOUNCEMENT", "MONITOR", "SPEAKER", "COMM"}


def speaker_tag(spk: str) -> str:
    """The label to show above a balloon: empty for ordinary cast speech (the
    tail identifies the speaker), the name for device/broadcast voices."""
    return spk if str(spk).upper() in LABELLED_SPEAKERS else ""


def _sfx_style(text: str) -> tuple[int, tuple[int, int, int]]:
    """Size + colour by loudness: quiet lowercase ticks stay small and cool;
    all-caps effects are big and warm."""
    t = text.strip()
    letters = re.sub(r"[^A-Za-z]", "", t)
    if t.isupper() and len(letters) >= 3:
        return 168, (255, 238, 170)          # loud: BZZT, WRRRN
    if t.islower() and len(letters) <= 3:
        return 78, (225, 228, 240)           # quiet: tik, bzz
    return 116, (250, 220, 120)              # medium


def genesis_draw_sfx(canvas: Image.Image, cx: float, cy: float, text: str, seed: int) -> None:
    """Draw a sound effect with an outline, loudness-based size, and a small
    deterministic rotation so it reads as integrated sound, not a floating label."""
    size, color = _sfx_style(text)
    f = ap._font("impact.ttf", size)
    probe = ImageDraw.Draw(canvas)
    bb = probe.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 10
    layer = Image.new("RGBA", (tw + 2 * pad + 8, th + 2 * pad + 8), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ox, oy = pad - bb[0], pad - bb[1]
    for dx in (-4, 0, 4):
        for dy in (-4, 0, 4):
            ld.text((ox + dx, oy + dy), text, font=f, fill=(0, 0, 0, 255))
    ld.text((ox, oy), text, font=f, fill=color + (255,))
    angle = ((seed * 37) % 25) - 12          # deterministic -12..+12 degrees
    rot = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    canvas.paste(rot, (int(cx - rot.width / 2), int(cy - rot.height / 2)), rot)


def _letter_panel(canvas: Image.Image, d: ImageDraw.ImageDraw, rect, panel: dict,
                  splash: bool, seed: int) -> list[str]:
    """Draw dialogue/caption/SFX for one panel; return lettering warnings."""
    sx, sy, sw, sh = rect
    warns = []
    parsed = split_dialogue(panel.get("dialogue", ""))
    speech = [(s, t) for s, t in parsed if s != "CAPTION"]
    dialogue_caps = [t for s, t in parsed if s == "CAPTION"]   # CAPTION: -> narration box
    if speech:
        max_w = min(560, int(sw * 0.8))
        step = sw / (len(speech) + 1)
        for i, (spk, txt) in enumerate(speech, 1):
            bx = sx + step * i
            by = sy + 0.17 * sh
            # keep the label only for electronic/off-panel voices; ordinary cast
            # speech uses the tail (no "STATIC:" style prefix)
            ap.draw_bubble(d, bx, by, txt, speaker_tag(spk), max_w=max_w)
            if len(txt.split()) > 35:
                warns.append(f"balloon >35 words: {panel['source_panel_id']}")
    # captions: scene stamp (panel["caption"]) + any CAPTION: narration
    cap_parts = [p for p in str(panel.get("caption", "")).split(" / ") if not ap._is_blank(p)]
    cap_parts += dialogue_caps
    cy = sy + 0.80 * sh
    for part in cap_parts:
        cx = sx + 0.03 * sw
        h = ap.draw_caption(d, cx, cy, part.strip(), max_w=int(sw * 0.9))
        cy -= (h + 14)                       # stack upward if more than one
    sfx = panel.get("sfx", "")
    if not ap._is_blank(sfx):
        sfx_y = 0.66 if speech else 0.14     # keep SFX clear of top-anchored balloons
        genesis_draw_sfx(canvas, sx + 0.60 * sw, sy + sfx_y * sh, sfx.strip(), seed)
    return warns


def render_page(page: dict, panel_dir: Path, crops: dict | None = None,
                native_dir: Path | None = None) -> tuple[Image.Image, list[str]]:
    canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(canvas)
    template = page["layout_template"]
    # scene/page-custom geometry: bespoke character beats get varied slot shapes
    # (2-up cells, asymmetric widths, feature bands); 16:9 KEEP panels stay full
    # bands. Falls back to the band templates if the synth yields the wrong count.
    rects = synth_page_rects(page["panels"], page["page_number"])
    if len(rects) != len(page["panels"]):
        rects = template_rects(template, page["panel_count"])
    warns = []
    splash = template == "splash"
    crops = crops or {}
    for idx, (panel, rect) in enumerate(zip(page["panels"], rects)):
        sx, sy, sw, sh = rect
        pid = panel["source_panel_id"]
        native = (native_dir / f"{pid}.png") if native_dir else None
        art_path = panel_dir / f"{pid}.png"
        if native and native.exists():
            # bespoke panel-native art (already composed landscape) -- no crop variation
            art = ap.fit_cover(Image.open(native).convert("RGB"), sw, sh, None)
            canvas.paste(art, (sx, sy))
        elif art_path.exists():
            crop = crops.get(pid)                        # crop-variation window (L,T,R,B) or None
            art = ap.fit_cover(Image.open(art_path).convert("RGB"), sw, sh, crop)
            canvas.paste(art, (sx, sy))
        else:
            d.rectangle([sx, sy, sx + sw, sy + sh], fill=(210, 210, 210))
            d.text((sx + 40, sy + 40), f"MISSING {pid}", font=ap.F_CAPTION, fill="red")
            warns.append(f"missing art: {pid}")
        d.rectangle([sx, sy, sx + sw, sy + sh], outline="black", width=BORDER)
        warns += _letter_panel(canvas, d, rect, panel, splash, page["page_number"] * 10 + idx)
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
    nxt = ap._font("impact.ttf", 130)
    teaser = ap._font("impact.ttf", 150)
    sub = ap._font("comicbd.ttf", 74)
    credit = ap._font("arial.ttf", 58)
    # teaser matches the back-cover art (a Fright-House / Halloween next issue)
    _centered(d, "NEXT ISSUE", 140, nxt, (250, 210, 70))
    _centered(d, "THE HOUSE THAT REMEMBERS", 300, teaser, "white")
    _centered(d, "MonkeyZoo · Issue 02", 470, sub, (220, 220, 225))
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

    # crop-variation windows (from genesis_dupes) reframe reused backgrounds
    crops_file = genesis_dir / "metadata" / "panel_crops.json"
    crops = json.loads(crops_file.read_text(encoding="utf-8"))["crops"] if crops_file.exists() else {}
    # bespoke panel-native art (from genesis_charart) overrides the source composite
    native_dir = genesis_dir / "generated_art" / "panel_native"

    # story pages -> numbered 02..23 (01=front, 24=back)
    page_imgs = []
    for pg in plan["pages"]:
        img, warns = render_page(pg, panel_dir, crops, native_dir)
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
