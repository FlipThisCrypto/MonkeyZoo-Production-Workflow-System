import json, sys
from pathlib import Path
import pytest, yaml

APP=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(APP))
import page_panel_workspace as layout

SCRIPT="""# MZ-2027-03-01 — Script
### Page 1 — Opening
**Panel 1.1 (Half)**
- Location: Signal Lab
- Characters: MZ-CHAR-001, MZ-CHAR-PATCH
- Camera: Wide
- Action: The team enters.
- Emotion: Alert
- Dialogue: ASH: Ready.
- Caption: —
- SFX: PING
- Visual notes: Console visible
- Continuity notes: Current canon
- Props: signal console
### Page 2 — Resolution
**Panel 2.1 (Full)**
- Location: Signal Lab
- Characters: MZ-CHAR-001
- Camera: Close
- Action: Ash confirms the signal.
- Emotion: Relieved
- Dialogue: ASH: Confirmed.
- Caption: End
- SFX: —
- Visual notes: Clear face
- Continuity notes: Current canon
"""

@pytest.fixture()
def factory(tmp_path):
    (tmp_path/"02_MONTHLY_ISSUES").mkdir(); (tmp_path/"05_RELEASE_ARCHIVE").mkdir(); (tmp_path/"00_SYSTEM").mkdir()
    real=Path(__file__).resolve().parents[3]
    (tmp_path/"00_SYSTEM/page_panel_plan_schema.json").write_text((real/"00_SYSTEM/page_panel_plan_schema.json").read_text(),encoding="utf-8")
    for cid,name in (("MZ-CHAR-001","Ash"),("MZ-CHAR-ZOMBIE","Patch")):
        p=tmp_path/"character-bibles"/cid; p.mkdir(parents=True); (p/"bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":cid,"current_display_name":name}}),encoding="utf-8")
    a=tmp_path/"character-bibles/MZ-CHAR-PATCH"; a.mkdir(); (a/"bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":"MZ-CHAR-PATCH","current_display_name":"Patch","alias_of":"MZ-CHAR-ZOMBIE"}}),encoding="utf-8")
    issue=tmp_path/"02_MONTHLY_ISSUES/2027-03_Issue_01"; issue.mkdir(); (issue/"issue_brief.md").write_text("Issue ID: MZ-2027-03-01\n",encoding="utf-8"); (issue/"metadata.json").write_text(json.dumps({"issue_id":"MZ-2027-03-01","title":"Test"}),encoding="utf-8"); (issue/"issue_script.md").write_text(SCRIPT,encoding="utf-8")
    layout._write_json(issue/".workflow-status.json",{"schema_version":"1.0","active_stage":"page_plan","transitions":[],"approvals":{}}); layout.bible_store._IDENTITY_INDEXES.clear()
    return tmp_path,issue

def test_parser_builds_schema_valid_plan_and_resolves_alias(factory):
    root,issue=factory; plan=layout.parse_script(issue,root); result=layout.validate_plan(plan,root)
    assert result["status"]=="passed"; assert plan["pages"][0]["panels"][0]["characters"]==["MZ-CHAR-001","MZ-CHAR-ZOMBIE"]
    assert plan["pages"][0]["panels"][0]["_props"]==["signal console"]

UNKNOWN_SCRIPT="""# MZ-2027-03-01 — Script
### Page 1 — Opening
**Panel 1.1 (Full)**
- Location: Signal Lab
- Characters: MZ-CHAR-001, MZ-CHAR-DOESNOTEXIST
- Camera: Wide
- Action: A stranger appears.
- Emotion: Alert
- Dialogue: ASH: Who are you?
- Caption: —
- SFX: —
- Visual notes: —
- Continuity notes: —
"""

def test_unknown_character_is_flagged_not_fatal(factory):
    # A script naming an unknown character must DEGRADE (surface the name in
    # _unknown_characters), never crash the whole parse. This relies on
    # bible_store.BibleStoreError subclassing ValueError so parse_script's
    # `except ValueError` catches the unresolved name. Lock both the observable
    # behaviour and the underlying type contract, so a future reparent of
    # BibleStoreError (or a narrowed except) can't silently turn one bad name in
    # a user-authored script into a hard failure of the entire layout stage.
    assert issubclass(layout.bible_store.BibleStoreError, ValueError)
    root,issue=factory; (issue/"issue_script.md").write_text(UNKNOWN_SCRIPT,encoding="utf-8")
    plan=layout.parse_script(issue,root)                     # must not raise
    panel=plan["pages"][0]["panels"][0]
    assert panel["characters"]==["MZ-CHAR-001"]             # the resolvable name still resolves
    assert panel["_unknown_characters"]==["MZ-CHAR-DOESNOTEXIST"]  # the unknown is flagged, not fatal
    assert "MZ-CHAR-DOESNOTEXIST" not in panel["references_required"]

def test_variant_requires_page_plan_stage(factory):
    root,issue=factory; state=json.loads((issue/".workflow-status.json").read_text()); state["active_stage"]="script"; layout._write_json(issue/".workflow-status.json",state)
    with pytest.raises(layout.PagePanelError,match="current stage is script"): layout.create_variant(issue,root)

def test_duplicate_and_missing_panel_numbers_fail(factory):
    root,issue=factory; plan=layout.parse_script(issue,root); duplicate=json.loads(json.dumps(plan)); duplicate["pages"][0]["panels"].append(duplicate["pages"][0]["panels"][0])
    result=layout.validate_plan(duplicate,root); assert result["status"]=="failed"; assert any("Duplicate" in f["message"] for f in result["findings"])

def test_multiple_variants_unique_and_preserved(factory):
    root,issue=factory; one=layout.create_variant(issue,root); two=layout.create_variant(issue,root)
    assert one["variant_id"]!=two["variant_id"]; assert len(layout.variants(issue))==2

def test_approval_explicit_immutable_and_script_bound(factory):
    root,issue=factory; variant=layout.create_variant(issue,root); approved=layout.approve(issue,root,variant["variant_id"]); assert approved["approval_current"]
    with pytest.raises(layout.PagePanelError,match="immutable"): layout.approve(issue,root,variant["variant_id"])
    (issue/"issue_script.md").write_text(SCRIPT+"\nChanged\n",encoding="utf-8"); assert layout.variants(issue)[0]["script_stale"]
    with pytest.raises(layout.PagePanelError,match="current approved"): layout.promote(issue,root,variant["variant_id"])

def test_unapproved_cannot_promote(factory):
    root,issue=factory; variant=layout.create_variant(issue,root)
    with pytest.raises(layout.PagePanelError,match="current approved"): layout.promote(issue,root,variant["variant_id"])

def test_promotion_atomic_overwrite_and_duplicate_guards(factory):
    root,issue=factory; variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"]); result=layout.promote(issue,root,variant["variant_id"])
    assert result["ok"]; assert json.loads((issue/"page_panel_plan.json").read_text())["pages"]; assert not list(issue.rglob("*.tmp"))
    with pytest.raises(layout.PagePanelError,match="already promoted"): layout.promote(issue,root,variant["variant_id"],True)

def test_existing_canonical_plan_not_silently_overwritten(factory):
    root,issue=factory; (issue/"page_panel_plan.json").write_text('{"owner":true}',encoding="utf-8"); variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"])
    with pytest.raises(layout.PagePanelError,match="replacement confirmation"): layout.promote(issue,root,variant["variant_id"])
    assert json.loads((issue/"page_panel_plan.json").read_text())=={"owner":True}

def _fail_post_write_validation(monkeypatch):
    original = layout.validate_canonical_payload
    calls = 0
    def validate(plan, root):
        nonlocal calls
        calls += 1
        if calls == 2:
            return {"status":"failed","findings":[{"severity":"error","message":"injected final validation failure"}],"errors":1}
        return original(plan, root)
    monkeypatch.setattr(layout, "validate_canonical_payload", validate)

def test_failed_final_validation_restores_existing_plan_and_writes_no_provenance(factory, monkeypatch):
    root,issue=factory; destination=issue/"page_panel_plan.json"; original=b'{"owner":true}\n'; destination.write_bytes(original)
    variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"]); _fail_post_write_validation(monkeypatch)
    with pytest.raises(layout.PagePanelError,match="Post-promotion validation failed"): layout.promote(issue,root,variant["variant_id"],True)
    assert destination.read_bytes()==original
    assert not (issue/".layout-workspace/promotions"/f'{variant["variant_id"]}.json').exists()

def test_failed_final_validation_does_not_create_plan_or_provenance(factory, monkeypatch):
    root,issue=factory; variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"]); _fail_post_write_validation(monkeypatch)
    with pytest.raises(layout.PagePanelError,match="Post-promotion validation failed"): layout.promote(issue,root,variant["variant_id"])
    assert not (issue/"page_panel_plan.json").exists()
    assert not (issue/".layout-workspace/promotions"/f'{variant["variant_id"]}.json').exists()

def test_successful_replacement_preserves_backup_and_writes_canonical_plan(factory):
    root,issue=factory; destination=issue/"page_panel_plan.json"; original=b'{"owner":true}\n'; destination.write_bytes(original)
    variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"]); result=layout.promote(issue,root,variant["variant_id"],True)
    backup=issue/result["promotion"]["backup"]
    assert backup.read_bytes()==original
    assert json.loads(destination.read_text(encoding="utf-8"))["issue_id"]=="MZ-2027-03-01"
    assert (issue/".layout-workspace/promotions"/f'{variant["variant_id"]}.json').exists()

def test_concurrent_promotion_lock_returns_conflict(factory):
    root,issue=factory; variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"]); lock=issue/".layout-workspace/.promotion.lock"; lock.write_text("busy")
    with pytest.raises(layout.PagePanelError,match="already in progress"): layout.promote(issue,root,variant["variant_id"])
    assert not (issue/"page_panel_plan.json").exists()

def test_invalid_variant_id_rejects_traversal(factory):
    root,issue=factory
    with pytest.raises(layout.PagePanelError,match="Invalid"): layout.approve(issue,root,"../escape")


# ---------------------------------------------------------------------------
# CLI/Studio divergence: the two surfaces must agree on "is this plan complete?"
#
# The Stage 4/5/9 CLI gate required four non-empty fields:
#     validate_issue.py: for field in ("action", "emotion", "location", "camera_angle")
# Both Studio validators checked only two:
#     page_panel_workspace.py: for field in ("location", "action")
# and the schema declared emotion/camera_angle as bare {"type": "string"}, so ""
# satisfied it. A plan with empty camera_angle/emotion therefore PASSED the
# Studio's promote gate and then hard-failed the CLI gate -- after art had been
# generated from it against fabricated defaults ("medium shot" / "neutral").
#
# Reachable without anyone doing anything odd: the Studio's own script generator
# emits the label "- Camera angle:", while the parser keys on "camera", so that
# panel parses to camera_angle "" (00_SYSTEM/agents/stage_04_script.md requires
# the field: "no field left blank").
#
# Fixed in the ONE place all four validators already read -- the schema. Both
# Studio validators run Draft202012Validator against it
# (page_panel_workspace.py:180 and :206), issue_workflow._schema_errors is
# schema-only, and validate_issue.schema_check uses the same file. Scoped to
# exactly these four fields: art_prompt/negative_prompt/controlnet_required are
# legitimately "" until Stage 5 fills them (stage_04_script.md rule 8).
# ---------------------------------------------------------------------------
import json as _json

from jsonschema import Draft202012Validator as _Validator

_GATED_FIELDS = ("location", "camera_angle", "action", "emotion")
_ROOT = Path(__file__).resolve().parents[3]


def _panel_schema() -> dict:
    schema = _json.loads(
        (_ROOT / "00_SYSTEM" / "page_panel_plan_schema.json").read_text(encoding="utf-8"))
    return schema["properties"]["pages"]["items"]["properties"]["panels"]["items"]["properties"]


def test_schema_requires_the_same_four_fields_the_cli_gate_requires():
    """The CLI's field list is the documented contract; the schema must enforce it."""
    props = _panel_schema()
    for field in _GATED_FIELDS:
        assert props[field].get("minLength") == 1, f"{field} may still be empty"
        assert props[field].get("pattern") == r"\S", f"{field} may still be whitespace-only"


def test_stage5_filled_fields_are_still_allowed_to_be_empty():
    """Over-correction guard: these are legitimately "" until Stage 5 (rule 8)."""
    props = _panel_schema()
    for field in ("art_prompt", "negative_prompt", "controlnet_required"):
        assert "minLength" not in props[field], (
            f"{field} was tightened; Stage 4 writes it as \"\" and Stage 5 fills it, "
            "so this would block every promotion")


def _plan_with(**overrides):
    panel = {
        "panel_id": "MZ-2026-05-01_P01_PANEL01", "characters": ["MZ-CHAR-001"],
        "location": "Alley", "camera_angle": "Wide", "action": "Moodz walks",
        "emotion": "Wary", "dialogue": "", "caption": "", "visual_notes": "n",
        "continuity_notes": "n", "art_prompt": "", "negative_prompt": "",
        "references_required": [], "lora_required": [], "controlnet_required": "",
        "seed_strategy": "per_panel",
    }
    panel.update(overrides)
    return {"issue_id": "MZ-2026-05-01", "issue_title": "T", "page_count": 1,
            "pages": [{"page_number": 1, "page_purpose": "Open", "panels": [panel]}]}


def _schema_errors(plan) -> list[str]:
    schema = _json.loads(
        (_ROOT / "00_SYSTEM" / "page_panel_plan_schema.json").read_text(encoding="utf-8"))
    return [e.message for e in _Validator(schema).iter_errors(plan)]


@pytest.mark.parametrize("field", _GATED_FIELDS)
def test_empty_gated_field_is_rejected(field):
    assert _schema_errors(_plan_with(**{field: ""})), f"empty {field} still validates"


@pytest.mark.parametrize("field", _GATED_FIELDS)
def test_whitespace_only_gated_field_is_rejected(field):
    """The Studio used a falsy check, the CLI used .strip() -- '   ' split them."""
    assert _schema_errors(_plan_with(**{field: "   "})), f"whitespace-only {field} still validates"


def test_a_complete_panel_still_validates():
    assert _schema_errors(_plan_with()) == []


def test_every_tracked_page_plan_still_satisfies_the_tightened_schema():
    """Real data guard: tightening must not invalidate a plan the factory shipped.

    2026-07_Mango_Pier is excluded: it fails on a pre-existing issue_id naming
    violation (`MZ-2026-07-MANGO`), unrelated to these four fields. Verified: 0
    of its 21 errors are on location/camera_angle/action/emotion.
    """
    plans = sorted((_ROOT / "02_MONTHLY_ISSUES").glob("*/page_panel_plan.json"))
    assert plans, "no tracked page plans found -- the guard is not actually checking anything"
    for path in plans:
        if "Mango_Pier" in str(path):
            continue
        errors = _schema_errors(_json.loads(path.read_text(encoding="utf-8")))
        assert errors == [], f"{path.name} stopped validating: {errors[:3]}"
