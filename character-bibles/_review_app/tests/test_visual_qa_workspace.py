import io,json,sys
from pathlib import Path
import pytest
from PIL import Image
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import visual_qa_workspace as qa
@pytest.fixture()
def factory(tmp_path):
 (tmp_path/"02_MONTHLY_ISSUES").mkdir();(tmp_path/"05_RELEASE_ARCHIVE").mkdir();issue=tmp_path/"02_MONTHLY_ISSUES/2027-05_Issue_01";issue.mkdir();(issue/"issue_brief.md").write_text("Issue ID: MZ-2027-05-01\n",encoding="utf-8");(issue/"metadata.json").write_text(json.dumps({"issue_id":"MZ-2027-05-01","title":"QA Test"}),encoding="utf-8");(issue/"cover_prompt.md").write_text("cover");(issue/"final_export_checklist.md").write_text("checklist")
 panel={"panel_id":"MZ-2027-05-01_P01_PANEL01","characters":["MZ-CHAR-001"],"dialogue":"Ready","caption":"","continuity_notes":"Keep badge"};(issue/"page_panel_plan.json").write_text(json.dumps({"issue_id":"MZ-2027-05-01","pages":[{"page_number":1,"panels":[panel]}]}));selected=issue/"generated_art/selected_panels";selected.mkdir(parents=True);Image.new("RGB",(40,30),"blue").save(selected/f"{panel['panel_id']}.png")
 qa._write_json(issue/".workflow-status.json",{"schema_version":"1.0","active_stage":"qa","transitions":[],"approvals":{}});return tmp_path,issue,panel["panel_id"]
def test_evidence_inventory_dimensions_and_mapping(factory):
 root,issue,pid=factory;ev=qa.evidence(issue);assert ev["selected_panel_count"]==1;assert ev["panels"][0]["width"]==40;assert ev["panels"][0]["format"]=="PNG";assert not ev["blockers"];assert ev["advisories"]==["cover image is absent; Release owns the blocking cover-deliverable requirement"]
def test_missing_duplicate_invalid_and_metadata_checks(factory):
 root,issue,pid=factory;(issue/"generated_art/selected_panels"/f"{pid}.png").unlink();ev=qa.evidence(issue);assert ev["checks"]["missing_panels"]==[pid]
def test_pass_blocked_by_evidence_but_hold_and_fail_allowed(factory):
 root,issue,pid=factory;(issue/"generated_art/selected_panels"/f"{pid}.png").unlink();review=qa.create_review(issue,root)
 with pytest.raises(qa.VisualQAError,match="PASS is blocked"):qa.finalize(issue,root,review["review_id"],"pass")
 finalized=qa.finalize(issue,root,review["review_id"],"hold","Needs art",["identity pending"]);assert finalized["verdict"]=="HOLD";assert finalized["approval_current"]
 failed=qa.create_review(issue,root);assert qa.finalize(issue,root,failed["review_id"],"fail")["verdict"]=="FAIL"

def test_checklist_and_required_continuity_block_pass(factory):
 root,issue,pid=factory;(issue/"final_export_checklist.md").unlink();plan=json.loads((issue/"page_panel_plan.json").read_text());plan["pages"][0]["panels"][0]["continuity_notes"]="";(issue/"page_panel_plan.json").write_text(json.dumps(plan));review=qa.create_review(issue,root)
 assert "final export checklist is missing" in review["evidence"]["blockers"];assert any("continuity notes missing" in x for x in review["evidence"]["blockers"])
 with pytest.raises(qa.VisualQAError,match="PASS is blocked"):qa.finalize(issue,root,review["review_id"],"pass")
def test_finalized_review_immutable_and_stale_evidence_blocks(factory):
 root,issue,pid=factory;review=qa.create_review(issue,root);qa.finalize(issue,root,review["review_id"],"pass")
 with pytest.raises(qa.VisualQAError,match="immutable"):qa.finalize(issue,root,review["review_id"],"fail")
 Image.new("RGB",(41,30),"red").save(issue/"generated_art/selected_panels"/f"{pid}.png");assert qa.reviews(issue)[0]["evidence_stale"]
 with pytest.raises(qa.VisualQAError,match="current finalized"):qa.promote(issue,root,review["review_id"])
def test_promotion_writes_verdict_and_workflow_gate_reads_it(factory):
 root,issue,pid=factory;review=qa.create_review(issue,root);qa.finalize(issue,root,review["review_id"],"pass");result=qa.promote(issue,root,review["review_id"]);assert result["ok"];assert "VERDICT: PASS" in (issue/"qa_report.md").read_text();assert qa.issue_workflow._stage_validation("qa",issue,root)["status"]=="passed"
def test_existing_report_and_duplicate_promotion_blocked(factory):
 root,issue,pid=factory;(issue/"qa_report.md").write_text("owner");review=qa.create_review(issue,root);qa.finalize(issue,root,review["review_id"],"pass")
 with pytest.raises(qa.VisualQAError,match="replacement confirmation"):qa.promote(issue,root,review["review_id"])
 qa.promote(issue,root,review["review_id"],True)
 with pytest.raises(qa.VisualQAError,match="already promoted"):qa.promote(issue,root,review["review_id"],True)
def test_invalid_review_id_and_wrong_stage(factory):
 root,issue,pid=factory
 with pytest.raises(qa.VisualQAError,match="Invalid"):qa.finalize(issue,root,"../x","pass")
 state=json.loads((issue/".workflow-status.json").read_text());state["active_stage"]="art_production";qa._write_json(issue/".workflow-status.json",state)
 with pytest.raises(qa.VisualQAError,match="current stage"):qa.create_review(issue,root)
def test_cover_change_stales_review_and_promotion_lock_blocks(factory):
 root,issue,pid=factory;cover=issue/"generated_art/covers";cover.mkdir(parents=True);Image.new("RGB",(40,30),"green").save(cover/"main_cover.png");review=qa.create_review(issue,root);Image.new("RGB",(40,30),"red").save(cover/"main_cover.png");assert qa.reviews(issue)[0]["evidence_stale"]
 review2=qa.create_review(issue,root);qa.finalize(issue,root,review2["review_id"],"pass");lock=issue/".qa-workspace/.promotion.lock";lock.write_text("busy")
 with pytest.raises(qa.VisualQAError,match="already in progress") as error:qa.promote(issue,root,review2["review_id"])
 assert error.value.status==409

def test_provenance_failure_restores_existing_owner_report(factory,monkeypatch):
 root,issue,pid=factory;destination=issue/"qa_report.md";owner=b"owner-authored\r\nexact bytes\r\n";destination.write_bytes(owner);review=qa.create_review(issue,root);qa.finalize(issue,root,review["review_id"],"pass")
 monkeypatch.setattr(qa,"_write_json",lambda *_:(_ for _ in ()).throw(OSError("provenance failed")))
 with pytest.raises(OSError,match="provenance failed"):qa.promote(issue,root,review["review_id"],True)
 assert destination.read_bytes()==owner;assert not (issue/".qa-workspace/promotions"/f'{review["review_id"]}.json').exists()

def test_provenance_failure_removes_first_report_and_provenance(factory,monkeypatch):
 root,issue,pid=factory;review=qa.create_review(issue,root);qa.finalize(issue,root,review["review_id"],"pass");monkeypatch.setattr(qa,"_write_json",lambda *_:(_ for _ in ()).throw(OSError("provenance failed")))
 with pytest.raises(OSError):qa.promote(issue,root,review["review_id"])
 assert not (issue/"qa_report.md").exists();assert not (issue/".qa-workspace/promotions"/f'{review["review_id"]}.json').exists()

def test_successful_replacement_preserves_backup_and_verifies_identity(factory):
 root,issue,pid=factory;destination=issue/"qa_report.md";owner=b"owner original\n";destination.write_bytes(owner);review=qa.create_review(issue,root);finalized=qa.finalize(issue,root,review["review_id"],"pass");result=qa.promote(issue,root,review["review_id"],True);report=destination.read_text();provenance=result["promotion"]
 assert (issue/provenance["backup"]).read_bytes()==owner
 assert f'Review ID: {review["review_id"]}' in report;assert f'Evidence hash: {finalized["evidence_hash"]}' in report;assert "VERDICT: PASS" in report
 assert provenance["review_id"]==review["review_id"] and provenance["evidence_hash"]==finalized["evidence_hash"] and provenance["verdict"]=="PASS"

def test_release_gate_rejects_promoted_non_pass_verdict(factory):
 root,issue,pid=factory;(issue/"generated_art/selected_panels"/f"{pid}.png").unlink();review=qa.create_review(issue,root);qa.finalize(issue,root,review["review_id"],"hold");qa.promote(issue,root,review["review_id"])
 assert qa.issue_workflow._stage_validation("qa",issue,root)["status"]=="failed"
