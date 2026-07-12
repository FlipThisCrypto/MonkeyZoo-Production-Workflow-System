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

def test_concurrent_promotion_lock_returns_conflict(factory):
    root,issue=factory; variant=layout.create_variant(issue,root); layout.approve(issue,root,variant["variant_id"]); lock=issue/".layout-workspace/.promotion.lock"; lock.write_text("busy")
    with pytest.raises(layout.PagePanelError,match="already in progress"): layout.promote(issue,root,variant["variant_id"])
    assert not (issue/"page_panel_plan.json").exists()

def test_invalid_variant_id_rejects_traversal(factory):
    root,issue=factory
    with pytest.raises(layout.PagePanelError,match="Invalid"): layout.approve(issue,root,"../escape")
