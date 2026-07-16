#!/usr/bin/env python3
"""Drive Issue 02 (Static / Signals In The Silence) through outline + script → page_plan.

Uses MZ-2026-09-02 to avoid colliding with published probe folder 2026-09_Issue_01.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"
ISSUE_ID = "MZ-2026-09-02"
YEAR, MONTH, EDITION = 2026, 9, 2
TITLE = "Signals In The Silence"


def req(method: str, path: str, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode() or "null"), None
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
    print(f"[{'PASS' if ok else 'FAIL'}] {step}" + (f" — {detail}" if detail else ""))
    if not ok:
        raise SystemExit(f"Stopped at {step}: {detail}")


def wait_ready(timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, payload, _ = req("GET", "/api/runtime-capabilities")
        if code == 200 and payload and payload.get("writable") is True:
            return
        time.sleep(0.25)
    raise SystemExit("Studio not writable at 127.0.0.1:8765")


def outline_md() -> str:
    return f"""# {ISSUE_ID} — {TITLE}

Logline: After summer, storm-season devices all emit the same interference; Static proves the noise is a structured six-tone search while Clever maps the hardware, and Static learns to share one clear warning at a time.
Theme: Sensitivity without being silenced
Page count: 8
Emotional arc: Overload and dismissal risk → structured proof → choice to keep listening on his terms → clear usable warning
Conflict: Public systems broadcast interference Static alone can parse; overload makes him hard to hear even when he is right
Ending: Old relay junction located before overload; Static’s four-part method for future emergencies

## Page map
Page 1 — Tiny disruptions only Static notices
Page 2 — Storm burst hits every device; Static reacts first
Page 3 — Clever inspects equipment; Static over-explains
Page 4 — Six tones isolated; one matches August cyan frequency
Page 5 — Signal searching for responses, not broadcasting outward
Page 6 — Emergency systems catch interference; team gives Static space
Page 7 — Static reduces to one repeating element; points to old relay junction
Page 8 — Method established; powered-off radio soft tone final image

## Cast
- Featured: Static (MZ-CHAR-003)
- Guest: Clever Monkey (MZ-CHAR-CLEVER)
- Supporting: NeonBlue, TwoTone, Moodz, Scarline, Ash

## Locations (approved canon)
- storm-routines, transit-announcement-hub, school-pa-zone, old-relay-junction, zoo-city-streets

## Props (approved canon)
- transit-board, school-speaker, personal-device-burst, signal-analyzer, six-tone-motif, powered-off-radio, cyan-relay-marker, echo-symbol

## Continuity notes
- Six tones include August cyan frequency match
- Do not treat Static as irrational
- Growth is method, not a cure
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
- Visual notes: MonkeyZoo house style; early-fall storm light; keep Static identity readable
- Continuity notes: {continuity}
- Props: {props}
"""


def script_md() -> str:
    panels = [
        (1, 1, "Zoo City Streets", "MZ-CHAR-003",
         "Static freezes on a sidewalk as a transit board clicks off-rhythm.",
         "STATIC: That click… it repeated.",
         "Tiny disruption", "transit-board", "Others ignore it"),
        (1, 2, "School / Public Address Zone", "MZ-CHAR-003, MZ-CHAR-001",
         "A PA speaker glitches a half-second; Moodz watches Static flinch.",
         "MOODZ: You heard it again.",
         "School speaker glitch", "school-speaker", "Moodz believes without pressure"),
        (1, 3, "Zoo City Streets", "MZ-CHAR-003, MZ-CHAR-005",
         "NeonBlue tries to reassure; Static’s ears still track a buzz.",
         "NEONBLUE: Probably just old wires—",
         "Quick reassurance risk", "personal-device-burst", "NeonBlue believes but soothes too fast"),
        (2, 1, "Early-Fall Storm Streets and Routine Nodes", "MZ-CHAR-003, MZ-CHAR-002, MZ-CHAR-005",
         "Storm rolls in; every device emits the same interference burst.",
         "STATIC: It’s the same burst!",
         "Storm burst", "personal-device-burst, transit-board", "Citywide pattern"),
        (2, 2, "Transit Announcement Hub", "MZ-CHAR-003",
         "Static reacts before the hub screens finish glitching.",
         "STATIC: Before the sound finishes—danger is already here.",
         "First reaction", "transit-board", "Static first"),
        (2, 3, "Transit Announcement Hub", "MZ-CHAR-003, MZ-CHAR-006",
         "Scarline steadies the space without shutting Static down.",
         "SCARLINE: Don’t drown him out.",
         "Space to listen", "transit-board", "Scarline protects signal space"),
        (3, 1, "Transit Announcement Hub", "MZ-CHAR-CLEVER, MZ-CHAR-003",
         "Clever arrives with analyzer gear and opens a panel.",
         "CLEVER: Hardware first. Pattern later.",
         "Clever inspects", "signal-analyzer", "Maps mechanism"),
        (3, 2, "Transit Announcement Hub", "MZ-CHAR-003, MZ-CHAR-CLEVER",
         "Static talks too fast—six signals, three dangers, old memories.",
         "STATIC: Six—no, three—no, listen—",
         "Overload speech", "signal-analyzer", "Correct but unusable delivery"),
        (3, 3, "School / Public Address Zone", "MZ-CHAR-CLEVER, MZ-CHAR-004",
         "Clever follows wires; Ash asks one short question.",
         "ASH: Which part repeats?",
         "Ash cuts noise", "school-speaker, signal-analyzer", "Proposed Ash line"),
        (4, 1, "Transit Announcement Hub", "MZ-CHAR-CLEVER, MZ-CHAR-003",
         "Clever isolates six distinct tones on the analyzer display.",
         "CLEVER: Six tones. Structured. Not random.",
         "Six tones proven", "signal-analyzer, six-tone-motif", "Clever proves structure"),
        (4, 2, "Transit Announcement Hub", "MZ-CHAR-003, MZ-CHAR-005",
         "One tone matches August’s cyan frequency; NeonBlue goes still.",
         "STATIC: That’s the cyan one… from summer.",
         "August frequency match", "cyan-relay-marker, six-tone-motif", "Continuity with Issue 01"),
        (4, 3, "Zoo City Streets", "MZ-CHAR-003, MZ-CHAR-002",
         "TwoTone helps pair frequencies into readable couples.",
         "TWOTONE: Pair them. Don’t stack them.",
         "Paired frequencies", "six-tone-motif", "TwoTone support"),
        (5, 1, "Early-Fall Storm Streets and Routine Nodes", "MZ-CHAR-003, MZ-CHAR-CLEVER",
         "Static realizes the signal is searching for responses, not broadcasting out.",
         "STATIC: It’s listening for us.",
         "Searching not broadcasting", "six-tone-motif", "Key midpoint insight"),
        (5, 2, "School / Public Address Zone", "MZ-CHAR-001, MZ-CHAR-003",
         "Moodz blocks pressure for Static to “just calm down.”",
         "MOODZ: He doesn’t have to be comfortable for you.",
         "Protection from pressure", "school-speaker", "Moodz function"),
        (5, 3, "Transit Announcement Hub", "MZ-CHAR-003, MZ-CHAR-006",
         "Scarline offers a clear choice: keep listening or stop.",
         "SCARLINE: Do you want to keep listening?",
         "Clear choice", "transit-board", "Agency for Static"),
        (6, 1, "Early-Fall Storm Streets and Routine Nodes", "MZ-CHAR-003, MZ-CHAR-005, MZ-CHAR-002",
         "Interference spreads into emergency systems; Static begins repeating every danger at once.",
         "STATIC: Flood—fire—relay—stop—",
         "Overload crisis", "personal-device-burst", "Confusion risk"),
        (6, 2, "Zoo City Streets", "MZ-CHAR-001, MZ-CHAR-006, MZ-CHAR-003",
         "Team gives Static space instead of ordering silence.",
         "MOODZ: Room. Not volume.",
         "Space not order", "none", "Team growth"),
        (6, 3, "Zoo City Streets", "MZ-CHAR-003, MZ-CHAR-006",
         "Static answers Scarline: yes—on his terms.",
         "STATIC: Yes. But one line at a time.",
         "Choice yes", "none", "On his terms"),
        (7, 1, "Transit Announcement Hub", "MZ-CHAR-003, MZ-CHAR-CLEVER",
         "Static reduces the interference to one repeating element and states it cleanly.",
         "STATIC: The third tone. Every twelve seconds. West sector.",
         "One clear warning", "signal-analyzer, six-tone-motif", "Usable communication"),
        (7, 2, "Old Relay Junction", "MZ-CHAR-003, MZ-CHAR-CLEVER, MZ-CHAR-002",
         "Team reaches the old relay junction before overload; cyan residual glow in dormant nodes.",
         "CLEVER: Junction confirmed. Acting now.",
         "Relay located", "none", "Physical Echo node"),
        (7, 3, "Old Relay Junction", "MZ-CHAR-003, MZ-CHAR-005, MZ-CHAR-004",
         "Team acts on Static’s warning; systems stabilize enough for a breath.",
         "NEONBLUE: We heard you.",
         "Warning used", "echo-symbol", "Belief becomes action"),
        (8, 1, "Zoo City Streets", "MZ-CHAR-003",
         "Static writes his method: sense / know / fear / check.",
         "STATIC: What I sense. What I know. What I fear. What needs checking.",
         "Method established", "none", "Growth not cure"),
        (8, 2, "Early-Fall Storm Streets and Routine Nodes", "MZ-CHAR-003, MZ-CHAR-CLEVER",
         "Clever packs the analyzer; respects Static’s emotional reading as data of another kind.",
         "CLEVER: I can map the how. You map the why.",
         "Guest resolution", "signal-analyzer", "Complement not overwrite"),
        (8, 3, "Zoo City Streets", "MZ-CHAR-003",
         "Final image: powered-off radio still emits one soft final tone.",
         "—",
         "Final soft tone", "powered-off-radio", "Issue 02 final image prop"),
    ]
    body = [f"# {ISSUE_ID} — {TITLE} — Script\n"]
    current = 0
    for p in panels:
        if p[0] != current:
            current = p[0]
            body.append(f"### Page {current}\n")
        body.append(_panel(*p))
    return "\n".join(body)


def promote(kind: str, variant_id: str) -> None:
    code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/{kind}s/{variant_id}/promote", {"replace": False})
    if code != 200:
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/{kind}s/{variant_id}/promote", {"replace": True})
    must(code == 200, f"{kind}_promote", err or "ok")


def main() -> int:
    wait_ready()
    print("=== ONE THING: Issue 02 Static story package (outline + script) ===")

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
            "primary_character": "MZ-CHAR-003",
            "guest_character": "MZ-CHAR-CLEVER",
            "core_premise": "Storm-season interference carries a six-tone pattern Static can sense and Clever can prove",
            "main_conflict": "Static is right about the warning but overload makes him hard to use as a communicator",
            "emotional_goal": "Trust sensitivity without being silenced or cured",
            "opening_situation": "Tiny device disruptions only Static notices as fall routines resume",
            "ending_direction": "Old relay junction found; Static’s four-part emergency method; soft radio tone",
            "required_canon_references": "Static identity; Clever guest; six-tone motif; August cyan frequency continuity",
            "prohibited_story_elements": "No treating Static as irrational; no curing sensitivity; no complete Echo emblem",
            "page_count": 8,
            "panel_count": 24,
            "output_requirements": ["cover", "metadata", "social copy", "QA"],
        }
        code, created, err = req("POST", "/api/issues", payload)
        must(code == 201 and created and created.get("issue_id") == ISSUE_ID, "create_issue", err or json.dumps(created)[:300])
    else:
        print(f"[INFO] {ISSUE_ID} exists")

    def wf():
        return req("GET", f"/api/issues/{ISSUE_ID}/workflow")

    def advance(stage: str) -> None:
        code, data, err = req("POST", f"/api/issues/{ISSUE_ID}/advance", {"stage": stage})
        must(code == 200, f"advance:{stage}", err or (data or {}).get("active_stage", ""))

    def approve_gate(stage: str) -> None:
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/workflow/approve", {
            "stage": stage, "approved": True, "note": "Issue 02 Static season package"
        })
        must(code == 200, f"workflow_approve:{stage}", err or "ok")

    code, data, err = wf()
    must(code == 200, "workflow_get", err)
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
        must(code == 201, "outline_import", err or "")
        must((variant or {}).get("validation", {}).get("status") == "passed", "outline_validation", json.dumps((variant or {}).get("validation"))[:400])
        vid = variant["variant_id"]
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/outlines/{vid}/approve", {"note": "Season bible Issue 02"})
        must(code == 200, "outline_approve", err or "ok")
        promote("outline", vid)
        advance("outline")
        stage = "script"
    if stage == "script":
        code, svariant, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/import", {
            "content": script_md(), "provider": "season_bible_manual"
        })
        must(code == 201, "script_import", err or "")
        must((svariant or {}).get("validation", {}).get("status") == "passed", "script_validation", json.dumps((svariant or {}).get("validation"))[:400])
        svid = svariant["variant_id"]
        code, _, err = req("POST", f"/api/issues/{ISSUE_ID}/story/scripts/{svid}/approve", {"note": "Season bible Issue 02 script"})
        must(code == 200, "script_approve", err or "ok")
        promote("script", svid)
        approve_gate("script")
        advance("script")
        stage = "page_plan"

    code, data, err = wf()
    must(code == 200 and data.get("active_stage") == "page_plan", "final_stage", data.get("active_stage") if data else err)
    folder = ROOT / "02_MONTHLY_ISSUES" / f"{YEAR:04d}-{MONTH:02d}_Issue_{EDITION:02d}"
    must((folder / "issue_outline.md").is_file(), "outline_file")
    must((folder / "issue_script.md").is_file(), "script_file")
    print("DONE", folder.relative_to(ROOT), "stage=page_plan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
