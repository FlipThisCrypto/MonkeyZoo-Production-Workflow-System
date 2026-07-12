import json,sys
from pathlib import Path
import pytest
from PIL import Image
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import release_workspace as release
@pytest.fixture()
def factory(tmp_path):
 (tmp_path/"02_MONTHLY_ISSUES").mkdir();(tmp_path/"05_RELEASE_ARCHIVE").mkdir();issue=tmp_path/"02_MONTHLY_ISSUES/2027-06_Issue_01";issue.mkdir();(issue/"issue_brief.md").write_text("Issue ID: MZ-2027-06-01\n");metadata={"issue_id":"MZ-2027-06-01","title":"Release","format":"CHIP-0015","name":"Release","description":"Description","attributes":[],"data":{"url":"ipfs://real","sha256":"abc"}};(issue/"metadata.json").write_text(json.dumps(metadata));(issue/"social_posts.md").write_text("social");(issue/"final_export_checklist.md").write_text("checked");(issue/"cover_prompt.md").write_text("cover");panel_id="MZ-2027-06-01_P01_PANEL01";(issue/"page_panel_plan.json").write_text(json.dumps({"issue_id":"MZ-2027-06-01","pages":[{"page_number":1,"panels":[{"panel_id":panel_id,"characters":["MZ-CHAR-001"],"continuity_notes":"Keep identity","dialogue":"","caption":""}]}]}));selected=issue/"generated_art/selected_panels";selected.mkdir(parents=True);Image.new("RGB",(40,40),"blue").save(selected/f"{panel_id}.png");covers=issue/"generated_art/covers";covers.mkdir(parents=True);Image.new("RGB",(40,40),"yellow").save(covers/"main_cover.png");qa_hash=release.visual_qa_workspace.evidence(issue)["evidence_hash"];(issue/"qa_report.md").write_text(f"Evidence hash: {qa_hash}\nVERDICT: PASS\n");exports=issue/"exports";exports.mkdir();(exports/"issue.pdf").write_bytes(b"%PDF-real");(exports/"issue.cbz").write_bytes(b"PK-real");release._write_json(issue/".workflow-status.json",{"schema_version":"1.0","active_stage":"release","transitions":[],"approvals":{}});return tmp_path,issue
def test_complete_evidence_is_ready_for_approval(factory):
 root,issue=factory;ev=release.evidence(issue,root);assert not ev["blockers"];assert ev["metadata"]["format"]=="CHIP-0015";assert ev["pdfs"]==["issue.pdf"]
def test_missing_exports_qa_and_metadata_todos_block(factory):
 root,issue=factory;(issue/"exports/issue.pdf").unlink();(issue/"qa_report.md").write_text("VERDICT: HOLD");meta=json.loads((issue/"metadata.json").read_text());meta["data"]["url"]="TODO-IPFS";(issue/"metadata.json").write_text(json.dumps(meta));ev=release.evidence(issue,root);assert any("PDF" in x for x in ev["blockers"]);assert any("QA" in x for x in ev["blockers"]);assert any("TODO" in x for x in ev["blockers"])
def test_release_requires_exact_pass_and_current_qa_evidence(factory):
 root,issue=factory;(issue/"qa_report.md").write_text("VERDICT: RELEASE\n");assert any("exact PASS" in x for x in release.evidence(issue,root)["blockers"])
 qa_hash=release.visual_qa_workspace.evidence(issue)["evidence_hash"];(issue/"qa_report.md").write_text(f"Evidence hash: {qa_hash}\nVERDICT: PASS\n");Image.new("RGB",(41,40),"red").save(issue/"generated_art/selected_panels/MZ-2027-06-01_P01_PANEL01.png");assert any("stale" in x for x in release.evidence(issue,root)["blockers"])
def test_manifest_hashes_every_release_file_and_is_deterministic(factory):
 root,issue=factory;one=release.manifest(issue,root);two=release.manifest(issue,root);assert one["manifest_hash"]==two["manifest_hash"];assert all(len(x["sha256"])==64 for x in one["files"])
def test_approval_explicit_stales_on_evidence_change(factory):
 root,issue=factory;approved=release.approve(issue,root,"Owner approved");assert release.readiness(issue,root)["approval_current"];(issue/"social_posts.md").write_text("changed");status=release.readiness(issue,root);assert not status["approval_current"];assert not status["release_ready"]
def test_blockers_prevent_approval(factory):
 root,issue=factory;(issue/"exports/issue.cbz").unlink()
 with pytest.raises(release.ReleaseError,match="approval blocked"):release.approve(issue,root)
def test_manifest_promotion_requires_current_approval_and_overwrite_confirmation(factory):
 root,issue=factory
 with pytest.raises(release.ReleaseError,match="approval"):release.promote_manifest(issue,root)
 release.approve(issue,root);result=release.promote_manifest(issue,root);assert result["ok"]
 with pytest.raises(release.ReleaseError,match="replacement confirmation"):release.promote_manifest(issue,root)
def test_published_readiness_requires_archive_evidence(factory):
 root,issue=factory;release.approve(issue,root);state=json.loads((issue/".workflow-status.json").read_text());state["active_stage"]="published";release._write_json(issue/".workflow-status.json",state);assert not release.readiness(issue,root)["publication_ready"];archive=root/"05_RELEASE_ARCHIVE/2027/Issue_01";archive.mkdir(parents=True);assert not release.readiness(issue,root)["publication_ready"];(archive/"issue.pdf").write_bytes(b"pdf");assert release.readiness(issue,root)["publication_ready"]
def test_wrong_stage_rejected(factory):
 root,issue=factory;state=json.loads((issue/".workflow-status.json").read_text());state["active_stage"]="qa";release._write_json(issue/".workflow-status.json",state)
 with pytest.raises(release.ReleaseError,match="current stage"):release.manifest(issue,root)
def test_release_operation_lock_blocks_concurrent_approval(factory):
 root,issue=factory;lock=issue/".release-workspace/.manifest.lock";lock.parent.mkdir();lock.write_text("busy")
 with pytest.raises(release.ReleaseError,match="already in progress"):release.approve(issue,root)
def test_zero_byte_release_artifacts_block(factory):
 root,issue=factory;(issue/"exports/issue.pdf").write_bytes(b"");(issue/"social_posts.md").write_text("");ev=release.evidence(issue,root);assert any("PDF" in x for x in ev["blockers"]);assert any("social_posts" in x for x in ev["blockers"])
