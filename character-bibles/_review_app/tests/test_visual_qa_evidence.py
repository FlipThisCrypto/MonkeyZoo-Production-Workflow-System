"""Determinism regression for the QA evidence hash (visual_qa_workspace.evidence).

The evidence hash is folded from a file list in order; covers were enumerated
via an UNSORTED rglob (line 73) while every sibling (release_workspace) sorts.
With two or more cover PNGs the fingerprint became filesystem/platform
dependent, so a backup/restore or a Windows-vs-CI recompute could flip a
frozen approval's evidence_stale/approval_current and spuriously block a
release whose content never changed. These pin order-independence.
"""
import json
import pathlib
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import visual_qa_workspace as vqw  # noqa: E402


def _issue_with_two_covers(root: Path) -> Path:
    folder = root / "issue"
    folder.mkdir()
    (folder / "page_panel_plan.json").write_text(
        json.dumps({"issue_id": "MZ-2026-05-01", "page_count": 0, "pages": []}), encoding="utf-8")
    (folder / "metadata.json").write_text(
        json.dumps({"issue_id": "MZ-2026-05-01", "title": "T"}), encoding="utf-8")
    (folder / "cover_prompt.md").write_text("# cover", encoding="utf-8")
    (folder / "final_export_checklist.md").write_text("# checklist", encoding="utf-8")
    art = folder / "generated_art"
    art.mkdir()
    (art / "main_cover.png").write_bytes(b"MAINCOVERBYTES")
    (art / "variant_cover.png").write_bytes(b"VARIANTCOVERBYTES")
    return folder


def test_evidence_hash_is_cover_order_independent(tmp_path, monkeypatch):
    folder = _issue_with_two_covers(tmp_path)
    h1 = vqw.evidence(folder)["evidence_hash"]

    # Force cover enumeration in the opposite order. Only line 73 (covers) uses
    # rglob inside evidence(), so this isolates the cover ordering. The sorted()
    # guard must neutralize it; the pre-fix list() path yields a different hash.
    real_rglob = pathlib.Path.rglob
    monkeypatch.setattr(pathlib.Path, "rglob",
                        lambda self, pattern: list(real_rglob(self, pattern))[::-1])
    h2 = vqw.evidence(folder)["evidence_hash"]

    assert h1 == h2, "QA evidence hash must not depend on cover filesystem enumeration order"


def test_evidence_hash_stable_across_repeat_calls(tmp_path):
    folder = _issue_with_two_covers(tmp_path)
    ev1, ev2 = vqw.evidence(folder), vqw.evidence(folder)
    assert ev1["evidence_hash"] == ev2["evidence_hash"]
    assert ev1["checks"]["cover_images"] == 2
