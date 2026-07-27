#!/usr/bin/env python3
"""ONE THING: scaffold Issue 03 Scarline (MZ-2026-10-02) through outline ready.

Uses edition 02 so published live-probe 2026-10_Issue_01 is not collided with.
Creates package, promotes season-bible brief, advances intake → canon_review
(with approval) → outline.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8765"
ISSUE_ID = "MZ-2026-10-02"
YEAR, MONTH, EDITION = 2026, 10, 2
TITLE = "The House That Remembers"


def req(method: str, path: str, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return exc.code, payload


def must(ok: bool, step: str, detail="") -> None:
    print(("PASS" if ok else "FAIL"), step, str(detail)[:500])
    if not ok:
        raise SystemExit(f"Stopped at {step}")


def wait_ready(timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, payload = req("GET", "/api/runtime-capabilities")
        if code == 200 and payload and payload.get("writable") is True:
            return
        time.sleep(0.25)
    raise SystemExit("Studio not writable")


def brief_md() -> str:
    return f"""# Issue Brief — {ISSUE_ID} — {TITLE}

Issue Month: 2026-10
Issue Number: 2
Working Title: {TITLE}
Issue Type: Monthly
Core Idea: A Halloween haunted-house attraction built over old FusionZoo infrastructure misdirects exits; Scarline must share enough experience for informed choice without taking control.
Opening Situation: Playful attraction scares; Scarline is the least impressed while Zombie recognizes old-system residue.
Theme: Experience can guide without controlling
Emotional Core: Validation over rescue; real choice over false exits
Main Character: MZ-CHAR-006 (Scarline)
Supporting Characters: MZ-CHAR-ZOMBIE (guest); Static, Moodz, TwoTone, NeonBlue, Ash
Conflict: Exit signs route characters toward different doors; one door must not be opened; fear and memory reshape rooms
Antagonist or Problem: Older FusionZoo system under theatrical scares; false rescue choices that test compliance
Setting: Haunted attraction over abandoned FusionZoo path; Halloween MonkeyZoo
Ending: Scarline explains immediate risk and asks what they choose; origin: she survived because someone gave her a real choice (no facial scar)
Next Issue Teaser: Community meal / Moodz seating harmony (season Issue 04)
Required Visuals: haunted attraction interiors, misdirect exit signs, wall marking residue, no complete Echo emblem
Required Canon References: Scarline and Zombie approved identity; green glow reserved for zombie/cracked-chamber content only when intentional
Forbidden Changes: No facial scar on Scarline; no complete Echo emblem; do not let Zombie solve Scarline's decision for her
Continuity Risks: Honor six-tone / old-relay geography from Issue 02; partial cyan Echo; Patch/Keeper still open
Page Count: 8
Panel Count: 24
Release Assets Needed: cover, metadata, social copy, QA
"""


def outline_md() -> str:
    return f"""# {ISSUE_ID} — {TITLE}

Logline: MonkeyZoo reopens a haunted attraction over old FusionZoo infrastructure; Scarline recognizes danger others treat as theater while Zombie confirms residual past systems, and Scarline must guide without controlling.
Theme: Experience can guide without controlling
Page count: 8
Emotional arc: Detached calm read as secrecy → shared risk → informed choice → belief in validation over rescue
Conflict: Misdirect exits and fear-responsive rooms; one door must stay closed
Ending: Group chooses with eyes open; Scarline's origin is a real choice she was given, not a scar; partial season signal continues

## Page map
Page 1 — Playful attraction scares; Scarline unimpressed
Page 2 — Zombie recognizes old-system residue / smell
Page 3 — Room changes; exit signs disagree
Page 4 — Scarline names the one door that must not open
Page 5 — Midpoint: Scarline admits she has been here before
Page 6 — False rescue choices; Zombie past vs Scarline present
Page 7 — Crisis: guided choice, not orders
Page 8 — Land; residual wall mark; season signal thread warm

## Cast
- Featured: Scarline (MZ-CHAR-006)
- Guest: Zombie Monkey (MZ-CHAR-ZOMBIE)
- Supporting: Static, Moodz, TwoTone, NeonBlue, Ash

## Locations (approved / proposed)
- haunted-attraction (proposed if not yet filed), abandoned FusionZoo path residue, exit corridors

## Props
- misdirect-exit-sign, wall-marking-residue, theatrical scare props vs real residue

## Continuity notes
- Signal belongs to older FusionZoo system (Echo mystery tracker Issue 03)
- No facial scar; green glow only if zombie/cracked-chamber intentional
- Do not complete Echo emblem
"""


def main() -> int:
    wait_ready()

    # Create if missing
    code, existing = req("GET", f"/api/issues/{ISSUE_ID}")
    if code != 200:
        body = {
            "issue_id": ISSUE_ID,
            "title": TITLE,
            "year": YEAR,
            "month": MONTH,
            "edition_number": EDITION,
            "issue_type": "Monthly",
            "primary_character": "MZ-CHAR-006",
            "guest_character": "MZ-CHAR-ZOMBIE",
            "core_premise": "A Halloween haunted attraction over old FusionZoo infrastructure misdirects exits; Scarline must share experience without controlling choice",
            "main_conflict": "False rescue doors and fear-responsive rooms; Scarline's calm reads as secrecy until she reveals enough for informed choice",
            "emotional_goal": "Guide with experience without taking control",
            "opening_situation": "Playful attraction scares; Scarline unimpressed; Zombie recognizes old-system residue",
            "ending_direction": "Group chooses with eyes open; Scarline origin is a real choice she was given; no facial scar; season signal warm",
            "required_canon_references": "Scarline MZ-CHAR-006; Zombie MZ-CHAR-ZOMBIE; Issue 02 old-relay / six-tone continuity",
            "prohibited_story_elements": "No Scarline facial scar; no complete Echo emblem; Zombie does not decide for Scarline",
            "page_count": 8,
            "panel_count": 24,
            "output_requirements": ["cover", "metadata", "social copy", "QA"],
        }
        code, created = req("POST", "/api/issues", body)
        must(code in (200, 201), "create_issue", created)
        print("created", ISSUE_ID)
    else:
        print("exists", ISSUE_ID)

    code, wf = req("GET", f"/api/issues/{ISSUE_ID}/workflow")
    must(code == 200, "workflow", wf)
    active = (wf or {}).get("active_stage")
    print("active", active)

    # Promote brief as outline stub replacement via story workspace when at intake
    if active == "intake":
        # Write issue_brief via outline import is wrong; use story if available
        # Many issues use direct file for brief + advance after stubs exist.
        # Prefer story outline only after canon; for intake just advance if brief exists.
        from pathlib import Path
        folder = Path(__file__).resolve().parents[1] / "02_MONTHLY_ISSUES" / f"{YEAR:04d}-{MONTH:02d}_Issue_{EDITION:02d}"
        (folder / "issue_brief.md").write_text(brief_md(), encoding="utf-8")
        brief_json = {
            "issue_id": ISSUE_ID,
            "title": TITLE,
            "year": YEAR,
            "month": MONTH,
            "edition_number": EDITION,
            "primary_character": "MZ-CHAR-006",
            "guest_character": "MZ-CHAR-ZOMBIE",
            "theme": "Experience can guide without controlling",
            "logline": "Haunted attraction over old FusionZoo infrastructure; Scarline guides without controlling.",
            "page_count": 8,
            "panel_count": 24,
            "status": "in_production",
        }
        (folder / "issue_brief.json").write_text(json.dumps(brief_json, indent=2) + "\n", encoding="utf-8")
        (folder / "metadata.json").write_text(
            json.dumps(
                {
                    "issue_id": ISSUE_ID,
                    "title": TITLE,
                    "name": TITLE,
                    "year": YEAR,
                    "month": MONTH,
                    "edition_number": EDITION,
                    "primary_character": "MZ-CHAR-006",
                    "guest_character": "MZ-CHAR-ZOMBIE",
                    "status": "in_production",
                    "workflow_stage": "1. Intake",
                    "page_count": 8,
                    "panel_count": 24,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/advance", {"stage": "intake"})
        must(code == 200, "advance_intake")
        active = "canon_review"

    if active == "canon_review":
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/workflow/approve", {
            "stage": "canon_review",
            "approved": True,
            "note": "Scarline + Zombie resolve to approved bibles; season Issue 03 scaffold",
        })
        must(code == 200, "approve_canon")
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/advance", {"stage": "canon_review"})
        must(code == 200, "advance_canon")
        active = "outline"

    if active == "outline":
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/prompt", {})
        print("outline_prompt", code)
        code, variant = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/import", {
            "content": outline_md(),
            "provider": "season_bible_scaffold",
        })
        must(code in (200, 201) and (variant or {}).get("validation", {}).get("status") == "passed", "outline_import", variant)
        vid = variant["variant_id"]
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/approve", {"note": "Issue 03 Scarline season outline"})
        must(code == 200, "outline_approve")
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/promote", {"replace": True})
        if code != 200:
            code, _ = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/promote", {"replace": True})
        must(code == 200, "outline_promote")
        code, _ = req("POST", f"/api/issues/{ISSUE_ID}/advance", {"stage": "outline"})
        must(code == 200, "advance_outline")

    code, wf = req("GET", f"/api/issues/{ISSUE_ID}/workflow")
    must(code == 200 and (wf or {}).get("active_stage") == "script", "now_script", (wf or {}).get("active_stage"))
    print("DONE Issue 03 scaffold → script stage (outline promoted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
