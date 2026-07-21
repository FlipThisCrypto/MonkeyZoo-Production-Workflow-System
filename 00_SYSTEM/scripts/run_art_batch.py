#!/usr/bin/env python3
"""Stage 6 batch runner: queue an issue's art_prompt_pack.json in ComfyUI.

Usage:
    python run_art_batch.py 2026-08_Issue_06 [--variants 2] [--only P00,P04]
        [--checkpoint animagine-xl-4.0.safetensors] [--style-prefix "..."]
        [--host 127.0.0.1:8188] [--dry-run]

Queues panels in automation_rules order: plates (page 0) first, then fewest
characters first. Each variant uses seed, seed+1, ... (prompt_rules §5 reroll
policy). Output filename prefix: <issue_id>/<panel_id>_seed<seed> under
ComfyUI's output directory.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]


def build_workflow(panel, pack, args, seed):
    w, h = (panel.get("resolution") or "1216x832").split("x")
    prompt_text = panel["prompt"]
    lock = pack["style_lock_phrase"]
    if panel["page_number"] == 0 and args.plate_style:
        # establishing plates: the character-describing lock phrase fights
        # "no characters" on tag-trained models — swap in a scenery lock
        prompt_text = args.plate_style + prompt_text[len(lock):]
    elif args.style_prefix:
        # tag-style prefix helps illustration checkpoints lock the look;
        # inserted AFTER the style lock phrase so validation still passes
        prompt_text = lock + ", " + args.style_prefix + prompt_text[len(lock):]
    neg = panel["negative_prompt"]
    if args.neg_suffix:
        neg = neg + ", " + args.neg_suffix
    if args.engine == "zimage":
        # official ComfyUI Z-Image Turbo recipe: lumina2 CLIP, AuraFlow shift 3,
        # 8 steps, cfg 1 (negative zeroed — turbo ignores negative prompts).
        # cfg 1 side effects observed in MZ-2026-08-06 batch 1: lettering
        # clauses ("clear for two balloons") render as literal balloons, and
        # the words "MonkeyZoo house style" render as logo text. Filter both.
        clauses = [c for c in prompt_text.split(", ")
                   if "clear for" not in c and "balloon" not in c.lower()
                   and "SFX" not in c]
        prompt_text = ", ".join(clauses)
        prompt_text = prompt_text.replace("MonkeyZoo house style: ", "")
        if not panel.get("character_tokens"):
            # characterless panel: drop the monkey-describing lock entirely
            # (same failure mode as plates — the model draws the described
            # monkey since negatives are inert)
            body = prompt_text.split("dark cartoon sci-fi cyberpunk backdrop, ", 1)
            plate_lock = (args.plate_style or
                          "flat color cartoon background art in a dark sci-fi "
                          "style, thick clean black outlines, cel shading")
            prompt_text = plate_lock + ", " + (body[1] if len(body) > 1 else body[0])
        prompt_text += (", generous plain empty space for lettering, no text, "
                        "no letters, no words, no logo anywhere in the image")
        return {
            "1": {"class_type": "UNETLoader",
                  "inputs": {"unet_name": "z_image_turbo_bf16.safetensors",
                             "weight_dtype": "default"}},
            "2": {"class_type": "CLIPLoader",
                  "inputs": {"clip_name": "qwen_3_4b.safetensors",
                             "type": "lumina2", "device": "default"}},
            "3": {"class_type": "VAELoader",
                  "inputs": {"vae_name": "z_image_ae.safetensors"}},
            "4": {"class_type": "CLIPTextEncode",
                  "inputs": {"clip": ["2", 0], "text": prompt_text}},
            "5": {"class_type": "ConditioningZeroOut",
                  "inputs": {"conditioning": ["4", 0]}},
            "6": {"class_type": "EmptySD3LatentImage",
                  "inputs": {"width": int(w), "height": int(h), "batch_size": 1}},
            "7": {"class_type": "ModelSamplingAuraFlow",
                  "inputs": {"model": ["1", 0], "shift": 3.0}},
            "8": {"class_type": "KSampler",
                  "inputs": {"model": ["7", 0], "positive": ["4", 0],
                             "negative": ["5", 0], "latent_image": ["6", 0],
                             "seed": seed, "steps": 8, "cfg": 1.0,
                             "sampler_name": "res_multistep",
                             "scheduler": "simple", "denoise": 1.0}},
            "9": {"class_type": "VAEDecode",
                  "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
            "10": {"class_type": "SaveImage",
                   "inputs": {"images": ["9", 0],
                              "filename_prefix": f"{pack['issue_id']}/{panel['panel_id']}_seed{seed}"}},
        }
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": args.checkpoint}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["1", 1], "text": prompt_text}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"clip": ["1", 1], "text": neg}},
        "4": {"class_type": "EmptyLatentImage",
              "inputs": {"width": int(w), "height": int(h), "batch_size": 1}},
        "5": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "positive": ["2", 0],
                         "negative": ["3", 0], "latent_image": ["4", 0],
                         "seed": seed, "steps": args.steps, "cfg": args.cfg,
                         "sampler_name": "dpmpp_2m", "scheduler": "karras",
                         "denoise": 1.0}},
        "6": {"class_type": "VAEDecode",
              "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage",
              "inputs": {"images": ["6", 0],
                         "filename_prefix": f"{pack['issue_id']}/{panel['panel_id']}_seed{seed}"}},
    }


def queue(host, workflow):
    body = json.dumps({"prompt": workflow}).encode()
    req = urllib.request.Request(f"http://{host}/prompt", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        return {"node_errors": {"connection": f"Failed to connect to http://{host}/prompt: {exc.reason}"}}



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--variants", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--checkpoint", default="animagine-xl-4.0.safetensors")
    ap.add_argument("--style-prefix", default="")
    ap.add_argument("--neg-suffix", default="")
    ap.add_argument("--plate-style", default="")
    ap.add_argument("--engine", default="sdxl", choices=["sdxl", "zimage"])
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--cfg", type=float, default=6.0)
    ap.add_argument("--host", default="127.0.0.1:8188")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pack_file = FACTORY / "02_MONTHLY_ISSUES" / args.issue / "art_prompt_pack.json"
    pack = json.loads(pack_file.read_text(encoding="utf-8"))

    panels = pack["panels"]
    only = [p.strip() for p in args.only.split(",") if p.strip()]
    if only:
        panels = [p for p in panels
                  if any(tag in p["panel_id"] for tag in only)]
    # batch order: plates first, then fewest characters first, story order
    panels.sort(key=lambda p: (p["page_number"] != 0,
                               len(p.get("character_tokens", [])),
                               p["page_number"], p["panel_number"]))

    result = run_batch(pack, panels, args)
    print(f"{result['ok']} generations queued, {result['failed']} failed.")
    # Exit non-zero when any submission failed (e.g. ComfyUI unreachable) so an
    # agent or automated run can detect the failure instead of reading a
    # success-looking "queued" tally.
    if result["failed"]:
        sys.exit(1)


def run_batch(pack, panels, args, queue_fn=queue):
    """Queue every panel/variant. Returns {'ok': n, 'failed': n}; a submission
    whose response carries node_errors counts as failed, not as queued."""
    ok = failed = 0
    for panel in panels:
        for v in range(args.variants):
            seed = panel["seed"] + v
            if args.dry_run:
                print(f"DRY {panel['panel_id']} seed={seed} res={panel.get('resolution')}")
                continue
            resp = queue_fn(args.host, build_workflow(panel, pack, args, seed))
            err = resp.get("node_errors")
            if err:
                failed += 1
                print(f"queued {panel['panel_id']} seed={seed} -> ERR {json.dumps(err)}")
            else:
                ok += 1
                print(f"queued {panel['panel_id']} seed={seed} -> ok")
    return {"ok": ok, "failed": failed}


if __name__ == "__main__":
    main()
