from __future__ import annotations

from pathlib import Path
import sys

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

import bible_store as store
import story_context
import issue_workflow
import story_workspace
import page_panel_workspace
import art_queue_workspace
import art_prompt_workspace
import visual_qa_workspace
import release_workspace
import canon_catalog
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00_SYSTEM" / "scripts"))
import new_issue

APP_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = APP_DIR.parents[1]
BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"

app = Flask(__name__, static_folder="static", static_url_path="/static")

def story_kind(value: str) -> str:
    kinds = {"outline": "outline", "outlines": "outline", "script": "script", "scripts": "script"}
    if value not in kinds:
        raise story_workspace.StoryWorkspaceError("Story kind must be outline, outlines, script, or scripts")
    return kinds[value]


@app.get("/")
def index():
    return send_from_directory(APP_DIR / "static", "index.html")


@app.get("/api/runtime-capabilities")
def runtime_capabilities():
    """Explicit same-origin proof required before the UI enables mutations."""
    return jsonify({
        "schema_version": "1.0",
        "runtime": "monkeyzoo-local",
        "capability": "monkeyzoo-production-write-v1",
        "writable": True,
    })


@app.get("/api/characters")
def characters():
    return jsonify([store.character_summary(cid, data) for cid, data in store.load_all(BIBLES_ROOT)])


@app.get("/api/locations")
def locations():
    return jsonify(canon_catalog.list_locations(WORKSPACE_ROOT))


@app.get("/api/locations/<location_id>")
def location_detail(location_id):
    return jsonify(canon_catalog.get_location(WORKSPACE_ROOT, location_id))


@app.get("/api/props")
def props():
    return jsonify(canon_catalog.list_props(WORKSPACE_ROOT))


@app.get("/api/props/<prop_id>")
def prop_detail(prop_id):
    return jsonify(canon_catalog.get_prop(WORKSPACE_ROOT, prop_id))


@app.get("/api/canon-catalog/summary")
def canon_catalog_summary():
    return jsonify(canon_catalog.catalog_summary(WORKSPACE_ROOT))


@app.get("/api/expressions")
def expressions():
    return jsonify(canon_catalog.list_expression_sets(WORKSPACE_ROOT))


@app.get("/api/expressions/<slug>")
def expression_detail(slug):
    return jsonify(canon_catalog.get_expression_set(WORKSPACE_ROOT, slug))


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

@app.post("/api/issues/<issue_id>/workflow/approve")
def approve_issue_stage(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    body = request.get_json(silent=True) or {}
    return jsonify(issue_workflow.record_approval(folder, WORKSPACE_ROOT, body.get("stage"), body.get("approved"), body.get("note")))

@app.get("/api/issues/<issue_id>/story")
def issue_story_workspace(issue_id):
    return jsonify(story_workspace.summary(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT))

@app.get("/api/issues/<issue_id>/story/canon")
def issue_story_canon(issue_id):
    return jsonify(story_workspace.canon_snapshot(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, request.args.get("type", "outline")))

@app.post("/api/issues/<issue_id>/story/canon/refresh")
def issue_story_canon_refresh(issue_id):
    return jsonify(story_workspace.canon_snapshot(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, (request.get_json(silent=True) or {}).get("type", "outline"), True))

@app.post("/api/issues/<issue_id>/story/<kind>/prompt")
def issue_story_prompt(issue_id, kind):
    return jsonify(story_workspace.prompt_package(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, story_kind(kind)))

@app.get("/api/issues/<issue_id>/story/<kind>")
def issue_story_variants(issue_id, kind):
    return jsonify(story_workspace.variants(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, story_kind(kind)))

@app.post("/api/issues/<issue_id>/story/<kind>/import")
def issue_story_import(issue_id, kind):
    return jsonify(story_workspace.import_variant(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, story_kind(kind), request.get_json(silent=True) or {})), 201

@app.post("/api/issues/<issue_id>/story/<kind>/<variant_id>/approve")
def issue_story_approve(issue_id, kind, variant_id):
    body = request.get_json(silent=True) or {}
    return jsonify(story_workspace.approve(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, story_kind(kind), variant_id, body.get("note")))

@app.post("/api/issues/<issue_id>/story/<kind>/<variant_id>/promote")
def issue_story_promote(issue_id, kind, variant_id):
    body = request.get_json(silent=True) or {}
    return jsonify(story_workspace.promote(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, story_kind(kind), variant_id, body.get("replace") is True))

@app.get("/api/issues/<issue_id>/layout")
def issue_layout(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(page_panel_workspace.summary(folder, WORKSPACE_ROOT))

@app.post("/api/issues/<issue_id>/layout/variants")
def create_layout_variant(issue_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT)
    return jsonify(page_panel_workspace.create_variant(folder, WORKSPACE_ROOT)), 201

@app.post("/api/issues/<issue_id>/layout/variants/<variant_id>/approve")
def approve_layout_variant(issue_id, variant_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT); body = request.get_json(silent=True) or {}
    return jsonify(page_panel_workspace.approve(folder, WORKSPACE_ROOT, variant_id, body.get("note")))

@app.post("/api/issues/<issue_id>/layout/variants/<variant_id>/promote")
def promote_layout_variant(issue_id, variant_id):
    folder = issue_workflow.find_issue(issue_id, WORKSPACE_ROOT); body = request.get_json(silent=True) or {}
    return jsonify(page_panel_workspace.promote(folder, WORKSPACE_ROOT, variant_id, body.get("replace") is True))

@app.get("/api/issues/<issue_id>/art-prompts")
def issue_art_prompts(issue_id):
    return jsonify(art_prompt_workspace.summary(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT))

@app.post("/api/issues/<issue_id>/art-prompts/variants")
def create_art_prompt_variant(issue_id):
    return jsonify(art_prompt_workspace.create_variant(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT)), 201

@app.post("/api/issues/<issue_id>/art-prompts/variants/<variant_id>/approve")
def approve_art_prompt_variant(issue_id, variant_id):
    body = request.get_json(silent=True) or {}
    return jsonify(art_prompt_workspace.approve(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, variant_id, body.get("note")))

@app.post("/api/issues/<issue_id>/art-prompts/variants/<variant_id>/promote")
def promote_art_prompt_variant(issue_id, variant_id):
    body = request.get_json(silent=True) or {}
    return jsonify(art_prompt_workspace.promote(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, variant_id, body.get("replace") is True))

@app.get("/api/issues/<issue_id>/art-queue")
def issue_art_queue(issue_id):
    return jsonify(art_queue_workspace.summary(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT))

@app.post("/api/issues/<issue_id>/art-queue/build")
def build_art_queue(issue_id):
    return jsonify(art_queue_workspace.build_queue(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, True))

@app.post("/api/issues/<issue_id>/art-queue/<panel_id>/prompt")
def export_panel_prompt(issue_id,panel_id):
    return jsonify(art_queue_workspace.prompt_package(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, panel_id))

@app.post("/api/issues/<issue_id>/art-queue/<panel_id>/attempts")
def import_panel_attempt(issue_id,panel_id):
    upload=request.files.get("image")
    if not upload: raise art_queue_workspace.ArtQueueError("Multipart image upload is required")
    return jsonify(art_queue_workspace.import_attempt(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, panel_id, upload.read(), upload.filename, request.form.get("provider"))),201

@app.post("/api/issues/<issue_id>/art-queue/<panel_id>/attempts/<attempt_id>/select")
def select_panel_attempt(issue_id,panel_id,attempt_id):
    return jsonify(art_queue_workspace.select_preferred(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, panel_id,attempt_id))

@app.post("/api/issues/<issue_id>/art-queue/<panel_id>/attempts/<attempt_id>/status")
def review_panel_attempt(issue_id,panel_id,attempt_id):
    return jsonify(art_queue_workspace.set_attempt_status(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT,panel_id,attempt_id,(request.get_json(silent=True) or {}).get("status")))

@app.get("/api/issues/<issue_id>/qa")
def issue_qa(issue_id): return jsonify(visual_qa_workspace.summary(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT))
@app.post("/api/issues/<issue_id>/qa/reviews")
def create_qa_review(issue_id): return jsonify(visual_qa_workspace.create_review(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT)),201
@app.post("/api/issues/<issue_id>/qa/reviews/<review_id>/finalize")
def finalize_qa_review(issue_id,review_id):
 body=request.get_json(silent=True) or {};return jsonify(visual_qa_workspace.finalize(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT,review_id,body.get("verdict"),body.get("notes"),body.get("continuity_checks")))
@app.post("/api/issues/<issue_id>/qa/reviews/<review_id>/promote")
def promote_qa_review(issue_id,review_id):
 body=request.get_json(silent=True) or {};return jsonify(visual_qa_workspace.promote(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT,review_id,body.get("replace") is True))

@app.get("/api/issues/<issue_id>/release")
def issue_release(issue_id): return jsonify(release_workspace.readiness(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT))
@app.post("/api/issues/<issue_id>/release/manifest")
def create_release_manifest(issue_id): return jsonify(release_workspace.manifest(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT,True)),201
@app.post("/api/issues/<issue_id>/release/approve")
def approve_release(issue_id): return jsonify(release_workspace.approve(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT,(request.get_json(silent=True) or {}).get("note")))
@app.post("/api/issues/<issue_id>/release/promote-manifest")
def promote_release_manifest(issue_id): return jsonify(release_workspace.promote_manifest(issue_workflow.find_issue(issue_id,WORKSPACE_ROOT),WORKSPACE_ROOT,(request.get_json(silent=True) or {}).get("replace") is True))
@app.post("/api/issues/<issue_id>/release/publish-archive")
def publish_release_archive(issue_id):
    body = request.get_json(silent=True) or {}
    return jsonify(release_workspace.publish_archive(issue_workflow.find_issue(issue_id, WORKSPACE_ROOT), WORKSPACE_ROOT, body.get("replace") is True)), 201


@app.get("/media/locations/<slug>/<path:filename>")
def media_location(slug, filename):
    path = canon_catalog.resolve_canon_media(WORKSPACE_ROOT, "locations", slug, filename)
    return send_from_directory(path.parent, path.name)


@app.get("/media/props/<slug>/<path:filename>")
def media_prop(slug, filename):
    path = canon_catalog.resolve_canon_media(WORKSPACE_ROOT, "props", slug, filename)
    return send_from_directory(path.parent, path.name)


@app.get("/media/expressions/<slug>/<path:filename>")
def media_expression(slug, filename):
    path = canon_catalog.resolve_canon_media(WORKSPACE_ROOT, "expressions", slug, filename)
    return send_from_directory(path.parent, path.name)


@app.get("/media/<character_id>/<path:rel_path>")
def media(character_id, rel_path):
    character_id = store.resolve_character_id(character_id, BIBLES_ROOT)
    base = BIBLES_ROOT / character_id
    return send_from_directory(base, rel_path)


@app.errorhandler(Exception)
def handle_error(exc):
    if isinstance(exc, story_workspace.StoryWorkspaceError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, page_panel_workspace.PagePanelError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, art_queue_workspace.ArtQueueError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, art_prompt_workspace.ArtPromptError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, visual_qa_workspace.VisualQAError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, release_workspace.ReleaseError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, canon_catalog.CanonCatalogError):
        status, message = exc.status, str(exc)
    elif isinstance(exc, (store.BibleStoreError, story_context.StoryContextError, new_issue.IssueCreationError, issue_workflow.IssueWorkflowError)):
        status, message = 400, str(exc)
    else:
        status, message = 500, "Unexpected server error"
    return jsonify({"ok": False, "error": message}), status


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=True)
