"""Tests for the Genesis release packager: reading-order enforcement + CBZ."""
from __future__ import annotations

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
