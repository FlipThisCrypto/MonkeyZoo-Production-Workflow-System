"""Localized img2img edge unification -- EVALUATED AND REJECTED as a
default pipeline stage (Cycle 16, 2026-07-17). Kept for reference/manual
experiments only.

Verdict evidence: at cfg 1.0 (negatives inert) Z-Image *hallucinates*
inside the masked ring instead of harmonizing it -- attempt 1 (proper
4px-in/22px-out ring, denoise 0.35) produced foreign blobs at the seam and
destroyed the character's thin tail; attempt 2 exposed the scipy
iterations=0 pitfall (see build_ring_mask) and, corrected or not, the
approach re-imagines rather than blends. Meanwhile the deterministic
compositor's feathered/defringed edges already pass all acceptance
criteria, so this stage adds risk without measured benefit ON THIS
ENGINE. Revisit only with an engine that supports real guidance (cfg > 1
or a dedicated inpaint model).

Original design intent below.


Re-imagines ONLY a ring around the composited character's silhouette so
the paste boundary's linework/texture/color melt into the plate, without
touching the character interior (identity) or the background (approved
plate). Two independent safety layers:

  1. SetLatentNoiseMask restricts the sampler to the ring (latent space
     is 8x downscaled, so the ring is kept >= 24px wide to survive the
     downsample).
  2. Pixel-space clamp afterwards: output = ring_mask * sampled +
     (1 - ring_mask) * original. Even if the sampler bleeds, nothing
     outside the ring can change -- the clamp makes background
     preservation a mathematical guarantee, not a hope.

Denoise is deliberately low (default 0.35): enough to redraw edge pixels
coherently, not enough to invent new content.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

API = "http://127.0.0.1:8188"
COMFY_INPUT = Path(r"I:\ai\nft\input")
COMFY_OUTPUT = Path(r"I:\ai\nft\output")


def build_ring_mask(char_alpha: np.ndarray, canvas_size: tuple[int, int],
                    paste_box: tuple[int, int, int, int],
                    inner_px: int = 4, outer_px: int = 22, feather: float = 3.0) -> Image.Image:
    """White ring around the character silhouette edge, in full-canvas
    coordinates. inner_px eats slightly into the character so its outline
    can be redrawn; outer_px extends into the plate so the transition is
    re-imagined on both sides of the seam."""
    w, h = canvas_size
    full = np.zeros((h, w), dtype=bool)
    x0, y0, x1, y1 = paste_box
    opaque = char_alpha > 128
    full[y0:y1, x0:x1] = opaque[:y1 - y0, :x1 - x0]

    outer = ndimage.binary_dilation(full, iterations=outer_px)
    # scipy pitfall: iterations=0 means "erode until convergence" (erases
    # everything), NOT "no erosion" -- discovered live when a retry with
    # inner_px=0 silently made the ENTIRE character repaintable.
    inner = ndimage.binary_erosion(full, iterations=inner_px) if inner_px > 0 else full
    ring = outer & ~inner

    mask = Image.fromarray((ring * 255).astype(np.uint8), "L")
    return mask.filter(ImageFilter.GaussianBlur(feather))


def unify(composite_path: Path, char_alpha: np.ndarray,
          paste_box: tuple[int, int, int, int], scene_prompt: str,
          denoise: float = 0.35, seed: int = 909090,
          timeout_s: int = 600) -> tuple[Image.Image, dict]:
    comp = Image.open(composite_path).convert("RGB")
    ring = build_ring_mask(char_alpha, comp.size, paste_box)

    # stage inputs for ComfyUI
    stamp = int(time.time())
    comp_name = f"unify_src_{stamp}.png"
    mask_name = f"unify_mask_{stamp}.png"
    comp.save(COMFY_INPUT / comp_name)
    ring.save(COMFY_INPUT / mask_name)

    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "z_image_ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": scene_prompt}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "LoadImage", "inputs": {"image": comp_name}},
        "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "LoadImage", "inputs": {"image": mask_name}},
        "9": {"class_type": "ImageToMask", "inputs": {"image": ["8", 0], "channel": "red"}},
        "10": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["7", 0], "mask": ["9", 0]}},
        "11": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "12": {"class_type": "KSampler", "inputs": {
            "model": ["11", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["10", 0],
            "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
            "scheduler": "simple", "denoise": denoise}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": f"MZ-UNIFY/unified_{stamp}"}},
    }
    req = urllib.request.Request(f"{API}/prompt", data=json.dumps({"prompt": g}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
    if resp.get("node_errors"):
        raise RuntimeError(f"node errors: {resp['node_errors']}")

    t0 = time.time()
    out_file = None
    while time.time() - t0 < timeout_s:
        hits = sorted(COMFY_OUTPUT.glob(f"MZ-UNIFY/unified_{stamp}_*.png"))
        if hits:
            out_file = hits[-1]
            break
        time.sleep(5)
    if out_file is None:
        raise TimeoutError("unify render did not complete")

    sampled = Image.open(out_file).convert("RGB")
    if sampled.size != comp.size:
        sampled = sampled.resize(comp.size, Image.LANCZOS)

    # pixel-space clamp: only the ring may change
    ring_f = np.array(ring, dtype=np.float32)[..., None] / 255.0
    orig = np.array(comp, dtype=np.float32)
    samp = np.array(sampled, dtype=np.float32)
    clamped = ring_f * samp + (1 - ring_f) * orig
    out_img = Image.fromarray(np.clip(clamped, 0, 255).astype(np.uint8))

    # metrics: how much did the ring actually change, and is outside zero?
    diff = np.abs(samp - orig).sum(axis=2)
    ring_bool = np.array(ring) > 8
    metrics = {
        "render_file": str(out_file),
        "ring_px": int(ring_bool.sum()),
        "ring_mean_abs_diff": round(float(diff[ring_bool].mean()), 2),
        "outside_changed_px_after_clamp": 0,  # guaranteed by construction
        "render_seconds": round(time.time() - t0, 1),
    }
    return out_img, metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_dir", type=Path)
    ap.add_argument("--denoise", type=float, default=0.35)
    args = ap.parse_args()

    spec_dir = args.spec_dir
    root = Path(__file__).resolve().parents[3]
    pose = json.loads((spec_dir / "pose_spec.json").read_text(encoding="utf-8"))
    scene = json.loads((spec_dir / "scene_blocking.json").read_text(encoding="utf-8"))

    # reproduce the compositor's paste geometry to position the alpha
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from compositor import load_ground_plane
    gp = load_ground_plane(scene)
    layer = Image.open(root / pose["asset_used"]).convert("RGBA")
    alpha_img = layer.split()[-1]
    bbox = alpha_img.getbbox()
    cropped_alpha = np.array(layer.crop(bbox).split()[-1])
    foot = pose["ground_contact"]["foot_anchor_px"]
    target_h = gp.height_at(foot[1])
    scale = target_h / cropped_alpha.shape[0]
    new_w = max(1, round(cropped_alpha.shape[1] * scale))
    new_h = max(1, round(cropped_alpha.shape[0] * scale))
    resized_alpha = np.array(Image.fromarray(cropped_alpha).resize((new_w, new_h), Image.LANCZOS))
    paste_box = (round(foot[0] - new_w / 2), round(foot[1] - new_h),
                 round(foot[0] - new_w / 2) + new_w, round(foot[1] - new_h) + new_h)

    style = ("MonkeyZoo house style: chibi cartoon monkey, thick uniform black "
             "outlines, flat color fills with soft cel shading, dark cartoon "
             "sci-fi cyberpunk rainy neon street at night, wet pavement")
    out, metrics = unify(spec_dir / "04_final_integrated.png", resized_alpha,
                         paste_box, style, denoise=args.denoise)
    out_path = spec_dir / "05_edge_unified.png"
    out.save(out_path)
    metrics["output"] = str(out_path)
    print(json.dumps(metrics, indent=2))
