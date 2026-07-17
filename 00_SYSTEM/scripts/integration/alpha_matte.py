"""Chroma-key alpha extraction for MonkeyZoo character reference images.

Character refs (03_APPROVED_CANON/approved_characters/<name>/*.png and
docs/media/expressions/<name>/*.webp) are rendered on a flat solid-color
backdrop (see gen_char_refs.py TAIL/CHARS["bg"]). That backdrop is never
pixel-perfect (diffusion noise), so we can't key on an exact RGB match --
instead we:

  1. Estimate the backdrop color from the four corners (median, robust to
     a stray anti-aliased pixel).
  2. Flood-fill connected background from the image border inward using a
     per-pixel color-distance threshold (scipy.ndimage label on a binary
     "close to backdrop color" mask, keeping only components touching the
     border). This avoids clipping character regions that happen to share
     the backdrop hue (e.g. skin/hair tones near the background color) --
     unlike a naive global threshold, an enclosed similar-colored patch
     that never touches the border is NOT removed.
  3. Feather the mask edge (small gaussian blur on the alpha channel) and
     decontaminate a 2px edge band (unmix backdrop color out of the color
     channels) so no colored halo survives at the silhouette boundary.

Output: RGBA PNG, transparent background, defringed edge.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

COLOR_DIST_THRESHOLD = 28.0   # euclidean RGB distance considered "background-like"
FEATHER_PX = 1.2              # gaussian sigma applied to the alpha channel
DECONTAMINATE_BAND = 2        # pixels in from the mask edge to strip backdrop bleed


def estimate_backdrop_color(arr: np.ndarray, corner: int = 12) -> np.ndarray:
    h, w, _ = arr.shape
    samples = np.concatenate([
        arr[:corner, :corner].reshape(-1, 3),
        arr[:corner, w - corner:].reshape(-1, 3),
        arr[h - corner:, :corner].reshape(-1, 3),
        arr[h - corner:, w - corner:].reshape(-1, 3),
    ])
    return np.median(samples, axis=0)


def background_mask(arr: np.ndarray, bg_color: np.ndarray, threshold: float) -> np.ndarray:
    dist = np.linalg.norm(arr.astype(np.float32) - bg_color.astype(np.float32), axis=2)
    close = dist < threshold
    labels, n = ndimage.label(close, structure=np.ones((3, 3)))
    if n == 0:
        return np.zeros(close.shape, dtype=bool)
    h, w = close.shape
    border_labels = set(labels[0, :].tolist()) | set(labels[-1, :].tolist()) \
        | set(labels[:, 0].tolist()) | set(labels[:, -1].tolist())
    border_labels.discard(0)
    return np.isin(labels, list(border_labels))


def defringe(arr: np.ndarray, alpha: np.ndarray, bg_color: np.ndarray, band: int) -> np.ndarray:
    """Push edge-pixel colors away from the backdrop color proportional to
    how close to fully-transparent they are, so no tinted halo remains once
    composited over a different background."""
    opaque = alpha > 250
    edge_zone = ndimage.binary_dilation(opaque, iterations=band) & ~opaque & (alpha > 0)
    out = arr.astype(np.float32).copy()
    a = alpha.astype(np.float32) / 255.0
    # unmix: observed = bg*(1-a) + fg*a  =>  fg = (observed - bg*(1-a)) / a
    a_safe = np.clip(a, 0.12, 1.0)[..., None]
    fg = (out - bg_color[None, None, :] * (1 - a_safe)) / a_safe
    out[edge_zone] = np.clip(fg[edge_zone], 0, 255)
    return out


def strip_baked_ground_shadow(arr: np.ndarray, alpha: np.ndarray, bg_color: np.ndarray,
                              band_frac: float = 0.30, threshold: float = 62.0) -> np.ndarray:
    """Z-Image likes to bake a soft backdrop-tinted drop-shadow ellipse
    under a character's feet (found live in Cycle 15: a pink ellipse rode
    through the matte into the composite because it's backdrop-FAMILY but
    beyond the strict key threshold). In the bottom band of the opaque
    bbox, re-key with a relaxed threshold: the ellipse is always close to
    the backdrop color there, while boots/legs are far from it."""
    ys, xs = np.where(alpha > 0)
    if len(ys) == 0:
        return alpha
    y0, y1 = ys.min(), ys.max()
    band_start = int(y1 - (y1 - y0) * band_frac)
    dist = np.linalg.norm(arr.astype(np.float32) - bg_color.astype(np.float32), axis=2)
    band = np.zeros_like(alpha, dtype=bool)
    band[band_start:, :] = True
    kill = band & (dist < threshold) & (alpha > 0)
    out = alpha.copy()
    out[kill] = 0
    return out


def extract(src: Path, dst: Path, threshold: float = COLOR_DIST_THRESHOLD) -> dict:
    img = Image.open(src).convert("RGB")
    arr = np.array(img)
    bg = estimate_backdrop_color(arr)

    bg_mask = background_mask(arr, bg, threshold)
    alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
    alpha = strip_baked_ground_shadow(arr, alpha, bg)

    # feather: blur alpha, but keep the fully-opaque core untouched so the
    # character doesn't shrink -- only the transition band softens.
    alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(FEATHER_PX))
    alpha = np.array(alpha_img)

    rgb = defringe(arr, alpha, bg, DECONTAMINATE_BAND)

    out = np.dstack([rgb.astype(np.uint8), alpha])
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, mode="RGBA").save(dst)

    transparent_frac = float((alpha == 0).mean())
    opaque_frac = float((alpha == 255).mean())
    edge_frac = 1.0 - transparent_frac - opaque_frac
    corner_alpha = [int(alpha[0, 0]), int(alpha[0, -1]), int(alpha[-1, 0]), int(alpha[-1, -1])]
    return {
        "src": str(src),
        "dst": str(dst),
        "backdrop_color_est": [round(float(c), 1) for c in bg],
        "transparent_frac": round(transparent_frac, 4),
        "opaque_frac": round(opaque_frac, 4),
        "edge_frac": round(edge_frac, 4),
        "corner_alpha": corner_alpha,
        "corners_fully_transparent": all(c == 0 for c in corner_alpha),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--threshold", type=float, default=COLOR_DIST_THRESHOLD)
    args = ap.parse_args()
    report = extract(args.src, args.dst, args.threshold)
    for k, v in report.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
