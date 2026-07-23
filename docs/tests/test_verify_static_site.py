"""Coverage for the deployed static-site consistency gate.

verify_static_site re-derives every media URL the exported catalog declares and
confirms it resolves to a real file in docs/, and that each data JSON parses. It
exists because the exporter once shipped 51 dangling locations/props references
(absolute /media/... URLs whose files were never exported); these pin the
detection of that class and confirm the committed site stays consistent.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import verify_static_site as vss  # noqa: E402


def _minimal(docs: Path, catalog=None, characters=None, media=()):
    (docs / "static").mkdir(parents=True)
    (docs / "index.html").write_text("<html></html>", encoding="utf-8")
    for name in ("styles.css", "app.js"):
        (docs / "static" / name).write_text("x", encoding="utf-8")
    (docs / "static" / "canon-catalog.json").write_text(
        json.dumps(catalog if catalog is not None else {"locations": [], "props": [], "expressions": []}),
        encoding="utf-8")
    (docs / "static" / "characters.json").write_text(
        json.dumps(characters if characters is not None else []), encoding="utf-8")
    for rel in media:
        target = docs / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"img")
    return docs


def test_valid_empty_site_passes(tmp_path):
    assert vss.verify_static_site(_minimal(tmp_path / "docs")) == []


def test_existing_media_reference_resolves(tmp_path):
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [{"location_id": "L1", "primary_image_url": "./media/locations/l1/p.webp"}],
                 "props": [], "expressions": []},
        media=["media/locations/l1/p.webp"])
    assert vss.verify_static_site(docs) == []


def test_dangling_relative_media_reference_detected(tmp_path):
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [{"location_id": "L1", "primary_image_url": "./media/locations/l1/missing.webp"}],
                 "props": [], "expressions": []})
    assert any("dangling media reference" in p and "missing.webp" in p
               for p in vss.verify_static_site(docs))


def test_root_relative_unexported_media_detected(tmp_path):
    # the exact class that broke the props gallery: absolute /media/... never exported
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [], "expressions": [],
                 "props": [{"prop_id": "P1", "primary_image_url": "/media/props/p1/primary-reference.png"}]})
    assert any("dangling media reference" in p for p in vss.verify_static_site(docs))


def test_null_primary_image_is_not_flagged(tmp_path):
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [{"location_id": "L1", "has_primary_image": False, "primary_image_url": None}],
                 "props": [], "expressions": []})
    assert vss.verify_static_site(docs) == []


def test_expression_base_and_image_urls_checked(tmp_path):
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [], "props": [], "expressions": [
            {"slug": "ash", "base_image_url": "./media/expressions/ash/b.webp",
             "images": [{"filename": "b.webp", "url": "./media/expressions/ash/b.webp"}]}]})
    problems = vss.verify_static_site(docs)
    assert any("expression ash base" in p for p in problems)
    assert any("expression ash/b.webp" in p for p in problems)


def test_character_portrait_reference_checked(tmp_path):
    docs = _minimal(
        tmp_path / "docs",
        characters=[{"character_id": "MZ-CHAR-001", "primary_image": "./media/MZ-CHAR-001/portrait.webp"}])
    assert any("character MZ-CHAR-001" in p for p in vss.verify_static_site(docs))


def test_invalid_json_detected(tmp_path):
    docs = _minimal(tmp_path / "docs")
    (docs / "static" / "canon-catalog.json").write_text("{not json", encoding="utf-8")
    assert any("invalid JSON in static/canon-catalog.json" in p for p in vss.verify_static_site(docs))


def test_missing_required_file_detected(tmp_path):
    docs = _minimal(tmp_path / "docs")
    (docs / "static" / "app.js").unlink()
    assert any("missing required file" in p and "app.js" in p for p in vss.verify_static_site(docs))


def test_url_with_spaces_resolves(tmp_path):
    # expression slugs contain spaces ("lil devil"); the raw URL must resolve
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [], "props": [], "expressions": [
            {"slug": "lil devil", "base_image_url": "./media/expressions/lil devil/x.webp", "images": []}]},
        media=["media/expressions/lil devil/x.webp"])
    assert vss.verify_static_site(docs) == []


# ---- the committed site + CLI contract ----

def test_real_committed_docs_passes():
    assert vss.verify_static_site(vss.DOCS) == []


def test_cli_exit_zero_on_real_docs():
    result = subprocess.run([sys.executable, str(DOCS / "verify_static_site.py"), str(DOCS)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout


def test_cli_exit_one_on_broken_site(tmp_path):
    docs = _minimal(
        tmp_path / "docs",
        catalog={"locations": [{"location_id": "L1", "primary_image_url": "./media/locations/l1/missing.webp"}],
                 "props": [], "expressions": []})
    result = subprocess.run([sys.executable, str(DOCS / "verify_static_site.py"), str(docs)],
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert "FAILED" in result.stdout
