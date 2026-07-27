#!/usr/bin/env python3
"""Drive Issue 01 (NeonBlue / The Last Light Of Summer) through outline + script promotion.

ONE THING (Master Prompt + Project Map):
  Stand up MZ-2026-08-01 as a real season package and finish story stages
  (intake → canon_review → outline → script → page_plan ready).

Does not invent art or force full-issue publish — stops at page_plan stage.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"
ISSUE_ID = "MZ-2026-08-01"
YEAR, MONTH, EDITION = 2026, 8, 1
TITLE = "The Last Light Of Summer"


def req(method: str, path: str, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode() or "null"), None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"error": raw}
        return exc.code, payload, str(payload.get("error") or raw)
    except Exception as exc:  # noqa: BLE001
        return 0, None, str(exc)


def must(ok: bool, step: str, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {step}" + (f" — {detail}" if detail else ""))
    if not ok:
        raise SystemExit(f"Stopped at {step}: {detail}")


def wait_ready(timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, payload, _ = req("GET", "/api/runtime-capabilities")
        if code == 200 and payload and payload.get("writable") is True:
            return
        time.sleep(0.25)
    raise SystemExit("Studio not reachable with writable capability at 127.0.0.1:8765")


def outline_md() -> str:
    return f"""# {ISSUE_ID} — {TITLE}

Logline: At MonkeyZoo’s end-of-summer night festival, NeonBlue races after a moving blackout pattern and must choose overlooked people over the public spotlight when a cyan pulse echoes his guilt about Patch.
Theme: Honest hope can admit danger
Page count: 8
Emotional arc: Cheerful over-reassurance → fear dressed as slogans → honest plan → hope that includes risk
Conflict: Moving power failures pull NeonBlue into denial while Lil Devil pushes for reckless force; the team must rescue a group trapped in a dark service corridor during the main-stage countdown
Ending: Festival continues reduced; NeonBlue refuses to call the night perfect; a partial cyan Echo segment flickers unseen

## Page map
Page 1 — Arrival and over-volunteering at the festival grounds
Page 2 — First blackout and failed backup reassurance
Page 3 — Outages travel; fractured cyan on public screens; Static hears a pattern
Page 4 — Lil Devil at the service gate and control box; system reacts to NeonBlue
Page 5 — Midpoint: Patch-linked frequency marker; Moodz names the pretending
Page 6 — Crisis: overlooked group trapped in festival service corridor vs main stage countdown
Page 7 — Climax: honest plan; directed force; rescue of the left-behind
Page 8 — Resolution and partial Echo reveal; new question about the relay

## Cast
- Featured: NeonBlue (MZ-CHAR-005)
- Guest: Lil Devil (MZ-CHAR-LILDEVIL)
- Supporting: Static, TwoTone, Scarline, Moodz, Ash

## Locations (approved canon)
- festival-grounds, festival-main-stage, festival-service-corridor, festival-control-node

## Props (approved canon)
- public-projection-screen, festival-backup-panel, service-gate, control-box, cyan-relay-marker, echo-symbol

## Continuity notes
- Proposed story canon: Patch emotional link; cyan relay memory; do not resolve Patch status.
- Echo: one-sixth of symbol lights only after NeonBlue chooses the unseen group.
"""


def _panel(page: int, n: int, location: str, characters: str, action: str, dialogue: str, caption: str, props: str, continuity: str) -> str:
    return f"""**Panel {page}.{n} (Standard)**
- Location: {location}
- Characters: {characters}
- Camera: Medium
- Action: {action}
- Emotion: Clear and readable
- Dialogue: {dialogue}
- Caption: {caption}
- SFX: —
- Visual notes: MonkeyZoo house style; keep NeonBlue cyan readable; empty-plate environments match approved location refs
- Continuity notes: {continuity}
- Props: {props}
"""


def script_md() -> str:
    panels = [
        # Page 1
        (1, 1, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-001, MZ-CHAR-002, MZ-CHAR-003, MZ-CHAR-004, MZ-CHAR-006",
         "The six Emo Monkeys arrive at the neon night festival; NeonBlue is already scanning tasks.",
         "NEONBLUE: We can cover games, rides, and the stage—easy!",
         "End of summer, Zoo City festival lights",
         "festival signage", "All six identifiable; festival-grounds plate"),
        (1, 2, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-LILDEVIL",
         "NeonBlue volunteers the group for multiple jobs before anyone agrees; Lil Devil cracks knuckles.",
         "LIL DEVIL: Or we force the fun.",
         "Volunteering without consent",
         "none", "Lil Devil restless energy; NeonBlue cheerful"),
        (1, 3, "Festival Main Stage", "MZ-CHAR-005, MZ-CHAR-001",
         "Main stage countdown board glows; NeonBlue points optimistically.",
         "NEONBLUE: Backup systems never miss a finale.",
         "Public spotlight warming up",
         "public-projection-screen", "Main stage empty of crisis yet"),
        # Page 2
        (2, 1, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-003",
         "First blackout drops a small food-stand section into darkness; Static flinches first.",
         "STATIC: Something’s wrong in the power.",
         "First failure",
         "festival-backup-panel", "Static senses interference before others"),
        (2, 2, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-002",
         "NeonBlue reassures the crowd that the backup will restore lights immediately.",
         "NEONBLUE: It’s fine—watch the backup kick!",
         "Reassurance before facts",
         "festival-backup-panel", "Promise before understanding"),
        (2, 3, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-006",
         "Backup fails; darkness stays; Scarline watches the crowd, not the wires.",
         "SCARLINE: Panic isn’t the real threat.",
         "Backup fails",
         "festival-backup-panel", "Scarline warns against wrong focus"),
        # Page 3
        (3, 1, "Festival Grounds", "MZ-CHAR-002, MZ-CHAR-003",
         "Outages hop across booths in a moving pattern; TwoTone traces two paths with a finger.",
         "TWOTONE: Two routes converging.",
         "Pattern emerges",
         "none", "TwoTone maps dual paths"),
        (3, 2, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-003",
         "Public screens flash fractured cyan shapes; Static covers his ears.",
         "STATIC: It’s not noise—it’s a pattern.",
         "Cyan fracture on screens",
         "public-projection-screen", "Fractured cyan motif; not full Echo"),
        (3, 3, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-001",
         "NeonBlue laughs too hard, herding people, eyes too bright.",
         "NEONBLUE: We’ve got this—everyone stay happy!",
         "Optimism as armor",
         "none", "Moodz observes quietly nearby"),
        # Page 4
        (4, 1, "Festival Control Node", "MZ-CHAR-LILDEVIL, MZ-CHAR-005",
         "Lil Devil grabs the locked service gate, ready to force it.",
         "LIL DEVIL: Smash the box. Open it.",
         "Impatience at the gate",
         "service-gate", "Do not force yet"),
        (4, 2, "Festival Control Node", "MZ-CHAR-005, MZ-CHAR-LILDEVIL",
         "Malfunctioning control box flickers; LEDs change when NeonBlue steps closer.",
         "NEONBLUE: Wait—it changed when I got near.",
         "System reacts to NeonBlue",
         "control-box", "Key beat: different reaction near NeonBlue"),
        (4, 3, "Festival Control Node", "MZ-CHAR-LILDEVIL, MZ-CHAR-004",
         "Lil Devil still wants chaos; Ash gives one precise look.",
         "ASH: Hope can read warnings.",
         "Ash line",
         "control-box", "Proposed Ash line; not a forced catchphrase brand"),
        # Page 5 midpoint
        (5, 1, "Festival Service Corridor", "MZ-CHAR-005",
         "NeonBlue finds a cyan relay marker / frequency tag with Patch-linked designation.",
         "NEONBLUE: I’ve seen this pulse before…",
         "Midpoint recognition",
         "cyan-relay-marker", "Patch link emotional only; no full explain"),
        (5, 2, "Festival Service Corridor", "MZ-CHAR-005, MZ-CHAR-001",
         "NeonBlue’s cheer becomes louder and thinner; Moodz stands close.",
         "MOODZ: You don’t have to pretend this feels safe.",
         "Moodz truth",
         "cyan-relay-marker", "Moodz names the performance"),
        (5, 3, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-002, MZ-CHAR-003",
         "Team regroups; TwoTone and Static confirm the pattern aims somewhere not the stage.",
         "TWOTONE: Stage is the distraction path.",
         "Converging data",
         "none", "Team coordination rising"),
        # Page 6 crisis
        (6, 1, "Festival Main Stage", "MZ-CHAR-005, MZ-CHAR-LILDEVIL",
         "Main stage countdown hits critical; crowd surges toward the light.",
         "NEONBLUE: If we lose the stage, the whole festival panics—",
         "Public pressure",
         "public-projection-screen", "Obvious choice: restore stage"),
        (6, 2, "Festival Service Corridor", "MZ-CHAR-003, MZ-CHAR-006",
         "Static and Scarline find a younger group trapped in the dark service corridor.",
         "STATIC: They’re stuck back here!",
         "Overlooked trap",
         "none", "Overlooked people vs spotlight"),
        (6, 3, "Festival Service Corridor", "MZ-CHAR-005, MZ-CHAR-001",
         "NeonBlue freezes between stage and corridor; Moodz waits without deciding for him.",
         "NEONBLUE: …They’ll be left behind.",
         "Choice forming",
         "none", "NeonBlue chooses the unseen"),
        # Page 7 climax
        (7, 1, "Festival Control Node", "MZ-CHAR-005, MZ-CHAR-LILDEVIL, MZ-CHAR-003, MZ-CHAR-002",
         "NeonBlue stops promising and gives an honest plan: risk, force points, safe routes.",
         "NEONBLUE: The system may fail. Here’s what we do anyway.",
         "Honest plan",
         "control-box, service-gate", "Hope admits danger"),
        (7, 2, "Festival Control Node", "MZ-CHAR-LILDEVIL, MZ-CHAR-005",
         "Lil Devil applies force only where NeonBlue marks it safe on the gate/box.",
         "LIL DEVIL: Fine—directed smash only.",
         "Restrained power",
         "service-gate, control-box", "Lil Devil learns directed force"),
        (7, 3, "Festival Service Corridor", "MZ-CHAR-005, MZ-CHAR-002, MZ-CHAR-003, MZ-CHAR-006",
         "Team clears the corridor; trapped group exits into residual neon.",
         "NEONBLUE: We get everyone out. That’s the win.",
         "Rescue of the left-behind",
         "none", "Rescue succeeds because of choice"),
        # Page 8 resolution
        (8, 1, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-001, MZ-CHAR-LILDEVIL",
         "Festival continues in reduced form; NeonBlue does not sell perfection.",
         "NEONBLUE: Not perfect. We got them out. That’s enough.",
         "Reduced celebration",
         "none", "No slogan ending"),
        (8, 2, "Festival Grounds", "MZ-CHAR-005",
         "Behind NeonBlue, a small cyan segment of the Echo symbol flickers once on a dark panel.",
         "—",
         "One-sixth Echo",
         "echo-symbol, cyan-relay-marker", "Partial Echo only; incomplete emblem"),
        (8, 3, "Festival Grounds", "MZ-CHAR-005, MZ-CHAR-004",
         "NeonBlue looks at restored lights; Ash stands nearby; unanswered question hangs.",
         "NEONBLUE: Why did that relay know me?",
         "New question",
         "none", "Open Patch thread; no resolution"),
    ]
    body = [f"# {ISSUE_ID} — {TITLE} — Script\n"]
    current_page = 0
    for p in panels:
        page = p[0]
        if page != current_page:
            current_page = page
            body.append(f"### Page {page}\n")
        body.append(_panel(*p))
    return "\n".join(body)


def promote(kind: str, variant_id: str) -> None:
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/{kind}s/{variant_id}/promote", {"replace": False})
    if code != 200:
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/{kind}s/{variant_id}/promote", {"replace": True})
    must(code == 200, f"{kind}_promote", err or "ok")


def main() -> int:
    wait_ready()
    print("=== ONE THING: Issue 01 NeonBlue story package (outline + script) ===")

    # Create if missing
    code, issues, _ = req("GET", "/api/issues")
    existing = [i for i in (issues or []) if isinstance(i, dict) and i.get("issue_id") == ISSUE_ID]
    if not existing:
        payload = {
            "issue_id": ISSUE_ID,
            "title": TITLE,
            "year": YEAR,
            "month": MONTH,
            "edition_number": EDITION,
            "issue_type": "Monthly",
            "primary_character": "MZ-CHAR-005",
            "guest_character": "MZ-CHAR-LILDEVIL",
            "core_premise": "End-of-summer festival blackouts force NeonBlue to choose overlooked people over the public spotlight",
            "main_conflict": "Moving power failures and NeonBlue’s denial vs honest rescue of those left behind",
            "emotional_goal": "Hope that can admit danger",
            "opening_situation": "Six Emo Monkeys arrive at MonkeyZoo night festival; NeonBlue over-volunteers",
            "ending_direction": "Reduced festival; honest hope; partial cyan Echo segment; Patch question open",
            "required_canon_references": "NeonBlue identity; Lil Devil guest; festival locations; cyan relay / Echo motif proposed",
            "prohibited_story_elements": "No full Patch resolution; no complete six-segment Echo; no unapproved redesigns",
            "page_count": 8,
            "panel_count": 24,
            "output_requirements": ["cover", "metadata", "social copy", "QA"],
        }
        code, created, err = req("POST", "/api/issues", payload)
        must(code == 201 and created and created.get("issue_id") == ISSUE_ID, "create_issue", err or json.dumps(created)[:300])
    else:
        print(f"[INFO] Issue {ISSUE_ID} already exists; continuing workflow")

    def wf():
        return req("GET", f"/api/issues/{ISSUE_ID}/workflow")

    def advance(stage: str) -> None:
        code, data, err = req("POST", f"/api/issues/{ISSUE_ID}/advance", {"stage": stage})
        must(code == 200, f"advance:{stage}", err or (data or {}).get("active_stage", ""))

    def approve_gate(stage: str) -> None:
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/workflow/approve", {
            "stage": stage, "approved": True, "note": "Issue 01 NeonBlue season package — owner path"
        })
        must(code == 200, f"workflow_approve:{stage}", err or "ok")

    code, data, err = wf()
    must(code == 200, "workflow_get", err or data.get("active_stage"))
    stage = data.get("active_stage")
    print(f"[INFO] active_stage={stage}")

    if stage == "intake":
        advance("intake")
        stage = "canon_review"
    if stage == "canon_review":
        approve_gate("canon_review")
        advance("canon_review")
        stage = "outline"
    if stage == "outline":
        code, variant, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/import", {
            "content": outline_md(), "provider": "season_bible_manual"
        })
        must(code == 201, "outline_import", err or json.dumps((variant or {}).get("validation"))[:400])
        val = (variant or {}).get("validation", {})
        must(val.get("status") == "passed", "outline_validation", json.dumps(val)[:500])
        vid = variant["variant_id"]
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/approve", {"note": "Season bible Issue 01"})
        must(code == 200, "outline_approve", err or "ok")
        promote("outline", vid)
        advance("outline")
        stage = "script"
    if stage == "script":
        code, svariant, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/import", {
            "content": script_md(), "provider": "season_bible_manual"
        })
        must(code == 201, "script_import", err or json.dumps((svariant or {}).get("validation"))[:400])
        val = (svariant or {}).get("validation", {})
        must(val.get("status") == "passed", "script_validation", json.dumps(val)[:500])
        svid = svariant["variant_id"]
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/{svid}/approve", {"note": "Season bible Issue 01 script"})
        must(code == 200, "script_approve", err or "ok")
        promote("script", svid)
        approve_gate("script")
        advance("script")
        stage = "page_plan"

    code, data, err = wf()
    must(code == 200 and data.get("active_stage") == "page_plan", "final_stage_page_plan", data.get("active_stage") if data else err)

    folder = ROOT / "02_MONTHLY_ISSUES" / f"{YEAR:04d}-{MONTH:02d}_Issue_{EDITION:02d}"
    outline_path = folder / "issue_outline.md"
    script_path = folder / "issue_script.md"
    must(outline_path.is_file() and ISSUE_ID in outline_path.read_text(encoding="utf-8"), "outline_file", str(outline_path))
    must(script_path.is_file() and "**Panel 1.1" in script_path.read_text(encoding="utf-8"), "script_file", str(script_path))
    must("Last Light" in outline_path.read_text(encoding="utf-8") or "festival" in outline_path.read_text(encoding="utf-8").lower(), "outline_content")

    print("\n=== DONE: Issue 01 story package ready for page plan ===")
    print(f"Folder: {folder.relative_to(ROOT)}")
    print("Stage: page_plan")
    print("Next ONE THING (later): promote page_panel_plan from this script")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] unexpected: {exc}")
        raise
