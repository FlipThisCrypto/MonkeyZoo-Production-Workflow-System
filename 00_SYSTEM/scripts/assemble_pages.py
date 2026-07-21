#!/usr/bin/env python3
"""Stage 8: assemble lettered comic pages from selected/upscaled panels.

Usage (run with ComfyUI's embedded python, which has Pillow):
    python assemble_pages.py 2026-08_Issue_06

Reads  : page_panel_plan.json, layout/layout_overrides.json (optional),
         generated_art/upscaled/<panel_id>_print*.png (fallback: selected)
Writes : layout/print_layout/page_NN.png   (2480x3508 @300dpi, lettered)
         layout/web_layout/page_NN.png     (1600px wide)
         layout/social_crops/*             (1:1, 16:9, 4:5 x2)
         exports/MonkeyZoo_Issue_##_Print.pdf / _Web.pdf

DRAFT-TIER LETTERING: functional bubbles/captions/SFX for web/CBZ review.
Print-final lettering still goes through Krita/CSP per stage_08 agent file.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

__all__ = ["draw_bubble", "draw_caption", "draw_sfx", "PAGE_W", "PAGE_H", "MARGIN", "GUTTER", "BORDER"]


FACTORY = Path(__file__).resolve().parents[2]

PAGE_W, PAGE_H = 2480, 3508
MARGIN, GUTTER, BORDER = 100, 40, 12
FONTS = Path(r"C:\Windows\Fonts")


def _font(name: str, size: int):
    """Load a Windows font, but degrade gracefully when it is absent
    (Linux CI / non-Windows dev) so the module stays importable and
    testable instead of crashing at import. On Windows the exact fonts
    load as before; elsewhere it falls back to a system-resolvable name
    and finally to Pillow's default so page assembly still runs."""
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        try:
            return ImageFont.truetype(name, size)  # on the system font path?
        except OSError:
            return ImageFont.load_default()


F_BUBBLE = _font("comicbd.ttf", 46)
F_SPEAKER = _font("comic.ttf", 30)
F_CAPTION = _font("ariali.ttf", 44)
F_SFX = _font("impact.ttf", 90)
F_SFX_SMALL = _font("ariali.ttf", 52)
F_SCREEN = _font("consola.ttf", 40)
F_WM = _font("comicbd.ttf", 54)
F_PAGENO = _font("arial.ttf", 40)
F_TITLE = _font("impact.ttf", 170)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textbbox((0, 0), t, font=font)[2] <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def draw_bubble(draw, cx, cy, text, speaker, max_w=560, tail=True):
    lines = wrap(draw, text, F_BUBBLE, max_w)
    lh = 56
    tw = max(draw.textbbox((0, 0), l, font=F_BUBBLE)[2] for l in lines)
    bw, bh = tw + 70, len(lines) * lh + 50
    x0, y0 = cx - bw / 2, cy - bh / 2
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=45,
                           fill="white", outline="black", width=7)
    if tail:
        draw.polygon([(cx - 22, y0 + bh - 4), (cx + 26, y0 + bh - 4),
                      (cx + 2, y0 + bh + 46)], fill="white", outline="black")
        draw.line([(cx - 22, y0 + bh - 4), (cx + 2, y0 + bh + 46)], fill="black", width=7)
        draw.line([(cx + 26, y0 + bh - 4), (cx + 2, y0 + bh + 46)], fill="black", width=7)
    ty = y0 + 24
    for l in lines:
        lw = draw.textbbox((0, 0), l, font=F_BUBBLE)[2]
        draw.text((cx - lw / 2, ty), l, font=F_BUBBLE, fill="black")
        ty += lh
    if speaker:
        draw.text((x0 + 16, y0 - 34), speaker.title(), font=F_SPEAKER, fill=(60, 60, 60))
    return bh


def draw_caption(draw, x, y, text, max_w=900):
    lines = wrap(draw, text, F_CAPTION, max_w)
    lh = 56
    tw = max(draw.textbbox((0, 0), l, font=F_CAPTION)[2] for l in lines)
    draw.rectangle([x, y, x + tw + 50, y + len(lines) * lh + 34],
                   fill=(232, 232, 228), outline=(40, 40, 40), width=4)
    ty = y + 16
    for l in lines:
        draw.text((x + 25, ty), l, font=F_CAPTION, fill=(25, 25, 25))
        ty += lh
    return len(lines) * lh + 34


def draw_screen(draw, cx, cy, text, max_w=760):
    lines = wrap(draw, text, F_SCREEN, max_w)
    lh = 50
    tw = max(draw.textbbox((0, 0), l, font=F_SCREEN)[2] for l in lines)
    x0, y0 = cx - (tw + 60) / 2, cy - (len(lines) * lh + 30) / 2
    draw.rectangle([x0, y0, x0 + tw + 60, y0 + len(lines) * lh + 30],
                   fill=(25, 20, 5), outline=(255, 190, 60), width=4)
    ty = y0 + 14
    for l in lines:
        draw.text((x0 + 30, ty), l, font=F_SCREEN, fill=(255, 200, 80))
        ty += lh


def draw_sfx(draw, x, y, text, small=False):
    f = F_SFX_SMALL if small else F_SFX
    fill = (250, 220, 120) if small else "white"
    for dx in (-4, 4):
        for dy in (-4, 4):
            draw.text((x + dx, y + dy), text, font=f, fill="black")
    draw.text((x, y), text, font=f, fill=fill)


# The scripts use "—" (and other dash marks) plus blanks as the "none"
# convention for empty dialogue/caption/SFX fields. Without this guard the
# lettering drew a literal "—" bubble/caption/SFX on every such panel.
_BLANK_RE = re.compile(r"^[\s\-‐-―−]*$")


def _is_blank(s) -> bool:
    return not s or bool(_BLANK_RE.match(str(s)))


def parse_dialogue(s):
    if _is_blank(s):
        return []
    out = []
    for part in [p for p in s.split(" / ") if p.strip() and not _is_blank(p)]:
        m = re.match(r'\s*([^:]+):\s*"(.*)"\s*$', part)
        if m:
            out.append((m.group(1).strip(), m.group(2)))
        elif part.strip():
            out.append(("", part.strip().strip('"')))
    return out


def fit_cover(img, w, h, crop=None):
    if crop:
        L, T, R, B = crop
        img = img.crop((int(L * img.width), int(T * img.height),
                        int(R * img.width), int(B * img.height)))
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def find_art(issue_dir, pid):
    ups = list((issue_dir / "generated_art" / "upscaled").glob(f"{pid}_print*.png"))
    if ups:
        return ups[0]
    sel = issue_dir / "generated_art" / "selected_panels" / f"{pid}.png"
    return sel if sel.exists() else None


def compute_slots(recipe, panel_count):
    """Panel bounding boxes for a page. A splash is one full-bleed slot; a page
    with zero panels yields no slots -- guarding a legacy/malformed page whose
    empty panels list otherwise hit `usable_h // 0` and crashed the whole run
    with a ZeroDivisionError before any page was written."""
    if recipe == "splash":
        return [(0, 0, PAGE_W, PAGE_H)]
    if panel_count <= 0:
        return []
    usable_h = PAGE_H - 2 * MARGIN - (panel_count - 1) * GUTTER
    sh = usable_h // panel_count
    return [(MARGIN, MARGIN + i * (sh + GUTTER), PAGE_W - 2 * MARGIN, sh)
            for i in range(panel_count)]


def main():
    issue = sys.argv[1]
    issue_dir = FACTORY / "02_MONTHLY_ISSUES" / issue
    num = issue.split("_Issue_")[1]
    plan = json.loads((issue_dir / "page_panel_plan.json").read_text(encoding="utf-8"))
    ov_file = issue_dir / "layout" / "layout_overrides.json"
    ov = json.loads(ov_file.read_text(encoding="utf-8")) if ov_file.exists() else {}

    print_dir = issue_dir / "layout" / "print_layout"
    web_dir = issue_dir / "layout" / "web_layout"
    pages_out = []

    for page in plan["pages"]:
        n = page["page_number"]
        panels = page["panels"]
        recipe = page.get("layout_recipe", "custom")
        canvas = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        d = ImageDraw.Draw(canvas)

        slots = compute_slots(recipe, len(panels))

        for panel, (sx, sy, sw, shh) in zip(panels, slots):
            pid = panel["panel_id"]
            po = ov.get(pid, {})
            art_path = find_art(issue_dir, pid)
            if art_path:
                art = fit_cover(Image.open(art_path).convert("RGB"), sw, shh,
                                po.get("crop"))
                canvas.paste(art, (sx, sy))
            else:
                d.rectangle([sx, sy, sx + sw, sy + shh], fill=(210, 210, 210))
                d.text((sx + 40, sy + 40), f"MISSING {pid}", font=F_CAPTION, fill="red")
            if recipe != "splash":
                d.rectangle([sx, sy, sx + sw, sy + shh], outline="black", width=BORDER)

            # lettering
            balloons = parse_dialogue(panel.get("dialogue", ""))
            if balloons:
                step = sw / (len(balloons) + 1)
                for i, (spk, txt) in enumerate(balloons, 1):
                    bx = sx + step * i
                    by = sy + po.get("bubble_y", 0.16) * shh
                    draw_bubble(d, bx, by, txt, spk)
            cap = panel.get("caption", "")
            if not _is_blank(cap):
                for part in [p for p in cap.split(" / ") if not _is_blank(p)]:
                    cy = sy + po.get("caption_y", 0.82) * shh
                    cx = sx + 0.03 * sw
                    h = draw_caption(d, cx, cy, part.strip())
                    po["caption_y"] = po.get("caption_y", 0.82) - (h + 12) / shh
            sfx = panel.get("sfx", "")
            if not _is_blank(sfx):
                draw_sfx(d, sx + po.get("sfx_x", 0.66) * sw,
                         sy + po.get("sfx_y", 0.08) * shh, sfx,
                         small="bmp" in sfx.lower())
            if po.get("screen_text"):
                draw_screen(d, sx + po.get("screen_x", 0.5) * sw,
                            sy + po.get("screen_y", 0.45) * shh, po["screen_text"])

        # watermark + page number
        d.text((PAGE_W - 340, PAGE_H - 78), "MonkeyZoo", font=F_WM, fill=(70, 70, 70))
        if recipe != "splash":
            d.text((PAGE_W / 2 - 20, PAGE_H - 76), str(n), font=F_PAGENO, fill=(90, 90, 90))

        canvas.save(print_dir / f"page_{n:02d}.png")
        web = canvas.resize((1600, round(PAGE_H * 1600 / PAGE_W)), Image.LANCZOS)
        web.save(web_dir / f"page_{n:02d}.png")
        pages_out.append(canvas)
        print(f"page {n:02d} assembled ({recipe}, {len(panels)} panels)")

    # PDFs — palette mode: flate-compressed (lossless) and avoids the JPEG
    # encoder, which this embedded Pillow lacks. Flat-color pages suit it.
    exp = issue_dir / "exports"
    def to_p(img):
        return img.convert("P", palette=Image.ADAPTIVE, colors=256)
    prints = [to_p(p) for p in pages_out]
    prints[0].save(exp / f"MonkeyZoo_Issue_{num}_Print.pdf", save_all=True,
                   append_images=prints[1:], resolution=300)
    webs = [to_p(Image.open(web_dir / f"page_{p['page_number']:02d}.png"))
            for p in plan["pages"]]
    webs[0].save(exp / f"MonkeyZoo_Issue_{num}_Web.pdf", save_all=True,
                 append_images=webs[1:])
    print("PDFs written")

    # social crops
    soc = issue_dir / "layout" / "social_crops"
    crops = ov.get("_social", {})
    for name, spec in crops.items():
        src = find_art(issue_dir, spec["panel"])
        if not src:
            continue
        img = Image.open(src).convert("RGB")
        w, h = spec["size"]
        fit_cover(img, w, h, spec.get("crop")).save(soc / f"{name}.png")
        print(f"social crop {name}")


if __name__ == "__main__":
    main()
