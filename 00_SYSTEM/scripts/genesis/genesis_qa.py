#!/usr/bin/env python3
"""Genesis QA: structural, lettering, and shot-variety reconciliation.

Reconciles the layout plan against the source panels and the rendered output,
and writes machine-readable QA sidecars + a human report. Exits non-zero on a
structural failure (missing page, dropped panel, broken sequence).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]
SCRIPTS = FACTORY / "00_SYSTEM" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
GEN = Path(__file__).resolve().parent
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))

import genesis_plan as gp          # noqa: E402
import genesis_build as gb         # noqa: E402

ALLOWED_CAPTIONS = set(gp.LOCATION_CAPTIONS.values()) | {gp.OPENING_CAPTION, gp.CLOSING_CAPTION} | \
    {v for v in gp.LOCATION_CAPTIONS.values()}


def structural(plan: dict, genesis_dir: Path) -> dict:
    problems = []
    pages = plan["pages"]
    if len(pages) != 22:
        problems.append(f"expected 22 story pages, got {len(pages)}")
    if plan["total_panels"] != 96:
        problems.append(f"expected 96 panels, got {plan['total_panels']}")
    ids = [pa["source_panel_id"] for pg in pages for pa in pg["panels"]]
    if len(ids) != 96 or len(set(ids)) != 96:
        problems.append(f"panel reconciliation: {len(ids)} refs, {len(set(ids))} unique")
    # rendered file sequence 01..24
    covers = sorted((genesis_dir / "web" / "covers").glob("*.jpg"))
    story = sorted((genesis_dir / "web" / "story_pages").glob("*.jpg"))
    # Filenames are expected to start with a two-digit page number (01..24). A
    # stray file without that prefix must be reported as a QA problem, not crash
    # the gate with a ValueError (int('co')) — the gate's job is to emit a verdict.
    seq = []
    malformed = []
    for p in sorted(covers + story, key=lambda p: p.name):
        prefix = p.name[:2]
        if prefix.isdigit():
            seq.append(int(prefix))
        else:
            malformed.append(p.name)
    if malformed:
        problems.append(f"render file(s) without a two-digit page prefix: {malformed[:5]}")
    if seq != list(range(1, 25)):
        problems.append(f"page file sequence not 01..24: {seq}")
    if len(story) != 22:
        problems.append(f"expected 22 story-page files, got {len(story)}")
    # every source panel image exists
    panel_dir = FACTORY / plan["source_panel_dir"]
    missing = [i for i in ids if not (panel_dir / f"{i}.png").exists()]
    if missing:
        problems.append(f"missing source panel art: {missing[:5]} (+{max(0,len(missing)-5)})")
    return {"pass": not problems, "problems": problems,
            "story_page_files": len(story), "cover_files": len(covers)}


def lettering(plan: dict) -> dict:
    problems = []
    warnings = []
    src = json.loads(gp.SOURCE_PLAN.read_text(encoding="utf-8"))
    # every source panel that has real dialogue must carry dialogue in the plan
    src_speaking = set()
    for pg in src["pages"]:
        for pa in pg["panels"]:
            if not gp._blank(pa.get("dialogue")):
                src_speaking.add(pa["panel_id"])
    plan_speaking = {pa["source_panel_id"] for pg in plan["pages"] for pa in pg["panels"]
                     if pa["dialogue"]}
    dropped = src_speaking - plan_speaking
    if dropped:
        problems.append(f"dialogue dropped from {len(dropped)} panels: {sorted(dropped)[:5]}")
    # captions must only be scene stamps (no production/beat notes leaked through)
    bad_caps = []
    for pg in plan["pages"]:
        for pa in pg["panels"]:
            c = pa["caption"]
            if c and c not in ALLOWED_CAPTIONS:
                bad_caps.append(c)
    if bad_caps:
        problems.append(f"non-scene captions rendered: {bad_caps[:5]}")
    # overflow: balloons over 35 words
    for pg in plan["pages"]:
        for pa in pg["panels"]:
            for spk, txt in gb.split_dialogue(pa["dialogue"]):
                if len(txt.split()) > 35:
                    warnings.append(f"balloon >35 words on {pa['source_panel_id']}")
    return {"pass": not problems, "problems": problems, "warnings": warnings,
            "source_speaking_panels": len(src_speaking),
            "rendered_speaking_panels": len(plan_speaking)}


def shots(plan: dict) -> dict:
    dist = Counter()
    adjacent_close = []
    for pg in plan["pages"]:
        prev = None
        for pa in pg["panels"]:
            dist[pa["shot"]] += 1
            if pa["shot"] in ("close", "extreme_close") and prev in ("close", "extreme_close"):
                adjacent_close.append(pg["page_number"])
            prev = pa["shot"]
    n = sum(dist.values())
    close_fraction = round((dist["close"] + dist["extreme_close"]) / n, 3) if n else 0.0
    return {
        "by_shot": dict(dist),
        "close_fraction": close_fraction,
        "adjacent_closeups_same_page": sorted(set(adjacent_close)),
        "distinct_shot_types": len(dist),
    }


def report(genesis_dir: Path) -> dict:
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    s = structural(plan, genesis_dir)
    l = lettering(plan)
    sh = shots(plan)
    counts = [p["panel_count"] for p in plan["pages"]]
    qa = {
        "structural": s, "lettering": l, "shots": sh,
        "pacing": {"avg": round(sum(counts) / len(counts), 2), "min": min(counts),
                   "max": max(counts), "distribution": dict(Counter(counts)),
                   "adjacent_same_template": sum(1 for i in range(1, len(plan["pages"]))
                       if plan["pages"][i]["layout_template"] == plan["pages"][i - 1]["layout_template"])},
        "overall_pass": s["pass"] and l["pass"],
    }
    qdir = genesis_dir / "qa"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "genesis_qa.json").write_text(json.dumps(qa, indent=2) + "\n", encoding="utf-8")

    md = ["# MonkeyZoo: Genesis — Technical QA Report", "",
          f"**Overall: {'PASS' if qa['overall_pass'] else 'FAIL'}**", "",
          "## Structural",
          f"- {'PASS' if s['pass'] else 'FAIL'} — {len(s['problems'])} problem(s)",
          f"- Story-page files: {s['story_page_files']}/22 · cover files: {s['cover_files']}/2"]
    md += [f"  - {p}" for p in s["problems"]]
    md += ["", "## Lettering",
           f"- {'PASS' if l['pass'] else 'FAIL'} — dialogue on {l['rendered_speaking_panels']}/"
           f"{l['source_speaking_panels']} source speaking panels; {len(l['warnings'])} overflow warning(s)"]
    md += [f"  - {p}" for p in l["problems"]]
    md += ["", "## Shot variety",
           f"- Distribution: {sh['by_shot']} (close fraction {sh['close_fraction']})",
           f"- Pages with adjacent same-scale close-ups: {sh['adjacent_closeups_same_page'] or 'none'}",
           "", "## Pacing",
           f"- Avg {qa['pacing']['avg']} panels/page (min {qa['pacing']['min']}, max {qa['pacing']['max']})",
           f"- Distribution: {qa['pacing']['distribution']}",
           f"- Adjacent identical templates: {qa['pacing']['adjacent_same_template']}", ""]
    (genesis_dir / "GENESIS_TECHNICAL_QA_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    return qa


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    qa = report(genesis_dir)
    print(f"Genesis QA: overall {'PASS' if qa['overall_pass'] else 'FAIL'}")
    print(f"  structural: {'PASS' if qa['structural']['pass'] else 'FAIL'} {qa['structural']['problems']}")
    print(f"  lettering:  {'PASS' if qa['lettering']['pass'] else 'FAIL'} {qa['lettering']['problems']}")
    print(f"  shots: {qa['shots']['by_shot']} close={qa['shots']['close_fraction']} "
          f"adj-closeups={qa['shots']['adjacent_closeups_same_page']}")
    print(f"  pacing: avg {qa['pacing']['avg']} dist {qa['pacing']['distribution']}")
    if not qa["overall_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
