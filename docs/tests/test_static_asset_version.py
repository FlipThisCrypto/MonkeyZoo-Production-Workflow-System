"""Coverage for the static-asset cache-busting used by the public-site deploy.

sync_docs.ps1 stamps ./static/app.js, ./static/styles.css and
./static/banana-theme.css with ?v=<sha256-of-deployed-bytes> so returning
visitors never render against a stale cached bundle. The string rewrite runs on
every deploy and had no tests; these pin the contract:
  * a fresh reference gains exactly one ?v= token,
  * re-versioning replaces the old token (never appends a second),
  * versioning one asset never corrupts another whose name it is a prefix of,
  * the deployed-bytes helper hashes the real file and writes it back.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import static_asset_version as sav  # noqa: E402


def test_version_token_is_deterministic_sha256(tmp_path):
    f = tmp_path / "a.css"
    f.write_bytes(b"body{}")
    import hashlib
    assert sav.version_token(f) == hashlib.sha256(b"body{}").hexdigest()
    assert sav.version_token(f) == sav.version_token(f)


def test_adds_version_to_unversioned_reference():
    html = '<link rel="stylesheet" href="./static/styles.css">'
    out = sav.replace_asset_version(html, "abc123", "./static/styles.css")
    assert out == '<link rel="stylesheet" href="./static/styles.css?v=abc123">'


def test_reversion_replaces_old_token_not_appends():
    html = '<script src="./static/app.js?v=OLDHASH"></script>'
    out = sav.replace_asset_version(html, "NEWHASH", "./static/app.js")
    assert out == '<script src="./static/app.js?v=NEWHASH"></script>'
    assert "OLDHASH" not in out
    assert out.count("?v=") == 1


def test_prefix_asset_does_not_corrupt_longer_reference():
    # Stamping app.js must not rewrite the app.json reference into
    # "app.js?v=Xon". Right-anchoring is what protects the longer path.
    html = '<a href="./static/app.js"></a><a href="./static/app.json"></a>'
    out = sav.replace_asset_version(html, "X", "./static/app.js")
    assert './static/app.js?v=X"' in out
    assert './static/app.json"' in out  # untouched, no ?v= injected mid-name
    assert "app.json?v=" not in out
    assert "app.js?v=Xon" not in out


def test_multiple_occurrences_all_updated():
    html = 'a ./static/app.js?v=1 b ./static/app.js c'
    out = sav.replace_asset_version(html, "2", "./static/app.js")
    assert out.count("./static/app.js?v=2") == 2
    assert "?v=1" not in out


def test_two_assets_are_versioned_independently():
    html = ('<link href="./static/styles.css">'
            '<link href="./static/banana-theme.css">')
    out = sav.replace_asset_version(html, "S", "./static/styles.css")
    out = sav.replace_asset_version(out, "B", "./static/banana-theme.css")
    assert './static/styles.css?v=S"' in out
    assert './static/banana-theme.css?v=B"' in out


def test_update_html_for_deployed_asset_round_trip(tmp_path):
    css = tmp_path / "styles.css"
    css.write_bytes(b"body{color:red}")
    html = tmp_path / "index.html"
    html.write_text('<link href="./static/styles.css">\n', encoding="utf-8")
    token = sav.update_html_for_deployed_asset(html, "./static/styles.css", css)
    assert token == sav.version_token(css)
    written = html.read_text(encoding="utf-8")
    assert f'./static/styles.css?v={token}' in written
    # newline="" write must not introduce CRLF that would change the deployed hash.
    assert "\r\n" not in written


def test_update_html_for_deployed_bundle_targets_app_js(tmp_path):
    bundle = tmp_path / "app.js"
    bundle.write_bytes(b"console.log(1)")
    html = tmp_path / "index.html"
    html.write_text('<script src="./static/app.js?v=old"></script>', encoding="utf-8")
    token = sav.update_html_for_deployed_bundle(html, bundle)
    assert f'./static/app.js?v={token}' in html.read_text(encoding="utf-8")
    assert "?v=old" not in html.read_text(encoding="utf-8")
