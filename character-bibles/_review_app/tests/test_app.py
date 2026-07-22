import sys
from pathlib import Path

import pytest
import yaml

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

import app as review_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    root = tmp_path / "character-bibles"
    char = root / "MZ-CHAR-API"
    (char / "references").mkdir(parents=True)
    data = {
        "schema_version": "1.0",
        "identification": {
            "current_display_name": "API Test",
            "series_name": "API",
            "personal_name": None,
            "codename": None,
            "nicknames": [],
            "naming_status": "unresolved",
            "character_id": "MZ-CHAR-API",
            "development_level": 1,
            "canon_status": "experimental",
        },
        "visual_canon": {
            "primary_reference_image": None,
            "supporting_reference_images": [],
            "features_that_must_never_change": [],
            "features_that_may_vary": [],
            "prohibited_visual_additions": [],
            "glasses_status": "unknown",
        },
        "character_core": {
            "dominant_traits": [{
                "category": "role",
                "name": "test trait",
                "value": "test",
                "status": "experimental",
                "strength": "moderate",
                "usage_frequency": "sometimes",
                "confidence": "experimental suggestion",
                "rationale": "test",
                "evidence": ["test"],
                "compatible_contexts": [],
                "incompatible_contexts": [],
                "first_eligible_issue": "next",
                "last_used_issue": None,
                "source_refs": ["test"],
                "notes": None,
            }]
        },
        "relationships": [],
        "issue_level_usage": {
            "traits_eligible_for_selection": [],
            "maximum_defining_traits_per_issue": 1,
            "maximum_minor_quirks_per_issue": 1,
        },
    }
    (char / "bible.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(review_app, "BIBLES_ROOT", root)
    review_app.app.config.update(TESTING=True)
    with review_app.app.test_client() as test_client:
        yield test_client


def test_character_api_lists_bibles(client):
    res = client.get("/api/characters")
    assert res.status_code == 200
    data = res.get_json()
    assert data[0]["character_id"] == "MZ-CHAR-API"


def test_health_ok_when_data_root_present(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok" and body["bibles_root_ok"] is True
    assert body["service"] == "monkeyzoo-banana-lab"


def test_health_degraded_503_when_data_root_missing(client, monkeypatch, tmp_path):
    # readiness must fail loudly (503) if the data root is missing/unmounted
    monkeypatch.setattr(review_app, "BIBLES_ROOT", tmp_path / "does-not-exist")
    res = client.get("/api/health")
    assert res.status_code == 503
    assert res.get_json()["status"] == "degraded"


def test_health_probes_all_critical_roots(client):
    body = client.get("/api/health").get_json()
    assert body["approved_canon_ok"] is True     # 03_APPROVED_CANON present
    assert body["monthly_issues_ok"] is True      # 02_MONTHLY_ISSUES present
    assert body["degraded_roots"] == []


def test_health_degraded_503_when_canon_or_issues_root_missing(client, monkeypatch, tmp_path):
    # bibles root present (fixture) but the canon-catalog / issue-workflow roots
    # are unmounted -> readiness must fail and name them, not report healthy while
    # /api/locations, /api/props and /api/issues would break.
    monkeypatch.setattr(review_app, "WORKSPACE_ROOT", tmp_path / "unmounted-workspace")
    res = client.get("/api/health")
    assert res.status_code == 503
    body = res.get_json()
    assert body["status"] == "degraded"
    assert "approved_canon_ok" in body["degraded_roots"]
    assert "monthly_issues_ok" in body["degraded_roots"]
    assert body["bibles_root_ok"] is True         # this root is still fine


def test_runtime_capability_requires_exact_trusted_contract(client):
    res = client.get("/api/runtime-capabilities")
    assert res.status_code == 200
    assert res.get_json() == {"schema_version":"1.0", "runtime":"monkeyzoo-local", "capability":"monkeyzoo-production-write-v1", "writable":True}


def test_trait_api_updates_bible(client):
    res = client.post("/api/characters/MZ-CHAR-API/trait", json={
        "path": "character_core.dominant_traits.0",
        "updates": {"action": "approve_established"},
        "note": "approved in API test",
    })
    assert res.status_code == 200
    assert res.get_json()["trait"]["status"] == "established"


@pytest.mark.parametrize("route", [
    "/api/characters/MZ-CHAR-API/trait",
    "/api/characters/MZ-CHAR-API/field",
])
def test_write_endpoint_missing_path_is_structured_400(client, route):
    # a valid JSON body without the required "path" used to raise KeyError -> 500
    res = client.post(route, json={"note": "no path given"})
    assert res.status_code == 400
    body = res.get_json()
    assert body["ok"] is False and "path" in body["error"]


@pytest.mark.parametrize("route", [
    "/api/characters/MZ-CHAR-API/trait",
    "/api/characters/MZ-CHAR-API/field",
    "/api/compare",
])
def test_write_endpoint_non_object_body_is_structured_400(client, route):
    # a non-object JSON body (list/string) used to raise TypeError/AttributeError -> 500
    res = client.post(route, json=["not", "an", "object"])
    assert res.status_code == 400
    body = res.get_json()
    assert body["ok"] is False and "JSON object" in body["error"]


@pytest.mark.parametrize("route", ["/api/health", "/api/characters", "/"])
def test_security_headers_on_all_responses(client, route):
    res = client.get(route)
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "no-referrer"


def test_request_size_cap_is_configured():
    # legitimate art uploads are 25 MB; the cap keeps headroom for multipart overhead
    assert review_app.app.config["MAX_CONTENT_LENGTH"] == 32 * 1024 * 1024


def test_oversized_request_body_is_413(client, monkeypatch):
    # a body over the cap is rejected (413) before being buffered fully into memory
    monkeypatch.setitem(review_app.app.config, "MAX_CONTENT_LENGTH", 50)
    res = client.post("/api/compare", data=b"x" * 300, content_type="application/json")
    assert res.status_code == 413
    assert res.get_json()["ok"] is False


def test_story_preview_api_uses_compact_context(client):
    res = client.post("/api/story/preview", json={
        "issue_id": "MZ-API-STORY",
        "characters": [{"character_id": "MZ-CHAR-API", "role": "primary"}],
        "page_count": 1,
        "panel_count": 4,
        "topic": "test",
        "adventure_style": "Mystery",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["packet"]["issue_id"] == "MZ-API-STORY"
    assert data["packet"]["selection_rules"]["full_bible_injected"] is False
    assert "test trait" in data["prompt"]


def test_story_generate_sample_api_returns_script(client):
    res = client.post("/api/story/generate-sample", json={
        "issue_id": "MZ-API-SAMPLE",
        "characters": [{"character_id": "MZ-CHAR-API", "role": "primary"}],
        "page_count": 1,
        "panel_count": 3,
        "topic": "sample",
        "adventure_style": "Comedy of errors",
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "Generated Sample Issue" in data["generated_script"]
    assert data["continuity_proposal"]["status"] == "proposed_owner_review_required"


def test_create_issue_api_returns_structured_validation_error(client):
    res = client.post("/api/issues", json={"issue_id": "../escape"})
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


@pytest.mark.parametrize("body,content_type", [
    (None, None),
    ("{broken", "application/json"),
    ("[]", "application/json"),
    ('"text"', "application/json"),
])
def test_create_issue_api_rejects_bad_json_as_400(client, body, content_type):
    res = client.post("/api/issues", data=body, content_type=content_type)
    assert res.status_code == 400
    assert res.get_json()["ok"] is False
    assert res.get_json()["error"]


# --- Flask debug (Werkzeug RCE console) must default OFF on the writable server ---

def test_debug_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MZ_STUDIO_DEBUG", raising=False)
    assert review_app._debug_enabled() is False


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "  ", "nope"])
def test_debug_stays_off_for_non_truthy_values(monkeypatch, value):
    monkeypatch.setenv("MZ_STUDIO_DEBUG", value)
    assert review_app._debug_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "Yes", "on"])
def test_debug_opt_in_only_via_explicit_flag(monkeypatch, value):
    monkeypatch.setenv("MZ_STUDIO_DEBUG", value)
    assert review_app._debug_enabled() is True


# --- CSRF / cross-origin request-trust boundary on the writable service --------

def test_cross_site_mutation_blocked_by_origin(client):
    res = client.post("/api/compare", json={"character_ids": []},
                      headers={"Origin": "http://evil.example"})
    assert res.status_code == 403
    assert "Cross-site" in res.get_json()["error"]


def test_cross_site_mutation_blocked_by_referer(client):
    # a cross-site form POST that carries only a Referer must also be rejected
    res = client.post("/api/compare", json={"character_ids": []},
                      headers={"Referer": "http://evil.example/attack.html"})
    assert res.status_code == 403


def test_null_origin_mutation_blocked(client):
    res = client.post("/api/compare", json={"character_ids": []},
                      headers={"Origin": "null"})
    assert res.status_code == 403


def test_same_origin_mutation_allowed(client):
    res = client.post("/api/compare", json={"character_ids": []},
                      headers={"Origin": "http://localhost"})
    assert res.status_code == 200


def test_mutation_without_origin_or_referer_allowed(client):
    # non-browser clients (CLI / the test suite) send neither header; a body-less
    # cross-site attack cannot avoid sending an Origin, so this is safe to allow.
    res = client.post("/api/compare", json={"character_ids": []})
    assert res.status_code == 200


def test_safe_method_ignores_cross_origin(client):
    res = client.get("/api/characters", headers={"Origin": "http://evil.example"})
    assert res.status_code == 200


def test_body_less_mutation_endpoint_is_csrf_protected(client):
    # /undo takes no body: proves the boundary intercepts BEFORE the handler runs
    # (evil origin -> 403, not the handler's 400 "no history").
    res = client.post("/api/characters/MZ-CHAR-API/undo",
                      headers={"Origin": "http://evil.example"})
    assert res.status_code == 403


# --- structured operations log: durable audit of every mutation ----------------

import json as _json          # noqa: E402
import logging as _logging     # noqa: E402


def _capture_ops(monkeypatch):
    """Attach an in-memory handler to the operations logger and return the list
    of emitted JSON records."""
    records = []

    class _Capture(_logging.Handler):
        def emit(self, record):
            records.append(_json.loads(record.getMessage()))

    handler = _Capture()
    review_app._OPS_LOG.addHandler(handler)
    # ensure the guard in _log_operation sees a handler even if file setup was skipped
    monkeypatch.setattr(review_app._OPS_LOG, "level", _logging.INFO, raising=False)
    return records, handler


def test_mutation_is_recorded_in_operations_log(client, monkeypatch):
    records, handler = _capture_ops(monkeypatch)
    try:
        client.post("/api/compare", json={"character_ids": []}, headers={"Origin": "http://localhost"})
    finally:
        review_app._OPS_LOG.removeHandler(handler)
    entry = next((r for r in records if r["path"] == "/api/compare"), None)
    assert entry is not None
    assert entry["method"] == "POST"
    assert entry["status"] == 200
    assert isinstance(entry["duration_ms"], float)
    assert entry["ts"].endswith("+00:00") or "T" in entry["ts"]


def test_safe_get_is_not_logged_as_operation(client, monkeypatch):
    records, handler = _capture_ops(monkeypatch)
    try:
        client.get("/api/characters")
    finally:
        review_app._OPS_LOG.removeHandler(handler)
    assert all(r["path"] != "/api/characters" for r in records)


def test_blocked_cross_site_mutation_is_logged_with_403(client, monkeypatch):
    # a rejected CSRF attempt must still be auditable (status 403 recorded)
    records, handler = _capture_ops(monkeypatch)
    try:
        client.post("/api/compare", json={"character_ids": []}, headers={"Origin": "http://evil.example"})
    finally:
        review_app._OPS_LOG.removeHandler(handler)
    entry = next((r for r in records if r["path"] == "/api/compare"), None)
    assert entry is not None and entry["status"] == 403


def test_operations_log_writes_to_configured_dir(tmp_path, monkeypatch):
    # end-to-end: the file handler actually persists a JSON line to disk
    monkeypatch.setenv("MZ_STUDIO_LOG_DIR", str(tmp_path / "opslogs"))
    review_app._OPS_LOG.handlers.clear()          # force reconfigure with the env dir
    review_app._configure_operations_log()
    try:
        with review_app.app.test_client() as c:
            c.post("/api/compare", json={"character_ids": []}, headers={"Origin": "http://localhost"})
        for h in review_app._OPS_LOG.handlers:
            h.flush()
        log_file = tmp_path / "opslogs" / "operations.log"
        assert log_file.is_file()
        lines = [l for l in log_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert any(_json.loads(l)["path"] == "/api/compare" for l in lines)
    finally:
        review_app._OPS_LOG.handlers.clear()
        review_app._configure_operations_log()     # restore default config


# --- request correlation id: trace a request across header, ops log, error ------

def test_every_response_carries_a_request_id_header(client):
    res = client.get("/api/characters")
    rid = res.headers.get("X-Request-ID")
    assert rid and len(rid) == 12


def test_request_id_is_unique_per_request(client):
    a = client.get("/api/health").headers.get("X-Request-ID")
    b = client.get("/api/health").headers.get("X-Request-ID")
    assert a and b and a != b


def test_error_response_carries_request_id_header(client):
    # errors keep the stable {"ok","error"} body; the correlation id rides the
    # X-Request-ID header so a reported failure is still findable in the logs.
    res = client.post("/api/characters/MZ-CHAR-API/field", json={"note": "no path key"})
    assert res.status_code == 400
    assert set(res.get_json()) == {"ok", "error"}       # body contract unchanged
    assert res.headers.get("X-Request-ID")              # but traceable via the header


def test_ops_log_request_id_matches_response_header(client, monkeypatch):
    records, handler = _capture_ops(monkeypatch)
    try:
        res = client.post("/api/compare", json={"character_ids": []},
                          headers={"Origin": "http://localhost"})
    finally:
        review_app._OPS_LOG.removeHandler(handler)
    entry = next(r for r in records if r["path"] == "/api/compare")
    assert entry["request_id"] == res.headers.get("X-Request-ID")  # ops log <-> client correlated


def test_server_error_is_traceable_via_request_id(client, monkeypatch):
    # force an unexpected 500 and confirm the same id appears in header + body,
    # so the operator can map a reported error to its server-side traceback.
    def _raise(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(review_app.store, "load_all", _raise)
    res = client.get("/api/characters")
    assert res.status_code == 500
    assert res.get_json() == {"ok": False, "error": "Unexpected server error"}  # sanitized body
    assert res.headers.get("X-Request-ID")             # traceable to the server-side traceback
