"""Regression coverage for public-media URL encoding in the catalog exporter.

Expression plates live in owner-named folders ("Neon Alley", unicode, etc.).
Their URLs are baked into canon-catalog.json and resolved by the browser on
GitHub Pages, so each path segment must be percent-encoded while the "./" prefix
and "/" structure stay intact. A regression here breaks image links on the
public site silently (the JSON still validates; the images just 404), so the
encoding is isolated in _encode_media_url and pinned here.
"""
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]        # docs/
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))

import export_static_catalog as cat  # noqa: E402


def test_plain_ascii_path_is_unchanged():
    rel = "./media/expressions/happy/page_00_clean_base.webp"
    assert cat._encode_media_url(rel) == rel


def test_spaces_are_percent_encoded_per_segment():
    out = cat._encode_media_url("./media/expressions/Neon Alley/base plate.webp")
    assert out == "./media/expressions/Neon%20Alley/base%20plate.webp"
    assert " " not in out


def test_dot_and_dotdot_segments_preserved():
    # navigation segments must NOT be encoded or the relative URL breaks
    assert cat._encode_media_url("../a/b.webp") == "../a/b.webp"
    assert cat._encode_media_url("./x.webp").startswith("./")


def test_structural_slashes_survive_but_slashes_in_names_do_not_appear():
    out = cat._encode_media_url("./media/expressions/set/img.webp")
    assert out.count("/") == 4                       # 4 structural separators preserved


def test_unicode_and_reserved_chars_are_encoded():
    out = cat._encode_media_url("./media/expressions/café#1/a.webp")
    assert "café" not in out and "#" not in out      # both encoded, none left raw
    assert out.startswith("./media/expressions/")


def test_safe_punctuation_in_filenames_is_kept_readable():
    # '.', '_' and '-' are declared safe so filenames stay human-readable
    rel = "./media/expressions/set/MZ_char-01_clean.base.webp"
    assert cat._encode_media_url(rel) == rel


def test_backslashes_are_normalised_to_forward_slashes():
    out = cat._encode_media_url(".\\media\\expressions\\set\\a.webp")
    assert "\\" not in out
    assert out == "./media/expressions/set/a.webp"
