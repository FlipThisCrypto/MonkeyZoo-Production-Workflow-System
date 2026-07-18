"""Release-packaging unit tests (build_release.py): CBZ assembly ordering
and the archive immutability guard -- both release-critical and previously
untested."""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_release as br


def _issue_with_pages(root: Path, name="2027-01_Issue_01", pages=3, cover=True):
    issue = root / "02_MONTHLY_ISSUES" / name
    web = issue / "layout" / "web_layout"
    web.mkdir(parents=True)
    for i in range(1, pages + 1):
        (web / f"page_{i:02d}.png").write_bytes(b"PNGDATA" + str(i).encode())
    if cover:
        exports = issue / "exports"; exports.mkdir(parents=True, exist_ok=True)
        (exports / "cover.png").write_bytes(b"COVER")
    return issue


def test_cbz_orders_pages_and_prepends_cover(tmp_path):
    issue = _issue_with_pages(tmp_path, pages=3, cover=True)
    br.build_cbz(issue, "01")
    cbz = issue / "exports" / "MonkeyZoo_Issue_01_CBZ.zip"
    assert cbz.exists()
    with zipfile.ZipFile(cbz) as z:
        names = z.namelist()
    assert names == ["000_cover.png", "001_page_01.png", "002_page_02.png", "003_page_03.png"]


def test_cbz_without_cover_still_builds_pages(tmp_path):
    issue = _issue_with_pages(tmp_path, pages=2, cover=False)
    br.build_cbz(issue, "02")
    with zipfile.ZipFile(issue / "exports" / "MonkeyZoo_Issue_02_CBZ.zip") as z:
        names = z.namelist()
    assert names == ["001_page_01.png", "002_page_02.png"]


def test_cbz_skips_when_no_pages(tmp_path):
    issue = tmp_path / "02_MONTHLY_ISSUES" / "2027-01_Issue_09"
    (issue / "layout" / "web_layout").mkdir(parents=True)
    br.build_cbz(issue, "09")
    assert not (issue / "exports" / "MonkeyZoo_Issue_09_CBZ.zip").exists()


def test_archive_excludes_raw_panels_and_is_immutable(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "FACTORY", tmp_path)
    issue = _issue_with_pages(tmp_path, pages=1, cover=True)
    raw = issue / "generated_art" / "raw_panels"; raw.mkdir(parents=True)
    (raw / "huge.png").write_bytes(b"x" * 1000)
    (issue / "metadata.json").write_text("{}", encoding="utf-8")

    br.archive(issue, "01")
    dest = tmp_path / "05_RELEASE_ARCHIVE" / "2027" / "2027-01_Issue_01"
    assert dest.exists()
    assert (dest / "metadata.json").exists()
    assert not (dest / "generated_art" / "raw_panels").exists()   # heavy raw art excluded

    # re-archiving the same issue must refuse (immutable release record)
    with pytest.raises(SystemExit):
        br.archive(issue, "01")


def test_archive_interrupted_copy_leaves_no_partial_and_allows_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "FACTORY", tmp_path)
    issue = _issue_with_pages(tmp_path, pages=1, cover=True)
    (issue / "metadata.json").write_text("{}", encoding="utf-8")
    dest = tmp_path / "05_RELEASE_ARCHIVE" / "2027" / "2027-01_Issue_01"
    year_dir = tmp_path / "05_RELEASE_ARCHIVE" / "2027"

    real_copytree = br.shutil.copytree
    calls = {"n": 0}

    def flaky_copytree(src, dst, *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            os.makedirs(dst, exist_ok=True)      # partial dir created...
            raise KeyboardInterrupt("interrupted mid-copy")   # ...then interrupted
        return real_copytree(src, dst, *a, **k)

    monkeypatch.setattr(br.shutil, "copytree", flaky_copytree)
    with pytest.raises(KeyboardInterrupt):
        br.archive(issue, "01")
    assert not dest.exists()                                   # nothing committed
    assert list(year_dir.glob(".*partial*")) == []            # temp cleaned up

    # retry now succeeds -- before the fix the partial dest permanently blocked it
    monkeypatch.setattr(br.shutil, "copytree", real_copytree)
    br.archive(issue, "01")
    assert dest.exists()
    assert (dest / "metadata.json").exists()
