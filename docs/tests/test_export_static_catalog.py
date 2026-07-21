"""Regression: the catalog exporter must emit RAW (unencoded) media URLs.

The public site's single client-side mediaUrl() (static/app.js) percent-encodes
every path segment exactly once. Every canon media source (canon_catalog
locations/props, character portraits) therefore stores RAW paths. The expression
exporter must do the same: if it pre-encodes, a spaced slug like "lil devil"
becomes %20 in the JSON and the client re-encodes it to %2520 -> a literal
"lil%20devil" folder request that 404s on GitHub Pages. Pin the raw-URL contract.
"""
import sys
import urllib.parse
from pathlib import Path

import pytest

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

DOCS = Path(__file__).resolve().parents[1]        # docs/
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import export_static_catalog as cat  # noqa: E402


def _seed_expression(root: Path, slug: str, filename: str) -> None:
    d = root / "03_APPROVED_CANON" / "approved_expressions" / slug
    d.mkdir(parents=True)
    Image.new("RGB", (8, 8), (200, 40, 190)).save(d / filename)


def _client_media_url(url: str) -> str:
    """Mirror of static/app.js mediaUrl(): encodeURIComponent each segment, then
    restore the structural slashes."""
    return "/".join(urllib.parse.quote(seg, safe="") for seg in url.split("/")).replace("%2F", "/")


def test_exporter_emits_raw_unencoded_urls_for_spaced_slugs(tmp_path, monkeypatch):
    monkeypatch.setattr(cat, "ROOT", tmp_path)
    _seed_expression(tmp_path, "lil devil", "lildevil_00_clean_base.png")

    exported = cat._export_expression_assets()

    assert len(exported) == 1
    item = exported[0]
    assert item["slug"] == "lil devil"
    for url in [item["base_image_url"], *[i["url"] for i in item["images"]]]:
        assert url.startswith("./media/expressions/lil devil/"), url
        assert "%" not in url, f"URL must be RAW (client encodes once), got: {url}"
        assert " " in url                                   # the raw space is present


def test_raw_url_survives_one_client_encode_but_a_preencoded_one_would_not(tmp_path, monkeypatch):
    monkeypatch.setattr(cat, "ROOT", tmp_path)
    _seed_expression(tmp_path, "lil devil", "lildevil_00_clean_base.png")

    raw = cat._export_expression_assets()[0]["base_image_url"]
    once = _client_media_url(raw)
    assert "%20" in once and "%2520" not in once           # single-encoded -> resolves
    # a hypothetical pre-encoded URL would double-encode to the broken 404 form
    assert "%2520" in _client_media_url(raw.replace(" ", "%20"))
