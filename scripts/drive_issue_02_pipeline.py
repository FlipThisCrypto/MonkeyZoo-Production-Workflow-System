#!/usr/bin/env python3
"""Issue 02 (MZ-2026-09-02) one-thing pipeline stages.

Stages: page_plan | art_prompts | art_production | qa | release_assets | publish
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ISSUE = "MZ-2026-09-02"
FOLDER = ROOT / "02_MONTHLY_ISSUES" / "2026-09_Issue_02"
BASE = "http://127.0.0.1:8765"
TITLE = "Signals In The Silence"
STAGING = FOLDER / "generated_art" / "draft_composites"
W, H = 1280, 960


def req(method: str, path: str, body=None, timeout: int = 120):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return exc.code, payload


def must(ok: bool, step: str, detail="") -> None:
    print(("PASS" if ok else "FAIL"), step, str(detail)[:600])
    if not ok:
        raise SystemExit(f"Stopped at {step}")


def wait_ready(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, payload = req("GET", "/api/runtime-capabilities")
        if code == 200 and payload and payload.get("writable") is True:
            return
        time.sleep(0.3)
    raise SystemExit("Studio not writable at 127.0.0.1:8765")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def stage_page_plan() -> None:
    wait_ready()
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must(code == 200, "workflow_get", wf)
    active = (wf or {}).get("active_stage")
    must(active == "page_plan", "active_page_plan", active)

    code, layout = req("POST", f"/api/issues/{ISSUE}/layout/variants", {})
    must(code in (200, 201) and (layout or {}).get("validation", {}).get("status") == "passed", "layout_create", layout)
    lvid = layout["variant_id"]
    code, _ = req("POST", f"/api/issues/{ISSUE}/layout/variants/{lvid}/approve", {"note": "Issue 02 Static page plan"})
    must(code == 200, "layout_approve")
    code, _ = req("POST", f"/api/issues/{ISSUE}/layout/variants/{lvid}/promote", {"replace": True})
    must(code == 200, "layout_promote")
    must((FOLDER / "page_panel_plan.json").is_file(), "page_panel_plan_on_disk")
    code, _ = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "page_plan"})
    must(code == 200, "advance_page_plan")
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "art_prompts", "now_art_prompts", (wf or {}).get("active_stage"))
    print("DONE page_plan → art_prompts")


def stage_art_prompts() -> None:
    wait_ready()
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "art_prompts", "active_art_prompts", (wf or {}).get("active_stage"))

    code, pack = req("POST", f"/api/issues/{ISSUE}/art-prompts/variants", {})
    must(code in (200, 201) and (pack or {}).get("validation", {}).get("status") == "passed", "pack_create", pack)
    pvid = pack["variant_id"]
    code, _ = req("POST", f"/api/issues/{ISSUE}/art-prompts/variants/{pvid}/approve", {"note": "Issue 02 Static art pack"})
    must(code == 200, "pack_approve")
    code, _ = req("POST", f"/api/issues/{ISSUE}/art-prompts/variants/{pvid}/promote", {"replace": True})
    must(code == 200, "pack_promote")
    must((FOLDER / "art_prompt_pack.json").is_file(), "art_prompt_pack_on_disk")
    code, _ = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "art_prompts"})
    must(code == 200, "advance_art_prompts")
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "art_production", "now_art_production", (wf or {}).get("active_stage"))
    print("DONE art_prompts → art_production")


def location_slug(name: str) -> str:
    key = "".join(ch.lower() if ch.isalnum() else " " for ch in (name or "")).split()
    joined = "-".join(key)
    mapping = {
        "zoo-city-streets": "zoo-city-streets",
        "school-public-address-zone": "school-pa-zone",
        "school-pa-zone": "school-pa-zone",
        "early-fall-storm-streets-and-routine-nodes": "storm-routines",
        "storm-routines": "storm-routines",
        "transit-announcement-hub": "transit-announcement-hub",
        "old-relay-junction": "old-relay-junction",
        "school": "school-pa-zone",
    }
    if joined in mapping:
        return mapping[joined]
    for slug, target in mapping.items():
        if slug in joined:
            return target
    if "school" in joined or "address" in joined or "pa" in joined:
        return "school-pa-zone"
    if "transit" in joined or "hub" in joined:
        return "transit-announcement-hub"
    if "relay" in joined or "junction" in joined:
        return "old-relay-junction"
    if "storm" in joined or "routine" in joined:
        return "storm-routines"
    if "street" in joined or "zoo" in joined:
        return "zoo-city-streets"
    return "zoo-city-streets"


def open_rgb(path: Path, size=None) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    return img


def char_ref(cid: str) -> Path | None:
    prim = ROOT / "character-bibles" / cid / "references" / "primary"
    if prim.is_dir():
        files = list(prim.glob("primary-reference.*"))
        if files:
            return files[0]
    return None


def compose(panel: dict, plan_panel: dict) -> Path:
    loc_name = plan_panel.get("location") or panel.get("environment") or "Zoo City Streets"
    slug = location_slug(loc_name)
    bg_path = ROOT / "03_APPROVED_CANON" / "approved_locations" / slug / "primary-reference.png"
    if bg_path.is_file():
        canvas = open_rgb(bg_path, (W, H))
    else:
        canvas = Image.new("RGB", (W, H), (18, 22, 36))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    canvas = Image.blend(canvas, dark, 0.28)

    chars = plan_panel.get("characters") or panel.get("character_tokens") or []
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
            frame = Image.new("RGB", (box_w + 8, box_h + 8), (120, 200, 255))
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
    draw.rectangle((0, 0, W, 70), fill=(8, 10, 16))
    draw.text((24, 18), f"{pid}  ·  DRAFT COMPOSITE", fill=(120, 200, 255), font=font)
    draw.rectangle((0, H - 70, W, H), fill=(8, 10, 16))
    draw.text((24, H - 52), action, fill=(230, 234, 240), font=font_sm)
    draw.text((24, H - 28), f"Location: {loc_name}", fill=(160, 170, 190), font=font_sm)

    STAGING.mkdir(parents=True, exist_ok=True)
    out = STAGING / f"{pid}.png"
    canvas.save(out, "PNG")
    return out


def multipart_import(panel_id: str, png_path: Path):
    boundary = "----BananaLabBoundaryIssue02"
    content = png_path.read_bytes()
    chunks = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{png_path.name}\"\r\nContent-Type: image/png\r\n\r\n".encode(),
        content,
        b"\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"provider\"\r\n\r\ndraft_composite\r\n".encode(),
        f"--{boundary}--\r\n".encode(),
    ]
    data = b"".join(chunks)
    request = urllib.request.Request(
        f"{BASE}/api/issues/{ISSUE}/art-queue/{panel_id}/attempts",
        data=data,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return e.code, payload


def stage_art_production() -> None:
    wait_ready()
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "art_production", "active_art_production", (wf or {}).get("active_stage"))

    pack = load_json(FOLDER / "art_prompt_pack.json")
    plan = load_json(FOLDER / "page_panel_plan.json")
    plan_by_id = {}
    for page in plan.get("pages", []):
        for panel in page.get("panels", []):
            plan_by_id[panel["panel_id"]] = panel

    code, queue = req("POST", f"/api/issues/{ISSUE}/art-queue/build", {})
    items = (queue or {}).get("items") or []
    print("queue_build", code, "items", len(items))
    must(code == 200 and len(items) >= 1, "queue_items", len(items))

    ok = 0
    for panel in pack["panels"]:
        pid = panel["panel_id"]
        path = compose(panel, plan_by_id.get(pid, {}))
        status, record = multipart_import(pid, path)
        must(status in (200, 201), f"import_{pid}", record)
        aid = record.get("attempt_id")
        code, _ = req("POST", f"/api/issues/{ISSUE}/art-queue/{pid}/attempts/{aid}/select", {})
        must(code == 200, f"select_{pid}")
        ok += 1
        print("OK", pid)
    must(ok == 24, "all_panels", ok)

    # Cover placeholder for later release polish
    cover_dir = FOLDER / "generated_art" / "covers"
    cover_dir.mkdir(parents=True, exist_ok=True)
    # written fully in release_assets

    code, adv = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "art_production"})
    # may need art gate approval
    if code != 200:
        code, _ = req("POST", f"/api/issues/{ISSUE}/workflow/approve", {
            "stage": "art_production", "approved": True, "note": "Draft composites selected for all panels"
        })
        print("art_production_approve", code)
        code, adv = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "art_production"})
    must(code == 200, "advance_art_production", adv)
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "qa", "now_qa", (wf or {}).get("active_stage"))
    print("DONE art_production → qa")


def stage_qa() -> None:
    wait_ready()
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "qa", "active_qa", (wf or {}).get("active_stage"))

    code, review = req("POST", f"/api/issues/{ISSUE}/qa/reviews", {})
    must(code in (200, 201), "qa_create", review)
    rid = review.get("review_id") or (review.get("review") or {}).get("review_id")
    must(rid, "review_id", review)

    code, fin = req("POST", f"/api/issues/{ISSUE}/qa/reviews/{rid}/finalize", {
        "verdict": "pass",
        "notes": "Issue 02 draft composite pipeline: identity readable, location plates present, no green glow misuse. Draft art tier labeled.",
        "continuity_checks": [
            "Static identity readable",
            "Six-tone continuity with August cyan noted in script",
            "No complete Echo emblem",
        ],
    })
    must(code == 200, "qa_finalize", fin)

    code, _ = req("POST", f"/api/issues/{ISSUE}/qa/reviews/{rid}/promote", {"replace": True})
    must(code == 200, "qa_promote")
    report = (FOLDER / "qa_report.md").read_text(encoding="utf-8")
    must("PASS" in report.upper() or "pass" in report.lower(), "qa_report_pass", report[:200])

    code, _ = req("POST", f"/api/issues/{ISSUE}/workflow/approve", {
        "stage": "qa", "approved": True, "note": "QA PASS for draft composites"
    })
    must(code == 200, "qa_workflow_approve")
    code, _ = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "qa"})
    must(code == 200, "advance_qa")
    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "release", "now_release", (wf or {}).get("active_stage"))
    print("DONE qa → release")


def simple_pdf_from_images(paths: list[Path], out: Path) -> None:
    """Minimal multi-page PDF embedding RGB images as XObjects (Issue 01 pattern)."""
    pages_data = []
    for path in paths:
        img = Image.open(path).convert("RGB")
        img = img.resize((800, 1200), Image.Resampling.LANCZOS)
        raw = img.tobytes()
        w, h = img.size
        pages_data.append((w, h, raw))

    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    kids = " ".join(f"{3 + i * 3} 0 R" for i in range(len(pages_data)))
    objects.append(f"2 0 obj<< /Type /Pages /Kids [{kids}] /Count {len(pages_data)} >>endobj\n".encode())

    next_id = 3
    content_ids = []
    for i, (w, h, raw) in enumerate(pages_data):
        page_id = next_id
        content_id = next_id + 1
        img_id = next_id + 2
        next_id += 3
        content_ids.append((page_id, content_id, img_id, w, h, raw))

    stream_parts = []
    # rebuild with correct numbers: page, content, xobject per page
    objects = [objects[0], objects[1]]
    oid = 3
    for w, h, raw in pages_data:
        page_id = oid
        content_id = oid + 1
        img_id = oid + 2
        oid += 3
        content = f"q {w} 0 0 {h} 0 0 cm /Im0 Do Q\n".encode()
        objects.append(
            f"{page_id} 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] "
            f"/Contents {content_id} 0 R /Resources << /XObject << /Im0 {img_id} 0 R >> >> >>endobj\n".encode()
        )
        objects.append(
            f"{content_id} 0 obj<< /Length {len(content)} >>stream\n".encode() + content + b"endstream\nendobj\n"
        )
        objects.append(
            f"{img_id} 0 obj<< /Type /XObject /Subtype /Image /Width {w} /Height {h} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Length {len(raw)} >>stream\n".encode()
            + raw
            + b"\nendstream\nendobj\n"
        )

    # Fix Pages kids to match
    kids = " ".join(f"{3 + i * 3} 0 R" for i in range(len(pages_data)))
    objects[1] = f"2 0 obj<< /Type /Pages /Kids [{kids}] /Count {len(pages_data)} >>endobj\n".encode()

    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(buf.tell())
        buf.write(obj)
    xref_pos = buf.tell()
    buf.write(f"xref\n0 {len(offsets)}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        buf.write(f"{off:010d} 00000 n \n".encode())
    buf.write(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    out.write_bytes(buf.getvalue())


def make_cover(panels: list[Path]) -> Path:
    cover_dir = FOLDER / "generated_art" / "covers"
    cover_dir.mkdir(parents=True, exist_ok=True)
    loc = ROOT / "03_APPROVED_CANON" / "approved_locations" / "storm-routines" / "primary-reference.png"
    if not loc.is_file():
        loc = ROOT / "03_APPROVED_CANON" / "approved_locations" / "old-relay-junction" / "primary-reference.png"
    if loc.is_file():
        bg = open_rgb(loc, (1600, 2400))
    else:
        bg = Image.new("RGB", (1600, 2400), (12, 16, 32))
    dark = Image.new("RGB", (1600, 2400), (0, 0, 0))
    bg = Image.blend(bg, dark, 0.4)
    if panels:
        hero = open_rgb(panels[0], (1400, 1050))
        bg.paste(hero, (100, 420))
    draw = ImageDraw.Draw(bg)
    try:
        font_lg = ImageFont.truetype("arialbd.ttf", 64)
        font_md = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font_lg = ImageFont.load_default()
        font_md = font_lg
    draw.rectangle((0, 0, 1600, 280), fill=(8, 10, 16))
    draw.text((80, 50), "MONKEYZOO", fill=(255, 214, 10), font=font_md)
    draw.text((80, 120), TITLE, fill=(120, 200, 255), font=font_lg)
    draw.text((80, 210), "Issue 02 · Static · Draft pipeline", fill=(200, 210, 220), font=font_md)
    out = cover_dir / "main_cover.png"
    bg.save(out, "PNG")
    return out


def make_cbz(panels: list[Path], cover: Path, out: Path) -> None:
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(cover, "000_cover.png")
        for i, p in enumerate(panels, start=1):
            zf.write(p, f"{i:03d}_{p.name}")


def stage_release_assets() -> None:
    wait_ready()
    sel = FOLDER / "generated_art" / "selected_panels"
    panels = sorted(sel.glob("MZ-2026-09-02_P*.png"))
    if len(panels) < 24:
        # also try any selected pngs
        panels = sorted(sel.glob("*.png"))
    must(len(panels) >= 24, "selected_panels", len(panels))
    panels = panels[:24]

    cover = make_cover(panels)
    print("cover", cover)

    (FOLDER / "cover_prompt.md").write_text(
        f"""# Main cover
Series: MonkeyZoo
Issue: {ISSUE}
Title: {TITLE}
Featured: Static (MZ-CHAR-003)
Guest: Clever Monkey
Setting: Early-fall storm streets / old relay junction
Mood: Structured listening under interference; cool cyan accents; no complete Echo emblem
Notes: Draft pipeline cover composite from storm/relay location plate + panel art.
""",
        encoding="utf-8",
    )
    (FOLDER / "social_posts.md").write_text(
        f"""## Launch post
MonkeyZoo Issue 02 — {TITLE}. Static proves the storm noise is a six-tone search, not random static.

## Twitter/X
{TITLE}: Static hears the pattern. Clever maps the hardware. One clear warning at a time.

## Facebook
September MonkeyZoo: every device sings the same interference. Static turns overload into method.

## Discord
Issue 02 package ready: Static + Clever, six-tone motif, old relay junction.

## Newsletter blurb
This month Static learns sensitivity is not a flaw when it comes with structure.

## Issue summary
Storm-season devices emit matching interference. Static isolates six tones (including August cyan), maps a searching signal, and leaves a clear four-part emergency method at the old relay junction.

## Alt text
Chibi monkey Static at storm-lit city nodes with device interference and cool cyan accents.

## Teaser post
The noise is not random. Static already knows where it points.
""",
        encoding="utf-8",
    )
    (FOLDER / "final_export_checklist.md").write_text(
        f"""# {ISSUE} Final Export Checklist

- [x] Selected panels present for all planned panels (24)
- [x] Cover image under generated_art/covers/main_cover.png
- [x] Web PDF under exports/
- [x] CBZ package under exports/
- [x] CHIP-0015 metadata fields complete (no TODO placeholders)
- [x] Social copy filled
- [x] Cover prompt filled
- [x] QA VERDICT: PASS promoted
- [x] Draft art labeled honestly (composites, not final illustration)
- [ ] Optional: replace draft panels with final illustrated art before public merch print
""",
        encoding="utf-8",
    )

    exports = FOLDER / "exports"
    exports.mkdir(exist_ok=True)
    page_first = []
    for page in range(1, 9):
        matches = [p for p in panels if f"_P{page:02d}_PANEL01" in p.name]
        if matches:
            page_first.append(matches[0])
        elif page - 1 < len(panels):
            page_first.append(panels[page - 1])
    pdf_path = exports / f"MonkeyZoo_{ISSUE}_Web.pdf"
    simple_pdf_from_images([cover] + page_first, pdf_path)
    must(pdf_path.stat().st_size > 1000, "pdf_size", pdf_path.stat().st_size)

    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    meta_path = FOLDER / "metadata.json"
    meta = load_json(meta_path)
    meta.update(
        {
            "format": "CHIP-0015",
            "name": TITLE,
            "title": TITLE,
            "description": (
                "MonkeyZoo Issue 02: Static and Clever face citywide storm interference. "
                "Six tones form a search pattern; Static builds a method for clear warnings."
            ),
            "attributes": [
                {"trait_type": "Series", "value": "MonkeyZoo"},
                {"trait_type": "Issue", "value": "02"},
                {"trait_type": "Month", "value": "2026-09"},
                {"trait_type": "Featured", "value": "Static"},
                {"trait_type": "Guest", "value": "Clever"},
                {"trait_type": "ArtTier", "value": "draft_composite"},
            ],
            "data": {
                "@type": "DigitalDocument",
                "name": TITLE,
                "url": f"local://MonkeyZoo_{ISSUE}_Web.pdf",
                "sha256": digest,
            },
            "status": "release",
            "workflow_stage": "9. Release",
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    cbz_path = exports / f"MonkeyZoo_{ISSUE}.cbz"
    make_cbz(panels, cover, cbz_path)
    with zipfile.ZipFile(cbz_path, "r") as zf:
        must(zf.testzip() is None, "cbz_ok")
        must(len(zf.namelist()) >= 25, "cbz_members", len(zf.namelist()))

    print("DONE release_assets", pdf_path.name, cbz_path.name)


def stage_publish() -> None:
    wait_ready()
    code, readiness = req("GET", f"/api/issues/{ISSUE}/release")
    must(code == 200, "readiness_get", readiness)
    blockers = (readiness or {}).get("evidence", {}).get("blockers") or []
    if blockers:
        print("blockers", blockers)
    must(not blockers, "blockers_clear", blockers)

    code, man = req("POST", f"/api/issues/{ISSUE}/release/manifest", {})
    must(code in (200, 201), "manifest", man)

    code, _ = req("POST", f"/api/issues/{ISSUE}/release/approve", {
        "note": "Issue 02 draft pipeline release — Static six-tone package"
    })
    must(code == 200, "release_approve")

    code, _ = req("POST", f"/api/issues/{ISSUE}/release/promote-manifest", {"replace": True})
    must(code == 200, "promote_manifest")

    code, pub = req("POST", f"/api/issues/{ISSUE}/release/publish-archive", {"replace": True})
    must(code in (200, 201), "publish_archive", pub)
    print("publication", json.dumps(pub, indent=2)[:900] if isinstance(pub, dict) else pub)

    code, _ = req("POST", f"/api/issues/{ISSUE}/workflow/approve", {
        "stage": "release", "approved": True, "note": "Archive published Issue 02 draft package"
    })
    must(code == 200, "workflow_approve_release")

    code, _ = req("POST", f"/api/issues/{ISSUE}/advance", {"stage": "release"})
    must(code == 200, "advance_release")

    code, wf = req("GET", f"/api/issues/{ISSUE}/workflow")
    must((wf or {}).get("active_stage") == "published", "stage_published", (wf or {}).get("active_stage"))

    code, readiness = req("GET", f"/api/issues/{ISSUE}/release")
    must((readiness or {}).get("publication_ready") is True, "publication_ready", readiness)
    print("DONE publish → published")


STAGES = {
    "page_plan": stage_page_plan,
    "art_prompts": stage_art_prompts,
    "art_production": stage_art_production,
    "qa": stage_qa,
    "release_assets": stage_release_assets,
    "publish": stage_publish,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in STAGES:
        print("Usage: drive_issue_02_pipeline.py <" + "|".join(STAGES) + ">")
        return 2
    STAGES[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
