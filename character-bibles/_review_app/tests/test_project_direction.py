import json
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(APP))
import project_direction as pd  # noqa: E402


def test_repo_project_direction_loads_and_counts():
    data = pd.load_direction(ROOT)
    assert data["schema_version"] == "1.0"
    assert data["north_star"]
    assert data["tracks"]
    enriched = pd.enrich(data)
    counts = enriched["task_counts"]
    assert counts["total"] >= 20
    assert counts["done"] + counts["active"] + counts["next"] + counts["later"] + counts["blocked"] == counts["total"]
    assert enriched["recommended_tasks"]
    assert enriched["source_path"] == "00_SYSTEM/project_direction.json"


def test_missing_direction_errors(tmp_path):
    with pytest.raises(pd.ProjectDirectionError, match="missing"):
        pd.load_direction(tmp_path)


def test_malformed_direction_errors(tmp_path):
    path = tmp_path / "00_SYSTEM" / "project_direction.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(pd.ProjectDirectionError, match="malformed"):
        pd.load_direction(tmp_path)


def test_task_counts_unknown_status_bucketed(tmp_path):
    payload = {
        "tracks": [
            {
                "id": "t1",
                "title": "T",
                "tasks": [
                    {"id": "a", "title": "A", "status": "done"},
                    {"id": "b", "title": "B", "status": "weird"},
                ],
            }
        ]
    }
    path = tmp_path / "00_SYSTEM" / "project_direction.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    data = pd.load_direction(tmp_path)
    counts = pd.task_counts(data)
    assert counts["done"] == 1
    assert counts["later"] == 1
    assert counts["total"] == 2
