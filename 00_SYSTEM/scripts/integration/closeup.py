"""Close-up panel builder for decompressed acting inserts.

The ground-plane compositor places full bodies; close-up panels (eyes,
face, shoulders) instead take the HEAD REGION of an existing character
layer and stage it large over a treated crop of the scene plate
(darkened + slightly blurred so depth-of-field pushes focus to the face).

Deterministic preview-quality tooling: the format's close-up inserts may
eventually deserve bespoke portrait renders (gen_scene_pose portrait
clause); this makes the 96-panel edition previewable today without
faking a capability that isn't there. Layer linework is untouched.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def closeup_panel(layer_path, plate_path, plate_crop_box,
                  out_size=(1280, 720), head_window=(0.05, 0.60),
                  char_height_frac=1.02, char_x_frac=0.56,
                  bg_darken=0.82, bg_blur=2.5, char_darken=0.94) -> Image.Image:
    """head_window: (top_frac, bottom_frac) of the character bbox to crop.
    First version took (0, 0.42) -- on chibi proportions that's almost all
    hair dome with the eyes sliced at the frame edge (found on the page-1
    preview). The default window now starts below the crown and ends
    under the muzzle so eyes land in the upper third of the panel."""
    plate = Image.open(plate_path).convert("RGB")
    bg = plate.crop(plate_crop_box).resize(out_size, Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(bg_darken).filter(ImageFilter.GaussianBlur(bg_blur))

    layer = Image.open(layer_path).convert("RGBA")
    bbox = layer.split()[-1].getbbox()
    char = layer.crop(bbox)
    y0 = int(char.height * head_window[0])
    y1 = int(char.height * head_window[1])
    head = char.crop((0, y0, char.width, y1))

    target_h = int(out_size[1] * char_height_frac)
    scale = target_h / head.height
    head = head.resize((max(1, int(head.width * scale)), target_h), Image.LANCZOS)
    arr = np.array(head).astype(np.float32)
    arr[..., :3] *= char_darken
    head = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    canvas = bg.convert("RGBA")
    px = int(out_size[0] * char_x_frac - head.width / 2)
    py = -int(target_h * 0.04)
    canvas.alpha_composite(head, (px, py))
    return canvas.convert("RGB")
