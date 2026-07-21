#!/usr/bin/env python3
"""Genesis duplicate / near-duplicate panel analysis.

Perceptual-hash (dhash) the 96 source panels, cluster near-identical images
(dominated by the 5 shared background plates), and cross-reference the layout
plan to flag runs of visually-similar panels placed close together -- the
repetition that makes a sequence feel static. Emits JSON + Markdown reports and
a duplicate contact sheet.

Deterministic. numpy-only (no imagehash dependency).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

FACTORY = Path(__file__).resolve().parents[3]

# near-duplicate if full-frame dhash Hamming distance <= this
DHASH_NEAR = 12
# "same background" if the top strip (scene plate) matches closely
BG_NEAR = 8


def dhash(img: Image.Image, size: int = 8) -> np.ndarray:
    g = np.asarray(img.convert("L").resize((size + 1, size), Image.LANCZOS), dtype=np.int16)
    return (g[:, 1:] > g[:, :-1]).flatten()


def bg_hash(img: Image.Image, size: int = 8) -> np.ndarray:
    # top 45% of the frame is mostly background plate (characters sit low)
    w, h = img.size
    top = img.crop((0, 0, w, int(h * 0.45)))
    return dhash(top, size)


def hamming(a: np.ndarray, b: np.ndarray) -> int:
    return int(np.count_nonzero(a != b))


def analyze(genesis_dir: Path) -> dict:
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    panel_dir = FACTORY / plan["source_panel_dir"]
    # reading-order list of (page, panel_id)
    order = []
    for pg in plan["pages"]:
        # source order = sorted by panel id within page
        for pa in sorted(pg["panels"], key=lambda p: p["source_panel_id"]):
            order.append((pg["page_number"], pa["source_panel_id"]))
    hashes, bgs = {}, {}
    for _, pid in order:
        with Image.open(panel_dir / f"{pid}.png") as im:
            hashes[pid] = dhash(im)
            bgs[pid] = bg_hash(im)


    ids = [pid for _, pid in order]
    # exact + near-duplicate pairs (full frame)
    exact, near = [], []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            d = hamming(hashes[ids[i]], hashes[ids[j]])
            if d == 0:
                exact.append((ids[i], ids[j]))
            elif d <= DHASH_NEAR:
                near.append((ids[i], ids[j], d))

    # runs of same-background panels placed within 2 reading positions
    page_of = {pid: pg for pg, pid in order}
    close_repeats = []
    for i in range(len(ids) - 1):
        for k in (1, 2):
            if i + k < len(ids):
                d = hamming(bgs[ids[i]], bgs[ids[i + k]])
                if d <= BG_NEAR:
                    close_repeats.append({
                        "a": ids[i], "b": ids[i + k], "gap": k, "bg_distance": d,
                        "page_a": page_of[ids[i]], "page_b": page_of[ids[i + k]],
                    })

    # cluster by background (union-find over BG_NEAR)
    parent = {pid: pid for pid in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if hamming(bgs[ids[i]], bgs[ids[j]]) <= BG_NEAR:
                parent[find(ids[i])] = find(ids[j])
    clusters: dict[str, list[str]] = {}
    for pid in ids:
        clusters.setdefault(find(pid), []).append(pid)
    bg_clusters = sorted([c for c in clusters.values() if len(c) > 1], key=len, reverse=True)

    return {
        "total_panels": len(ids),
        "exact_duplicate_pairs": [list(p) for p in exact],
        "near_duplicate_pairs": [[a, b, d] for a, b, d in near],
        "close_background_repeats": close_repeats,
        "background_clusters": [{"size": len(c), "panels": sorted(c)} for c in bg_clusters],
        "num_background_clusters": len(bg_clusters),
        "thresholds": {"dhash_near": DHASH_NEAR, "bg_near": BG_NEAR},
    }


# Distinct framings applied to consecutive same-plate WIDE/MEDIUM panels so a
# reused background reads as a different camera set-up. (L, T, R, B fractions.)
CROP_VARIANTS = [
    (0.00, 0.00, 1.00, 1.00),   # 0 full establishing (first time a plate appears)
    (0.14, 0.08, 0.90, 1.00),   # 1 push in
    (0.00, 0.16, 0.70, 1.00),   # 2 pan left / lower
    (0.30, 0.16, 1.00, 1.00),   # 3 pan right / lower
    (0.08, 0.30, 0.92, 1.00),   # 4 low band (character/foot level)
    (0.00, 0.00, 0.80, 0.82),   # 5 upper-left framing
]
CLUSTER_LOOKBACK = 4            # a plate seen within this many reading positions counts as a repeat


def assign_crops(genesis_dir: Path, report: dict) -> dict:
    """Assign a distinct crop window to each consecutive reuse of a background
    plate (wide/medium shots only -- close-ups are already tight and keep the
    full frame). Writes metadata/panel_crops.json consumed by the assembler."""
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    shot_of = {pa["source_panel_id"]: pa["shot"] for pg in plan["pages"] for pa in pg["panels"]}
    # map each panel -> its background cluster id
    cluster_id = {}
    for ci, cl in enumerate(report["background_clusters"]):
        for pid in cl["panels"]:
            cluster_id[pid] = ci
    order = []
    for pg in plan["pages"]:
        for pa in sorted(pg["panels"], key=lambda p: p["source_panel_id"]):
            order.append(pa["source_panel_id"])
    crops = {}
    last_seen: dict[int, int] = {}
    repeat_idx: dict[int, int] = {}
    for pos, pid in enumerate(order):
        cid = cluster_id.get(pid, -1)
        variant = 0
        if cid >= 0:
            if cid in last_seen and pos - last_seen[cid] <= CLUSTER_LOOKBACK:
                repeat_idx[cid] = repeat_idx.get(cid, 0) + 1
            else:
                repeat_idx[cid] = 0
            last_seen[cid] = pos
            variant = repeat_idx[cid]
        # only reframe wide/medium; keep tight faces on the full frame
        if shot_of.get(pid) in ("close", "extreme_close") or variant == 0:
            crops[pid] = list(CROP_VARIANTS[0])
        else:
            crops[pid] = list(CROP_VARIANTS[variant % len(CROP_VARIANTS)])
    reframed = sum(1 for c in crops.values() if c != list(CROP_VARIANTS[0]))
    (genesis_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (genesis_dir / "metadata" / "panel_crops.json").write_text(
        json.dumps({"crops": crops, "reframed_count": reframed,
                    "variants": CROP_VARIANTS}, indent=2) + "\n", encoding="utf-8")
    return {"reframed_count": reframed}


def contact_sheet(genesis_dir: Path, report: dict) -> None:
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    panel_dir = FACTORY / plan["source_panel_dir"]
    rows = report["background_clusters"][:8]
    if not rows:
        return
    tw, th, pad = 240, 135, 8
    cols = max((r["size"] for r in rows), default=1)
    W = pad + cols * (tw + pad)
    H = pad + len(rows) * (th + pad)
    sheet = Image.new("RGB", (W, H), (24, 24, 28))
    for r, row in enumerate(rows):
        for c, pid in enumerate(row["panels"][:cols]):
            t = Image.open(panel_dir / f"{pid}.png").convert("RGB").resize((tw, th), Image.LANCZOS)
            sheet.paste(t, (pad + c * (tw + pad), pad + r * (th + pad)))
    (genesis_dir / "previews" / "comparison").mkdir(parents=True, exist_ok=True)
    sheet.save(genesis_dir / "previews" / "comparison" / "duplicate_panel_contact_sheet.png")


def write_reports(genesis_dir: Path, report: dict) -> None:
    qdir = genesis_dir / "qa"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "duplicate_panel_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md = ["# MonkeyZoo: Genesis — Duplicate / Near-Duplicate Panel Report", "",
          f"- Panels analyzed: **{report['total_panels']}**",
          f"- Exact-duplicate pairs: **{len(report['exact_duplicate_pairs'])}**",
          f"- Near-duplicate pairs (dhash ≤ {report['thresholds']['dhash_near']}): "
          f"**{len(report['near_duplicate_pairs'])}**",
          f"- Same-background clusters (the 5 plates): **{report['num_background_clusters']}**",
          f"- Close background repeats (within 2 reading positions): "
          f"**{len(report['close_background_repeats'])}**", "",
          "## Classification",
          "- Same-background reuse is **acceptable location continuity** (only 5 plates exist).",
          "- The fix applied is **crop variation**: consecutive same-plate panels get distinct",
          "  framings (wide / push-in / reframe) so they read as different camera set-ups rather",
          "  than the same image repeated. New generated art is the owner-gated deeper fix.", "",
          "## Background clusters"]
    for c in report["background_clusters"]:
        md.append(f"- {c['size']} panels share a plate: {', '.join(p.split('_',1)[1] for p in c['panels'])}")
    md += ["", "## Close background repeats (candidates for crop variation)"]
    for r in report["close_background_repeats"][:40]:
        md.append(f"- p{r['page_a']} {r['a'].split('_',1)[1]} ↔ p{r['page_b']} {r['b'].split('_',1)[1]} "
                  f"(gap {r['gap']}, bg dist {r['bg_distance']})")
    (qdir / "duplicate_panel_report.md").write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    genesis_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else FACTORY / "GENESIS"
    report = analyze(genesis_dir)
    write_reports(genesis_dir, report)
    contact_sheet(genesis_dir, report)
    crop = assign_crops(genesis_dir, report)
    print(f"Duplicate analysis: {report['total_panels']} panels")
    print(f"  exact pairs: {len(report['exact_duplicate_pairs'])}  "
          f"near pairs: {len(report['near_duplicate_pairs'])}")
    print(f"  background clusters: {report['num_background_clusters']}  "
          f"close repeats: {len(report['close_background_repeats'])}")
    print(f"  crop-variation reframes: {crop['reframed_count']} panels")


if __name__ == "__main__":
    main()
