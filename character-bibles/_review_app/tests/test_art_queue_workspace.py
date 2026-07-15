import io,json,sys
from pathlib import Path
import pytest,yaml
from PIL import Image
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import art_queue_workspace as art

@pytest.fixture()
def factory(tmp_path):
 (tmp_path/"02_MONTHLY_ISSUES").mkdir();(tmp_path/"05_RELEASE_ARCHIVE").mkdir();issue=tmp_path/"02_MONTHLY_ISSUES/2027-04_Issue_01";issue.mkdir()
 (issue/"issue_brief.md").write_text("Issue ID: MZ-2027-04-01\n",encoding="utf-8");(issue/"metadata.json").write_text(json.dumps({"issue_id":"MZ-2027-04-01"}),encoding="utf-8")
 panel={"panel_id":"MZ-2027-04-01_P01_PANEL01","characters":["MZ-CHAR-001"],"location":"Lab","props":["console"],"action":"Enter","dialogue":"Ready","caption":"","continuity_notes":"Keep badge","art_prompt":"Ash enters the signal lab","negative_prompt":"no text"}
 (issue/"page_panel_plan.json").write_text(json.dumps({"issue_id":"MZ-2027-04-01","pages":[{"page_number":1,"panels":[panel]}]}),encoding="utf-8")
 bible=tmp_path/"character-bibles/MZ-CHAR-001";bible.mkdir(parents=True);(bible/"bible.yaml").write_text(yaml.safe_dump({"identification":{"character_id":"MZ-CHAR-001","current_display_name":"Ash"},"visual_canon":{"primary_reference_image":"references/primary.png","features_that_must_never_change":[]}}),encoding="utf-8")
 art._write_json(issue/".workflow-status.json",{"schema_version":"1.0","active_stage":"art_production","transitions":[],"approvals":{}});art.bible_store._IDENTITY_INDEXES.clear();return tmp_path,issue,panel["panel_id"]
def png(color="yellow"):
 out=io.BytesIO();Image.new("RGB",(32,24),color).save(out,"PNG");return out.getvalue()
def test_queue_has_one_item_per_panel_and_individual_refs(factory):
 root,issue,pid=factory;q=art.build_queue(issue,root,True);assert len(q["items"])==1;assert q["items"][0]["references"][0]["reference_kind"]=="individual_character";assert q["items"][0]["props"]==["console"];assert q["items"][0]["location_ref"]["display_name"]=="Lab";assert q["items"][0]["prop_refs"][0]["display_name"]=="console"
def test_prompt_is_manual_and_hash_bound(factory):
 root,issue,pid=factory;p=art.prompt_package(issue,root,pid);assert p["execution_mode"]=="manual";assert p["panel_id"]==pid;assert len(p["plan_hash"])==64
def test_import_validates_image_and_records_manual_source(factory):
 root,issue,pid=factory;r=art.import_attempt(issue,root,pid,png(),"panel.png","external");assert r["format"]=="PNG";assert r["source_type"]=="manual_import";assert len(art.attempts(issue,pid))==1
def test_invalid_file_and_panel_rejected(factory):
 root,issue,pid=factory
 with pytest.raises(art.ArtQueueError,match="valid supported image"):art.import_attempt(issue,root,pid,b"not image","bad.png")
 with pytest.raises(art.ArtQueueError,match="Invalid panel"):art.import_attempt(issue,root,"../escape",png(),"x.png")
def test_select_preferred_creates_real_png_and_updates_queue(factory):
 root,issue,pid=factory;r=art.import_attempt(issue,root,pid,png(),"panel.png");selected=art.select_preferred(issue,root,pid,r["attempt_id"]);assert selected["ok"];path=issue/selected["selected_path"];assert path.exists();assert Image.open(path).format=="PNG";assert art.build_queue(issue,root)["items"][0]["status"]=="approved"
def test_rejected_attempt_cannot_be_selected(factory):
 root,issue,pid=factory;r=art.import_attempt(issue,root,pid,png(),"panel.png");art.set_attempt_status(issue,root,pid,r["attempt_id"],"rejected")
 with pytest.raises(art.ArtQueueError,match="cannot be selected"):art.select_preferred(issue,root,pid,r["attempt_id"])
def test_import_and_selection_require_art_production(factory):
 root,issue,pid=factory;state=json.loads((issue/".workflow-status.json").read_text());state["active_stage"]="art_prompts";art._write_json(issue/".workflow-status.json",state);assert art.prompt_package(issue,root,pid)
 with pytest.raises(art.ArtQueueError,match="art_production"):art.import_attempt(issue,root,pid,png(),"x.png")
def test_plan_change_rebuilds_queue_hash(factory):
 root,issue,pid=factory;q=art.build_queue(issue,root,True);attempt=art.import_attempt(issue,root,pid,png(),"x.png");plan=json.loads((issue/"page_panel_plan.json").read_text());plan["pages"][0]["panels"][0]["action"]="Changed";(issue/"page_panel_plan.json").write_text(json.dumps(plan));updated=art.build_queue(issue,root);assert updated["plan_hash"]!=q["plan_hash"];assert updated["items"][0]["attempts"][0]["plan_stale"]
 with pytest.raises(art.ArtQueueError,match="stale"):art.select_preferred(issue,root,pid,attempt["attempt_id"])

def _preferred_setup(factory):
 root,issue,pid=factory;first=art.import_attempt(issue,root,pid,png("yellow"),"first.png");art.select_preferred(issue,root,pid,first["attempt_id"]);second=art.import_attempt(issue,root,pid,png("blue"),"second.png");return root,issue,pid,first,second

def test_failure_after_png_replacement_restores_previous_png(factory,monkeypatch):
 root,issue,pid,first,second=_preferred_setup(factory);selected=issue/"generated_art/selected_panels"/f"{pid}.png";before=selected.read_bytes()
 monkeypatch.setattr(art,"_write_json",lambda *_:(_ for _ in ()).throw(OSError("metadata failed")))
 with pytest.raises(OSError,match="metadata failed"):art.select_preferred(issue,root,pid,second["attempt_id"])
 assert selected.read_bytes()==before;assert [a["attempt_id"] for a in art.attempts(issue,pid) if a["status"]=="preferred"]==[first["attempt_id"]]

def test_failure_during_attempt_metadata_restores_all_statuses(factory,monkeypatch):
 root,issue,pid,first,second=_preferred_setup(factory);before={a["attempt_id"]:a["status"] for a in art.attempts(issue,pid)};original=art._write_json;calls=0
 def fail_second(path,data):
  nonlocal calls
  if path.parent.name==pid:
   calls+=1
   if calls==2:raise OSError("second metadata failed")
  return original(path,data)
 monkeypatch.setattr(art,"_write_json",fail_second)
 with pytest.raises(OSError,match="second metadata failed"):art.select_preferred(issue,root,pid,second["attempt_id"])
 assert {a["attempt_id"]:a["status"] for a in art.attempts(issue,pid)}==before

def test_failure_writing_queue_restores_png_statuses_and_queue(factory,monkeypatch):
 root,issue,pid,first,second=_preferred_setup(factory);selected=issue/"generated_art/selected_panels"/f"{pid}.png";queue=issue/".art-workspace/queue.json";png_before=selected.read_bytes();queue_before=queue.read_bytes();statuses={a["attempt_id"]:a["status"] for a in art.attempts(issue,pid)};original=art._write_json
 def fail_queue(path,data):
  if path==queue:raise OSError("queue failed")
  return original(path,data)
 monkeypatch.setattr(art,"_write_json",fail_queue)
 with pytest.raises(OSError,match="queue failed"):art.select_preferred(issue,root,pid,second["attempt_id"])
 assert selected.read_bytes()==png_before;assert queue.read_bytes()==queue_before;assert {a["attempt_id"]:a["status"] for a in art.attempts(issue,pid)}==statuses

def test_first_selection_failure_leaves_no_selected_png(factory,monkeypatch):
 root,issue,pid=factory;attempt=art.import_attempt(issue,root,pid,png(),"first.png");monkeypatch.setattr(art,"_write_json",lambda *_:(_ for _ in ()).throw(OSError("failed")))
 with pytest.raises(OSError):art.select_preferred(issue,root,pid,attempt["attempt_id"])
 assert not (issue/"generated_art/selected_panels"/f"{pid}.png").exists()

def test_concurrent_selection_returns_structured_conflict(factory):
 root,issue,pid=factory;attempt=art.import_attempt(issue,root,pid,png(),"first.png");lock=issue/".art-workspace/.selection.lock";lock.write_text("busy")
 with pytest.raises(art.ArtQueueError,match="already in progress") as error:art.select_preferred(issue,root,pid,attempt["attempt_id"])
 assert error.value.status==409

def test_successful_replacement_leaves_exactly_one_preferred(factory):
 root,issue,pid,first,second=_preferred_setup(factory);art.select_preferred(issue,root,pid,second["attempt_id"]);records=art.attempts(issue,pid)
 assert [a["attempt_id"] for a in records if a["status"]=="preferred"]==[second["attempt_id"]]
 assert next(a for a in records if a["attempt_id"]==first["attempt_id"])["status"]=="candidate"
