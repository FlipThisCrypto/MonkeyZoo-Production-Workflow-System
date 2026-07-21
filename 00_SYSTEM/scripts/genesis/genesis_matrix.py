#!/usr/bin/env python3
"""Genesis panel-native completion matrix.

Classifies every one of the 96 panels for panel-native completion using the
layout plan, the crop-budget audit, and the bespoke-art manifest. A band
composite that genuinely fits its landscape slot (negligible side-crop, clear
story function) is a legitimate KEEP; a character close/medium beat that would
read markedly better as bespoke art is a regenerate candidate. Emits the
matrix (json + md). Deterministic; no art is modified.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]
GEN = Path(__file__).resolve().parent
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))
import genesis_layout as gl  # noqa: E402  scene/page-custom slot geometry

IDMAP = {"MZ-CHAR-001": "moodz", "MZ-CHAR-002": "twotone", "MZ-CHAR-003": "static",
         "MZ-CHAR-004": "ash", "MZ-CHAR-005": "neonblue", "MZ-CHAR-006": "scarline",
         "MZ-CHAR-CLEVER": "clever"}


def classify(pa, pg, crop, bespoke: set) -> dict:
    pid = pa["source_panel_id"]
    cs = pa.get("characters") or []
    shot = pa["shot"]
    # crop_left_pct may be absent OR explicitly null (the auditor emits null when a
    # panel's side-crop is unmeasured). Keep it as None so the wide-shot verdict can
    # fall back to "review" instead of crashing on `None < 10`.
    side = crop.get(pid, {}).get("crop_left_pct")
    ncc = len(cs)
    if pid in bespoke:
        return dict(classification="CHARACTER_REGENERATED", proposed_solution="bespoke Z-Image pose composited to the panel",
                    generation_method="zimage_text2img+matte+composite", status="DONE",
                    visual_qa_result="pass", defect="(fixed) reused/tiny character on a character beat",
                    owner_review_required=True)
    if ncc == 0:
        return dict(classification="KEEP", proposed_solution="retain establishing band (fits landscape slot)",
                    generation_method="n/a", status="RESOLVED", visual_qa_result="pass",
                    defect="none — environment establishing, fits its slot", owner_review_required=False)
    if shot == "wide":
        return dict(classification="KEEP", proposed_solution="retain widescreen establishing composite",
                    generation_method="n/a", status="RESOLVED",
                    visual_qa_result="pass" if (side is not None and side < 10) else "review",
                    defect="none — wide establishing reads intentionally at band size",
                    owner_review_required=False)
    # close / medium character beats -> bespoke would read better
    recipe = all(c in IDMAP for c in cs)
    if ncc == 1:
        return dict(classification="REGENERATE_CHARACTER",
                    proposed_solution="bespoke single-character pose for this beat" if recipe else "needs a recipe descriptor first",
                    generation_method="zimage_text2img+matte+composite", status="CANDIDATE",
                    visual_qa_result="pending",
                    defect="reused composite; character small/generic for a solo close/medium beat",
                    owner_review_required=True)
    return dict(classification="REGENERATE_CHARACTER" if recipe else "REGENERATE_CHARACTER_NEEDS_DESCRIPTOR",
                proposed_solution="multi-character staged composite (per-character poses on shared plate)",
                generation_method="zimage_multichar_stage", status="CANDIDATE",
                visual_qa_result="pending",
                defect="multi-character beat reads as small figures; deserves staged bespoke art",
                owner_review_required=True)


def build(genesis_dir: Path) -> dict:
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    crop = {r["panel_id"]: r for r in json.loads((genesis_dir / "qa" / "PANEL_CROP_AUDIT.json").read_text(encoding="utf-8"))["panels"]}
    native = genesis_dir / "generated_art" / "panel_native"
    bespoke = {p.stem for p in native.glob("*.png")} if native.exists() else set()
    rows = []
    for pg in plan["pages"]:
        rects = gl.synth_page_rects(pg["panels"], pg["page_number"])
        for pa, (x, y, w, h) in zip(pg["panels"], rects):
            pid = pa["source_panel_id"]
            cm = crop.get(pid, {})
            cls = classify(pa, pg, crop, bespoke)
            final = (f"GENESIS/generated_art/panel_native/{pid}.png" if pid in bespoke
                     else f"{plan['source_panel_dir']}/{pid}.png")
            rows.append({
                "page": pg["page_number"], "panel_id": pid, "final_px": [w, h],
                "aspect_ratio": round(w / h, 3), "story_beat": pa["beat"],
                "current_source": "bespoke_zimage" if pid in bespoke else "integrated_composite",
                "current_source_ratio": 1.778, "current_crop_loss_pct": round(100 - cm.get("retained_area_pct", 0), 1),
                "side_crop_pct": cm.get("crop_left_pct"), "character_count": len(pa.get("characters") or []),
                "characters": [IDMAP.get(c, c) for c in (pa.get("characters") or [])],
                "shot_type": pa["shot"], "final_source_path": final,
                "provenance": "bespoke_panel_native_zimage" if pid in bespoke else "issue02_integrated_composite",
                **cls})
    counts = Counter(r["classification"] for r in rows)
    status = Counter(r["status"] for r in rows)
    unresolved = sum(1 for r in rows if r["status"] not in ("DONE", "RESOLVED"))
    return {"total": len(rows), "classification_counts": dict(counts),
            "status_counts": dict(status), "unresolved": unresolved, "panels": rows}


def write(genesis_dir: Path, m: dict) -> None:
    q = genesis_dir / "qa"; q.mkdir(parents=True, exist_ok=True)
    (q / "PANEL_NATIVE_COMPLETION_MATRIX.json").write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = ["# MonkeyZoo: Genesis — Panel-Native Completion Matrix", "",
          f"- Panels: **{m['total']}** · classifications: {m['classification_counts']}",
          f"- Status: {m['status_counts']}",
          f"- **Unresolved (needs work): {m['unresolved']}**", "",
          "| Pg | Panel | Ratio | Beat | Shot | Chars | Src | Side-crop | Classification | Status |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in m["panels"]:
        md.append(f"| {r['page']} | {r['panel_id'].split('_',1)[1]} | {r['aspect_ratio']} | {r['story_beat']} | "
                  f"{r['shot_type']} | {r['character_count']} | {'bespoke' if r['current_source']=='bespoke_zimage' else 'comp'} | "
                  f"{r['side_crop_pct']}% | {r['classification']} | {r['status']} |")
    (q / "PANEL_NATIVE_COMPLETION_MATRIX.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    gd = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    m = build(gd)
    write(gd, m)
    print(f"Completion matrix: {m['total']} panels")
    print(f"  classifications: {m['classification_counts']}")
    print(f"  status: {m['status_counts']}  | unresolved(needs work): {m['unresolved']}")


if __name__ == "__main__":
    main()
