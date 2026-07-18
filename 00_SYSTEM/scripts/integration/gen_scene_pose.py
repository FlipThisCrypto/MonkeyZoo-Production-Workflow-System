"""Generate a bespoke scene-specific character pose for the integration
pipeline, reusing gen_char_refs.py's proven identity recipe (BASE + hair
descriptor + flat backdrop, img2img from the minted frame-0 PNG at the
calibrated pose-change denoise of 0.85).

The output is a full-frame render on the character's flat backdrop color,
ready for alpha_matte.py -- NOT a finished panel. Queues N seed variants;
selection stays a human/agent inspection step (Gate A discipline).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

# reuse the canonical identity descriptors instead of duplicating them
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gen_char_refs import BASE, CHARS, TAIL, build  # noqa: E402

OUT_DIR = Path(r"I:\ai\nft\output")


def queue_pose(name: str, pose_desc: str, seeds: list[int], host: str,
               denoise: float = 0.85, prefix: str = "MZ-SCENE-POSE") -> list[str]:
    char = CHARS[name]
    queued = []
    for seed in seeds:
        g = build(name, char, "scene", pose_desc, seed, denoise=denoise,
                  init=f"mz-canon/{name}.png")
        g["10"]["inputs"]["filename_prefix"] = f"{prefix}/{name}_scene_seed{seed}"
        body = json.dumps({"prompt": g}).encode()
        req = urllib.request.Request(f"http://{host}/prompt", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        if resp.get("node_errors"):
            raise RuntimeError(f"node errors: {resp['node_errors']}")
        queued.append(resp["prompt_id"])
        print(f"queued {name} seed={seed} -> {resp['prompt_id']}", flush=True)
    return queued


def wait_for_outputs(name: str, seeds: list[int], timeout_s: int = 1200,
                     prefix: str = "MZ-SCENE-POSE") -> list[Path]:
    """Waits for THESE SPECIFIC seeds' files. (First version globbed
    `{name}_scene_seed*` and returned instantly when a previous batch's
    outputs matched -- found the hard way on the second batch of the same
    character. Seed-exact matching is the fix.)"""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        found = []
        for seed in seeds:
            hits = sorted((OUT_DIR / prefix).glob(f"{name}_scene_seed{seed}_*.png"))
            if hits:
                found.append(hits[-1])
        if len(found) >= len(seeds):
            print(f"all {len(seeds)} renders complete in {time.time()-t0:.0f}s", flush=True)
            return found
        time.sleep(10)
    raise TimeoutError(f"only {len(found)} of {len(seeds)} renders after {timeout_s}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("pose_desc")
    ap.add_argument("--seeds", default="777001,777002,777003")
    ap.add_argument("--host", default="127.0.0.1:8188")
    ap.add_argument("--denoise", type=float, default=0.85)
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    queue_pose(args.name, args.pose_desc, seeds, args.host, args.denoise)
    paths = wait_for_outputs(args.name, seeds)
    for p in paths:
        print(p)
