from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "character-bibles" / "_review_app" / "static"


def test_banana_lab_brand_hierarchy_and_navigation():
    html = (SOURCE / "index.html").read_text(encoding="utf-8")
    assert "<title>The Banana Lab by Fiend Studios — MonkeyZoo</title>" in html
    assert "The Banana Lab" in html
    assert "by Fiend Studios" in html
    assert "Active project" in html and "MonkeyZoo" in html
    for label in ("Dashboard", "Issues", "Characters", "Story Builder", "Canon", "Timeline", "Art Queue", "QA", "Release", "Settings"):
        assert label in html


def test_brand_assets_and_html_ids_are_safe():
    html = (SOURCE / "index.html").read_text(encoding="utf-8")
    assert (SOURCE / "banana-lab-mark.svg").is_file()
    assert (SOURCE / "banana-theme.css").is_file()
    ids = []
    import re
    ids.extend(re.findall(r'\bid="([^"]+)"', html))
    assert len(ids) == len(set(ids))
    assert "I:\\" not in html


def test_static_preview_brand_matches_and_remains_read_only():
    source = (SOURCE / "index.html").read_text(encoding="utf-8")
    static = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    for text in ("The Banana Lab", "by Fiend Studios", "MonkeyZoo"):
        assert text in source and text in static
    static_js = (ROOT / "docs" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Local backend required" in static_js
    assert '(cleanPath === "/api/issues"' in static_js
