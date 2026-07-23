"""Regression: the character exporter must not wipe sibling docs/media subtrees.

export_static_characters.py used to shutil.rmtree the entire docs/media tree
and only regenerate per-character portraits, deleting git-tracked
docs/media/expressions/** (372 files owned by export_static_catalog.py) -- the
root cause of an in-session 372-file deletion. It must now touch only the
per-character portrait folders it owns.
"""
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]        # docs/
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import export_static_characters as exp  # noqa: E402


def test_export_preserves_sibling_media_and_prunes_only_own_folders(tmp_path, monkeypatch):
    # fake the canon layer so no full bible fixture is needed
    monkeypatch.setattr(exp.bible_store, "load_all",
                        lambda bibles: [("MZ-CHAR-TEST", {"visual_canon": {}})])
    monkeypatch.setattr(exp.bible_store, "character_summary",
                        lambda cid, data: {"character_id": cid})
    (tmp_path / "character-bibles").mkdir()
    (tmp_path / "docs" / "static").mkdir(parents=True)
    expr = tmp_path / "docs" / "media" / "expressions" / "static"
    expr.mkdir(parents=True)
    keep = expr / "keep.webp"
    keep.write_bytes(b"EXPR-PLATE")                         # sibling subtree (owned by catalog exporter)
    stale = tmp_path / "docs" / "media" / "MZ-CHAR-GONE"    # a character no longer in canon
    stale.mkdir(parents=True)
    (stale / "portrait.png").write_bytes(b"old")

    exp.export(root=tmp_path)

    assert keep.exists(), "sibling docs/media/expressions must survive the character export"
    assert not stale.exists(), "a stale character portrait folder should be pruned"
    assert (tmp_path / "docs" / "static" / "characters.json").exists()


def test_same_size_portrait_change_is_recopied(tmp_path, monkeypatch):
    # A re-approved portrait that changes content but keeps its byte length must
    # be re-copied; a size-only staleness check would leave the stale image.
    bibles = tmp_path / "character-bibles" / "MZ-CHAR-TEST" / "refs"
    bibles.mkdir(parents=True)
    src = bibles / "primary.png"
    src.write_bytes(b"AAAA")
    monkeypatch.setattr(exp.bible_store, "load_all",
                        lambda b: [("MZ-CHAR-TEST",
                                    {"visual_canon": {"primary_reference_image": "refs/primary.png"}})])
    monkeypatch.setattr(exp.bible_store, "character_summary",
                        lambda cid, data: {"character_id": cid})
    (tmp_path / "docs" / "static").mkdir(parents=True)

    exp.export(root=tmp_path)
    target = tmp_path / "docs" / "media" / "MZ-CHAR-TEST" / "portrait.png"
    assert target.read_bytes() == b"AAAA"

    src.write_bytes(b"BBBB")          # same 4-byte size, different content
    exp.export(root=tmp_path)
    assert target.read_bytes() == b"BBBB", "same-size portrait change must be re-copied"
