import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "character-bibles" / "_review_app" / "static"


def _version_module():
    spec = importlib.util.spec_from_file_location("static_asset_version", ROOT / "docs" / "static_asset_version.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_mutation_controls_are_disabled_in_source_html_before_javascript():
    html = (SOURCE / "index.html").read_text(encoding="utf-8")
    ids = ["createIssueButton", "saveStoryBtn", "generateSampleBtn", "outlinePromptBtn", "outlineImportBtn",
           "scriptPromptBtn", "scriptImportBtn", "createPlanVariant", "buildArtQueue", "artAttemptFile",
           "createQAReview", "releaseManifest", "releaseApprove", "releasePromote", "validateStageButton",
           "approveStageButton", "advanceStageButton", "saveTraitBtn", "undoBtn", "storyImportSubmit"]
    for control_id in ids:
        tag = re.search(rf"<(?:button|input)\b[^>]*\bid=\"{control_id}\"[^>]*>", html)
        assert tag and "disabled" in tag.group(0), control_id


def test_runtime_capability_is_fail_closed_and_exact():
    js = (SOURCE / "app.js").read_text(encoding="utf-8")
    assert 'writable: false, reason: "unresolved"' in js
    assert 'data.runtime === "monkeyzoo-local"' in js
    assert 'data.capability === "monkeyzoo-production-write-v1"' in js
    assert "isTrustedRuntimeCapability(data)" in js
    assert "response.ok ? await response.json() : null" in js
    assert "Trusted writable local runtime required" in js
    assert "window.BANANA_LAB_STATIC_MODE === true" not in js


def test_static_asset_version_changes_with_content_and_is_deterministic(tmp_path):
    module = _version_module(); asset = tmp_path / "app.js"; asset.write_bytes(b"one")
    first = module.version_token(asset); assert first == module.version_token(asset)
    asset.write_bytes(b"two"); second = module.version_token(asset)
    assert first != second
    assert module.versioned_script_url(asset) == f"/static/app.js?v={second}"


def test_generated_preview_resolver_uses_current_inventory_without_demo_fallback():
    js = (ROOT / "docs" / "static" / "app.js").read_text(encoding="utf-8")
    assert "characters.find(item => item.character_id === cid)" in js
    assert "charactersMap" not in js
    assert 'display_name:`Unresolved character (${cid})`' in js
    assert 'charactersMap["MZ-CHAR-CLEVER"]' not in js
