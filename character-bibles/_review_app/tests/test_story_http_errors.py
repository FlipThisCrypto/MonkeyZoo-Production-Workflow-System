import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))
import app as review_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(review_app, "WORKSPACE_ROOT", tmp_path)
    monkeypatch.setattr(review_app.issue_workflow, "find_issue", lambda issue_id, root: tmp_path)
    review_app.app.config.update(TESTING=True)
    with review_app.app.test_client() as test_client:
        yield test_client, monkeypatch


def assert_error(response, status, message):
    assert response.status_code == status
    assert response.get_json() == {"ok": False, "error": message}
    body = response.get_data(as_text=True)
    assert "Traceback" not in body
    assert "I:\\" not in body


def test_wrong_stage_exposes_safe_409(client):
    test_client, monkeypatch = client
    message = "Outline workspace requires active workflow stage outline; current stage is intake"
    monkeypatch.setattr(review_app.story_workspace, "prompt_package", lambda *args: (_ for _ in ()).throw(review_app.story_workspace.StoryWorkspaceError(message, 409)))
    assert_error(test_client.post("/api/issues/MZ-2027-01-01/story/outlines/prompt", json={}), 409, message)


@pytest.mark.parametrize(("message", "route", "target"), [
    ("Canon changed since generation", "/api/issues/MZ-2027-01-01/story/outlines/outline-20270101T000000Z-abcdef/promote", "promote"),
    ("Script generation requires an approved outline", "/api/issues/MZ-2027-01-01/story/scripts/prompt", "prompt_package"),
    ("issue_outline.md already exists; explicit replacement confirmation is required", "/api/issues/MZ-2027-01-01/story/outlines/outline-20270101T000000Z-abcdef/promote", "promote"),
    ("Variant was already promoted", "/api/issues/MZ-2027-01-01/story/outlines/outline-20270101T000000Z-abcdef/promote", "promote"),
])
def test_story_conflicts_expose_exact_safe_reason(client, message, route, target):
    test_client, monkeypatch = client
    monkeypatch.setattr(review_app.story_workspace, target, lambda *args, **kwargs: (_ for _ in ()).throw(review_app.story_workspace.StoryWorkspaceError(message, 409)))
    assert_error(test_client.post(route, json={}), 409, message)


def test_invalid_kind_is_structured_400(client):
    test_client, _ = client
    assert_error(test_client.get("/api/issues/MZ-2027-01-01/story/scriptssss"), 400, "Story kind must be outline, outlines, script, or scripts")


def test_invalid_request_data_is_structured_400(client):
    test_client, monkeypatch = client
    message = "content must be non-empty Markdown"
    monkeypatch.setattr(review_app.story_workspace, "import_variant", lambda *args: (_ for _ in ()).throw(review_app.story_workspace.StoryWorkspaceError(message)))
    assert_error(test_client.post("/api/issues/MZ-2027-01-01/story/outlines/import", json={}), 400, message)


def test_unexpected_exception_is_sanitized(client):
    test_client, monkeypatch = client
    monkeypatch.setattr(review_app.story_workspace, "summary", lambda *args: (_ for _ in ()).throw(RuntimeError("secret at I:\\private\\token.txt")))
    assert_error(test_client.get("/api/issues/MZ-2027-01-01/story"), 500, "Unexpected server error")


def _assert_http_error(response, status):
    # the catch-all error handler used to mask every werkzeug HTTPException as a
    # generic 500; real HTTP errors must keep their status and stay JSON + leak-free.
    assert response.status_code == status
    body = response.get_json()
    assert body is not None and body["ok"] is False and body["error"]
    text = response.get_data(as_text=True)
    assert "Traceback" not in text and "I:\\" not in text


def test_unknown_url_is_404_not_500(client):
    test_client, _ = client
    _assert_http_error(test_client.get("/api/does-not-exist"), 404)


def test_wrong_method_is_405_not_500(client):
    test_client, _ = client
    _assert_http_error(test_client.post("/api/characters"), 405)   # GET-only route


def test_malformed_json_body_is_400_not_500(client):
    test_client, _ = client
    _assert_http_error(
        test_client.post("/api/compare", data="{bad json", content_type="application/json"), 400)
