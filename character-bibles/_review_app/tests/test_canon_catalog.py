import json
import sys
from pathlib import Path

import pytest
from PIL import Image

APP = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(APP))
import canon_catalog as catalog  # noqa: E402


@pytest.fixture()
def workspace(tmp_path):
    loc_root = tmp_path / "03_APPROVED_CANON" / "approved_locations"
    prop_root = tmp_path / "03_APPROVED_CANON" / "approved_props"
    expr_root = tmp_path / "03_APPROVED_CANON" / "approved_expressions"
    loc_root.mkdir(parents=True)
    prop_root.mkdir(parents=True)
    expr_root.mkdir(parents=True)
    locations = {
        "schema_version": "1.0",
        "locations": [
            {
                "location_id": "MZ-LOC-FESTIVAL-GROUNDS",
                "display_name": "Festival Grounds",
                "slug": "festival-grounds",
                "status": "proposed_story_canon",
                "month": "2026-08",
                "season_role": "Issue 01 setpiece",
            }
        ],
    }
    props = {
        "schema_version": "1.0",
        "props": [
            {
                "prop_id": "MZ-PROP-ECHO-SYMBOL",
                "display_name": "Echo Symbol",
                "status": "proposed_story_canon",
                "category": "mystery-motif",
                "notes": "Six segments",
            }
        ],
    }
    (loc_root / "locations-inventory.json").write_text(json.dumps(locations), encoding="utf-8")
    (prop_root / "props-inventory.json").write_text(json.dumps(props), encoding="utf-8")
    (loc_root / "festival-grounds").mkdir()
    (loc_root / "festival-grounds" / "bible.md").write_text("# Festival Grounds\n", encoding="utf-8")
    Image.new("RGB", (8, 8), (10, 20, 30)).save(loc_root / "festival-grounds" / "primary-reference.png")
    (prop_root / "echo-symbol").mkdir()
    (prop_root / "echo-symbol" / "bible.md").write_text("# Echo Symbol\n", encoding="utf-8")
    Image.new("RGB", (8, 8), (40, 50, 60)).save(prop_root / "echo-symbol" / "primary-reference.png")
    ash = expr_root / "ash"
    ash.mkdir()
    Image.new("RGB", (8, 8), (70, 80, 90)).save(ash / "ash_00_clean_base.png")
    Image.new("RGB", (8, 8), (70, 80, 90)).save(ash / "ash_01_neutral.png")
    return tmp_path


def test_list_and_detail_locations_and_props(workspace):
    locations = catalog.list_locations(workspace)
    props = catalog.list_props(workspace)
    assert len(locations) == 1
    assert locations[0]["has_bible"] is True
    assert locations[0]["has_primary_image"] is True
    assert locations[0]["primary_image_url"] == "/media/locations/festival-grounds/primary-reference.png"
    assert len(props) == 1
    assert props[0]["has_primary_image"] is True
    detail = catalog.get_location(workspace, "MZ-LOC-FESTIVAL-GROUNDS")
    assert "Festival Grounds" in (detail["bible_markdown"] or "")
    assert detail["primary_image_url"]
    prop = catalog.get_prop(workspace, "MZ-PROP-ECHO-SYMBOL")
    assert prop["summary"]["category"] == "mystery-motif"


def test_resolve_location_and_prop_refs(workspace):
    loc = catalog.resolve_location_ref(workspace, "Festival Grounds")
    assert loc["location_id"] == "MZ-LOC-FESTIVAL-GROUNDS"
    assert loc["primary_image_url"]
    props = catalog.resolve_prop_refs(workspace, ["Echo Symbol", "unknown prop"])
    assert props[0]["prop_id"] == "MZ-PROP-ECHO-SYMBOL"
    assert props[1]["error"]


def test_expression_sets_and_media_paths(workspace):
    sets = catalog.list_expression_sets(workspace)
    assert len(sets) == 1
    assert sets[0]["slug"] == "ash"
    assert sets[0]["image_count"] == 2
    detail = catalog.get_expression_set(workspace, "ash")
    assert detail["base_image"] == "ash_00_clean_base.png"
    path = catalog.resolve_canon_media(workspace, "locations", "festival-grounds", "primary-reference.png")
    assert path.is_file()
    with pytest.raises(catalog.CanonCatalogError):
        catalog.resolve_canon_media(workspace, "locations", "../escape", "primary-reference.png")
    with pytest.raises(catalog.CanonCatalogError):
        catalog.resolve_canon_media(workspace, "locations", "festival-grounds", "../secret.png")


def test_invalid_and_unknown_ids(workspace):
    with pytest.raises(catalog.CanonCatalogError, match="Invalid"):
        catalog.get_location(workspace, "../escape")
    with pytest.raises(catalog.CanonCatalogError, match="Unknown"):
        catalog.get_prop(workspace, "MZ-PROP-NOT-REAL")


def test_real_repo_inventory_loads():
    locations = catalog.list_locations(ROOT)
    props = catalog.list_props(ROOT)
    assert len(locations) >= 15
    assert len(props) >= 20
    assert all(x.get("has_primary_image") for x in locations)
    assert all(x.get("has_primary_image") for x in props)
    summary = catalog.catalog_summary(ROOT)
    assert summary["locations_count"] == len(locations)
    assert summary["props_count"] == len(props)
    assert summary["locations_with_primary"] == len(locations)
    assert summary["props_with_primary"] == len(props)
