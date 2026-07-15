#!/usr/bin/env python3
"""Compose draft preferred panels for Issue 01 from approved location/character refs.

ONE THING: finish art_production evidence for all 24 panels so QA can run.
These are production *drafts* (composites), not final lettered comic art.
"""
from __future__ import annotations

import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "MZ-2026-08-01"
FOLDER = ROOT / "02_MONTHLY_ISSUES" / "2026-08_Issue_01"
BASE = "http://127.0.0.1:8765"
STAGING = FOLDER / "generated_art" / "draft_composites"
W, H = 1280, 960


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def location_slug(name: str) -> str | None:
    key = "".join(ch.lower() if ch.isalnum() else " " for ch in name).split()
    joined = "-".join(key)
    mapping = {
        "festival-grounds": "festival-grounds",
        "festival-main-stage": "festival-main-stage",
        "festival-service-corridor": "festival-service-corridor",
        "festival-control-node": "festival-control-node",
    }
    for slug in mapping:
        if slug in joined or joined.replace(" ", "-") == slug:
            return slug
    # fuzzy
    if "main" in joined and "stage" in joined:
        return "festival-main-stage"
    if "service" in joined or "corridor" in joined:
        return "festival-service-corridor"
    if "control" in joined:
        return "festival-control-node"
    if "festival" in joined or "grounds" in joined:
        return "festival-grounds"
    return "festival-grounds"


def open_rgb(path: Path, size=None) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    return img


def char_ref(cid: str) -> Path | None:
    bible_root = ROOT / "character-bibles" / cid / "references" / "primary"
    for name in ("primary-reference.png", "primary-reference.webp", "primary-reference.jpg"):
        p = bible_root / name
        if p.is_file():
            return p
    # search any primary
    prim = ROOT / "character-bibles" / cid / "references" / "primary"
    if prim.is_dir():
        files = list(prim.glob("primary-reference.*"))
        if files:
            return files[0]
    return None


def compose(panel: dict, plan_panel: dict) -> Path:
    loc_name = plan_panel.get("location") or panel.get("environment") or "Festival Grounds"
    slug = location_slug(loc_name)
    bg_path = ROOT / "03_APPROVED_CANON" / "approved_locations" / slug / "primary-reference.png"
    if bg_path.is_file():
        canvas = open_rgb(bg_path, (W, H))
    else:
        canvas = Image.new("RGB", (W, H), (20, 24, 40))
    # darken slightly for readability of overlays
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    canvas = Image.blend(canvas, dark, 0.25)

    chars = plan_panel.get("characters") or panel.get("character_tokens") or []
    # place up to 4 character refs along bottom
    slots = min(4, len(chars))
    if slots:
        box_w, box_h = 220, 220
        gap = 24
        total_w = slots * box_w + (slots - 1) * gap
        x0 = (W - total_w) // 2
        y0 = H - box_h - 80
        for i, cid in enumerate(chars[:slots]):
            ref = char_ref(cid)
            x = x0 + i * (box_w + gap)
            if ref and ref.is_file():
                try:
                    face = open_rgb(ref, (box_w, box_h))
                except Exception:
                    face = Image.new("RGB", (box_w, box_h), (60, 60, 80))
            else:
                face = Image.new("RGB", (box_w, box_h), (60, 60, 80))
            # rounded-ish border frame
            frame = Image.new("RGB", (box_w + 8, box_h + 8), (255, 214, 10))
            canvas.paste(frame, (x - 4, y0 - 4))
            canvas.paste(face, (x, y0))

    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
        font_sm = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
        font_sm = font

    pid = panel.get("panel_id") or plan_panel.get("panel_id")
    action = (plan_panel.get("action") or panel.get("pose") or "")[:140]
    # banner
    draw.rectangle((0, 0, W, 70), fill=(8, 10, 16))
    draw.text((24, 18), f"{pid}  ·  DRAFT COMPOSITE", fill=(255, 214, 10), font=font)
    # action strip
    draw.rectangle((0, H - 70, W, H), fill=(8, 10, 16))
    draw.text((24, H - 52), action, fill=(230, 234, 240), font=font_sm)
    draw.text((24, H - 28), f"Location: {loc_name}", fill=(160, 170, 190), font=font_sm)

    STAGING.mkdir(parents=True, exist_ok=True)
    out = STAGING / f"{pid}.png"
    canvas.save(out, "PNG")
    return out


def multipart_import(panel_id: str, png_path: Path):
    boundary = "----BananaLabBoundaryIssue01"
    content = png_path.read_bytes()
    chunks = []
    chunks.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{png_path.name}\"\r\nContent-Type: image/png\r\n\r\n".encode()
    )
    chunks.append(content)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"provider\"\r\n\r\ndraft_composite\r\n".encode())
    chunks.append(f"--{boundary}--\r\n".encode())
    data = b"".join(chunks)
    url = f"{BASE}/api/issues/{ISSUE}/art-queue/{panel_id}/attempts"
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return e.code, payload


def req_json(method: str, path: str, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return e.code, payload


def main() -> int:
    pack = load_json(FOLDER / "art_prompt_pack.json")
    plan = load_json(FOLDER / "page_panel_plan.json")
    plan_by_id = {}
    for page in plan.get("pages", []):
        for panel in page.get("panels", []):
            plan_by_id[panel["panel_id"]] = panel

    # ensure queue
    code, queue, = req_json("POST", f"/api/issues/{ISSUE}/art-queue/build", {})
    print("queue_build", code, "items", len((queue or {}).get("items") or []))

    ok = 0
    fail = []
    for panel in pack["panels"]:
        pid = panel["panel_id"]
        plan_panel = plan_by_id.get(pid, {})
        path = compose(panel, plan_panel)
        status, record = multipart_import(pid, path)
        if status not in (200, 201):
            fail.append((pid, status, record))
            print("FAIL import", pid, status, record)
            continue
        aid = record.get("attempt_id")
        code, sel = req_json("POST", f"/api/issues/{ISSUE}/art-queue/{pid}/attempts/{aid}/select", {})
        if code != 200:
            fail.append((pid, code, sel))
            print("FAIL select", pid, code, sel)
            continue
        ok += 1
        print("OK", pid)

    print(f"selected={ok}/24 fails={len(fail)}")
    if fail:
        return 1

    # check if can advance art_production
    code, adv = req_json("POST", f"/api/issues/{ISSUE}/advance", {"stage": "art_production"})
    print("advance", code, adv)
    code, wf = req_json("GET", f"/api/issues/{ISSUE}/workflow")
    print("stage", (wf or {}).get("active_stage"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
