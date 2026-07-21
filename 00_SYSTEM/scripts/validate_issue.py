#!/usr/bin/env python3
"""Validate a MonkeyZoo issue package (gate checks for Stages 4/5/9).

Usage:
    python validate_issue.py 2026-07_Issue_05 [--art] [--integration]

Checks:
  - page_panel_plan.json / art_prompt_pack.json parse and match the schemas'
    required fields, ID patterns, and cross-references
  - panel ids are unique, sequential per page, and consistent between files
  - with --art: every planned panel has a file in generated_art/selected_panels
  - with --integration: every staged panel in generated_art/
    integration_preview runs through the pixel-level integration QA gate
    (00_SYSTEM/scripts/integration/validate_integration.py) with
    plate-baseline subtraction when the panel's spec dir declares its
    background plate. Panels without a preview are skipped, not failed --
    staging integrated art is optional per-panel.
Uses jsonschema if installed; otherwise falls back to built-in checks.
"""
import json
import re
import sys
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[2]
SYSTEM = FACTORY / "00_SYSTEM"
ERRORS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"MISSING FILE: {path.name}")
    except json.JSONDecodeError as e:
        err(f"INVALID JSON in {path.name}: {e}")
    return None


_SCHEMA_CACHE: dict[str, dict] = {}


def schema_check(instance, schema_file: str, label: str) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return  # fallback checks below still run
    if schema_file not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[schema_file] = json.loads((SYSTEM / schema_file).read_text(encoding="utf-8"))
    schema = _SCHEMA_CACHE[schema_file]
    validator = jsonschema.Draft202012Validator(schema)
    for e in validator.iter_errors(instance):
        err(f"{label}: {'/'.join(map(str, e.path)) or '<root>'}: {e.message}")



def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    issue_dir = FACTORY / "02_MONTHLY_ISSUES" / sys.argv[1]
    check_art = "--art" in sys.argv
    if not issue_dir.is_dir():
        sys.exit(f"No such issue folder: {issue_dir}")

    plan = load(issue_dir / "page_panel_plan.json")
    pack = load(issue_dir / "art_prompt_pack.json")

    plan_ids: list[str] = []
    if plan:
        schema_check(plan, "page_panel_plan_schema.json", "plan")
        iid = plan.get("issue_id", "")
        if not re.match(r"^MZ-\d{4}-\d{2}-\d{2}$", iid):
            err(f"plan: bad issue_id {iid!r}")
        pages = plan.get("pages", [])
        if plan.get("page_count") != len(pages):
            err(f"plan: page_count={plan.get('page_count')} but {len(pages)} pages present")
        for page in pages:
            pn = page.get("page_number")
            if not isinstance(pn, int) or isinstance(pn, bool):
                err(f"plan: page has non-integer page_number {pn!r}")
                continue
            for i, panel in enumerate(page.get("panels", []), 1):
                pid = panel.get("panel_id", "")
                expected = f"{iid}_P{pn:02d}_PANEL{i:02d}"
                if pid != expected:
                    err(f"plan: panel id {pid!r} expected {expected!r}")
                plan_ids.append(pid)
                for field in ("action", "emotion", "location", "camera_angle"):
                    if not str(panel.get(field, "")).strip():
                        err(f"plan {pid}: empty field {field!r}")
        if len(plan_ids) != len(set(plan_ids)):
            err("plan: duplicate panel ids")

    if pack:
        schema_check(pack, "art_prompt_pack_schema.json", "pack")
        if not pack.get("style_lock_phrase", "").startswith("MonkeyZoo house style"):
            err("pack: style_lock_phrase missing or altered (Rule 3)")
        pack_ids = []
        for p in pack.get("panels", []):
            pid = p.get("panel_id", "")
            pgno = p.get("page_number", 1)
            if not isinstance(pgno, int) or isinstance(pgno, bool):
                err(f"pack {pid}: non-integer page_number {pgno!r}")
                pgno = 1  # treat as a normal panel so the remaining checks still run
            if pgno > 0:  # page 0 = establishing plates
                pack_ids.append(pid)
            if not p.get("prompt", "").startswith(pack.get("style_lock_phrase", "x")):
                err(f"pack {pid}: prompt does not start with style lock phrase")
            if not p.get("negative_prompt", "").startswith(pack.get("base_negative_prompt", "x")):
                err(f"pack {pid}: negative does not start with base negative")
            if p.get("identity_stack", {}).get("tier") == "text-only":
                print(f"  WARN {pid}: identity tier text-only (extra QA scrutiny)")
        if plan_ids and sorted(pack_ids) != sorted(plan_ids):
            missing = set(plan_ids) - set(pack_ids)
            extra = set(pack_ids) - set(plan_ids)
            if missing:
                err(f"pack: missing panels {sorted(missing)}")
            if extra:
                err(f"pack: unknown panels {sorted(extra)}")

    if check_art and plan_ids:
        sel = issue_dir / "generated_art" / "selected_panels"
        for pid in plan_ids:
            if not (sel / f"{pid}.png").exists():
                err(f"art: no selected panel for {pid}")

    if "--integration" in sys.argv:
        preview = issue_dir / "generated_art" / "integration_preview"
        previews = sorted(preview.glob("*.png")) if preview.is_dir() else []
        # covers carry deliberate flat lettering blocks (title text) that the
        # flat-region detector would flag; they are Gate B items, not panels
        previews = [p for p in previews
                    if not p.stem.endswith("_compare") and not p.stem.startswith("COVER_")]
        if not previews:
            print("  integration: no staged previews to check (skipped)")
        else:
            sys.path.insert(0, str(SYSTEM / "scripts" / "integration"))
            from validate_integration import run_gate  # noqa: E402
            spec_root = SYSTEM / "integration_upgrade" / "poc"
            # Flat-region check is skipped for (a) Close shots — a flat-cel
            # face is legitimately a big flat field — and (b) establishing
            # panels with no characters — those ARE just the plate, whose
            # flat sky/wall regions are scene content, not a pasted card.
            cameras, characterless = {}, set()
            if plan:
                for _pg in plan.get("pages", []):
                    for _pa in _pg.get("panels", []):
                        cameras[_pa["panel_id"]] = _pa.get("camera_angle", "")
                        if not _pa.get("characters"):
                            characterless.add(_pa["panel_id"])
            n_pass = 0
            for pv in previews:
                pid = pv.stem
                plate = None
                spec_file = spec_root / pid / "scene_blocking.json"
                if spec_file.exists():
                    spec = json.loads(spec_file.read_text(encoding="utf-8"))
                    candidate = FACTORY / spec.get("background_plate", "")
                    plate = candidate if candidate.exists() else None
                is_close = cameras.get(pid, "").lower().startswith("close")
                is_establish = pid in characterless
                result = run_gate(pv, plate_path=plate, skip_flat_regions=is_close or is_establish)
                tag = " (close-up)" if is_close else (" (establish)" if is_establish else "")
                base = (" (plate-baselined)" if plate else "") + tag
                if result["verdict"] == "PASS":
                    n_pass += 1
                    print(f"  integration {pid}: PASS{base}")
                else:
                    err(f"integration {pid}: {'; '.join(result['fail_reasons'])}")
            print(f"  integration: {n_pass}/{len(previews)} staged previews pass the pixel gate")

    if ERRORS:
        print(f"FAIL — {len(ERRORS)} problem(s):")
        for e in ERRORS:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS — issue package is structurally valid.")


if __name__ == "__main__":
    main()
