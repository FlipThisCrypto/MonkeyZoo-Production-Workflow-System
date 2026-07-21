"""Puddle/wet-surface reflection for a composited character.

Mirrors the (already scaled + relit) character sprite across its ground
contact line, squashes it slightly (reflections foreshorten on a ground
plane viewed from above), fades it vertically (strongest at the contact
line), applies a small per-row sine ripple, tints it toward the water
color, and clips the result to a declared reflective-surface polygon from
scene_blocking.json. Deterministic -- no randomness at all.

Restraint is deliberate: house style is flat cel shading, and the plate's
own neon reflections are soft/diffuse, so a mirror-sharp reflection would
read as out of style. Defaults are tuned to "suggestion of a reflection",
matching the plate's own signage reflections.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def add_puddle_reflection(
    canvas: Image.Image,
    char_scaled: Image.Image,
    paste_box: tuple[int, int, int, int],
    surface_polygon: list[tuple[int, int]],
    opacity: float = 0.30,
    squash: float = 0.80,
    ripple_amp_px: float = 2.2,
    ripple_period_px: float = 11.0,
    tint: tuple[int, int, int] = (60, 80, 115),
    tint_strength: float = 0.45,
    blur_px: float = 1.4,
) -> tuple[Image.Image, dict]:
    """canvas: current composite BEFORE the character is pasted (so the
    reflection sits under the character's own feet). char_scaled: the
    exact sprite that will be pasted (already relit/scaled). paste_box:
    where it will go ([x0, y0, x1, y1]; y1 is the ground contact line)."""
    canvas = canvas.convert("RGBA")
    x0, y0, x1, y1 = paste_box
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0 or not surface_polygon or len(surface_polygon) < 3:
        # a degenerate paste box or a missing/too-small puddle surface (surface
        # detection failed) -> skip the reflection rather than crash the composite
        # (PIL's polygon fill needs >= 2 points; resize needs a positive size).
        return canvas, {"reflection_visible_px": 0}

    # mirror + squash
    flipped = char_scaled.transpose(Image.FLIP_TOP_BOTTOM)
    refl_h = max(1, round(h * squash))
    flipped = flipped.resize((w, refl_h), Image.LANCZOS)
    arr = np.array(flipped).astype(np.float32)

    # vertical fade: alpha strongest at the contact line (row 0 of the
    # reflection), gone by the bottom
    fade = np.linspace(1.0, 0.06, refl_h, dtype=np.float32)[:, None]
    arr[..., 3] *= fade * opacity

    # water tint on the color channels
    t = np.array(tint, dtype=np.float32)
    arr[..., :3] = arr[..., :3] * (1 - tint_strength) + t[None, None, :] * tint_strength

    # per-row horizontal ripple displacement
    out_rgba = np.zeros_like(arr)
    for row in range(refl_h):
        shift = int(round(ripple_amp_px * math.sin(2 * math.pi * row / ripple_period_px)))
        out_rgba[row] = np.roll(arr[row], shift, axis=0)
    refl_img = Image.fromarray(np.clip(out_rgba, 0, 255).astype(np.uint8), "RGBA")
    refl_img = refl_img.filter(ImageFilter.GaussianBlur(blur_px))

    # clip to the reflective surface polygon
    surface_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(surface_mask).polygon([tuple(p) for p in surface_polygon], fill=255)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(refl_img, (x0, y1))  # reflection starts AT the contact line, extends down
    layer_arr = np.array(layer)
    mask_arr = np.array(surface_mask, dtype=np.float32) / 255.0
    layer_arr[..., 3] = (layer_arr[..., 3].astype(np.float32) * mask_arr).astype(np.uint8)
    layer = Image.fromarray(layer_arr, "RGBA")

    out = canvas.copy()
    out.alpha_composite(layer)

    visible_px = int((np.array(layer)[..., 3] > 8).sum())
    return out, {"reflection_visible_px": visible_px}
