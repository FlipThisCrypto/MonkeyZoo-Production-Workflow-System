import sys
from pathlib import Path
import pytest
APP=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(APP)); import app as review_app

@pytest.fixture()
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(review_app,"WORKSPACE_ROOT",tmp_path); monkeypatch.setattr(review_app.issue_workflow,"find_issue",lambda *_:tmp_path); review_app.app.config.update(TESTING=True)
    with review_app.app.test_client() as value: yield value,monkeypatch

def test_layout_conflict_preserves_409_message(client):
    c,m=client; message="Layout workspace requires active workflow stage page_plan; current stage is script"; m.setattr(review_app.page_panel_workspace,"create_variant",lambda *_:(_ for _ in()).throw(review_app.page_panel_workspace.PagePanelError(message,409)))
    response=c.post("/api/issues/MZ-2027-03-01/layout/variants",json={}); assert response.status_code==409; assert response.json=={"ok":False,"error":message}

def test_unexpected_layout_error_sanitized(client):
    c,m=client; m.setattr(review_app.page_panel_workspace,"summary",lambda *_:(_ for _ in()).throw(RuntimeError("secret I:\\private")))
    response=c.get("/api/issues/MZ-2027-03-01/layout"); assert response.status_code==500; assert response.json=={"ok":False,"error":"Unexpected server error"}; assert "I:\\" not in response.get_data(as_text=True)
