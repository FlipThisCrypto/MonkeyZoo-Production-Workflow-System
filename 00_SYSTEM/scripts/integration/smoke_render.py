"""One-shot ComfyUI smoke render for hang-recovery verification.

Per mz-art-run's VRAM-LEAK TRAP rule: a relaunched server is not trusted
until (a) /system_stats shows ~15.8GB vram_free AND (b) one render
actually completes. This queues a minimal Z-Image graph and polls until
the output file exists or a timeout expires. Exit 0 = verified.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8188"
OUT_DIR = Path(r"I:\ai\nft\output")
PREFIX = "integration_smoke"


def zimage_graph(prompt: str, seed: int, w: int = 512, h: int = 512) -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "z_image_ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "8": {"class_type": "KSampler", "inputs": {
            "model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0],
            "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
            "scheduler": "simple", "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": PREFIX}},
    }


def main(timeout_s: int = 900) -> int:
    existing = set(p.name for p in OUT_DIR.glob(f"{PREFIX}*.png"))
    graph = zimage_graph("simple flat cartoon test pattern, colorful geometric shapes", seed=424242)
    req = urllib.request.Request(f"{API}/prompt", data=json.dumps({"prompt": graph}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
    print("queued:", resp.get("prompt_id"), flush=True)

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        new = [p for p in OUT_DIR.glob(f"{PREFIX}*.png") if p.name not in existing]
        if new:
            dt = time.time() - t0
            print(f"COMPLETE in {dt:.0f}s -> {new[0]}", flush=True)
            return 0
        time.sleep(10)
    print("TIMEOUT: render did not complete", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
