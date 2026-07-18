from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import backup_production as bp


@pytest.fixture()
def source(tmp_path, monkeypatch):
    """A tiny fake workspace so the backup runs fast and deterministically,
    instead of copying the real (huge) production trees."""
    src = tmp_path / "workspace"
    (src / "02_MONTHLY_ISSUES" / "2027-01_Issue_01").mkdir(parents=True)
    (src / "02_MONTHLY_ISSUES" / "2027-01_Issue_01" / "issue_brief.md").write_text("Issue ID: MZ-2027-01-01\n", encoding="utf-8")
    (src / "03_APPROVED_CANON").mkdir()
    (src / "03_APPROVED_CANON" / "canon.txt").write_text("locked", encoding="utf-8")
    # noise that must be excluded from the backup
    cache = src / "03_APPROVED_CANON" / "__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_text("bytecode", encoding="utf-8")
    (src / "03_APPROVED_CANON" / "module.pyc").write_text("bytecode", encoding="utf-8")
    monkeypatch.setattr(bp, "ROOT", src)
    return src


def _targets():
    # include one present dir, one file-less present dir, and one missing target
    return ["02_MONTHLY_ISSUES", "03_APPROVED_CANON", "does_not_exist"]


def test_backup_creates_verifiable_manifest(source, tmp_path):
    dest_root = tmp_path / "backups"
    dest_root.mkdir()
    dest = bp.backup(dest_root, _targets())

    manifest = json.loads((dest / "BACKUP_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["skipped_missing"] == ["does_not_exist"]
    assert manifest["file_count"] == len(manifest["files"]) > 0

    # every recorded hash must match the copied file exactly (integrity)
    for entry in manifest["files"]:
        copied = dest / entry["path"]
        assert copied.is_file(), entry["path"]
        got = hashlib.sha256(copied.read_bytes()).hexdigest()
        assert got == entry["sha256"], entry["path"]
        assert copied.stat().st_size == entry["size"]

    # README exists and the backup is self-describing
    assert (dest / "BACKUP_README.md").exists()


def test_backup_excludes_pycache_and_bytecode(source, tmp_path):
    dest_root = tmp_path / "backups"; dest_root.mkdir()
    dest = bp.backup(dest_root, ["03_APPROVED_CANON"])
    paths = {e["path"] for e in json.loads((dest / "BACKUP_MANIFEST.json").read_text(encoding="utf-8"))["files"]}
    assert any(p.endswith("canon.txt") for p in paths)
    assert not any("__pycache__" in p for p in paths), paths
    assert not any(p.endswith(".pyc") for p in paths), paths


def test_dry_run_writes_nothing(source, tmp_path):
    dest_root = tmp_path / "backups"; dest_root.mkdir()
    dest = bp.backup(dest_root, _targets(), dry_run=True)
    # dry run returns the intended path but must not create it
    assert not dest.exists()
    assert list(dest_root.iterdir()) == []


def test_existing_destination_is_refused(source, tmp_path, monkeypatch):
    dest_root = tmp_path / "backups"; dest_root.mkdir()
    # first backup succeeds
    first = bp.backup(dest_root, ["03_APPROVED_CANON"])
    # force the SAME timestamp so the second call collides
    monkeypatch.setattr(bp, "datetime", _FixedDatetime(first.name.split("monkeyzoo-backup-")[-1]))
    with pytest.raises(SystemExit):
        bp.backup(dest_root, ["03_APPROVED_CANON"])


class _FixedDatetime:
    """Freeze datetime.now().strftime to reproduce a known backup stamp."""
    def __init__(self, stamp): self._stamp = stamp
    def now(self, tz=None): return self
    def strftime(self, _fmt): return self._stamp
    def isoformat(self, timespec="seconds"): return "2027-01-01T00:00:00+00:00"
