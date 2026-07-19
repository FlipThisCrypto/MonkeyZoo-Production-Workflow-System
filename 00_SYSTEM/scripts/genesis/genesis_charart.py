#!/usr/bin/env python3
"""Genesis bespoke per-panel character art: generate -> matte -> composite.

Generates an on-model character pose with the proven Z-Image text2img identity
recipe (hair + card-colour backdrop), keys out the flat backdrop by HUE (robust
to the render's vignette, which broke the flood-fill matte), and composites the
character onto the panel's darkened location plate as a finished landscape band.

Character identity (hair, card colour) is inherited from gen_char_refs.CHARS.
Nothing here promotes canon; outputs land in the working Genesis tree.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from scipy import ndimage

FACTORY = Path(__file__).resolve().parents[3]
SCRIPTS = FACTORY / "00_SYSTEM" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "integration"))
from gen_char_refs import CHARS, build  # noqa: E402
from shadow import draw_contact_shadow   # noqa: E402

HOST = "127.0.0.1:8188"
OUT_DIR = Path(r"I:\ai\nft\output")
PLATES = {
    "Zoo City Streets": "03_APPROVED_CANON/approved_locations/zoo-city-streets/primary-reference.png",
    "School / Public Address Zone": "03_APPROVED_CANON/approved_locations/school-pa-zone/primary-reference.png",
    "Early-Fall Storm Streets and Routine Nodes": "03_APPROVED_CANON/approved_locations/zoo-city-streets/primary-reference.png",
    "Transit Announcement Hub": "03_APPROVED_CANON/approved_locations/transit-announcement-hub/primary-reference.png",
    "Old Relay Junction": "03_APPROVED_CANON/approved_locations/old-relay-junction/primary-reference.png",
}


# Clever is a NON-standard design (olive face, glasses, ponytail, pi-tee) that
# conflicts with the shared BASE (white face + punk studs), so he gets his own
# full text2img prompt instead of BASE + hair. Identity pilot passed 2026-07-18.
CLEVER_PROMPT = (
    "cute chibi cartoon MONKEY character (not a human), oversized round head, "
    "olive-tan khaki colored face and muzzle with two tiny nostrils and small mouth, "
    "huge white oval eyes with black dot pupils behind BIG round thick black-rimmed nerd glasses, "
    "brown hair swept to one side gathered into a high side ponytail tied with a pink hair-tie, "
    "round brown monkey ears, brown furry arms with brown mitten fists, long curled brown monkey tail, "
    "wearing a blue short-sleeve t-shirt with white raglan sleeves and a small red roundel on the chest, "
    "red shorts, brown feet, very thick uniform black outlines, flat solid colors no gradients, "
    "clean vector cartoon sticker look")
CLEVER_BG = "flat solid turquoise cyan background"


def _graph(prompt: str, seed: int, prefix: str) -> dict:
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "z_image_ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "7": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["4", 0], "negative": ["5", 0],
              "latent_image": ["6", 0], "seed": seed, "steps": 8, "cfg": 1.0,
              "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1.0}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 832, "height": 1216, "batch_size": 1}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": prefix}},
    }


def generate(name: str, pose: str, seed: int, prefix: str = "MZ-GEN") -> Path:
    """Queue a text2img character render and return the output PNG path."""
    if name == "clever":
        prompt = f"{CLEVER_PROMPT}, {pose}, {CLEVER_BG}, single character alone centered"
        g = _graph(prompt, seed, f"{prefix}/{name}_seed{seed}")
    else:
        g = build(name, CHARS[name], "gen", pose, seed, denoise=1.0, init=None)
        g["10"]["inputs"]["filename_prefix"] = f"{prefix}/{name}_seed{seed}"
    req = urllib.request.Request(f"http://{HOST}/prompt",
                                 data=json.dumps({"prompt": g}).encode(),
                                 headers={"Content-Type": "application/json"})
    file_prefix = f"{prefix}/{name}_seed{seed}"
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    pid = r["prompt_id"]
    if r.get("node_errors"):
        raise RuntimeError(r["node_errors"])

    def _by_prefix() -> Path | None:
        hits = sorted((OUT_DIR / prefix).glob(f"{name}_seed{seed}_*.png"))
        return hits[-1] if hits else None

    t0 = time.time()
    while time.time() - t0 < 300:
        h = json.loads(urllib.request.urlopen(f"http://{HOST}/history/{pid}", timeout=15).read())
        if pid in h and h[pid].get("status", {}).get("completed"):
            outs = h[pid].get("outputs", {})
            if outs.get("10", {}).get("images"):
                im = outs["10"]["images"][0]
                return OUT_DIR / im["subfolder"] / im["filename"]
            # execution_cached (identical prior prompt) -> outputs empty; find on disk
            p = _by_prefix()
            if p:
                return p
            raise RuntimeError(f"completed with no output image for {pid}")
        time.sleep(5)
    p = _by_prefix()
    if p:
        return p
    raise TimeoutError(f"render {pid} timed out")


def key_backdrop(src: Path) -> Image.Image:
    """Remove the flat card-colour backdrop by hue (border-connected), robust to
    the vignette. Returns an RGBA character with a clean alpha."""
    p = Image.open(src).convert("RGB")
    hsv = np.asarray(p.convert("HSV")).astype(np.int16)
    H, S = hsv[..., 0], hsv[..., 1]
    corner = np.concatenate([hsv[:20, :20].reshape(-1, 3), hsv[:20, -20:].reshape(-1, 3)])
    bh = int(np.median(corner[:, 0]))                       # backdrop hue (0-255)
    dh = np.minimum(np.abs(H - bh), 256 - np.abs(H - bh))   # circular hue distance
    bgmask = (dh < 20) & (S > 55)                           # same saturated hue = backdrop
    # character = NOT backdrop; keep the largest connected blob, fill, erode
    fg = ~bgmask
    lab, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1))
        fg = lab == (int(np.argmax(sizes)) + 1)
    fg = ndimage.binary_fill_holes(fg)
    fg = ndimage.binary_erosion(fg, iterations=2)
    alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    return Image.fromarray(np.dstack([np.asarray(p), np.asarray(alpha)]), "RGBA")


def composite(location: str, character: Image.Image, band_px=(1280, 540),
              scale_h=0.86, cx_frac=0.30) -> Image.Image:
    W, H = band_px
    plate = Image.open(FACTORY / PLATES[location]).convert("RGB").resize((1280, 720), Image.LANCZOS)
    top = int((720 - 720 * H / W * (W / 1280)) / 2) if False else 90
    bg = ImageEnhance.Brightness(plate.crop((0, top, 1280, top + H))).enhance(0.74).convert("RGBA")
    s = int(H * scale_h) / character.height
    ch = character.resize((max(1, int(character.width * s)), int(H * scale_h)), Image.LANCZOS)
    cx = int(W * cx_frac); fy = int(H * 0.99)
    px, py = cx - ch.width // 2, fy - ch.height
    bg = draw_contact_shadow(bg, foot_anchor_px=(cx, fy), character_width_px=ch.width)
    bg.alpha_composite(ch, (px, py))
    return bg.convert("RGB")


def compose_multi(location: str, chars: list[tuple[Image.Image, float, float]],
                  band_px=(1280, 540)) -> Image.Image:
    """Stage several matted characters on one darkened plate sharing a common
    ground line, back-to-front, each with a contact shadow. chars = list of
    (rgba_character, cx_frac, scale_h)."""
    W, H = band_px
    plate = Image.open(FACTORY / PLATES[location]).convert("RGB").resize((1280, 720), Image.LANCZOS)
    bg = ImageEnhance.Brightness(plate.crop((0, 90, 1280, 90 + H))).enhance(0.74).convert("RGBA")
    fy = int(H * 0.99)
    # farther (smaller) characters first so nearer ones overlap in front
    for ch, cx_frac, scale_h in sorted(chars, key=lambda c: c[2]):
        s = int(H * scale_h) / ch.height
        c2 = ch.resize((max(1, int(ch.width * s)), int(H * scale_h)), Image.LANCZOS)
        cx = int(W * cx_frac)
        bg = draw_contact_shadow(bg, foot_anchor_px=(cx, fy), character_width_px=c2.width)
        bg.alpha_composite(c2, (cx - c2.width // 2, fy - c2.height))
    return bg.convert("RGB")


def make_multi_panel(names: list[str], panel: dict, location: str, seed0: int, out: Path) -> dict:
    """Regenerate a multi-character panel: one bespoke pose per character, matted,
    staged on the shared plate with matched ground + shadows."""
    action = str(panel.get("action", "")).strip()
    emotion = str(panel.get("emotion", "")).strip()
    n = len(names)
    xs = {2: [0.27, 0.71], 3: [0.20, 0.50, 0.80]}.get(n, [(i + 1) / (n + 1) for i in range(n)])
    scales = {2: [0.80, 0.74], 3: [0.74, 0.80, 0.70]}.get(n, [0.76] * n)
    staged, meta = [], []
    for i, name in enumerate(names):
        facing = "facing right" if xs[i] < 0.5 else "facing left"
        pose = f"full body, {facing}, {action}, {emotion} expression, on a wet neon street at night"
        render = generate(name, pose, seed0 + i * 7)
        ch = key_backdrop(render)
        a = np.asarray(ch)[..., 3]
        staged.append((ch, xs[i], scales[i]))
        meta.append({"character": name, "corners_clear": bool((a[:8, :8] < 12).all() and (a[:8, -8:] < 12).all()),
                     "render": str(render)})
    panel_img = compose_multi(location, staged)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel_img.save(out)
    return {"panel": panel["source_panel_id"], "characters": names, "n": n, "staged": meta, "out": str(out)}


def make_panel(name: str, pose: str, location: str, seed: int, out: Path,
               band_px=(1280, 540), scale_h=0.86, cx_frac=0.30) -> dict:
    render = generate(name, pose, seed)
    ch = key_backdrop(render)
    opaque = round((np.asarray(ch)[..., 3] > 128).mean(), 3)
    corners_clear = bool((np.asarray(ch)[:8, :8, 3] < 12).all() and (np.asarray(ch)[:8, -8:, 3] < 12).all())
    panel = composite(location, ch, band_px, scale_h, cx_frac)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.save(out)
    return {"render": str(render), "opaque_frac": opaque, "corners_clear": corners_clear, "panel": str(out)}


ID_MAP = {f"MZ-CHAR-{c['seed'] % 1000:03d}": n for n, c in CHARS.items()}
ID_MAP["MZ-CHAR-CLEVER"] = "clever"   # Clever uses the dedicated CLEVER_PROMPT, not CHARS/BASE


def derive_pose(panel: dict, shot: str) -> str:
    action = str(panel.get("action", "")).strip().rstrip(".")
    emotion = str(panel.get("emotion", "")).strip().rstrip(".")
    framing = {"close": "head-and-shoulders close-up, large expressive face",
               "medium": "upper body, medium shot"}.get(shot, "full body")
    bits = [framing]
    if action:
        bits.append(action)
    if emotion:
        bits.append(f"{emotion} expression")
    bits.append("on a wet neon-lit rainy street at night, dramatic rim light")
    return ", ".join(bits)


def composite_shot(location: str, character: Image.Image, shot: str, band_px=(1280, 540)) -> Image.Image:
    """Shot-aware placement: close = big head-crop portrait; medium/other = grounded body."""
    if shot == "close":
        a = np.asarray(character)
        ys = np.where(a[..., 3].max(1) > 40)[0]
        if len(ys):
            top = ys[0]
            head_h = int((ys[-1] - top) * 0.62)          # head + shoulders
            character = character.crop((0, top, character.width, min(character.height, top + head_h)))
        return composite(location, character, band_px, scale_h=1.02, cx_frac=0.26)
    return composite(location, character, band_px, scale_h=0.86, cx_frac=0.28)


def make_panel_native(name: str, panel: dict, shot: str, location: str, seed: int, out: Path) -> dict:
    render = generate(name, derive_pose(panel, shot), seed)
    ch = key_backdrop(render)
    a = np.asarray(ch)[..., 3]
    panel_img = composite_shot(location, ch, shot)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel_img.save(out)
    return {"panel": panel["source_panel_id"], "character": name, "shot": shot,
            "opaque_frac": round((a > 128).mean(), 3),
            "corners_clear": bool((a[:8, :8] < 12).all() and (a[:8, -8:] < 12).all()),
            "render": str(render), "out": str(out)}


def run_batch(genesis_dir: Path, seed0: int = 55000) -> dict:
    """Regenerate bespoke art for single-character close/medium hero panels."""
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    out_dir = genesis_dir / "generated_art" / "panel_native"
    done, skipped = [], []
    i = 0
    for pg in plan["pages"]:
        for pa in pg["panels"]:
            cs = pa.get("characters") or []
            if len(cs) == 1 and pa["shot"] in ("close", "medium") and cs[0] in ID_MAP \
                    and pg["location"] in PLATES:
                name = ID_MAP[cs[0]]
                r = make_panel_native(name, pa, pa["shot"], pg["location"], seed0 + i,
                                      out_dir / f"{pa['source_panel_id']}.png")
                r["page"] = pg["page_number"]
                done.append(r)
                print(f"  regen p{pg['page_number']:02d} {pa['source_panel_id'].split('_',1)[1]} "
                      f"{name} {pa['shot']} -> corners_clear={r['corners_clear']}", flush=True)
                i += 1
            elif len(cs) == 1 and pa["shot"] in ("close", "medium"):
                skipped.append({"panel": pa["source_panel_id"], "reason": "no recipe (e.g. Clever) or plate"})
    manifest = {"regenerated": done, "skipped": skipped, "count": len(done)}
    (genesis_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (genesis_dir / "metadata" / "panel_native_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def run_full_batch(genesis_dir: Path, seed0: int = 60000, limit: int | None = None) -> dict:
    """Resumable: regenerate every character close/medium candidate panel (solo
    and multi) that has recipe characters and isn't already in panel_native.
    Wide/establishing panels are KEEP and skipped. Saves each panel as it goes."""
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    native = genesis_dir / "generated_art" / "panel_native"
    native.mkdir(parents=True, exist_ok=True)
    done, skipped, i = [], [], 0
    for pg in plan["pages"]:
        for pa in pg["panels"]:
            cs = pa.get("characters") or []
            pid = pa["source_panel_id"]
            out = native / f"{pid}.png"
            if out.exists():
                continue
            if not cs or pa["shot"] == "wide" or pg["location"] not in PLATES:
                continue
            names = [ID_MAP[c] for c in cs if c in ID_MAP]
            if len(names) != len(cs):
                skipped.append({"panel": pid, "reason": "unmapped character"}); continue
            try:
                if len(names) == 1:
                    r = make_panel_native(names[0], pa, pa["shot"], pg["location"], seed0 + i * 11, out)
                else:
                    r = make_multi_panel(names, pa, pg["location"], seed0 + i * 11, out)
                r["page"] = pg["page_number"]; done.append(r)
                print(f"  [{len(done)}] p{pg['page_number']:02d} {pid.split('_',1)[1]} {names} -> {out.name}", flush=True)
                i += 1
                if limit and len(done) >= limit:
                    return {"regenerated": done, "skipped": skipped, "count": len(done), "partial": True}
            except Exception as e:  # noqa: BLE001 - keep going; log the failure
                skipped.append({"panel": pid, "reason": str(e)[:120]})
                print(f"  FAIL {pid}: {e}", flush=True)
    return {"regenerated": done, "skipped": skipped, "count": len(done), "partial": False}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="regenerate all candidate panels (resumable)")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    gd = FACTORY / "GENESIS"
    m = run_full_batch(gd, limit=a.limit) if a.full else run_batch(gd)
    (gd / "metadata" / "panel_native_batch_log.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    print(f"\nRegenerated {m['count']} panels this run; skipped {len(m['skipped'])}.")
