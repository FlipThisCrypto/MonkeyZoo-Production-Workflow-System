from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

import bible_store as store
import story_context
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
    results = []
    for folder in sorted((WORKSPACE_ROOT / "02_MONTHLY_ISSUES").iterdir()):
        if not folder.is_dir() or folder.name.startswith(".") or "_Issue_" not in folder.name:
            continue
        metadata = folder / "metadata.json"
        data = {}
        if metadata.exists():
            try:
                import json
                data = json.loads(metadata.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                pass
        brief = folder / "issue_brief.md"
        degraded = not metadata.exists() or not data
        if degraded and not brief.exists():
            continue
        stage = data.get("workflow_stage")
        if not stage:
            evidence = [("final_export_checklist.md", "9. Final QA"), ("qa_report.md", "7. Art QA"), ("issue_script.md", "4. Script"), ("issue_outline.md", "3. Showrunner"), ("issue_brief.md", "1. Intake")]
            stage = next((label for filename, label in evidence if (folder / filename).exists() and (folder / filename).stat().st_size > 0), "Stage unavailable")
        results.append({"issue_id": data.get("issue_id", folder.name), "title": data.get("title") or data.get("name") or "Title unavailable", "stage": stage, "location": str(folder.relative_to(WORKSPACE_ROOT)), "degraded": degraded})
    return jsonify(results)

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


@app.get("/media/<character_id>/<path:rel_path>")
def media(character_id, rel_path):
    base = BIBLES_ROOT / character_id
    return send_from_directory(base, rel_path)


@app.errorhandler(Exception)
def handle_error(exc):
    status = 400 if isinstance(exc, (store.BibleStoreError, story_context.StoryContextError, new_issue.IssueCreationError)) else 500
    message = str(exc) if status == 400 else "Unexpected server error"
    return jsonify({"ok": False, "error": message}), status


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=True)
