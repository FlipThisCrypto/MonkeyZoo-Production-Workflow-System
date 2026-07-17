"""Automated integration QA gate.

Runs pixel-level checks against a finished, flattened panel image (no
alpha channel -- this is post-compositing, what actually ships) for the
brief's named failure modes that are mechanically checkable:

  1. flat_card_regions -- large near-uniform-color rectangular blocks,
     which is what a pasted NFT card or a flat solid-color reference
     backdrop looks like sitting in an otherwise painted/illustrated
     scene. Catches "visible rectangular reference background",
     "visible NFT border" as a side effect (the border ring is itself a
     second, thinner flat region concentric with the card).
  2. contact_shadow_present -- local-contrast check under a declared foot
     anchor: is the ground genuinely darker there than its immediate
     surroundings, or is the character floating with no grounding cue.

Deliberately does NOT attempt pose/identity/perspective QA -- those need
either a human eye or a vision model, not pixel statistics. This gate
catches the mechanically-detectable subset only, same spirit as
validate_issue.py's schema/file-existence checks vs. the human Gate A/B
checklist for everything else.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def _local_std_map(gray: np.ndarray, window: int) -> np.ndarray:
    mean = ndimage.uniform_filter(gray, size=window)
    mean_sq = ndimage.uniform_filter(gray.astype(np.float64) ** 2, size=window)
    var = np.clip(mean_sq - mean ** 2, 0, None)
    return np.sqrt(var)


def find_flat_card_regions(
    img: Image.Image,
    window: int = 9,
    std_thresh: float = 2.5,
    min_area: int = 1500,
    max_aspect: float = 2.2,
) -> list[dict]:
    """Catches large flat-color rectangular blocks that don't belong in a
    painted scene (e.g. leftover debug caption strips, an un-alpha'd
    reference backdrop pasted whole). Tested against the real
    MZ-2026-09-02_P01_PANEL01 draft composite: a version of this detector
    with morphological closing was tried first to re-merge a card's flat
    backdrop around its interior character art, but at any iteration count
    strong enough to bridge those gaps it also engulfed the plate's own
    dark night sky (which is flat by the same std measure) into one giant
    false-positive blob covering most of the frame. Reverted -- closing is
    the wrong tool here. See `known_reference_color_regions()` below for
    the check that actually catches a pasted, unmasked character card;
    this function is kept for the separate, genuinely-caught case of
    flat non-scene UI elements (caption bars, debug banners)."""
    gray = np.array(img.convert("L"), dtype=np.float64)
    std_map = _local_std_map(gray, window)
    flat = std_map < std_thresh

    # ignore a thin border strip -- some plates have soft vignettes there
    flat[:4, :] = flat[-4:, :] = flat[:, :4] = flat[:, -4:] = False

    labels, n = ndimage.label(flat)
    findings = []
    for i in range(1, n + 1):
        ys, xs = np.where(labels == i)
        area = len(ys)
        if area < min_area:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        w, h = x1 - x0 + 1, y1 - y0 + 1
        aspect = max(w, h) / max(1, min(w, h))
        if aspect > max_aspect:
            continue  # long thin flat strips (e.g. a wall panel) are not card-shaped
        bbox_area = w * h
        fill_ratio = area / bbox_area
        if fill_ratio < 0.6:
            continue  # not actually rectangular, just a sparse scatter of flat pixels
        rgb = np.array(img.convert("RGB"))
        mean_color = rgb[labels == i].mean(axis=0).round(1).tolist()
        findings.append({
            "bbox": [int(x0), int(y0), int(x1), int(y1)],
            "area_px": int(area),
            "fill_ratio": round(float(fill_ratio), 2),
            "mean_color": mean_color,
        })
    return findings


# Known reference/card backdrop colors that should never appear in a
# shipped, painted panel -- the six gen_char_refs.py solid backdrops, plus
# the MintGarden/CHIP-0015 minted-card light-blue border observed directly
# in MZ-2026-09-02_P01_PANEL01's draft composite ([120,200,255], sampled
# from the actual file, not guessed).
KNOWN_BAD_COLORS = {
    "moodz_backdrop_orange": (255, 200, 140),
    "twotone_backdrop_purple": (170, 68, 178),
    "static_backdrop_hotpink": (221, 69, 128),
    "ash_backdrop_teal": (40, 179, 178),
    "neonblue_backdrop_springgreen": (97, 225, 140),
    "scarline_backdrop_grey": (194, 194, 194),
    "minted_card_border_cyan": (120, 200, 255),
    "minted_card_fill_pink": (245, 120, 231),
}


def known_reference_color_regions(
    img: Image.Image, threshold: float = 18.0, min_area: int = 200, flatness_std_thresh: float = 6.0
) -> list[dict]:
    """Color match alone false-positives on legitimate saturated neon
    signage (verified directly: the POC's MonkeyZoo sign glow reads as
    'minted_card_fill_pink' by color distance alone, in a scene that has
    no card in it). A pasted flat-backdrop card is a hard-edged uniform
    fill; a glowing sign is a soft gradient/bloom. Require local flatness
    (same std measure as find_flat_card_regions) in addition to color
    match so gradient glow is excluded but a genuine flat paste is kept."""
    rgb = np.array(img.convert("RGB"), dtype=np.float32)
    gray = np.array(img.convert("L"), dtype=np.float64)
    flat = _local_std_map(gray, 9) < flatness_std_thresh
    findings = []
    for name, color in KNOWN_BAD_COLORS.items():
        dist = np.linalg.norm(rgb - np.array(color, dtype=np.float32), axis=2)
        mask = (dist < threshold) & flat
        labels, n = ndimage.label(mask)
        for i in range(1, n + 1):
            area = int((labels == i).sum())
            if area < min_area:
                continue
            ys, xs = np.where(labels == i)
            findings.append({
                "matched_color": name,
                "rgb": list(color),
                "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                "area_px": area,
            })
    return findings


def check_contact_shadow(img: Image.Image, foot_anchor_px: tuple[float, float], radius: int = 45) -> dict:
    gray = np.array(img.convert("L"), dtype=np.float64)
    h, w = gray.shape
    x, y = foot_anchor_px
    near = gray[max(0, int(y - radius // 2)):min(h, int(y + radius // 2)),
                max(0, int(x - radius)):min(w, int(x + radius))]
    far = gray[max(0, int(y - radius * 2)):max(0, int(y - radius)),
               max(0, int(x - radius * 2)):min(w, int(x + radius * 2))]
    if near.size == 0 or far.size == 0:
        return {"verdict": "SKIP", "reason": "anchor too close to image edge"}
    near_mean, far_mean = float(near.mean()), float(far.mean())
    darkened = far_mean - near_mean
    return {
        "verdict": "PASS" if darkened > 2.0 else "FAIL",
        "near_mean_luma": round(near_mean, 2),
        "far_mean_luma": round(far_mean, 2),
        "darkened_by": round(darkened, 2),
    }


def run_gate(image_path: Path, foot_anchor_px: tuple[float, float] | None = None) -> dict:
    img = Image.open(image_path).convert("RGB")
    flat_regions = find_flat_card_regions(img)
    bad_color_regions = known_reference_color_regions(img)
    result = {
        "image": str(image_path),
        "flat_card_regions_found": len(flat_regions),
        "flat_card_regions": flat_regions,
        "known_bad_color_regions_found": len(bad_color_regions),
        "known_bad_color_regions": bad_color_regions,
    }
    if foot_anchor_px:
        result["contact_shadow"] = check_contact_shadow(img, foot_anchor_px)

    fails = []
    if flat_regions:
        fails.append(f"{len(flat_regions)} flat-color rectangular region(s) detected (possible debug/UI overlay)")
    if bad_color_regions:
        fails.append(f"{len(bad_color_regions)} region(s) matching a known reference-backdrop or minted-card color")
    if foot_anchor_px and result.get("contact_shadow", {}).get("verdict") == "FAIL":
        fails.append("no measurable contact shadow at declared foot anchor")
    result["verdict"] = "FAIL" if fails else "PASS"
    result["fail_reasons"] = fails
    return result


if __name__ == "__main__":
    path = Path(sys.argv[1])
    anchor = None
    if len(sys.argv) > 3:
        anchor = (float(sys.argv[2]), float(sys.argv[3]))
    print(json.dumps(run_gate(path, anchor), indent=2))
