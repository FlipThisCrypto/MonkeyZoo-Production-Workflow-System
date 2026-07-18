#!/usr/bin/env python3
"""Genesis panel-native specifications, provenance, and regen prompts.

For every final panel, emit a panel-native art spec (exact dimensions, story
beat, shot, characters, lettering-safe region) and a source-provenance record.
For panels the crop audit flags as heavy side-crop, emit a panel-specific art
prompt -- the ready-to-run hand-off for the owner-gated ComfyUI regeneration.

This does NOT generate art; it produces the authoritative specs that a future
panel-native art pass (mine, once authorized, or the owner's) consumes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]
GEN = Path(__file__).resolve().parent
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))
import genesis_build as gb  # noqa: E402

STYLE_REF = ("MonkeyZoo house style: flat-cel chibi monkey characters, bold black "
             "outlines, neon-noir rainy Zoo City, teal/magenta/green neon, wet "
             "reflective ground. Preserve exact approved character design (hair + "
             "card-colour identity). Do not restyle, do not go photoreal.")


def _load(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def _lettering_region(panel: dict) -> str:
    if gb.split_dialogue(panel.get("dialogue", "")):
        return "upper third kept visually quiet for one or two speech balloons"
    if not gb.ap._is_blank(panel.get("caption", "")):
        return "lower-left corner kept quiet for a small location caption"
    return "no balloon required; keep the SFX region (upper-right) uncluttered"


def build(genesis_dir: Path) -> dict:
    plan = _load(genesis_dir / "GENESIS_LAYOUT_PLAN.json")
    crop = {r["panel_id"] + f"@{r['page']}": r for r in _load(genesis_dir / "qa" / "PANEL_CROP_AUDIT.json", {"panels": []})["panels"]}
    specs, provenance, regen = [], [], []
    for pg in plan["pages"]:
        rects = gb.template_rects(pg["layout_template"], pg["panel_count"])
        for i, (panel, (x, y, w, h)) in enumerate(zip(pg["panels"], rects), 1):
            pid = panel["source_panel_id"]
            cm = crop.get(f"{pid}@{pg['page_number']}", {})
            spec = {
                "page": pg["page_number"], "panel": i, "source_panel_id": pid,
                "target_px": [w, h], "aspect_ratio": round(w / h, 3),
                "orientation": "landscape" if w >= h else "portrait",
                "story_beat": panel["beat"], "location": pg["location"],
                "characters": panel.get("characters") or [],
                "shot": panel["shot"], "emphasis": panel.get("emphasis", False),
                "dialogue": panel["dialogue"], "sfx": panel["sfx"],
                "lettering_safe_region": _lettering_region(panel),
                "crop_classification": cm.get("classification", "unknown"),
                "retained_area_pct": cm.get("retained_area_pct"),
                "side_crop_pct": cm.get("crop_left_pct"),
            }
            specs.append(spec)
            provenance.append({
                "final_panel": f"page_{pg['page_number']:02d}_panel_{i:02d}",
                "source_panel_id": pid,
                "source_type": "original_integrated_composite_16x9",
                "source_path": f"{plan['source_panel_dir']}/{pid}.png",
                "crop_window": _load(genesis_dir / "metadata" / "panel_crops.json", {}).get("crops", {}).get(pid),
                "retained_area_pct": cm.get("retained_area_pct"),
                "side_crop_pct": cm.get("crop_left_pct"),
                "classification": cm.get("classification", "unknown"),
                "regenerated": False,
            })
            if cm.get("classification") == "recompose_or_regenerate":
                regen.append(spec)
    return {"specs": specs, "provenance": provenance, "regen": regen,
            "issue": "MonkeyZoo: Genesis", "total": len(specs),
            "regen_count": len(regen)}


def _prompt(spec: dict) -> str:
    return "\n".join([
        f"PANEL: page {spec['page']:02d}, panel {spec['panel']:02d}  (replaces {spec['source_panel_id']})",
        f"TARGET: {spec['orientation']} panel, {spec['target_px'][0]}x{spec['target_px'][1]} px, "
        f"aspect ratio {spec['aspect_ratio']}",
        f"SHOT: {spec['shot']} — {spec['story_beat']} beat, {spec['location']}",
        f"CAST: {', '.join(spec['characters']) or 'environment only'} "
        f"(stage at intentional scale, feet grounded, full silhouette unless an intentional close-up)",
        f"DIALOGUE (for lettering room, do not draw text): {spec['dialogue'] or '(none)'}",
        f"LETTERING-SAFE: {spec['lettering_safe_region']}",
        "COMPOSE FOR THIS EXACT RATIO. Do not center-crop a wider image into this frame.",
        "DO NOT: clip ears/chin/hands/feet; reuse a prior camera; place text in the art; drift identity colours.",
        f"STYLE: {STYLE_REF}",
        "", ])


def write(genesis_dir: Path, data: dict) -> None:
    sp = genesis_dir / "source_plan"
    (sp / "prompts").mkdir(parents=True, exist_ok=True)
    (genesis_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (sp / "PANEL_NATIVE_ART_SPECS.json").write_text(
        json.dumps({"issue": data["issue"], "panels": data["specs"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (genesis_dir / "metadata" / "panel_source_provenance.json").write_text(
        json.dumps({"issue": data["issue"], "panels": data["provenance"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # markdown spec summary
    md = ["# MonkeyZoo: Genesis — Panel-Native Art Specs", "",
          f"All {data['total']} panels are specified for their exact final dimensions.",
          f"Panels flagged for panel-native regeneration (heavy side-crop): **{data['regen_count']}**.",
          "", "| Pg | Pnl | Target px | Ratio | Shot | Beat | Crop class | Side-crop |",
          "|---|---|---|---|---|---|---|---|"]
    for s in data["specs"]:
        md.append(f"| {s['page']} | {s['panel']} | {s['target_px'][0]}x{s['target_px'][1]} | {s['aspect_ratio']} | "
                  f"{s['shot']} | {s['story_beat']} | {s['crop_classification']} | {s['side_crop_pct']}% |")
    (sp / "PANEL_NATIVE_ART_SPECS.md").write_text("\n".join(md), encoding="utf-8")
    # regen prompts (the owner-gated hand-off)
    for s in data["regen"]:
        (sp / "prompts" / f"page_{s['page']:02d}_panel_{s['panel']:02d}.md").write_text(_prompt(s), encoding="utf-8")


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    data = build(genesis_dir)
    write(genesis_dir, data)
    print(f"Panel-native specs: {data['total']} panels specified; provenance recorded; "
          f"{data['regen_count']} regen prompt(s) written for the owner-gated art pass.")


if __name__ == "__main__":
    main()
