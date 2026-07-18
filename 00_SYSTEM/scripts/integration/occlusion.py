"""Foreground occlusion layers -- environmental elements that must pass IN
FRONT of a composited character (rain, fog, fence wire, railings, ...).

Cycle 6 implements rain-in-front, matched to the plate's own rain angle,
because it's the POC panel's occlusion requirement. The function is kept
general (any region, any streak params) so later panels needing fog/fence/
railing occlusion can add sibling functions without restructuring this
module.
"""
from __future__ import annotations

import random

from PIL import Image, ImageDraw, ImageFilter

# NOTE: like the perspective calibration in scene_blocking.json, this angle
# is a visual estimate from the plate (streaks lean slightly screen-left as
# they fall), not measured with a streak-detection tool -- flagged as a
# possible precision follow-up, same as the ground-plane values.
DEFAULT_RAIN_ANGLE_DEG = 100  # measured from +x axis; 90 = straight down
DEFAULT_STREAK_COLOR = (215, 225, 235)


def add_foreground_rain(
    canvas: Image.Image,
    region_bbox: tuple[int, int, int, int],
    density: int = 55,
    angle_deg: float = DEFAULT_RAIN_ANGLE_DEG,
    length_range: tuple[int, int] = (14, 34),
    opacity_range: tuple[float, float] = (0.12, 0.32),
    width_px: int = 1,
    seed: int = 60301,  # fixed seed: deterministic, reproducible output
    blur_px: float = 0.6,
    pad: int = 40,
) -> Image.Image:
    """Draws thin streaked lines over region_bbox (expanded by pad on each
    side so streaks entering/exiting the character read naturally) on a new
    top layer, alpha-composited over canvas. Deterministic given the same
    seed, so re-running the compositor produces byte-identical output."""
    rng = random.Random(seed)
    canvas = canvas.convert("RGBA")
    x0, y0, x1, y1 = region_bbox
    x0, y0 = x0 - pad, y0 - pad
    x1, y1 = x1 + pad, y1 + pad

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    import math
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)

    for _ in range(density):
        length = rng.uniform(*length_range)
        px = rng.uniform(x0, x1)
        py = rng.uniform(y0, y1)
        ex, ey = px + dx * length, py + dy * length
        alpha = int(255 * rng.uniform(*opacity_range))
        draw.line([(px, py), (ex, ey)], fill=DEFAULT_STREAK_COLOR + (alpha,), width=width_px)

    layer = layer.filter(ImageFilter.GaussianBlur(blur_px))
    out = canvas.copy()
    out.alpha_composite(layer)
    return out
