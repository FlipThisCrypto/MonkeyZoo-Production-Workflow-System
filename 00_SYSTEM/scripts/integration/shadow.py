"""Procedural surface-aware contact shadow.

Draws a soft, directionally-offset ellipse under a character's foot anchor
so standing characters read as touching the ground instead of floating.
Not a raytraced shadow -- a deliberately cheap, deterministic approximation
that is good enough for a flat-lit cel-shaded house style, and much safer
than a full-panel regeneration (see automation_rules.md's caution against
unnecessary background damage).
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter


def draw_contact_shadow(
    canvas: Image.Image,
    foot_anchor_px: tuple[float, float],
    character_width_px: float,
    shadow_direction_deg: float = 225,  # down-left, screen-space (0=right, 90=down)
    length_factor: float = 0.55,
    width_factor: float = 0.85,
    blur_px: float = 6.0,
    opacity: float = 0.42,
) -> Image.Image:
    """Returns a new RGBA canvas with the shadow composited under the
    existing content at foot_anchor_px. Caller pastes the character on top
    afterward so the shadow sits correctly beneath it."""
    canvas = canvas.convert("RGBA")
    if character_width_px <= 0:                 # degenerate footprint -> nothing to draw
        return canvas.copy()
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    w = character_width_px * width_factor
    h = w * 0.34  # flattened ellipse footprint, not a circle
    rad = math.radians(shadow_direction_deg)
    offset_x = math.cos(rad) * character_width_px * length_factor * 0.4
    offset_y = abs(math.sin(rad)) * character_width_px * length_factor * 0.15

    cx = foot_anchor_px[0] + offset_x
    cy = foot_anchor_px[1] + offset_y

    bbox = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]

    # Ground-adaptive opacity (Cycle 26): 0.42 was tuned on a dark night
    # street; the same alpha over bright sunlit tile leaves the character
    # visually floating (found on the school hallway panel). Sample the
    # ground under the footprint and strengthen the shadow on bright
    # ground; dark-scene output is unchanged (factor is 1.0 below
    # luma 90).
    import numpy as np
    # Clamp the ground-sample box into the canvas and order it: a footprint whose
    # anchor sits at/past a canvas edge would otherwise produce an inverted crop box
    # and PIL raises "right < left". A degenerate box falls back to neutral luma.
    gx0 = min(max(0, int(cx - w / 2)), canvas.width)
    gx1 = min(max(0, int(cx + w / 2)), canvas.width)
    gy0 = min(max(0, int(cy - h / 2)), canvas.height)
    gy1 = min(max(0, int(cy + h / 2)), canvas.height)
    gx0, gx1 = min(gx0, gx1), max(gx0, gx1)
    gy0, gy1 = min(gy0, gy1), max(gy0, gy1)
    if gx1 > gx0 and gy1 > gy0:
        patch = np.array(canvas.convert("L").crop((gx0, gy0, gx1, gy1)), dtype=np.float32)
        ground_luma = float(patch.mean()) if patch.size else 128.0
    else:
        ground_luma = 128.0
    effective = min(0.65, opacity * (1.0 + max(0.0, ground_luma - 90.0) / 255.0 * 1.2))

    alpha = int(255 * effective)
    draw.ellipse(bbox, fill=(10, 8, 15, alpha))

    layer = layer.filter(ImageFilter.GaussianBlur(blur_px))

    out = canvas.copy()
    out.alpha_composite(layer)
    return out
