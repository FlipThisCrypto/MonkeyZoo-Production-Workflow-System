"""Identity-preservation QA for character layers.

Guards against the drift class found live in Cycle 13: a generated pose
render whose colors have slid off-canon (beige face instead of porcelain
white, lost black hair cap) while still "looking like a cute monkey."

Approach is evidence-derived, not hand-authored: each character's canon
palette is computed from its APPROVED alpha layer (quantized opaque-pixel
histogram), and a candidate layer is scored by how well the canon
palette's weighted bins are matched by the candidate's bins. The
pass/fail threshold is calibrated against real controls (approved layers
must self-score high; Cycle 13's actual beige-drift renders must fail) --
see tests/test_integration_pipeline.py.

Also provides a halo check: opaque-edge pixels matching the layer's OWN
backdrop-color family indicate a defringe failure at the silhouette rim.

KNOWN LIMITATION (measured, not hypothetical): this is a color-DRIFT
detector, not a character classifier. The six leads share one Emo body
template (white face, black clothes, brown fur, grey boots), so a
Scarline layer scores ~0.99 against Static's canon palette -- their
distinguishing marks (hair shape, stripe) are a small fraction of palette
mass. Wrong-character mix-ups must be caught by the human Gate A review
or a future hair-region-specific check, not by this score.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
LAYERS = ROOT / "00_SYSTEM" / "integration_upgrade" / "character_layers"

# Tolerances were CALIBRATED against real controls, not guessed: the
# Cycle-13 beige-drift face sits only ~29 RGB-units from canon porcelain
# white, so the credit window must close well below that while staying
# open above quantization noise. QUANT=8 keeps same-color adjacent-bin
# error under ~14; credit is full to 12 and zero by 30. A first draft
# with QUANT=32 / credit-to-120 scored the drift renders IDENTICALLY to
# canon (0.966 vs 0.966) -- the negative control caught it.
QUANT = 8


def _palette(img_rgba: np.ndarray, min_weight: float = 0.005) -> list[tuple[np.ndarray, float]]:
    """Quantized color histogram of opaque pixels -> [(bin_center_rgb, weight)],
    weights renormalized over kept bins so a perfect self-match scores 1.0."""
    opaque = img_rgba[..., 3] > 200
    px = img_rgba[opaque][:, :3]
    if len(px) == 0:
        return []
    q = (px // QUANT) * QUANT + QUANT // 2
    bins, counts = np.unique(q, axis=0, return_counts=True)
    weights = counts / counts.sum()
    keep = weights >= min_weight
    bins, weights = bins[keep], weights[keep]
    if weights.sum() > 0:
        weights = weights / weights.sum()
    order = np.argsort(-weights)
    return [(bins[order][i].astype(np.float32), float(weights[order][i])) for i in range(len(order))]


def identity_score(candidate_rgba: np.ndarray, canon_rgba: np.ndarray) -> float:
    """0..1: weighted fraction of the canon palette that the candidate
    reproduces within tight color distance. 1.0 = every significant canon
    color present; low = major canon colors missing or replaced (drift)."""
    canon = _palette(canon_rgba)
    cand = _palette(candidate_rgba, min_weight=0.002)
    if not canon or not cand:
        return 0.0
    cand_colors = np.stack([c for c, _ in cand])
    score = 0.0
    for color, weight in canon:
        dists = np.linalg.norm(cand_colors - color[None, :], axis=1)
        nearest = float(dists.min())
        credit = float(np.clip(1.0 - (nearest - 12.0) / 18.0, 0.0, 1.0))
        score += weight * credit
    return round(score, 4)


def check_identity(layer_path: Path, character: str,
                   canon_base: Path | None = None, threshold: float = 0.80) -> dict:
    if canon_base is None:
        canon_base = LAYERS / character / f"{character}_00_clean_base.png"
    cand = np.array(Image.open(layer_path).convert("RGBA"))
    canon = np.array(Image.open(canon_base).convert("RGBA"))
    score = identity_score(cand, canon)
    return {
        "layer": str(layer_path),
        "character": character,
        "canon_base": str(canon_base),
        "identity_score": score,
        "threshold": threshold,
        "verdict": "PASS" if score >= threshold else "FAIL",
    }


def check_halo(layer_path: Path, backdrop_rgb: tuple[float, float, float] | None = None,
               dist_thresh: float = 40.0, max_frac: float = 0.02) -> dict:
    """Fraction of opaque RIM pixels whose color matches the backdrop
    family. High fraction = defringe failure (colored halo will show once
    composited over a different background)."""
    arr = np.array(Image.open(layer_path).convert("RGBA"))
    alpha = arr[..., 3]
    opaque = alpha > 200
    if backdrop_rgb is None:
        # estimate from the nearly-transparent defringed edge's source: use
        # corner pixels of the ORIGINAL is unavailable here, so require the
        # caller to pass it when the layer has no transparent margin
        raise ValueError("backdrop_rgb required")
    rim = opaque & ~ndimage.binary_erosion(opaque, iterations=3)
    if not rim.any():
        return {"verdict": "SKIP", "reason": "no rim"}
    rim_px = arr[rim][:, :3].astype(np.float32)
    d = np.linalg.norm(rim_px - np.array(backdrop_rgb, dtype=np.float32)[None, :], axis=1)
    frac = float((d < dist_thresh).mean())
    return {
        "layer": str(layer_path),
        "halo_rim_fraction": round(frac, 4),
        "max_allowed": max_frac,
        "verdict": "PASS" if frac <= max_frac else "FAIL",
    }


if __name__ == "__main__":
    layer = Path(sys.argv[1])
    char = sys.argv[2]
    print(json.dumps(check_identity(layer, char), indent=2))
