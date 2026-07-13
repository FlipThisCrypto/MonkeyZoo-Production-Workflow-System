import sys
from pathlib import Path
import pytest
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import app as review_app
@pytest.fixture()
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(review_app,"WORKSPACE_ROOT",tmp_path);monkeypatch.setattr(review_app.issue_workflow,"find_issue",lambda *_:tmp_path);review_app.app.config.update(TESTING=True)
 with review_app.app.test_client() as c:yield c,monkeypatch
def test_art_conflict_message_preserved(client):
 c,m=client;msg="Art Queue requires workflow stage art_production; current stage is page_plan";m.setattr(review_app.art_queue_workspace,"build_queue",lambda *_args,**_kwargs:(_ for _ in()).throw(review_app.art_queue_workspace.ArtQueueError(msg,409)));r=c.post("/api/issues/MZ-2027-04-01/art-queue/build");assert r.status_code==409;assert r.json=={"ok":False,"error":msg}
def test_upload_requires_multipart_image(client):
 c,_=client;r=c.post("/api/issues/MZ-2027-04-01/art-queue/MZ-2027-04-01_P01_PANEL01/attempts");assert r.status_code==400;assert r.json["error"]=="Multipart image upload is required"
def test_unexpected_art_error_sanitized(client):
 c,m=client;m.setattr(review_app.art_queue_workspace,"summary",lambda *_:(_ for _ in()).throw(RuntimeError("secret")));r=c.get("/api/issues/MZ-2027-04-01/art-queue");assert r.status_code==500;assert r.json=={"ok":False,"error":"Unexpected server error"}
