#!/usr/bin/env python3
"""Genesis crop-budget audit.

For every placed panel, compute how much of the 16:9 source composite survives
cover-cropping into its final slot, per-edge crop, scale-up factor, and an
anatomy-clip risk flag. Classifies each panel keep / minor-crop / recompose /
regenerate. This is the authoritative measurement that drives the panel-native
work -- it does not modify art.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

FACTORY = Path(__file__).resolve().parents[3]
GEN = Path(__file__).resolve().parent
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))
import genesis_build as gb  # noqa: E402

# thresholds
MINOR_LOSS = 0.10          # <=10% area lost = fine / minor
RECOMPOSE_LOSS = 0.35      # >35% lost = the slot is badly incompatible
MAX_SCALE = 1.9            # scaling a 1280-wide source beyond this softens badly


def cover_metrics(sw: int, sh: int, tw: int, th: int) -> dict:
    """Metrics for cover-fitting a source (sw x sh) into a slot (tw x th)."""
    s = max(tw / sw, th / sh)
    scaled_w, scaled_h = sw * s, sh * s
    crop_x = max(0.0, (scaled_w - tw) / scaled_w)   # fraction of width removed (both sides)
    crop_y = max(0.0, (scaled_h - th) / scaled_h)
    retained = (tw * th) / (scaled_w * scaled_h)
    return {
        "source_ratio": round(sw / sh, 3), "target_ratio": round(tw / th, 3),
        "aspect_mismatch": round(abs((sw / sh) - (tw / th)), 3),
        "crop_left_pct": round(crop_x / 2 * 100, 1), "crop_right_pct": round(crop_x / 2 * 100, 1),
        "crop_top_pct": round(crop_y / 2 * 100, 1), "crop_bottom_pct": round(crop_y / 2 * 100, 1),
        "retained_area_pct": round(retained * 100, 1),
        "scale_up": round(s * sw / 1280, 2),        # relative to a 1280px master
    }


def classify(m: dict, shot: str) -> str:
    """Classify by SIDE crop (the anatomy-clip risk), not total area: characters
    sit low-centre in these 16:9 composites, so trimming sky top/bottom is
    harmless -- only losing the left/right edges endangers the characters."""
    side = m["crop_left_pct"]          # per-side horizontal loss
    total_loss = 1 - m["retained_area_pct"] / 100
    if m["scale_up"] > MAX_SCALE:
        return "recompose_or_regenerate"
    if side <= 6:                       # full-width band: characters intact
        return "keep" if total_loss <= MINOR_LOSS else "minor_crop"
    if side <= 16:                      # a modest side trim (e.g. 2-up cell)
        return "minor_crop"
    return "recompose_or_regenerate"    # heavy side crop -> new composition needed


def audit(genesis_dir: Path) -> dict:
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    panel_dir = FACTORY / plan["source_panel_dir"]
    rows = []
    for pg in plan["pages"]:
        rects = gb.template_rects(pg["layout_template"], pg["panel_count"])
        for panel, (x, y, w, h) in zip(pg["panels"], rects):
            with Image.open(panel_dir / f"{pid}.png") as im:
                m = cover_metrics(im.width, im.height, w, h)

            cls = classify(m, panel["shot"])
            rows.append({
                "page": pg["page_number"], "panel_id": pid, "shot": panel["shot"],
                "slot_px": [w, h], **m, "classification": cls,
                "anatomy_clip_risk": bool(m["target_ratio"] < 0.8 and m["crop_left_pct"] > 18
                                          and panel["shot"] in ("wide", "medium")),
            })
    cls_counts = Counter(r["classification"] for r in rows)
    return {
        "total_panels": len(rows),
        "avg_retained_area_pct": round(sum(r["retained_area_pct"] for r in rows) / len(rows), 1),
        "panels_over_35pct_loss": sum(1 for r in rows if r["retained_area_pct"] < 65),
        "anatomy_clip_risk_panels": sum(1 for r in rows if r["anatomy_clip_risk"]),
        "panels_scaled_over_limit": sum(1 for r in rows if r["scale_up"] > MAX_SCALE),
        "classification": dict(cls_counts),
        "panels": rows,
    }


def write(genesis_dir: Path, data: dict) -> None:
    qdir = genesis_dir / "qa"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "PANEL_CROP_AUDIT.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    md = ["# MonkeyZoo: Genesis — Panel Crop Audit", "",
          f"- Panels: **{data['total_panels']}**  ·  avg source area retained after crop: "
          f"**{data['avg_retained_area_pct']}%**",
          f"- Panels losing >35% of the source: **{data['panels_over_35pct_loss']}**",
          f"- Anatomy-clip-risk panels (wide/medium art in a tall slot): "
          f"**{data['anatomy_clip_risk_panels']}**",
          f"- Panels scaled past the softening limit ({MAX_SCALE}x): **{data['panels_scaled_over_limit']}**",
          f"- Classification: {data['classification']}", "",
          "## Worst offenders (lowest retained area)", "",
          "| Page | Panel | Shot | Slot ratio | Retained | L/R crop | Class |", "|---|---|---|---|---|---|---|"]
    worst = sorted(data["panels"], key=lambda r: r["retained_area_pct"])[:20]
    for r in worst:
        md.append(f"| {r['page']} | {r['panel_id'].split('_',1)[1]} | {r['shot']} | {r['target_ratio']} | "
                  f"{r['retained_area_pct']}% | {r['crop_left_pct']}% | {r['classification']} |")
    (qdir / "PANEL_CROP_AUDIT.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    data = audit(genesis_dir)
    write(genesis_dir, data)
    print(f"Crop audit: avg retained {data['avg_retained_area_pct']}% | "
          f">35%-loss {data['panels_over_35pct_loss']} | anatomy-risk {data['anatomy_clip_risk_panels']} | "
          f"over-scale {data['panels_scaled_over_limit']}")
    print(f"  classification: {data['classification']}")


if __name__ == "__main__":
    main()
