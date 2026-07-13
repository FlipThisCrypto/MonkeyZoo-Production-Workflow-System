import sys
from pathlib import Path
import pytest
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import app as review_app
@pytest.fixture()
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(review_app,"WORKSPACE_ROOT",tmp_path);monkeypatch.setattr(review_app.issue_workflow,"find_issue",lambda *_:tmp_path);review_app.app.config.update(TESTING=True)
 with review_app.app.test_client() as c:yield c,monkeypatch
def test_qa_conflict_preserves_message(client):
 c,m=client;msg="QA workspace requires active workflow stage qa; current stage is art_production";m.setattr(review_app.visual_qa_workspace,"create_review",lambda *_:(_ for _ in()).throw(review_app.visual_qa_workspace.VisualQAError(msg,409)));r=c.post("/api/issues/MZ-2027-05-01/qa/reviews");assert r.status_code==409;assert r.json=={"ok":False,"error":msg}
def test_unexpected_qa_error_sanitized(client):
 c,m=client;m.setattr(review_app.visual_qa_workspace,"summary",lambda *_:(_ for _ in()).throw(RuntimeError("secret")));r=c.get("/api/issues/MZ-2027-05-01/qa");assert r.status_code==500;assert r.json=={"ok":False,"error":"Unexpected server error"}
