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
    alpha = int(255 * opacity)
    draw.ellipse(bbox, fill=(10, 8, 15, alpha))

    layer = layer.filter(ImageFilter.GaussianBlur(blur_px))

    out = canvas.copy()
    out.alpha_composite(layer)
    return out
