"""Stage an integrated panel into its issue workspace for owner review.

Copies the compositor's final render into
    <issue>/generated_art/integration_preview/<panel_id>.png
and builds a labeled before/after sheet against the CURRENTLY SHIPPED
selected panel at
    <issue>/generated_art/integration_preview/<panel_id>_compare.png

Gate discipline: this script never writes into selected_panels/ --
promotion of integrated art over the shipped draft composites is a
human Gate A decision, and the comparison sheet exists precisely to give
the owner the evidence for that call.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]


def build_compare_sheet(before: Image.Image, after: Image.Image,
                        title: str) -> Image.Image:
    target_h = 620
    def fit(img):
        w = round(img.width * target_h / img.height)
        return img.convert("RGB").resize((w, target_h), Image.LANCZOS)
    b, a = fit(before), fit(after)
    pad, header = 14, 46
    sheet = Image.new("RGB", (b.width + a.width + pad * 3, target_h + header + pad * 2), (16, 16, 20))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 12), f"{title} -- integration preview (left: shipped draft, right: integrated)",
           fill=(230, 230, 235))
    sheet.paste(b, (pad, header))
    sheet.paste(a, (b.width + pad * 2, header))
    d.text((pad + 4, header + 6), "BEFORE (selected_panels)", fill=(255, 200, 90))
    d.text((b.width + pad * 2 + 4, header + 6), "AFTER (integration pipeline)", fill=(120, 255, 150))
    return sheet


def stage(spec_dir: Path, issue_dir: Path) -> dict:
    # single-char panels write 04_final_integrated.png; multi-char final_integrated.png
    for name in ("04_final_integrated.png", "final_integrated.png"):
        final = spec_dir / name
        if final.exists():
            break
    else:
        raise FileNotFoundError(f"no final render in {spec_dir}")

    # panel id from whichever spec file the dir carries
    for spec_name in ("pose_spec.json", "characters_spec.json", "scene_blocking.json"):
        f = spec_dir / spec_name
        if f.exists():
            panel_id = json.loads(f.read_text(encoding="utf-8")).get("panel_id")
            if panel_id:
                break
    else:
        raise ValueError(f"no panel_id found in {spec_dir}")

    preview_dir = issue_dir / "generated_art" / "integration_preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    staged = preview_dir / f"{panel_id}.png"
    shutil.copyfile(final, staged)

    shipped = issue_dir / "generated_art" / "selected_panels" / f"{panel_id}.png"
    compare_path = None
    if shipped.exists():
        sheet = build_compare_sheet(Image.open(shipped), Image.open(final), panel_id)
        compare_path = preview_dir / f"{panel_id}_compare.png"
        sheet.save(compare_path)

    return {
        "panel_id": panel_id,
        "staged": str(staged),
        "compare_sheet": str(compare_path) if compare_path else None,
        "selected_panels_untouched": True,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_dir", type=Path)
    ap.add_argument("issue_dir", type=Path)
    args = ap.parse_args()
    print(json.dumps(stage(args.spec_dir, args.issue_dir), indent=2))
