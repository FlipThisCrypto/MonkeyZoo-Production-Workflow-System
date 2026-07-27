import io,json,sys,zipfile
from pathlib import Path
import pytest
from PIL import Image
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import release_workspace as release
def zip_bytes(name="page.txt",data=b"release"):
 out=io.BytesIO()
 with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as archive:
  if name is not None:archive.writestr(name,data)
 return out.getvalue()
@pytest.fixture()
def factory(tmp_path):
 (tmp_path/"02_MONTHLY_ISSUES").mkdir();(tmp_path/"05_RELEASE_ARCHIVE").mkdir();issue=tmp_path/"02_MONTHLY_ISSUES/2027-06_Issue_01";issue.mkdir();(issue/"issue_brief.md").write_text("Issue ID: MZ-2027-06-01\n");metadata={"issue_id":"MZ-2027-06-01","title":"Release","format":"CHIP-0015","name":"Release","description":"Description","attributes":[],"data":{"url":"ipfs://real","sha256":"abc"}};(issue/"metadata.json").write_text(json.dumps(metadata));(issue/"social_posts.md").write_text("social");(issue/"final_export_checklist.md").write_text("checked");(issue/"cover_prompt.md").write_text("cover");panel_id="MZ-2027-06-01_P01_PANEL01";(issue/"page_panel_plan.json").write_text(json.dumps({"issue_id":"MZ-2027-06-01","pages":[{"page_number":1,"panels":[{"panel_id":panel_id,"characters":["MZ-CHAR-001"],"continuity_notes":"Keep identity","dialogue":"","caption":""}]}]}));selected=issue/"generated_art/selected_panels";selected.mkdir(parents=True);Image.new("RGB",(40,40),"blue").save(selected/f"{panel_id}.png");covers=issue/"generated_art/covers";covers.mkdir(parents=True);Image.new("RGB",(40,40),"yellow").save(covers/"main_cover.png");qa_hash=release.visual_qa_workspace.evidence(issue)["evidence_hash"];(issue/"qa_report.md").write_text(f"Evidence hash: {qa_hash}\nVERDICT: PASS\n");exports=issue/"exports";exports.mkdir();(exports/"issue.pdf").write_bytes(b"%PDF-real");(exports/"issue.cbz").write_bytes(zip_bytes());release._write_json(issue/".workflow-status.json",{"schema_version":"1.0","active_stage":"release","transitions":[],"approvals":{}});return tmp_path,issue
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
 root,issue=factory;release.approve(issue,root,"Owner approved");assert release.readiness(issue,root)["approval_current"];(issue/"social_posts.md").write_text("changed");status=release.readiness(issue,root);assert not status["approval_current"];assert not status["release_ready"]
def test_blockers_prevent_approval(factory):
 root,issue=factory;(issue/"exports/issue.cbz").unlink()
 with pytest.raises(release.ReleaseError,match="approval blocked"):release.approve(issue,root)
@pytest.mark.parametrize("content",[b"random nonzero bytes",b""])
def test_invalid_or_zero_byte_cbz_blocks_release(factory,content):
 root,issue=factory;(issue/"exports/issue.cbz").write_bytes(content);ev=release.evidence(issue,root);assert ev["invalid_packages"]==["issue.cbz"]
 with pytest.raises(release.ReleaseError,match="Invalid CBZ or ZIP"):release.approve(issue,root)
def test_empty_zip_blocks_release(factory):
 root,issue=factory;(issue/"exports/issue.cbz").write_bytes(zip_bytes(None));ev=release.evidence(issue,root);assert ev["packages"]==[];assert "issue.cbz" in ev["invalid_packages"]
def test_truncated_zip_blocks_release(factory):
 root,issue=factory;payload=zip_bytes();(issue/"exports/issue.cbz").write_bytes(payload[:-8]);assert "issue.cbz" in release.evidence(issue,root)["invalid_packages"]
@pytest.mark.parametrize("suffix",["zip","cbz"])
def test_valid_archive_with_real_member_satisfies_package_requirement(factory,suffix):
 root,issue=factory;(issue/"exports/issue.cbz").unlink();(issue/f"exports/issue.{suffix}").write_bytes(zip_bytes("page.png",b"real image bytes"));ev=release.evidence(issue,root);assert ev["packages"]==[f"issue.{suffix}"];assert not ev["invalid_packages"]
def test_manifest_promotion_requires_current_approval_and_overwrite_confirmation(factory):
 root,issue=factory
 with pytest.raises(release.ReleaseError,match="approval"):release.promote_manifest(issue,root)
 release.approve(issue,root);result=release.promote_manifest(issue,root);assert result["ok"]
 with pytest.raises(release.ReleaseError,match="replacement confirmation"):release.promote_manifest(issue,root)
def test_manifest_promotion_lock_returns_structured_conflict(factory):
 root,issue=factory;release.approve(issue,root);lock=issue/".release-workspace/.manifest.lock";lock.write_text("busy")
 with pytest.raises(release.ReleaseError,match="already in progress") as exc:release.promote_manifest(issue,root)
 assert exc.value.status==409
def test_promotion_verification_failure_restores_existing_manifest(factory,monkeypatch):
 root,issue=factory;release.approve(issue,root);destination=issue/"release_hash_manifest.json";original=b"owner-authored exact bytes\r\n";destination.write_bytes(original);real=release._read_json
 def fail_destination(path,default=None):
  if path==destination:raise release.ReleaseError("verification failed",409)
  return real(path,default)
 monkeypatch.setattr(release,"_read_json",fail_destination)
 with pytest.raises(release.ReleaseError,match="verification failed"):release.promote_manifest(issue,root,True)
 assert destination.read_bytes()==original
def test_first_promotion_verification_failure_leaves_no_manifest(factory,monkeypatch):
 root,issue=factory;release.approve(issue,root);destination=issue/"release_hash_manifest.json";real=release._read_json
 monkeypatch.setattr(release,"_read_json",lambda path,default=None: (_ for _ in ()).throw(release.ReleaseError("verification failed",409)) if path==destination else real(path,default))
 with pytest.raises(release.ReleaseError,match="verification failed"):release.promote_manifest(issue,root)
 assert not destination.exists()
def test_stale_evidence_blocks_manifest_promotion(factory):
 root,issue=factory;release.approve(issue,root);(issue/"social_posts.md").write_text("changed")
 with pytest.raises(release.ReleaseError,match="Current release approval"):release.promote_manifest(issue,root)
def test_missing_and_mismatched_approved_manifest_block_promotion(factory):
 root,issue=factory;approved=release.approve(issue,root);source=issue/".release-workspace/manifests"/f"{approved['manifest_hash']}.json";source.unlink()
 with pytest.raises(release.ReleaseError,match="missing"):release.promote_manifest(issue,root)
 release._write_json(source,{"manifest_hash":approved["manifest_hash"],"evidence_hash":"0"*64})
 with pytest.raises(release.ReleaseError,match="hash is missing or mismatched"):release.promote_manifest(issue,root)
def test_successful_promotion_agrees_with_approval_and_current_evidence(factory):
 root,issue=factory;approved=release.approve(issue,root);result=release.promote_manifest(issue,root);written=json.loads((issue/"release_hash_manifest.json").read_text());assert result["manifest_hash"]==approved["manifest_hash"]==written["manifest_hash"];assert result["evidence_hash"]==approved["evidence_hash"]==release.evidence(issue,root)["evidence_hash"]==written["evidence_hash"]
def test_published_readiness_requires_recognizable_release_artifact(factory):
 root,issue=factory;release.approve(issue,root);state=json.loads((issue/".workflow-status.json").read_text());state["active_stage"]="published";release._write_json(issue/".workflow-status.json",state);archive=root/"05_RELEASE_ARCHIVE/2027"/issue.name;archive.mkdir(parents=True);(archive/"unrelated.txt").write_text("not a release artifact");assert not release.readiness(issue,root)["publication_ready"];(archive/"issue.pdf").write_bytes(b"pdf");assert release.readiness(issue,root)["publication_ready"]
def test_wrong_stage_rejected(factory):
 root,issue=factory;state=json.loads((issue/".workflow-status.json").read_text());state["active_stage"]="qa";release._write_json(issue/".workflow-status.json",state)
 with pytest.raises(release.ReleaseError,match="current stage"):release.manifest(issue,root)
def test_release_operation_lock_blocks_concurrent_approval(factory):
 root,issue=factory;lock=issue/".release-workspace/.manifest.lock";lock.parent.mkdir();lock.write_text("busy")
 with pytest.raises(release.ReleaseError,match="already in progress"):release.approve(issue,root)
def test_zero_byte_release_artifacts_block(factory):
 root,issue=factory;(issue/"exports/issue.pdf").write_bytes(b"");(issue/"social_posts.md").write_text("");ev=release.evidence(issue,root);assert any("PDF" in x for x in ev["blockers"]);assert any("social_posts" in x for x in ev["blockers"])

def test_publish_archive_requires_approval_manifest_and_writes_artifacts(factory):
 root,issue=factory
 with pytest.raises(release.ReleaseError, match="approval"):
  release.publish_archive(issue, root)
 release.approve(issue, root)
 with pytest.raises(release.ReleaseError, match="release_hash_manifest"):
  release.publish_archive(issue, root)
 release.promote_manifest(issue, root)
 result = release.publish_archive(issue, root)
 assert result["ok"]
 archive = root / "05_RELEASE_ARCHIVE/2027" / issue.name
 assert archive.exists()
 assert any(archive.glob("*.pdf"))
 assert any(list(archive.glob("*.zip")) + list(archive.glob("*.cbz")))
 assert result["publication"]["archive_path"].endswith(issue.name.replace("\\", "/").split("/")[-1]) or issue.name in result["publication"]["archive_path"]
 assert release.readiness(issue, root)["publication_ready"] is False
 state = json.loads((issue / ".workflow-status.json").read_text())
 state["active_stage"] = "published"
 release._write_json(issue / ".workflow-status.json", state)
 assert release.readiness(issue, root)["publication_ready"]
 with pytest.raises(release.ReleaseError, match="replacement confirmation"):
  release.publish_archive(issue, root)
 release.publish_archive(issue, root, True)


def test_archive_path_is_unique_per_issue_folder_not_edition_only(factory):
 root, issue = factory
 primary = release._archive(issue, root)
 legacy = release._legacy_archive(issue, root)
 assert primary.name == issue.name
 assert legacy.name == "Issue_01"
 assert primary != legacy
 # Legacy still resolves when only legacy exists
 legacy.mkdir(parents=True)
 (legacy / "issue.pdf").write_bytes(b"pdf")
 assert release._resolve_archive(issue, root) == legacy


def test_publish_archive_survives_failed_recopy(factory, monkeypatch):
 # A re-publish (replace) whose copy fails partway must NOT destroy the
 # previously published release archive -- it is built in staging and swapped
 # in only on success.
 root, issue = factory
 release.approve(issue, root); release.promote_manifest(issue, root); release.publish_archive(issue, root)
 archive = root / "05_RELEASE_ARCHIVE/2027" / issue.name
 before = sorted(p.name for p in archive.iterdir()); assert before
 state = json.loads((issue / ".workflow-status.json").read_text()); state["active_stage"] = "published"; release._write_json(issue / ".workflow-status.json", state)
 import shutil as _sh
 real = _sh.copy2; calls = {"n": 0}
 def flaky(src, dst, *a, **k):
  calls["n"] += 1
  if calls["n"] == 2:
   raise OSError("disk full mid-publish")
  return real(src, dst, *a, **k)
 monkeypatch.setattr(_sh, "copy2", flaky)
 with pytest.raises(OSError):
  release.publish_archive(issue, root, True)
 monkeypatch.setattr(_sh, "copy2", real)
 assert archive.exists(); assert sorted(p.name for p in archive.iterdir()) == before   # old archive intact
 assert [p.name for p in archive.parent.iterdir() if ".staging" in p.name] == []        # no staging litter

