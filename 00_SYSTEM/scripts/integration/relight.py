"""Cheap environmental relighting for a flat cel-shaded character layer.

No real normal map exists (the house style is flat cel colors with a
single soft-shade pass, not a 3D render), so this approximates directional
lighting the way a 2D compositor would: a left-to-right (or whatever axis
the key/fill sources imply) tint gradient across the character's own
silhouette, plus a thin rim-light highlight on the edge facing the key
light, plus an overall exposure match so the character isn't brighter than
the scene it's standing in.

Deliberately does NOT touch the alpha channel or redraw any linework --
only recolors existing opaque pixels, so identity/line-art integrity from
character_bible.md is preserved (a full regen risking identity drift is
exactly what this track is trying to avoid).
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage


def _match_ambient_exposure(rgb: np.ndarray, alpha: np.ndarray, ambient_luma: float) -> np.ndarray:
    opaque = alpha > 200
    if not opaque.any():
        return rgb
    char_luma = rgb[opaque].astype(np.float32).mean()
    if char_luma <= 1:
        return rgb
    # move the character halfway toward the scene's ambient brightness --
    # halfway, not all the way, so it stays readable as a foreground subject
    # rather than melting into the background.
    target = (char_luma + ambient_luma) / 2
    factor = np.clip(target / char_luma, 0.35, 1.0)
    out = rgb.astype(np.float32) * factor
    return np.clip(out, 0, 255)


def _direction_gradient(width: int, height: int, axis: str) -> np.ndarray:
    if axis == "horizontal":
        g = np.linspace(0, 1, width, dtype=np.float32)[None, :].repeat(height, axis=0)
    else:
        g = np.linspace(0, 1, height, dtype=np.float32)[:, None].repeat(width, axis=1)
    return g


def relight(
    char_rgba: Image.Image,
    ambient_luma: float,
    key_color: tuple[int, int, int] = (150, 225, 255),
    fill_color: tuple[int, int, int] = (225, 90, 190),
    gradient_axis: str = "horizontal",
    key_on_high_side: bool = True,
    tint_strength: float = 0.24,
    rim_strength: float = 0.55,
) -> Image.Image:
    arr = np.array(char_rgba.convert("RGBA"))
    rgb, alpha = arr[..., :3].astype(np.float32), arr[..., 3]
    h, w = alpha.shape

    rgb = _match_ambient_exposure(rgb, alpha, ambient_luma)

    grad = _direction_gradient(w, h, gradient_axis)
    if not key_on_high_side:
        grad = 1 - grad
    key = np.array(key_color, dtype=np.float32)
    fill = np.array(fill_color, dtype=np.float32)
    tint_color = grad[..., None] * key[None, None, :] + (1 - grad[..., None]) * fill[None, None, :]

    opaque = (alpha > 0)[..., None]
    # screen blend on the key side (lighten), multiply blend on the fill side
    # -- gives directional light a believable brighten-vs-darken asymmetry.
    screen = 255 - (255 - rgb) * (255 - tint_color) / 255
    multiply = rgb * tint_color / 255
    mixed = grad[..., None] * screen + (1 - grad[..., None]) * multiply
    rgb = np.where(opaque, rgb * (1 - tint_strength) + mixed * tint_strength, rgb)

    opaque_mask = alpha > 200
    edge = ndimage.binary_dilation(opaque_mask, iterations=2) & ~ndimage.binary_erosion(opaque_mask, iterations=1)
    high_side = grad > 0.55
    rim_mask = edge & high_side & opaque_mask
    if rim_mask.any():
        rim_target = np.array(key_color, dtype=np.float32)
        rgb[rim_mask] = rgb[rim_mask] * (1 - rim_strength) + rim_target[None, :] * rim_strength

    out = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])
    return Image.fromarray(out, mode="RGBA")
