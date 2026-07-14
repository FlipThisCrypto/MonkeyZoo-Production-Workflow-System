import importlib.util
import hashlib
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
           "scriptPromptBtn", "scriptImportBtn", "createPlanVariant", "buildArtQueue", "createArtPromptPack",
           "artAttemptFile",
           "createQAReview", "releaseManifest", "releaseApprove", "releasePromote", "releasePublishArchive",
           "validateStageButton",
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
    # Source may read the static flag to short-circuit, but must never assign it.
    assert "window.BANANA_LAB_STATIC_MODE = true" not in js
    assert "window.BANANA_LAB_STATIC_MODE === true" in js
    assert 'reason: "static-preview"' in js


def test_static_asset_version_changes_with_content_and_is_deterministic(tmp_path):
    module = _version_module(); asset = tmp_path / "app.js"; asset.write_bytes(b"one")
    first = module.version_token(asset); assert first == module.version_token(asset)
    asset.write_bytes(b"two"); second = module.version_token(asset)
    assert first != second
    assert module.versioned_script_url(asset) == f"/static/app.js?v={second}"


def test_deployed_html_token_equals_exact_transformed_bundle_hash(tmp_path):
    module = _version_module()
    bundle = tmp_path / "app.js"
    html = tmp_path / "index.html"
    html.write_text('<script src="./static/app.js?v=source-hash"></script>', encoding="utf-8")
    bundle.write_bytes(b"source javascript\n// injected static API mock\n")

    token = module.update_html_for_deployed_bundle(html, bundle)

    assert token == hashlib.sha256(bundle.read_bytes()).hexdigest()
    assert f'./static/app.js?v={token}' in html.read_text(encoding="utf-8")


def test_static_injection_change_updates_deployed_token_and_is_idempotent(tmp_path):
    module = _version_module()
    bundle = tmp_path / "app.js"
    html = tmp_path / "index.html"
    html.write_text('<script src="./static/app.js?v=local-token"></script>', encoding="utf-8")

    bundle.write_bytes(b"source\n// static injection v1\n")
    first = module.update_html_for_deployed_bundle(html, bundle)
    first_html = html.read_bytes()
    assert module.update_html_for_deployed_bundle(html, bundle) == first
    assert html.read_bytes() == first_html

    bundle.write_bytes(b"source\n// static injection v2\n")
    second = module.update_html_for_deployed_bundle(html, bundle)
    assert second != first
    assert html.read_text(encoding="utf-8").count("?v=") == 1
    assert f"?v={second}" in html.read_text(encoding="utf-8")


def test_local_and_deployed_tokens_may_differ_and_query_replacement_does_not_accumulate():
    module = _version_module()
    html = '<script src="./static/app.js?v=local?v=stale"></script>'
    updated = module.replace_script_version(html, "deployed")
    assert updated == '<script src="./static/app.js?v=deployed"></script>'


def test_sync_hashes_bundle_only_after_static_injection_and_write():
    sync = (ROOT / "docs" / "sync_docs.ps1").read_text(encoding="utf-8")
    write_bundle = sync.index('Set-Content -Path "$DocsDir/static/app.js"')
    hash_bundle = sync.index('--update-html "$DocsDir/index.html" "$DocsDir/static/app.js"')
    assert sync.index("$ApiMock") < write_bundle < hash_bundle
    assert sync.index("$CanonicalResolver") < write_bundle < hash_bundle
    assert sync.index('$JsContent = $JsContent -replace "`r`n", "`n"') < write_bundle


def test_checked_in_static_html_token_matches_deployed_bundle():
    module = _version_module()
    bundle = ROOT / "docs" / "static" / "app.js"
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    match = re.search(r'\./static/app\.js\?v=([0-9a-f]{64})', html)
    assert match and match.group(1) == module.version_token(bundle)


def test_generated_preview_resolver_uses_current_inventory_without_demo_fallback():
    js = (ROOT / "docs" / "static" / "app.js").read_text(encoding="utf-8")
    assert "characters.find(item => item.character_id === cid)" in js
    assert "charactersMap" not in js
    assert 'display_name:`Unresolved character (${cid})`' in js
    assert 'charactersMap["MZ-CHAR-CLEVER"]' not in js
