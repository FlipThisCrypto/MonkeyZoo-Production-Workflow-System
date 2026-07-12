from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

import bible_store as store
import story_context
import issue_workflow
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00_SYSTEM" / "scripts"))
import new_issue

APP_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = APP_DIR.parents[1]
BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.get("/")
def index():
    return send_from_directory(APP_DIR / "static", "index.html")


@app.get("/api/characters")
def characters():
    return jsonify([store.character_summary(cid, data) for cid, data in store.load_all(BIBLES_ROOT)])


@app.get("/api/characters/<character_id>")
def character_detail(character_id):
    character_id = store.resolve_character_id(character_id, BIBLES_ROOT)
    data = store.load_bible(character_id, BIBLES_ROOT)
    return jsonify({
        "summary": store.character_summary(character_id, data),
        "detail": store.visible_sections(data),
        "traits": [{"path": path, **trait} for path, trait in store.walk_traits(data)],
    })


@app.post("/api/characters/<character_id>/trait")
def update_trait(character_id):
    body = request.get_json(force=True)
    trait = store.update_trait(character_id, body["path"], body.get("updates", {}), body.get("note"), BIBLES_ROOT)
    return jsonify({"ok": True, "trait": trait})


@app.post("/api/characters/<character_id>/field")
def update_field(character_id):
    body = request.get_json(force=True)
    value = store.update_field(character_id, body["path"], body.get("value"), body.get("action", "edit_field"), body.get("note"), BIBLES_ROOT)
    return jsonify({"ok": True, "value": value})


@app.post("/api/characters/<character_id>/undo")
def undo(character_id):
    return jsonify({"ok": True, "undone": store.undo_last(character_id, BIBLES_ROOT)})


@app.post("/api/compare")
def compare():
    body = request.get_json(force=True)
    return jsonify(store.comparison(body.get("character_ids", []), BIBLES_ROOT))


@app.get("/api/story/adventure-styles")
def adventure_styles():
    return jsonify(story_context.ADVENTURE_STYLES)


@app.post("/api/story/preview")
def story_preview():
    body = request.get_json(force=True)
    return jsonify(story_context.build_preview(body, BIBLES_ROOT, WORKSPACE_ROOT))


@app.post("/api/story/save")
def story_save():
    body = request.get_json(force=True)
    return jsonify(story_context.save_preview(body, BIBLES_ROOT, WORKSPACE_ROOT))


@app.post("/api/story/generate-sample")
def story_generate_sample():
    body = request.get_json(force=True)
    return jsonify(story_context.generate_sample_issue(body, BIBLES_ROOT, WORKSPACE_ROOT))


@app.post("/api/story/validate-script")
def story_validate_script():
    body = request.get_json(force=True)
    packet = body.get("packet")
    if not packet:
        packet = story_context.build_preview(body.get("setup", {}), BIBLES_ROOT, WORKSPACE_ROOT)["packet"]
    return jsonify({"warnings": story_context.validate_script_text(body.get("script_text", ""), packet)})

@app.get("/api/issues")
def issues():
    return jsonify(issue_workflow.list_issues(WORKSPACE_ROOT))

@app.post("/api/issues")
def create_issue():
    if not request.is_json:
        raise new_issue.IssueCreationError("Request Content-Type must be application/json")
    try:
        body = request.get_json(silent=False)
    except (BadRequest, UnsupportedMediaType):
        raise new_issue.IssueCreationError("Request body contains malformed JSON") from None
    if not isinstance(body, dict):
        raise new_issue.IssueCreationError("Request body must be a JSON object")
    return jsonify(new_issue.create_issue(body, WORKSPACE_ROOT)), 201

@app.get("/api/issues/<issue_id>")
def issue_production_detail(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(issue_workflow.issue_detail(folder, WORKSPACE_ROOT))

@app.get("/api/issues/<issue_id>/workflow")
def issue_production_workflow(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(issue_workflow.workflow_status(folder, WORKSPACE_ROOT))

@app.get("/api/issues/<issue_id>/artifacts")
def issue_artifacts(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(issue_workflow.issue_detail(folder, WORKSPACE_ROOT)["artifacts"])

@app.get("/api/issues/<issue_id>/artifact")
def issue_artifact(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(issue_workflow.view_artifact(folder, request.args.get("path", "")))

@app.post("/api/issues/<issue_id>/validate")
def validate_issue_stage(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(issue_workflow.workflow_status(folder, WORKSPACE_ROOT))

@app.post("/api/issues/<issue_id>/advance")
def advance_issue_stage(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    body = request.get_json(silent=True) or {}
    return jsonify(issue_workflow.record_advance(folder, WORKSPACE_ROOT, body.get("stage")))


@app.get("/media/<character_id>/<path:rel_path>")
def media(character_id, rel_path):
    character_id = store.resolve_character_id(character_id, BIBLES_ROOT)
    base = BIBLES_ROOT / character_id
    return send_from_directory(base, rel_path)


@app.errorhandler(Exception)
def handle_error(exc):
    status = 400 if isinstance(exc, (store.BibleStoreError, story_context.StoryContextError, new_issue.IssueCreationError, issue_workflow.IssueWorkflowError)) else 500
    message = str(exc) if status == 400 else "Unexpected server error"
    return jsonify({"ok": False, "error": message}), status


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=True)
