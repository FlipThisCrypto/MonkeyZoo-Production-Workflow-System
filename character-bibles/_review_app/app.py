from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import bible_store as store
import story_context

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


@app.get("/media/<character_id>/<path:rel_path>")
def media(character_id, rel_path):
    base = BIBLES_ROOT / character_id
    return send_from_directory(base, rel_path)


@app.errorhandler(Exception)
def handle_error(exc):
    status = 400 if isinstance(exc, (store.BibleStoreError, story_context.StoryContextError)) else 500
    return jsonify({"ok": False, "error": str(exc)}), status


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=True)
