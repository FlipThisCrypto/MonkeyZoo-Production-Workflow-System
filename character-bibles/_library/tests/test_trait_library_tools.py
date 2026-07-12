import sys
from collections import Counter
from pathlib import Path

import pytest

LIBRARY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LIBRARY_ROOT))

import trait_library_tools as tools


REQUIRED_FIELDS = {
    "trait_id",
    "category",
    "short_name",
    "description",
    "possible_story_uses",
    "suitable_archetypes",
    "unsuitable_archetypes",
    "visual_or_dialogue_or_behavioral",
    "intensity",
    "recommended_frequency",
    "possible_downside",
    "compatibility_tags",
    "conflict_tags",
    "requires_owner_approval",
    "example_usage",
    "overuse_warning",
}


@pytest.fixture()
def library():
    return tools.load_library(LIBRARY_ROOT / "trait-library.yaml")


def test_library_has_30_categories_and_15_options_each(library):
    assert library["categories"] == tools.CATEGORIES
    counts = Counter(entry["category"] for entry in library["entries"])
    assert len(counts) == 30
    assert all(counts[category] >= 15 for category in tools.CATEGORIES)


def test_entries_have_required_fields_and_owner_approval(library):
    ids = set()
    for entry in library["entries"]:
        assert REQUIRED_FIELDS <= set(entry)
        assert entry["trait_id"] not in ids
        ids.add(entry["trait_id"])
        assert entry["requires_owner_approval"] is True
        assert entry["visual_or_dialogue_or_behavioral"] in {"visual", "dialogue", "behavioral"}


def test_existing_project_options_are_included(library):
    names = {entry["short_name"] for entry in library["entries"]}
    assert "Not today." in names
    assert "Stay focused." in names
    assert "points out the clue" in names
    assert "home frequency" in names


def test_validate_library_passes(library):
    assert tools.validate_library(library) == []


def test_recommender_returns_top_five_without_canon_status(library):
    result = tools.recommend_traits("MZ-CHAR-CLEVER", library=library)
    assert len(result) == 5
    assert all(item["suggested_status"] in {"experimental", "optional", "reserved"} for item in result)
    assert all(item["suggested_status"] != "canon" for item in result)
    assert all("risks" in item and item["risks"] for item in result)
