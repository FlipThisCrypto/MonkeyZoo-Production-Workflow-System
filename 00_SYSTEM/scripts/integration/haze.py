"""Atmospheric depth haze for composited characters.

A character standing deep in a hazy scene must inherit the same fog veil
the plate paints over its own distant content, or it pops forward
unnaturally no matter how correct its scale is. Deterministic pixel mix:

    k = haze_max * clamp(1 - (foot_y - horizon) / (calib_y - horizon), 0, 1)
    rgb = rgb * (1 - k) + haze_color * k

so a character AT the calibration depth (or nearer) gets zero haze and
one approaching the horizon approaches the scene's declared haze_max.
The haze color should be SAMPLED from the plate's own far band (e.g.
zoo-city-streets measures [76, 80, 103]), not guessed.

Alpha untouched; linework recolored along with fills, exactly like the
plate's own hazed background linework.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def depth_haze_factor(foot_y: float, horizon_y: float, calib_y: float,
                      haze_max: float) -> float:
    depth_ratio = (foot_y - horizon_y) / max(1e-6, (calib_y - horizon_y))
    return float(haze_max * np.clip(1.0 - depth_ratio, 0.0, 1.0))


def apply_haze(char_rgba: Image.Image, k: float,
               haze_color: tuple[int, int, int]) -> Image.Image:
    if k <= 0.001:
        return char_rgba
    arr = np.array(char_rgba.convert("RGBA")).astype(np.float32)
    hc = np.array(haze_color, dtype=np.float32)
    arr[..., :3] = arr[..., :3] * (1 - k) + hc[None, None, :] * k
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
