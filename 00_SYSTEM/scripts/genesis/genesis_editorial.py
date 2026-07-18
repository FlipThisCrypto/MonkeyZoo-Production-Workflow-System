#!/usr/bin/env python3
"""Genesis editorial audit + before/after comparison sheets.

Produces the page-by-page editorial audit (md + json) from the layout plan,
duplicate report, crop map, and shot data, and composes labelled before/after
comparison images so the owner can see exactly what changed.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

FACTORY = Path(__file__).resolve().parents[3]
SCRIPTS = FACTORY / "00_SYSTEM" / "scripts"
for p in (str(SCRIPTS), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)
import assemble_pages as ap  # noqa: E402


def _load(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


# ---------------------------------------------------------------------------
# page-by-page editorial audit
# ---------------------------------------------------------------------------

def audit(genesis_dir: Path) -> dict:
    plan = _load(genesis_dir / "GENESIS_LAYOUT_PLAN.json")
    dupes = _load(genesis_dir / "qa" / "duplicate_panel_report.json", {})
    crops = _load(genesis_dir / "metadata" / "panel_crops.json", {}).get("crops", {})
    full = [0.0, 0.0, 1.0, 1.0]
    repeats_on_page = Counter()
    for r in dupes.get("close_background_repeats", []):
        repeats_on_page[r["page_a"]] += 1

    pages = []
    tmpls = [p["layout_template"] for p in plan["pages"]]
    for i, pg in enumerate(plan["pages"]):
        panels = pg["panels"]
        shots = [pa["shot"] for pa in panels]
        chars = sorted({c for pa in panels for c in (pa.get("characters") or [])})
        dwords = sum(pa["dialogue_words"] for pa in panels)
        balloons = sum(1 for pa in panels if pa["dialogue"])
        sfx = sum(1 for pa in panels if pa["sfx"])
        hero = next((pa["source_panel_id"] for pa in panels if pa.get("emphasis")), panels[0]["source_panel_id"])
        reframed = sum(1 for pa in panels if crops.get(pa["source_panel_id"], full) != full)
        prev_same = i > 0 and tmpls[i] == tmpls[i - 1]
        next_same = i < len(tmpls) - 1 and tmpls[i] == tmpls[i + 1]
        actions = []
        if reframed:
            actions.append(f"crop-variation reframed {reframed} reused-background panel(s)")
        actions.append("speaker prefixes removed from cast balloons")
        if sfx:
            actions.append("SFX styled by loudness + rotation")
        pages.append({
            "page": pg["page_number"], "reader_side": pg["reader_side"],
            "panel_count": pg["panel_count"], "layout_template": pg["layout_template"],
            "hero_panel": hero, "location": pg["location"], "characters": chars,
            "shots": shots, "shot_mix": dict(Counter(shots)),
            "dialogue_words": dwords, "balloon_count": balloons, "sfx_count": sfx,
            "close_background_repeats": repeats_on_page.get(pg["page_number"], 0),
            "panels_reframed": reframed,
            "layout_same_as_prev": prev_same, "layout_same_as_next": next_same,
            "story_beats": pg["beat_summary"], "page_turn_purpose": pg["page_turn_purpose"],
            "actions_taken": actions,
        })
    return {"issue": "MonkeyZoo: Genesis", "pages": pages,
            "summary": {
                "total_pages": len(pages),
                "pages_reframed": sum(1 for p in pages if p["panels_reframed"]),
                "total_panels_reframed": sum(p["panels_reframed"] for p in pages),
                "adjacent_same_template": sum(1 for p in pages if p["layout_same_as_prev"]),
            }}


def write_audit(genesis_dir: Path, data: dict) -> None:
    qdir = genesis_dir / "qa"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "GENESIS_PAGE_BY_PAGE_EDITORIAL_AUDIT.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = ["# MonkeyZoo: Genesis — Page-by-Page Editorial Audit", "",
          f"- Pages reframed by crop-variation: **{data['summary']['pages_reframed']}/{data['summary']['total_pages']}** "
          f"({data['summary']['total_panels_reframed']} panels)",
          f"- Adjacent identical templates: **{data['summary']['adjacent_same_template']}**", ""]
    for p in data["pages"]:
        md += [f"## Page {p['page']:02d} ({p['reader_side']}) — {p['panel_count']} panels · `{p['layout_template']}`",
               f"- Location: {p['location']}  ·  Hero panel: `{p['hero_panel'].split('_',1)[1]}`",
               f"- Shots: {p['shot_mix']}  ·  Dialogue: {p['dialogue_words']} words in {p['balloon_count']} balloons  ·  SFX: {p['sfx_count']}",
               f"- Beats: {', '.join(p['story_beats'])}",
               f"- Repetition: {p['close_background_repeats']} close background-repeat(s); "
               f"reframed {p['panels_reframed']} panel(s). Layout matches neighbour: "
               f"prev={p['layout_same_as_prev']}, next={p['layout_same_as_next']}",
               f"- Page-turn: {p['page_turn_purpose']}",
               f"- Actions: {'; '.join(p['actions_taken'])}", ""]
    (qdir / "GENESIS_PAGE_BY_PAGE_EDITORIAL_AUDIT.md").write_text("\n".join(md), encoding="utf-8")


# ---------------------------------------------------------------------------
# comparison sheets
# ---------------------------------------------------------------------------

def _label(img: Image.Image, text: str) -> Image.Image:
    f = ap._font("impact.ttf", max(28, img.width // 40))
    bar = Image.new("RGB", (img.width, f.size + 24), (18, 18, 22))
    d = ImageDraw.Draw(bar)
    d.text((16, 10), text, font=f, fill=(250, 220, 90))
    out = Image.new("RGB", (img.width, img.height + bar.height), (18, 18, 22))
    out.paste(bar, (0, 0))
    out.paste(img, (0, bar.height))
    return out


def _side_by_side(a: Image.Image, b: Image.Image, la: str, lb: str, gap: int = 24) -> Image.Image:
    h = max(a.height, b.height)
    a2 = _label(a, la)
    b2 = _label(b, lb)
    H = max(a2.height, b2.height)
    out = Image.new("RGB", (a2.width + b2.width + gap, H), (18, 18, 22))
    out.paste(a2, (0, 0))
    out.paste(b2, (a2.width + gap, 0))
    return out


def comparisons(genesis_dir: Path) -> list[str]:
    import genesis_build as gb
    cdir = genesis_dir / "previews" / "comparison"
    cdir.mkdir(parents=True, exist_ok=True)
    made = []

    # full issue: before vs after contact sheets
    before = cdir / "before_full_issue.jpg"
    after = genesis_dir / "previews" / "full_issue_contact_sheet.jpg"
    if before.exists() and after.exists():
        img = _side_by_side(Image.open(before).convert("RGB"), Image.open(after).convert("RGB"),
                            "BEFORE — uniform framing / speaker prefixes", "AFTER — crop variation + clean lettering")
        img.save(cdir / "before_after_full_issue.png")
        made.append("before_after_full_issue.png")

    # covers before/after
    bf, bb = cdir / "before_front_cover.jpg", cdir / "before_back_cover.jpg"
    af = genesis_dir / "web" / "covers" / "01_FRONT_COVER.jpg"
    ab = genesis_dir / "web" / "covers" / "24_BACK_COVER.jpg"
    if all(p.exists() for p in (bf, bb, af, ab)):
        row_b = _side_by_side(Image.open(bf).convert("RGB"), Image.open(bb).convert("RGB"), "BEFORE front", "BEFORE back")
        row_a = _side_by_side(Image.open(af).convert("RGB"), Image.open(ab).convert("RGB"), "AFTER front", "AFTER back")
        w = max(row_b.width, row_a.width)
        out = Image.new("RGB", (w, row_b.height + row_a.height + 16), (18, 18, 22))
        out.paste(row_b, (0, 0)); out.paste(row_a, (0, row_b.height + 16))
        out.save(cdir / "before_after_covers.png")
        made.append("before_after_covers.png")

    # repeated backgrounds: variant-0 (before) vs assigned crop (after) for the biggest cluster
    plan = _load(genesis_dir / "GENESIS_LAYOUT_PLAN.json")
    dupes = _load(genesis_dir / "qa" / "duplicate_panel_report.json", {})
    crops = _load(genesis_dir / "metadata" / "panel_crops.json", {}).get("crops", {})
    panel_dir = FACTORY / plan["source_panel_dir"]
    clusters = dupes.get("background_clusters", [])
    if clusters:
        cluster = max(clusters, key=lambda c: c["size"])["panels"][:6]
        tw, th, pad = 300, 169, 10
        rows = 2
        sheet = Image.new("RGB", (pad + len(cluster) * (tw + pad), pad + rows * (th + pad) + 60), (24, 24, 28))
        dd = ImageDraw.Draw(sheet)
        f = ap._font("impact.ttf", 30)
        dd.text((pad, 6), "REPEATED BACKGROUND — BEFORE (all full frame)  vs  AFTER (crop variation)", font=f, fill=(250, 220, 90))
        for c, pid in enumerate(cluster):
            src = Image.open(panel_dir / f"{pid}.png").convert("RGB")
            b = ap.fit_cover(src, tw, th, None)
            a = ap.fit_cover(src, tw, th, crops.get(pid))
            sheet.paste(b, (pad + c * (tw + pad), 50))
            sheet.paste(a, (pad + c * (tw + pad), 50 + th + pad))
        sheet.save(cdir / "before_after_repeated_backgrounds.png")
        made.append("before_after_repeated_backgrounds.png")

    return made


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    data = audit(genesis_dir)
    write_audit(genesis_dir, data)
    made = comparisons(genesis_dir)
    print(f"Editorial audit: {data['summary']['total_panels_reframed']} panels reframed across "
          f"{data['summary']['pages_reframed']} pages; adjacent-same-template "
          f"{data['summary']['adjacent_same_template']}")
    print(f"Comparison sheets: {made}")


if __name__ == "__main__":
    main()
