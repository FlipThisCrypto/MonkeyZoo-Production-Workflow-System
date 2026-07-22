"""Tests for the Genesis release packager: reading-order enforcement + CBZ."""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

GEN = Path(__file__).resolve().parents[1]
if str(GEN) not in sys.path:
    sys.path.insert(0, str(GEN))

import genesis_release as gr  # noqa: E402


def _fake_web(root: Path, story=22, front=True, back=True):
    covers = root / "web" / "covers"
    story_d = root / "web" / "story_pages"
    covers.mkdir(parents=True)
    story_d.mkdir(parents=True)
    if front:
        Image.new("RGB", (40, 60), "white").save(covers / "01_FRONT_COVER.jpg")
    for i in range(1, story + 1):
        Image.new("RGB", (40, 60), (i, i, i)).save(story_d / f"{i + 1:02d}_PAGE_{i:02d}.jpg")
    if back:
        Image.new("RGB", (40, 60), "black").save(covers / "24_BACK_COVER.jpg")
    return root


def test_ordered_pages_is_front_pages_back(tmp_path):
    _fake_web(tmp_path)
    files = gr.ordered_pages(tmp_path)
    assert len(files) == 24
    assert files[0].name == "01_FRONT_COVER.jpg"
    assert files[-1].name == "24_BACK_COVER.jpg"
    nums = [int(p.name[:2]) for p in files]
    assert nums == list(range(1, 25))


def test_sequence_check_rejects_missing_page(tmp_path):
    _fake_web(tmp_path, story=21)  # 23 files -> gap
    with pytest.raises(SystemExit):
        gr._check_sequence(gr.ordered_pages(tmp_path))


def test_sequence_check_rejects_missing_back_cover(tmp_path):
    _fake_web(tmp_path, back=False)
    with pytest.raises(SystemExit):
        gr._check_sequence(gr.ordered_pages(tmp_path))


def test_sequence_check_aborts_cleanly_on_misnamed_file(tmp_path):
    # A stray, non-page-numbered jpg landing in a render dir must trip the clean
    # ABORT, not crash the packager with a ValueError from int('th').
    _fake_web(tmp_path)
    Image.new("RGB", (40, 60), "red").save(tmp_path / "web" / "story_pages" / "thumbnail.jpg")
    with pytest.raises(SystemExit) as exc:
        gr._check_sequence(gr.ordered_pages(tmp_path))
    assert "two-digit page prefix" in str(exc.value)


def test_cbz_orders_pages_front_to_back(tmp_path):
    _fake_web(tmp_path)
    files = gr.ordered_pages(tmp_path)
    out = tmp_path / "test.cbz"
    gr.build_cbz(files, out)
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    assert names[0] == "01_FRONT_COVER.jpg"
    assert names[-1] == "24_BACK_COVER.jpg"
    assert names == sorted(names)


def test_package_writes_manifest_and_checksums(tmp_path):
    _fake_web(tmp_path)
    (tmp_path / "GENESIS_LAYOUT_PLAN.json").write_text("{}", encoding="utf-8")
    result = gr.package(tmp_path)
    rel = tmp_path / "release"
    assert (rel / "MonkeyZoo_Genesis.cbz").exists()
    assert (rel / "MonkeyZoo_Genesis.pdf").exists()
    assert (rel / "release_manifest.json").exists()
    sums = (rel / "SHA256SUMS.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(sums) == 26  # cbz + pdf + 24 images
    assert result["manifest"]["story_pages"] == 22


# --- verify(): release integrity + provenance before distribution/minting ------

def _packaged_release(tmp_path):
    _fake_web(tmp_path)
    (tmp_path / "GENESIS_LAYOUT_PLAN.json").write_text("{}", encoding="utf-8")
    gr.package(tmp_path)
    return tmp_path


def test_verify_passes_a_fresh_release(tmp_path):
    result = gr.verify(_packaged_release(tmp_path))
    assert result["problems"] == []
    assert result["verified"] == 24 + 2  # 22 pages + 2 covers + cbz + pdf listed; all intact


def test_verify_detects_corrupted_web_page(tmp_path):
    genesis = _packaged_release(tmp_path)
    page = genesis / "web" / "story_pages" / "02_PAGE_01.jpg"
    page.write_bytes(page.read_bytes() + b"corruption")
    problems = gr.verify(genesis)["problems"]
    assert any(p.startswith("HASH MISMATCH") and "02_PAGE_01.jpg" in p for p in problems)


def test_verify_detects_missing_file(tmp_path):
    genesis = _packaged_release(tmp_path)
    (genesis / "web" / "covers" / "24_BACK_COVER.jpg").unlink()
    problems = gr.verify(genesis)["problems"]
    assert any(p.startswith("MISSING") and "24_BACK_COVER.jpg" in p for p in problems)


def test_verify_detects_manifest_provenance_drift(tmp_path):
    genesis = _packaged_release(tmp_path)
    manifest_path = genesis / "release" / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["cbz"]["sha256"] = "0" * 64  # claim a hash the file doesn't have
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    problems = gr.verify(genesis)["problems"]
    assert any("manifest cbz sha256 mismatch" in p for p in problems)


def test_verify_detects_manifest_byte_drift(tmp_path):
    genesis = _packaged_release(tmp_path)
    manifest_path = genesis / "release" / "release_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["pdf"]["bytes"] = 1  # wrong recorded size
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    problems = gr.verify(genesis)["problems"]
    assert any("manifest pdf byte size mismatch" in p for p in problems)


def test_verify_missing_sums_raises(tmp_path):
    (tmp_path / "release").mkdir()
    with pytest.raises(SystemExit):
        gr.verify(tmp_path)


def test_verify_cli_exit_codes(tmp_path, monkeypatch, capsys):
    genesis = _packaged_release(tmp_path)
    monkeypatch.setattr(sys, "argv", ["genesis_release.py", str(genesis), "--verify"])
    with pytest.raises(SystemExit) as ok:
        gr.main()
    assert ok.value.code == 0
    assert "verify OK" in capsys.readouterr().out
    (genesis / "web" / "story_pages" / "02_PAGE_01.jpg").write_bytes(b"tampered")
    monkeypatch.setattr(sys, "argv", ["genesis_release.py", str(genesis), "--verify"])
    with pytest.raises(SystemExit) as bad:
        gr.main()
    assert bad.value.code == 1
    assert "verify FAILED" in capsys.readouterr().out
