#!/usr/bin/env python3
"""Live Banana Lab Studio HTTP test: create and drive one issue through the app APIs.

Uses the real Flask app over HTTP (not unit fixtures). Records pass/fail evidence
to docs/LIVE_APP_TEST_REPORT.md.
"""
from __future__ import annotations

import io
import json
import sys
import time
import traceback
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"
ISSUE_ID = "MZ-2026-10-01"
YEAR, MONTH, EDITION = 2026, 10, 1
TITLE = "Live App Probe - Signal Desk"
REPORT: list[dict] = []


def log(step: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    entry = {"step": step, "status": status, "detail": detail, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    REPORT.append(entry)
    print(f"[{status}] {step}" + (f" — {detail}" if detail else ""))


def req(method: str, path: str, body=None, form: dict | None = None, files: dict | None = None):
    url = BASE + path
    data = None
    headers = {}
    if files is not None:
        boundary = "----BananaLabBoundary7"
        chunks = []
        for name, (filename, content, content_type) in files.items():
            chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode())
            chunks.append(content)
            chunks.append(b"\r\n")
        if form:
            for k, v in form.items():
                chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        chunks.append(f"--{boundary}--\r\n".encode())
        data = b"".join(chunks)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read()
            payload = json.loads(raw.decode() or "null")
            return resp.status, payload, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return exc.code, payload, str(payload.get("error") or raw)
    except Exception as exc:  # noqa: BLE001
        return 0, None, str(exc)


def wait_ready(timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, payload, err = req("GET", "/api/runtime-capabilities")
        if code == 200 and payload and payload.get("writable") is True:
            return True
        time.sleep(0.25)
    return False


def png(color: str = "#3a7ca5") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (1024, 768), color).save(buf, format="PNG")
    return buf.getvalue()


def outline() -> str:
    return f"""# {ISSUE_ID} — {TITLE}
Logline: Moodz opens the signal desk and documents a quiet night.
Theme: Careful observation
Page count: 2
Emotional arc: alertness to calm certainty
Conflict: An unread queue of silent tickets
Ending: Desk closed, note left for the next shift

## Page map
Page 1 — Open the desk
Page 2 — Leave the note
"""


def script() -> str:
    return f"""# {ISSUE_ID} — Script
### Page 1 — Open
**Panel 1.1 (Half)**
- Location: Signal Desk
- Characters: MZ-CHAR-001
- Camera: Medium
- Action: Moodz powers on the quiet desk monitors.
- Emotion: Focused
- Dialogue: MOODZ: Night shift.
- Caption: Signal desk
- SFX: —
- Visual notes: Soft monitor glow
- Continuity notes: Keep blue streak readable
- Props: monitors
### Page 2 — Close
**Panel 2.1 (Full)**
- Location: Signal Desk
- Characters: MZ-CHAR-001, MZ-CHAR-002
- Camera: Wide
- Action: TwoTone arrives with tea; they leave a shift note.
- Emotion: Steady
- Dialogue: TWOTONE: For the morning crew.
- Caption: End
- SFX: —
- Visual notes: Note on desk
- Continuity notes: Keep identity markers
- Props: tea cup, paper note
"""


def main() -> int:
    if not wait_ready():
        log("server_ready", False, "Flask not reachable at 127.0.0.1:8765 with writable capability")
        write_report()
        return 1
    log("server_ready", True, "runtime-capabilities writable")

    code, caps, err = req("GET", "/api/runtime-capabilities")
    log("runtime_capabilities", code == 200 and caps.get("writable") is True, json.dumps(caps))

    code, chars, err = req("GET", "/api/characters")
    log("list_characters", code == 200 and isinstance(chars, list) and len(chars) > 0, f"count={len(chars) if isinstance(chars, list) else 0}")

    # Cleanup prior live probe if present
    folder = ROOT / "02_MONTHLY_ISSUES" / f"{YEAR:04d}-{MONTH:02d}_Issue_{EDITION:02d}"
    if folder.exists():
        import shutil
        shutil.rmtree(folder)
        log("cleanup_prior_issue", True, str(folder))
    idea = ROOT / "01_IDEAS_INBOX" / f"{YEAR:04d}-{MONTH:02d}-idea.md"
    if idea.exists():
        idea.unlink()

    payload = {
        "issue_id": ISSUE_ID,
        "title": TITLE,
        "year": YEAR,
        "month": MONTH,
        "edition_number": EDITION,
        "issue_type": "Monthly",
        "primary_character": "MZ-CHAR-001",
        "guest_character": "MZ-CHAR-002",
        "core_premise": "A quiet signal desk still needs a careful night shift",
        "main_conflict": "Unread silent tickets pile up without ownership",
        "emotional_goal": "Steady care",
        "opening_situation": "Midnight at the signal desk",
        "ending_direction": "Note left for morning crew",
        "required_canon_references": "Moodz and TwoTone approved identity",
        "prohibited_story_elements": "No unapproved redesigns",
        "page_count": 2,
        "panel_count": 2,
        "output_requirements": ["cover", "metadata", "social copy", "QA"],
    }
    code, created, err = req("POST", "/api/issues", payload)
    log("create_issue", code == 201 and created and created.get("issue_id") == ISSUE_ID, err or json.dumps(created)[:200])
    if code != 201:
        write_report()
        return 1

    def wf():
        return req("GET", f"/api/issues/{ISSUE_ID}/workflow")

    def advance(stage):
        code, data, err = req("POST", f"/api/issues/{ISSUE_ID}/advance", {"stage": stage})
        log(f"advance:{stage}", code == 200, err or data.get("active_stage") if isinstance(data, dict) else "")
        return code == 200, data

    def approve_gate(stage):
        code, data, err = req("POST", f"/api/issues/{ISSUE_ID}/workflow/approve", {"stage": stage, "approved": True, "note": "live app test"})
        log(f"workflow_approve:{stage}", code == 200, err or "")
        return code == 200

    code, data, err = wf()
    log("workflow_after_create", code == 200 and data.get("active_stage") == "intake", data.get("active_stage") if data else err)

    advance("intake")
    code, data, err = wf()
    log("after_intake", data and data.get("active_stage") == "canon_review", data.get("active_stage") if data else err)

    approve_gate("canon_review")
    advance("canon_review")

    # Story outline via API (mirrors Studio)
    code, prompt, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/prompt", {})
    log("outline_prompt", code == 200, err or (prompt or {}).get("generation_id", ""))
    code, variant, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/import", {"content": outline(), "provider": "live_test"})
    log("outline_import", code == 201 and (variant or {}).get("validation", {}).get("status") == "passed", err or "")
    vid = (variant or {}).get("variant_id")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/approve", {"note": "live"})
    log("outline_approve", code == 200, err or "")
    # First promote with replace false — expected fail if stubs exist
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/promote", {"replace": False})
    stub_blocked = code != 200
    log("outline_promote_replace_false", True, f"status={code} err={err} (stub overwrite behavior)")
    if stub_blocked:
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/promote", {"replace": True})
        log("outline_promote_replace_true", code == 200, err or "")
    else:
        log("outline_promote_replace_true", True, "not needed")
    advance("outline")

    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/prompt", {})
    log("script_prompt", code == 200, err or "")
    code, svariant, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/import", {"content": script(), "provider": "live_test"})
    log("script_import", code == 201 and (svariant or {}).get("validation", {}).get("status") == "passed", err or "")
    svid = (svariant or {}).get("variant_id")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/{svid}/approve", {"note": "live"})
    log("script_approve", code == 200, err or "")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/{svid}/promote", {"replace": False})
    if code != 200:
        log("script_promote_replace_false", True, f"blocked as expected: {err}")
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/{svid}/promote", {"replace": True})
    log("script_promote", code == 200, err or "")
    approve_gate("script")
    advance("script")

    code, layout, err = req("POST", f"/api/issues/{ISSUE_ID}/layout/variants", {})
    log("layout_create", code == 201 and (layout or {}).get("validation", {}).get("status") == "passed", err or "")
    lvid = (layout or {}).get("variant_id")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/layout/variants/{lvid}/approve", {"note": "live"})
    log("layout_approve", code == 200, err or "")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/layout/variants/{lvid}/promote", {"replace": True})
    log("layout_promote", code == 200, err or "")
    advance("page_plan")

    code, pack, err = req("POST", f"/api/issues/{ISSUE_ID}/art-prompts/variants", {})
    log("art_prompt_pack_create", code == 201 and (pack or {}).get("validation", {}).get("status") == "passed", err or "")
    pvid = (pack or {}).get("variant_id")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/art-prompts/variants/{pvid}/approve", {"note": "live"})
    log("art_prompt_pack_approve", code == 200, err or "")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/art-prompts/variants/{pvid}/promote", {"replace": True})
    log("art_prompt_pack_promote", code == 200, err or "")
    advance("art_prompts")

    code, queue, err = req("POST", f"/api/issues/{ISSUE_ID}/art-queue/build", {})
    items = ((queue or {}).get("items") if isinstance(queue, dict) else None) or (queue.get("queue", {}).get("items") if isinstance(queue, dict) else [])
    # build returns queue object directly from build_queue
    if isinstance(queue, dict) and "items" in queue:
        items = queue["items"]
    elif isinstance(queue, dict) and "queue" in queue:
        items = queue["queue"].get("items", [])
    log("art_queue_build", code == 200 and len(items) >= 1, f"items={len(items)} err={err}")

    for index, item in enumerate(items):
        pid = item["panel_id"]
        code, prompt, err = req("POST", f"/api/issues/{ISSUE_ID}/art-queue/{pid}/prompt", {})
        log(f"art_prompt_export:{pid}", code == 200, err or "")
        code, attempt, err = req(
            "POST",
            f"/api/issues/{ISSUE_ID}/art-queue/{pid}/attempts",
            files={"image": (f"{pid}.png", png(["#3a7ca5", "#c45c26"][index % 2]), "image/png")},
            form={"provider": "live_test"},
        )
        log(f"art_import:{pid}", code == 201, err or "")
        aid = (attempt or {}).get("attempt_id")
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/art-queue/{pid}/attempts/{aid}/select", {})
        log(f"art_select:{pid}", code == 200, err or "")

    # Pre-QA deliverables
    issue_folder = ROOT / "02_MONTHLY_ISSUES" / f"{YEAR:04d}-{MONTH:02d}_Issue_{EDITION:02d}"
    cover_dir = issue_folder / "generated_art" / "covers"
    cover_dir.mkdir(parents=True, exist_ok=True)
    (cover_dir / "main_cover.png").write_bytes(png("#f0c040"))
    (issue_folder / "cover_prompt.md").write_text(f"# Main cover\n{TITLE}\n", encoding="utf-8")
    (issue_folder / "final_export_checklist.md").write_text(f"# {ISSUE_ID} checklist\n- [x] ready\n", encoding="utf-8")
    (issue_folder / "social_posts.md").write_text("## Launch post\nLive app probe ready.\n", encoding="utf-8")
    exports = issue_folder / "exports"
    exports.mkdir(exist_ok=True)
    pdf = exports / f"MonkeyZoo_{ISSUE_ID}_Web.pdf"
    pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
    zpath = exports / f"MonkeyZoo_{ISSUE_ID}_CBZ.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("page1.png", png())
        zf.writestr("cover.png", png("#f0c040"))
    meta = json.loads((issue_folder / "metadata.json").read_text(encoding="utf-8"))
    meta.update({
        "format": "CHIP-0015",
        "name": TITLE,
        "title": TITLE,
        "issue_id": ISSUE_ID,
        "description": "Live app probe issue for Banana Lab ship readiness.",
        "attributes": [{"trait_type": "Series", "value": "MonkeyZoo"}],
        "data": {"@type": "DigitalDocument", "name": TITLE, "url": f"local://{pdf.name}", "sha256": "a" * 64},
    })
    (issue_folder / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    log("pre_qa_deliverables", True, "cover/pdf/zip/metadata written")

    approve_gate("art_production")
    advance("art_production")

    code, review, err = req("POST", f"/api/issues/{ISSUE_ID}/qa/reviews", {})
    log("qa_create", code == 201, err or (review or {}).get("review_id", ""))
    rid = (review or {}).get("review_id")
    blockers = ((review or {}).get("evidence") or {}).get("blockers") or []
    log("qa_blockers", len(blockers) == 0, str(blockers))
    code, fin, err = req("POST", f"/api/issues/{ISSUE_ID}/qa/reviews/{rid}/finalize", {"verdict": "pass", "notes": "live pass", "continuity_checks": ["identity ok"]})
    log("qa_finalize_pass", code == 200 and (fin or {}).get("verdict") == "PASS", err or "")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/qa/reviews/{rid}/promote", {"replace": True})
    log("qa_promote", code == 200, err or "")
    approve_gate("qa")
    advance("qa")

    code, readiness, err = req("GET", f"/api/issues/{ISSUE_ID}/release")
    log("release_readiness", code == 200 and not (readiness or {}).get("evidence", {}).get("blockers"), err or str((readiness or {}).get("evidence", {}).get("blockers")))
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/release/approve", {"note": "live release"})
    log("release_approve", code == 200, err or "")
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/release/promote-manifest", {"replace": True})
    log("release_promote_manifest", code == 200, err or "")
    code, pub, err = req("POST", f"/api/issues/{ISSUE_ID}/release/publish-archive", {"replace": True})
    log("release_publish_archive", code in (200, 201), err or (pub or {}).get("publication", {}).get("archive_path", ""))
    approve_gate("release")
    advance("release")

    code, final_wf, err = wf()
    log("final_stage_published", final_wf and final_wf.get("active_stage") == "published", final_wf.get("active_stage") if final_wf else err)
    code, readiness, err = req("GET", f"/api/issues/{ISSUE_ID}/release")
    log("publication_ready", readiness and readiness.get("publication_ready") is True, err or str(readiness.get("publication_ready") if readiness else None))

    # UI smoke via selenium
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait

        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1440,900")
        opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        driver = webdriver.Chrome(options=opts)
        try:
            driver.get(BASE + "/")
            WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(1.5)
            writable = driver.execute_script(
                "return window && document.getElementById('createIssueButton') && !document.getElementById('createIssueButton').disabled"
            )
            log("ui_create_issue_enabled", bool(writable), f"enabled={writable}")
            for view in ("dashboard", "issues", "storyBuilder", "layout", "artQueue", "qa", "release"):
                btns = driver.find_elements(By.CSS_SELECTOR, f'[data-view="{view}"]')
                if not btns:
                    log(f"ui_nav:{view}", False, "missing")
                    continue
                btns[0].click()
                time.sleep(0.35)
                log(f"ui_nav:{view}", True, "clicked")
            # art queue should show pack controls
            pack_btn = driver.find_elements(By.ID, "createArtPromptPack")
            pub_btn = driver.find_elements(By.ID, "releasePublishArchive")
            log("ui_art_prompt_pack_control", bool(pack_btn), "present" if pack_btn else "missing")
            # open release view for publish button
            rel = driver.find_elements(By.CSS_SELECTOR, '[data-view="release"]')
            if rel:
                rel[0].click()
                time.sleep(0.4)
            pub_btn = driver.find_elements(By.ID, "releasePublishArchive")
            log("ui_release_publish_control", bool(pub_btn), "present" if pub_btn else "missing")
            severe = [e for e in driver.get_log("browser") if e.get("level") == "SEVERE"]
            log("ui_console_severe", len(severe) == 0, str(severe[:3]))
        finally:
            driver.quit()
    except Exception as exc:  # noqa: BLE001
        log("ui_selenium", False, f"{type(exc).__name__}: {exc}")

    write_report()
    fails = sum(1 for r in REPORT if r["status"] == "FAIL")
    return 1 if fails else 0


def write_report() -> None:
    path = ROOT / "docs" / "LIVE_APP_TEST_REPORT.md"
    passes = sum(1 for r in REPORT if r["status"] == "PASS")
    fails = sum(1 for r in REPORT if r["status"] == "FAIL")
    lines = [
        "# Live App Test Report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Issue under test: `{ISSUE_ID}`",
        f"- Base URL: `{BASE}`",
        f"- Results: **{passes} passed**, **{fails} failed**",
        "",
        "## Chronology",
        "",
    ]
    for r in REPORT:
        lines.append(f"- **{r['status']}** `{r['step']}` — {r['detail']}")
    lines.extend([
        "",
        "## Interpretation notes",
        "",
        "- HTTP steps exercise the same Flask routes the Studio UI calls.",
        "- `outline_promote_replace_false` / script equivalent document whether create-issue stubs block first promote without `replace=true`.",
        "- UI steps verify navigation and control presence under a writable local runtime.",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        write_report()
        raise SystemExit(1)
