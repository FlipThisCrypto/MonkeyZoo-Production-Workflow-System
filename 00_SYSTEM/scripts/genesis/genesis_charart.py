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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_char_refs import CHARS, build  # noqa: E402
from shadow import draw_contact_shadow   # noqa: E402
from relight import relight              # noqa: E402  natural scene integration
from compositor import sample_ambient_luma  # noqa: E402
import genesis_layout as gl              # noqa: E402  scene/page-custom slot geometry

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

# The matte keys the flat backdrop by HUE, so the backdrop must not share a hue
# with any part of the character. Moodz's canon card colour is warm ORANGE -- the
# same hue as brown monkey fur, so the key ate his body and left a floating head.
# Scarline's card colour is light GREY (too low-saturation to hue-key at all). For
# generation only, those two get a vivid chroma-green backdrop (no character wears
# green); their locked identity (hair + fur) is unchanged. The other four cards
# (pink/purple/teal/spring-green) are already hue-safe and keep their proven look.
CHROMA_BG = ("flat solid vivid chroma-key green screen background, evenly lit, "
             "no shadows, no gradient")
GREEN_BG_CHARS = {"moodz", "scarline"}


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
    """Queue a text2img character render and return the output PNG path. If a render
    for this (name, seed) already exists on disk, reuse it -- so re-compositing an
    existing panel at a new slot aspect is instant and never re-runs diffusion
    (delete the render file to force a fresh render)."""
    existing = sorted((OUT_DIR / prefix).glob(f"{name}_seed{seed}_*.png"))
    if existing:
        return existing[-1]
    if name == "clever":
        prompt = f"{CLEVER_PROMPT}, {pose}, {CLEVER_BG}, single character alone centered"
        g = _graph(prompt, seed, f"{prefix}/{name}_seed{seed}")
    else:
        spec = CHARS[name]
        if name in GREEN_BG_CHARS:                    # hue-safe backdrop for a clean matte
            spec = {**spec, "bg": CHROMA_BG}
        g = build(name, spec, "gen", pose, seed, denoise=1.0, init=None)
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
    # character = NOT backdrop. Close first so any thin backdrop-hued sliver the key
    # nicked out of the body (e.g. a shaded neck) is bridged before we pick a blob --
    # otherwise the head can split off and "keep largest blob" leaves a floating head.
    fg = ndimage.binary_closing(~bgmask, iterations=3)
    lab, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1))
        fg = lab == (int(np.argmax(sizes)) + 1)
    fg = ndimage.binary_fill_holes(fg)
    # Z-Image often paints a solid GROUND PLATFORM under a standing character; it is
    # not the backdrop hue, so it survives the key and fuses to the feet. A REAL
    # floor spans nearly the full width AND reaches the very bottom of the figure, so
    # cut only the contiguous near-full-width band running UP from the bottom-most
    # opaque row. Narrow feet stop the scan immediately (nothing cut); a wide
    # elbows-out hip row mid-body is never reached -- that over-eager cut used to
    # slice the legs off (Moodz/Neonblue) or the head (large framing).
    roww = fg.sum(1)
    ys = np.where(roww > 0)[0]
    if len(ys):
        W = fg.shape[1]
        r = int(ys[-1])
        cut = False
        while r >= 0 and roww[r] > 0.94 * W:
            fg[r, :] = False; cut = True; r -= 1
        if cut:
            lab, n = ndimage.label(fg)                    # keep the character blob
            if n:
                sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1))
                fg = lab == (int(np.argmax(sizes)) + 1)
    # erode enough that the soft alpha edge sits INSIDE the black toon outline, so no
    # backdrop-tinted fringe survives to read as a cut-out halo; keep only a hair of blur.
    fg = ndimage.binary_erosion(fg, iterations=3)
    alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
    return Image.fromarray(np.dstack([np.asarray(p), np.asarray(alpha)]), "RGBA")


def _plate_band(location: str, band_px) -> Image.Image:
    """Darkened location plate cover-cropped to the slot's aspect (any shape, not
    just a wide band): keeps the street/ground low and trims symmetrically, so a
    tall 2-up cell keeps full height while a wide band trims only sky."""
    W, H = band_px
    plate = Image.open(FACTORY / PLATES[location]).convert("RGB")
    s = max(W / plate.width, H / plate.height)
    rw, rh = max(W, round(plate.width * s)), max(H, round(plate.height * s))
    plate = plate.resize((rw, rh), Image.LANCZOS)
    x = (rw - W) // 2
    y = int((rh - H) * 0.42)            # trim a little more sky than floor
    crop = plate.crop((x, y, x + W, y + H))
    return ImageEnhance.Brightness(crop).enhance(0.72).convert("RGBA")


def _fit_char_size(cw: int, chh: int, H: int, scale_h: float, max_w: float | None = None) -> tuple[int, int]:
    """Target (w, h) for a character: size by frame height (scale_h), but if that
    would exceed max_w (its horizontal share when several are staged side by side),
    clamp to max_w and keep aspect -- so characters never overlap or bloat to fill a
    tall/narrow cell."""
    th = max(1, int(H * scale_h))
    tw = max(1, round(cw * th / chh))
    if max_w and tw > max_w:
        tw = max(1, int(max_w))
        th = max(1, round(chh * tw / cw))
    return tw, th


def _place_char(bg: Image.Image, ch: Image.Image, cx: int, fy: int, H: int, scale_h: float,
                key=(150, 225, 255), fill=(225, 90, 190), max_w: float | None = None) -> Image.Image:
    """Scale, RELIGHT to the scene (exposure match + neon key/fill tint + rim),
    contact-shadow, and composite -- so the character sits IN the scene, not on
    it. This is what separates a naturally integrated panel from a paste."""
    tw, th = _fit_char_size(ch.width, ch.height, H, scale_h, max_w)
    c2 = ch.resize((tw, th), Image.LANCZOS)
    # sample the scene brightness where the body sits and match the character to it
    ambient = sample_ambient_luma(bg.convert("RGB"), (cx, max(0, fy - c2.height // 2)))
    key_side = cx < bg.width / 2                 # neon key faces the frame centre
    # a SUBTLE rim/tint reads as scene lighting; a strong all-around cyan rim reads as
    # a cut-out halo (owner/QA flagged it as a matte edge), so keep both gentle.
    c2 = relight(c2, ambient_luma=ambient, key_color=key, fill_color=fill,
                 key_on_high_side=key_side, tint_strength=0.20, rim_strength=0.16)
    bg = draw_contact_shadow(bg, foot_anchor_px=(cx, fy), character_width_px=c2.width)
    bg.alpha_composite(c2, (cx - c2.width // 2, fy - c2.height))
    return bg


def composite(location: str, character: Image.Image, band_px=(1280, 540),
              scale_h=0.86, cx_frac=0.30) -> Image.Image:
    W, H = band_px
    bg = _plate_band(location, band_px)
    bg = _place_char(bg, character, int(W * cx_frac), int(H * 0.99), H, scale_h, max_w=W * 0.96)
    return bg.convert("RGB")


def compose_multi(location: str, chars: list[tuple[Image.Image, float, float]],
                  band_px=(1280, 540)) -> Image.Image:
    """Stage several matted characters on one darkened plate: each relit to the
    scene, sharing a common ground line, back-to-front so nearer ones overlap.
    Each character is width-limited to its horizontal share (the gap to its nearest
    neighbour) so they read side by side and never overlap or bloat -- essential in
    a narrow/portrait 2-up cell where sizing by height alone would collide them."""
    W, H = band_px
    bg = _plate_band(location, band_px)
    fy = int(H * 0.99)
    xs = sorted(c[1] for c in chars)
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)] or [1.0]
    max_w = min(gaps) * W * 0.98                        # nearest-neighbour spacing
    for ch, cx_frac, scale_h in sorted(chars, key=lambda c: c[2]):  # farther first
        bg = _place_char(bg, ch, int(W * cx_frac), fy, H, scale_h, max_w=max_w)
    return bg.convert("RGB")


def make_multi_panel(names: list[str], panel: dict, location: str, seed0: int, out: Path,
                     band_px=(1280, 540)) -> dict:
    """Regenerate a multi-character panel: one bespoke pose per character, matted,
    staged on the shared plate (at the slot aspect) with matched ground + shadows."""
    action = str(panel.get("action", "")).strip()
    emotion = str(panel.get("emotion", "")).strip()
    n = len(names)
    xs = {2: [0.27, 0.71], 3: [0.20, 0.50, 0.80]}.get(n, [(i + 1) / (n + 1) for i in range(n)])
    scales = {2: [0.80, 0.74], 3: [0.74, 0.80, 0.70]}.get(n, [0.76] * n)
    staged, meta = [], []
    for i, name in enumerate(names):
        facing = "facing right" if xs[i] < 0.5 else "facing left"
        pose = (f"full body head to feet, standing, {facing}, {action}, {emotion} expression, "
                "isolated on a plain flat backdrop, no ground, no floor, no shadow")
        render = generate(name, pose, seed0 + i * 7)
        ch = key_backdrop(render)
        a = np.asarray(ch)[..., 3]
        staged.append((ch, xs[i], scales[i]))
        meta.append({"character": name, "corners_clear": bool((a[:8, :8] < 12).all() and (a[:8, -8:] < 12).all()),
                     "render": str(render)})
    panel_img = compose_multi(location, staged, band_px=band_px)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel_img.save(out)
    return {"panel": panel["source_panel_id"], "characters": names, "n": n,
            "band_px": list(band_px), "staged": meta, "out": str(out)}


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
    # NO scene/ground cue: a "street/floor" cue makes Z-Image paint a ground plane
    # coplanar with the feet, which the matte then can't separate from the legs. Keep
    # the figure isolated on a plain backdrop; scene lighting is added later by relight.
    bits.append("isolated on a plain flat backdrop, no ground, no floor, no cast shadow")
    return ", ".join(bits)


def composite_shot(location: str, character: Image.Image, shot: str, band_px=(1280, 540)) -> Image.Image:
    """Shot- and slot-aware placement. In a narrow/portrait slot the figure is
    centred and fills more of the frame; in a wide band it is offset to leave
    balloon room. Close beats keep head-through-torso (never an extreme face crop
    -- owner note: 'closeups too much')."""
    W, H = band_px
    narrow = W / H < 1.15                             # 2-up / portrait cell
    cx = 0.46 if narrow else 0.30
    if shot == "close":
        a = np.asarray(character)
        ys = np.where(a[..., 3].max(1) > 40)[0]
        if len(ys):
            top = ys[0]
            crop_h = int((ys[-1] - top) * 0.82)          # head + torso, not just face
            character = character.crop((0, top, character.width, min(character.height, top + crop_h)))
        return composite(location, character, band_px, scale_h=0.92 if narrow else 0.90, cx_frac=cx)
    return composite(location, character, band_px, scale_h=0.88 if narrow else 0.82, cx_frac=cx)


def make_panel_native(name: str, panel: dict, shot: str, location: str, seed: int, out: Path,
                      band_px=(1280, 540)) -> dict:
    render = generate(name, derive_pose(panel, shot), seed)
    ch = key_backdrop(render)
    a = np.asarray(ch)[..., 3]
    panel_img = composite_shot(location, ch, shot, band_px=band_px)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel_img.save(out)
    return {"panel": panel["source_panel_id"], "character": name, "shot": shot,
            "band_px": list(band_px), "opaque_frac": round((a > 128).mean(), 3),
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
    and multi) that has recipe characters and isn't already in panel_native. Each
    panel is composited at ITS page-layout slot aspect (from genesis_layout), so
    bespoke art is truly panel-native -- varied shapes, no re-crop at assembly.
    Wide/establishing panels are KEEP and skipped. Saves each panel as it goes."""
    plan = json.loads((genesis_dir / "GENESIS_LAYOUT_PLAN.json").read_text(encoding="utf-8"))
    native = genesis_dir / "generated_art" / "panel_native"
    native.mkdir(parents=True, exist_ok=True)
    done, skipped, i = [], [], 0
    for pg in plan["pages"]:
        rects = gl.synth_page_rects(pg["panels"], pg["page_number"])
        for pa, rect in zip(pg["panels"], rects):
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
            band_px = gl.slot_band_px(rect)
            try:
                if len(names) == 1:
                    r = make_panel_native(names[0], pa, pa["shot"], pg["location"], seed0 + i * 11, out, band_px=band_px)
                else:
                    r = make_multi_panel(names, pa, pg["location"], seed0 + i * 11, out, band_px=band_px)
                r["page"] = pg["page_number"]; done.append(r)
                print(f"  [{len(done)}] p{pg['page_number']:02d} {pid.split('_',1)[1]} {names} "
                      f"{band_px[0]}x{band_px[1]} -> {out.name}", flush=True)
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
