#!/usr/bin/env python3
"""Generate standardized character variant reference sets (Z-Image).

Usage:
    python gen_char_refs.py [--only moodz,ash] [--variants-only back,angry]
                            [--host 127.0.0.1:8188] [--dry-run]

Built from the minted webp canon (#1136/#1195/#1173/#1199/#99-4/#1028):
one shared Emo Faction base, identity = hair/headwear + card color.
Outputs to ComfyUI output dir under MZ-REFS/<name>_<variant>_seed<seed>.
QA'd winners are then copied into 03_APPROVED_CANON/approved_characters/<name>/.
"""
import argparse
import json
import urllib.request

BASE = ("cute chibi cartoon MONKEY character (not a human child), oversized "
        "round head, the entire face and muzzle colored flat porcelain WHITE "
        "with a faint grey tint (the face is white, never brown or skin "
        "tone), large rounded white muzzle with two tiny black dot nostrils "
        "set high, small simple mouth low on the muzzle, huge white oval "
        "eyes with round black dot pupils and one droopy heavy eyelid, grey "
        "eye-shadow rings around the eyes, plain porcelain-white chest patch "
        "with a single short vertical stitch seam and no other marks, round "
        "brown monkey ears with darker brown inside, brown furry arms with "
        "black studded wrist cuffs and brown mitten fists, long curled brown "
        "monkey tail, black punk pants with rows of silver studs, chunky "
        "grey platform boots with black soles and tread stripes, very thick "
        "uniform black outlines, flat solid colors with no gradients, clean "
        "vector cartoon sticker look, ")

CHARS = {
    "moodz": {
        "hair": "black bowl-cut emo hair under a blue beanie cap, dark grey patches around both eyes",
        "bg": "flat solid warm orange background", "seed": 100001,
    },
    "twotone": {
        "hair": "shaggy mop of hair split vertically half jet-black on the viewer-left and half white on the viewer-right with a clean center parting",
        "bg": "flat solid purple background", "seed": 100002,
    },
    "static": {
        "hair": "flat glossy jet-black slicked hair cap with short jagged bangs high on the forehead",
        "bg": "flat solid hot-pink background", "seed": 100003,
    },
    "ash": {
        "hair": "big shaggy silver-white hair with a long jagged emo fringe sweeping across and covering one eye",
        "bg": "flat solid teal-turquoise background", "seed": 100004,
    },
    "neonblue": {
        "hair": "spiky crown of white hair with ice-blue cyan streaks radiating upward and a soft cyan glow at the roots",
        "bg": "flat solid spring-green background", "seed": 100005,
    },
    "scarline": {
        "hair": "smooth white helmet-shaped hair with one thick scarlet-red stripe running front-to-back over the viewer-left side",
        "bg": "flat solid light-grey background", "seed": 100006,
    },
}

VARIANTS = {
    "01_neutral":     "standing facing the viewer, arms relaxed at sides, default bored droopy deadpan expression, full body",
    "02_threeqtr":    "standing in three-quarter view turned toward the left, bored deadpan expression, full body",
    "03_profile":     "standing in full side profile facing left, deadpan expression, full body",
    "04_overshoulder": "rear three-quarter view: the character faces away from the viewer and looks back over one shoulder, most of the back of the hair and back of the body visible, tail curled out to one side, full body",
    "05_portrait":    "close-up head and shoulders portrait, droopy deadpan eyes looking at the viewer",
    "06_angry":       "furious expression with gritted teeth showing two small white fangs, brows slammed down, clenched mitten fists at sides, full body",
    "07_sad":         "sad slumped posture, downturned mouth, a single blue teardrop below one eye, full body",
    "08_shocked":     "shocked alarmed expression, both huge eyes fully wide with tiny pupils, small open o-shaped mouth, hands raised, full body",
    "09_smile":       "rare soft genuine small smile, relaxed shoulders, calm eyes, full body",
    "10_walking":     "mid-stride walking pose seen from the side, one foot forward, arms swinging, full body",
    "11_armscrossed": "arms crossed over the chest, weight on one hip, unimpressed half-lidded stare, full body",
    "12_sitting":     "sitting cross-legged on the ground, hands resting on knees, calm settled expression, full body",
    "13_pointing":    "pointing forward with one mitten hand extended, other hand on hip, alert expression, full body",
    "14_shout":       "shouting with a huge wide-open mouth showing a pink tongue, one fist raised in the air, energetic pose, full body",
}

TAIL = (", single character alone, centered, nothing else in frame, no text, "
        "no letters, no numbers, no logo anywhere in the image")

# img2img denoise tiers (calibrated 2026-07-06, Ash ladder test):
# 0.70 keeps init pose (angles/portrait), 0.80 changes expression,
# 0.85 changes full pose while identity holds
DENOISE_TIERS = {
    "01": 0.70, "02": 0.75, "03": 0.80, "04": 0.80, "05": 0.70,
    "06": 0.80, "07": 0.80, "08": 0.80, "09": 0.80,
    "10": 0.85, "11": 0.85, "12": 0.85, "13": 0.85, "14": 0.85,
}


def build(name, char, vkey, vdesc, seed, denoise=1.0, init=None):
    prompt = BASE + char["hair"] + ", " + vdesc + ", " + char["bg"] + TAIL
    g = {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "z_image_ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "7": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "8": {"class_type": "KSampler",
              "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0],
                         "latent_image": ["6", 0], "seed": seed, "steps": 8, "cfg": 1.0,
                         "sampler_name": "res_multistep", "scheduler": "simple",
                         "denoise": denoise}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage",
               "inputs": {"images": ["9", 0],
                          "filename_prefix": f"MZ-REFS/{name}_{vkey}_seed{seed}"}},
    }
    if init:
        # img2img from the minted canon card: identity/palette from the init,
        # pose/expression from the prompt (production.json restyle pattern)
        g["11"] = {"class_type": "LoadImage", "inputs": {"image": init}}
        g["12"] = {"class_type": "ImageScale",
                   "inputs": {"image": ["11", 0], "upscale_method": "lanczos",
                              "width": 912, "height": 1216, "crop": "center"}}
        g["6"] = {"class_type": "VAEEncode",
                  "inputs": {"pixels": ["12", 0], "vae": ["3", 0]}}
    else:
        g["6"] = {"class_type": "EmptySD3LatentImage",
                  "inputs": {"width": 832, "height": 1216, "batch_size": 1}}
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--variants-only", default="")
    ap.add_argument("--host", default="127.0.0.1:8188")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--img2img", action="store_true",
                    help="init from minted webp in ComfyUI input dir mz-canon/<name>.webp")
    ap.add_argument("--denoise", type=float, default=0.0,
                    help="img2img denoise override; 0 = auto tier per variant")
    args = ap.parse_args()

    names = [n.strip() for n in args.only.split(",") if n.strip()] or list(CHARS)
    vkeys = [v.strip() for v in args.variants_only.split(",") if v.strip()]

    n = 0
    for name in names:
        char = CHARS[name]
        for i, (vkey, vdesc) in enumerate(VARIANTS.items()):
            if vkeys and not any(vk in vkey for vk in vkeys):
                continue
            seed = char["seed"] + i * 7
            if args.dry_run:
                print(f"DRY {name}_{vkey} seed={seed}")
                continue
            init = f"mz-canon/{name}.webp" if args.img2img else None
            dn = 1.0
            if args.img2img:
                dn = args.denoise or DENOISE_TIERS.get(vkey.split("_")[0], 0.8)
            body = json.dumps({"prompt": build(name, char, vkey, vdesc, seed,
                                               denoise=dn, init=init)}).encode()
            req = urllib.request.Request(f"http://{args.host}/prompt", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read())
            err = resp.get("node_errors")
            print(f"queued {name}_{vkey} seed={seed} {'ERR ' + json.dumps(err) if err else 'ok'}")
            n += 1
    print(f"{n} variant generations queued.")


if __name__ == "__main__":
    main()
