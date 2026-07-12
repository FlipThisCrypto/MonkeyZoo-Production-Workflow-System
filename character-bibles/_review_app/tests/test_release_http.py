import sys
from pathlib import Path
import pytest
APP=Path(__file__).resolve().parents[1];sys.path.insert(0,str(APP));import app as review_app
@pytest.fixture()
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(review_app,"WORKSPACE_ROOT",tmp_path);monkeypatch.setattr(review_app.issue_workflow,"find_issue",lambda *_:tmp_path);review_app.app.config.update(TESTING=True)
 with review_app.app.test_client() as c:yield c,monkeypatch
def test_release_conflict_preserves_reason(client):
 c,m=client;msg="Release approval blocked: Final PDF is missing";m.setattr(review_app.release_workspace,"approve",lambda *_:(_ for _ in()).throw(review_app.release_workspace.ReleaseError(msg,409)));r=c.post("/api/issues/MZ-2027-06-01/release/approve",json={});assert r.status_code==409;assert r.json=={"ok":False,"error":msg}
def test_unexpected_release_error_sanitized(client):
 c,m=client;m.setattr(review_app.release_workspace,"readiness",lambda *_:(_ for _ in()).throw(RuntimeError("secret")));r=c.get("/api/issues/MZ-2027-06-01/release");assert r.status_code==500;assert r.json=={"ok":False,"error":"Unexpected server error"}
