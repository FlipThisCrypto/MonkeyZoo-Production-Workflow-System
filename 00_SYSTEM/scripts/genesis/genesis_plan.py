#!/usr/bin/env python3
"""Genesis layout planner.

Reflows the 96 ordered "Signals in the Silence" panels (Issue 02 page_panel_plan)
into 22 variable-density story pages with deterministic, narrative-driven pacing.

It does NOT randomize reading order, dialogue ownership, continuity, or canon.
Variation is constrained: panels stay in story order and are partitioned into 22
contiguous pages by a dynamic program that (a) tracks a professional pacing curve
and (b) prefers page breaks at natural scene boundaries (location changes, act
breaks, cliffhanger beats). Given the same source plan and seed it reproduces the
same layout.

Output: GENESIS_LAYOUT_PLAN.json + .md and metadata sidecars.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[3]
SOURCE_ISSUE = FACTORY / "02_MONTHLY_ISSUES" / "2026-09_Issue_02"
SOURCE_PLAN = SOURCE_ISSUE / "page_panel_plan.json"
PREVIEW_DIR = SOURCE_ISSUE / "generated_art" / "integration_preview"

STORY_PAGES = 22
SEED = 20260718  # deterministic tie-breaks; changing it reshuffles equal-cost choices only

# Professional pacing spine: target panels per story page (sums to 96, range 3-6,
# avg 4.36). Opens quieter, builds, dips for escalation beats, spikes at the
# climax, winds down to a stinger. The DP tracks this while snapping page breaks
# to real scene boundaries.
PACING_TARGET = [3, 5, 5, 4, 5, 4, 5, 3, 5, 5, 4, 5, 4, 6, 3, 5, 6, 4, 5, 4, 3, 3]
assert len(PACING_TARGET) == STORY_PAGES
# per-page allowed [min,max] panels; opening/finale may run lighter for impact
SIZE_BOUNDS = [(2, 4)] + [(3, 6)] * (STORY_PAGES - 2) + [(2, 3)]

_DASH = re.compile(r"^[\s\-‐-―−]*$")


def _blank(s) -> bool:
    return not s or bool(_DASH.match(str(s)))


def _words(s) -> int:
    return 0 if _blank(s) else len(str(s).split())


def _shot(camera: str) -> str:
    c = str(camera or "").strip().lower()
    if c.startswith("extreme close") or c.startswith("ecu"):
        return "extreme_close"
    if c.startswith("close") or c.startswith("cu"):
        return "close"
    if c.startswith("wide") or c.startswith("establish") or c.startswith("ews") or c.startswith("ws"):
        return "wide"
    if c.startswith("medium") or c.startswith("ms") or c.startswith("mcu"):
        return "medium"
    if c.startswith("over"):
        return "ots"
    return "medium"


_MOTION = ("run", "leap", "grab", "throw", "burst", "slam", "rush", "swing", "dash",
           "strike", "flinch", "spin", "crash", "reach", "climb", "fall", "push")


def _beat(panel: dict, shot: str) -> str:
    action = str(panel.get("action", "")).lower()
    notes = str(panel.get("visual_notes", "")).lower()
    emotion = str(panel.get("emotion", "")).lower()
    dwords = _words(panel.get("dialogue"))
    has_sfx = not _blank(panel.get("sfx"))
    chars = panel.get("characters") or []
    reveal = any(k in (notes + " " + action) for k in ("reveal", "first appear", "discover", "realize", "signal source"))
    action_hit = any(m in action for m in _MOTION) or (has_sfx and not dwords)
    if reveal:
        return "reveal"
    if shot == "wide" and not chars:
        return "establishing"
    if shot == "wide" and dwords == 0:
        return "establishing"
    if action_hit:
        return "action"
    if shot in ("close", "extreme_close") and dwords <= 3:
        return "reaction"
    if dwords > 0:
        return "dialogue"
    if any(k in emotion for k in ("quiet", "still", "calm", "pause")):
        return "beat"
    return "transition"


IMPORTANCE = {
    "reveal": 1.0, "action": 0.72, "establishing": 0.6, "reaction": 0.5,
    "dialogue": 0.45, "beat": 0.4, "transition": 0.3,
}

# The source "caption" field holds beat/director shorthand ("Quick reassurance
# risk", "A real choice"), NOT reader copy -- rendering it makes the issue read
# like an annotated storyboard. We keep it as an internal beat_note and instead
# place clean scene-establishing captions at each new location (standard comic
# grammar, derived from real location data, not invented story).
LOCATION_CAPTIONS = {
    "Zoo City Streets": "ZOO CITY",
    "School / Public Address Zone": "ZOO CITY — SCHOOL",
    "Early-Fall Storm Streets and Routine Nodes": "ACROSS ZOO CITY",
    "Transit Announcement Hub": "TRANSIT HUB",
    "Old Relay Junction": "OLD RELAY JUNCTION",
}
OPENING_CAPTION = "ZOO CITY — EARLY FALL"
CLOSING_CAPTION = "END — MONKEYZOO RETURNS"


def load_panels() -> list[dict]:
    plan = json.loads(SOURCE_PLAN.read_text(encoding="utf-8"))
    out = []
    scene = -1
    prev_loc = None
    for page in plan["pages"]:
        for panel in page["panels"]:
            loc = panel.get("location", "")
            if loc != prev_loc:
                scene += 1
                prev_loc = loc
            shot = _shot(panel.get("camera_angle", ""))
            beat = _beat(panel, shot)
            out.append({
                "source_panel_id": panel["panel_id"],
                "orig_page": int(panel["panel_id"].split("_P")[1].split("_")[0]),
                "location": loc,
                "scene": scene,
                "characters": panel.get("characters") or [],
                "camera_angle": panel.get("camera_angle", ""),
                "shot": shot,
                "beat": beat,
                "importance": IMPORTANCE.get(beat, 0.4),
                "dialogue": "" if _blank(panel.get("dialogue")) else str(panel["dialogue"]),
                "caption": "" if _blank(panel.get("caption")) else str(panel["caption"]),
                "sfx": "" if _blank(panel.get("sfx")) else str(panel["sfx"]),
                "dialogue_words": _words(panel.get("dialogue")),
                "caption_words": _words(panel.get("caption")),
                "action": panel.get("action", ""),
                "emotion": panel.get("emotion", ""),
            })
    return out


def break_score(a: dict, b: dict) -> float:
    """Preference for a page break BETWEEN panel a and the next panel b."""
    s = 0.0
    if a["scene"] != b["scene"]:
        s += 3.0                     # scene / location change: strong break
    if a["orig_page"] != b["orig_page"]:
        s += 1.0                     # original act boundary
    if a["beat"] in ("reveal", "action") and a["sfx"]:
        s += 1.2                     # cliffhang on a hit -> page-turn
    if b["beat"] == "establishing":
        s += 0.8                     # let a new scene open a page
    return s


def segment(panels: list[dict]) -> list[tuple[int, int]]:
    """Partition the ordered panels into exactly STORY_PAGES contiguous pages via
    DP minimizing pacing deviation minus break-quality plus a repetition penalty.
    Returns a list of (start, end) index pairs."""
    n = len(panels)
    gaps = [break_score(panels[i], panels[i + 1]) for i in range(n - 1)] + [0.0]
    INF = float("inf")
    # dp[k][i] = best cost to split first i panels into k pages; back[k][i] = start
    dp = [[INF] * (n + 1) for _ in range(STORY_PAGES + 1)]
    back = [[-1] * (n + 1) for _ in range(STORY_PAGES + 1)]
    dp[0][0] = 0.0
    for k in range(1, STORY_PAGES + 1):
        lo, hi = SIZE_BOUNDS[k - 1]
        target = PACING_TARGET[k - 1]
        for i in range(1, n + 1):
            best, bj = INF, -1
            for size in range(lo, hi + 1):
                j = i - size
                if j < 0 or dp[k - 1][j] == INF:
                    continue
                boundary_gap = gaps[i - 1]                     # break after panel i-1
                same = 1.0 if (back[k - 1][j] != -1 and (j - back[k - 1][j]) == size) else 0.0
                cost = dp[k - 1][j] + 1.0 * (size - target) ** 2 - 1.6 * boundary_gap + 1.2 * same
                # deterministic tie-break seeded by (k,i,size)
                cost += 1e-6 * ((SEED + k * 131 + i * 17 + size) % 7)
                if cost < best:
                    best, bj = cost, j
            dp[k][i] = best
            back[k][i] = bj
    # reconstruct
    bounds = []
    i, k = n, STORY_PAGES
    while k > 0:
        j = back[k][i]
        bounds.append((j, i))
        i, k = j, k - 1
    bounds.reverse()
    return bounds


# --- layout template selection (variety without randomness) ---
# template ids are interpreted geometrically by the assembler.
# Landscape-band templates only (source art is 16:9). "hero_*" have a taller
# feature band first; "band_*" are even bands. No tall columns / 3-across rows.
TEMPLATES = {
    2: ["band2", "hero2"],
    3: ["band3", "hero3"],
    4: ["band4", "hero4"],
    5: ["band5", "hero5"],
    6: ["band6", "hero6"],
}


def _is_feature(t: str) -> bool:
    return t.startswith("hero")


def pick_template(size: int, page_idx: int, prev: str | None, has_strong_feature: bool) -> str:
    opts = TEMPLATES.get(size)
    if size == 1 or not opts:
        return "splash" if size == 1 else f"band{size}"
    # prefer a hero (feature) band when the page has a dominant panel; else even bands
    ordered = sorted(opts, key=lambda t: (0 if _is_feature(t) == has_strong_feature else 1))
    # rotate to avoid repeating the previous page's template
    for off in range(len(ordered)):
        cand = ordered[(page_idx + off) % len(ordered)]
        if cand != prev:
            return cand
    return ordered[0]


def build_plan() -> dict:
    panels = load_panels()
    bounds = segment(panels)
    pages = []
    prev_template = None
    prev_scene = None
    n_pages = len(bounds)
    for pi, (a, b) in enumerate(bounds):
        group = panels[a:b]
        size = len(group)
        # feature = highest-importance panel on the page; strong only if it stands out
        fi = max(range(size), key=lambda idx: group[idx]["importance"])
        imps = sorted((g["importance"] for g in group), reverse=True)
        strong = size >= 3 and (imps[0] - (imps[1] if len(imps) > 1 else 0)) >= 0.15
        template = pick_template(size, pi, prev_template, strong)
        prev_template = template
        # hero templates put the feature panel in the taller first band (slot 0)
        order = list(range(size))
        if _is_feature(template):
            order = [fi] + [k for k in range(size) if k != fi]
        page_panels = []
        for slot, gi in enumerate(order):
            g = group[gi]
            page_panels.append({
                "slot": slot,
                "source_panel_id": g["source_panel_id"],
                "emphasis": (slot == 0 and (_is_feature(template) or template == "splash")),
                "shot": g["shot"],
                "beat": g["beat"],
                "characters": g["characters"],
                "dialogue": g["dialogue"],
                "caption": "",                      # reader caption assigned below
                "beat_note": g["caption"],          # internal beat shorthand (not rendered)
                "sfx": g["sfx"],
                "dialogue_words": g["dialogue_words"],
            })
        # Scene-establishing caption on the first source-order panel of a page
        # that opens a new location; opening/closing get special captions.
        page_open = group[0]
        first_pid = page_open["source_panel_id"]
        cap = None
        if pi == 0:
            cap = OPENING_CAPTION
        elif page_open["scene"] != prev_scene:
            cap = LOCATION_CAPTIONS.get(page_open["location"], page_open["location"].upper())
        if cap:
            for pp in page_panels:
                if pp["source_panel_id"] == first_pid:
                    pp["caption"] = cap
                    break
        if pi == n_pages - 1:
            last_pid = group[-1]["source_panel_id"]
            for pp in page_panels:
                if pp["source_panel_id"] == last_pid:
                    pp["caption"] = CLOSING_CAPTION
                    break
        prev_scene = group[-1]["scene"]
        beats = [g["beat"] for g in group]
        pages.append({
            "page_number": pi + 1,
            "reader_side": "right" if (pi + 1) % 2 == 1 else "left",
            "panel_count": size,
            "layout_template": template,
            "location": group[0]["location"],
            "scene_span": sorted({g["scene"] for g in group}),
            "beat_summary": beats,
            "page_turn_purpose": _page_turn_purpose(group, pi),
            "panels": page_panels,
        })
    return {
        "schema_version": "genesis-1.0",
        "series": "MonkeyZoo",
        "issue_title": "Genesis",
        "story_subtitle": "Signals in the Silence",
        "production_issue": 8,
        "published_issue": 1,
        "slug": "genesis",
        "seed": SEED,
        "source_issue": SOURCE_PLAN.relative_to(FACTORY).as_posix(),
        "source_panel_dir": PREVIEW_DIR.relative_to(FACTORY).as_posix(),
        "story_page_count": STORY_PAGES,
        "front_cover": (PREVIEW_DIR / "COVER_FRONT.png").relative_to(FACTORY).as_posix(),
        "back_cover": (PREVIEW_DIR / "COVER_BACK.png").relative_to(FACTORY).as_posix(),
        "total_panels": sum(p["panel_count"] for p in pages),
        "pages": pages,
    }


def _page_turn_purpose(group: list[dict], pi: int) -> str:
    last = group[-1]
    if pi == 0:
        return "cold open — establish tone and the first anomaly"
    if pi == STORY_PAGES - 1:
        return "final image / next-issue stinger"
    if last["beat"] in ("reveal", "action") and last["sfx"]:
        return "cliffhanger into the turn"
    if last["beat"] == "reaction":
        return "hold on reaction before the turn"
    return "carry momentum into the next beat"


def sidecars(plan: dict) -> dict:
    from collections import Counter
    shot = Counter()
    beat = Counter()
    dwords = []
    per_page_counts = []
    for pg in plan["pages"]:
        per_page_counts.append(pg["panel_count"])
        for pa in pg["panels"]:
            shot[pa["shot"]] += 1
            beat[pa["beat"]] += 1
            if pa["dialogue_words"]:
                dwords.append(pa["dialogue_words"])
    n = plan["total_panels"]
    return {
        "shot_distribution": {"by_shot": dict(shot), "total": n,
                              "close_fraction": round((shot["close"] + shot["extreme_close"]) / n, 3)},
        "dialogue_metrics": {
            "panels_with_dialogue": len(dwords),
            "total_dialogue_words": sum(dwords),
            "avg_words_per_speaking_panel": round(sum(dwords) / len(dwords), 2) if dwords else 0,
            "max_words_in_panel": max(dwords) if dwords else 0,
        },
        "page_turns": [{"page": pg["page_number"], "side": pg["reader_side"],
                        "purpose": pg["page_turn_purpose"]} for pg in plan["pages"]],
        "beat_distribution": dict(beat),
        "panels_per_page": per_page_counts,
        "avg_panels_per_page": round(n / len(per_page_counts), 2),
        "min_panels_per_page": min(per_page_counts),
        "max_panels_per_page": max(per_page_counts),
    }


def to_markdown(plan: dict, meta: dict) -> str:
    lines = [f"# {plan['series']}: {plan['issue_title']} — Layout Plan",
             f"*{plan['story_subtitle']}* · Production Issue {plan['production_issue']} · "
             f"Published Issue {plan['published_issue']}", "",
             f"- Story pages: **{plan['story_page_count']}**  |  Panels: **{plan['total_panels']}**  |  "
             f"Avg/page: **{meta['avg_panels_per_page']}** (min {meta['min_panels_per_page']}, max {meta['max_panels_per_page']})",
             f"- Shot mix: {meta['shot_distribution']['by_shot']} (close fraction {meta['shot_distribution']['close_fraction']})",
             f"- Dialogue: {meta['dialogue_metrics']['total_dialogue_words']} words across "
             f"{meta['dialogue_metrics']['panels_with_dialogue']} panels "
             f"(avg {meta['dialogue_metrics']['avg_words_per_speaking_panel']}/panel, max {meta['dialogue_metrics']['max_words_in_panel']})",
             f"- Deterministic seed: `{plan['seed']}`", "", "## Page-by-page", ""]
    for pg in plan["pages"]:
        lines.append(f"### Page {pg['page_number']:02d} ({pg['reader_side']}) — {pg['panel_count']} panels · "
                     f"`{pg['layout_template']}` · {pg['location']}")
        lines.append(f"- Beats: {', '.join(pg['beat_summary'])}")
        lines.append(f"- Page-turn: {pg['page_turn_purpose']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    plan = build_plan()
    meta = sidecars(plan)
    # invariants
    assert plan["total_panels"] == 96, plan["total_panels"]
    assert plan["story_page_count"] == STORY_PAGES
    assert all(3 <= p["panel_count"] <= 6 or p["page_number"] in (1, STORY_PAGES) for p in plan["pages"])
    (out_dir).mkdir(parents=True, exist_ok=True)
    (out_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (out_dir / "GENESIS_LAYOUT_PLAN.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "GENESIS_LAYOUT_PLAN.md").write_text(to_markdown(plan, meta), encoding="utf-8")
    for name, data in (("shot_distribution", meta["shot_distribution"]),
                       ("dialogue_metrics", meta["dialogue_metrics"]),
                       ("page_turns", {"page_turns": meta["page_turns"]})):
        (out_dir / "metadata" / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Genesis plan: {plan['story_page_count']} pages, {plan['total_panels']} panels, "
          f"avg {meta['avg_panels_per_page']}/page (min {meta['min_panels_per_page']}, max {meta['max_panels_per_page']})")
    print(f"panels/page: {meta['panels_per_page']}")
    print(f"shots: {meta['shot_distribution']['by_shot']}")


if __name__ == "__main__":
    main()
