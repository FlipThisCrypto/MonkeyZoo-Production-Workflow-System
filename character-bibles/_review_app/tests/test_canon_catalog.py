import json
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(APP))
import canon_catalog as catalog  # noqa: E402


@pytest.fixture()
def workspace(tmp_path):
    loc_root = tmp_path / "03_APPROVED_CANON" / "approved_locations"
    prop_root = tmp_path / "03_APPROVED_CANON" / "approved_props"
    loc_root.mkdir(parents=True)
    prop_root.mkdir(parents=True)
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
    (prop_root / "echo-symbol").mkdir()
    (prop_root / "echo-symbol" / "bible.md").write_text("# Echo Symbol\n", encoding="utf-8")
    return tmp_path


def test_list_and_detail_locations_and_props(workspace):
    locations = catalog.list_locations(workspace)
    props = catalog.list_props(workspace)
    assert len(locations) == 1
    assert locations[0]["has_bible"] is True
    assert len(props) == 1
    detail = catalog.get_location(workspace, "MZ-LOC-FESTIVAL-GROUNDS")
    assert "Festival Grounds" in (detail["bible_markdown"] or "")
    prop = catalog.get_prop(workspace, "MZ-PROP-ECHO-SYMBOL")
    assert prop["summary"]["category"] == "mystery-motif"


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
    summary = catalog.catalog_summary(ROOT)
    assert summary["locations_count"] == len(locations)
    assert summary["props_count"] == len(props)
