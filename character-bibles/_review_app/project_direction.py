"""Load project direction + task map for the Studio Project Map dashboard."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DIRECTION_REL = Path("00_SYSTEM") / "project_direction.json"
VALID_STATUS = frozenset({"done", "active", "next", "later", "blocked"})


class ProjectDirectionError(ValueError):
    def __init__(self, message: str, status: int = 500):
        super().__init__(message)
        self.status = status


def direction_path(workspace: Path) -> Path:
    return workspace / DIRECTION_REL


def load_direction(workspace: Path) -> dict[str, Any]:
    path = direction_path(workspace)
    if not path.is_file():
        raise ProjectDirectionError("project_direction.json is missing", 404)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProjectDirectionError("project_direction.json is malformed", 500) from exc
    if not isinstance(data, dict):
        raise ProjectDirectionError("project_direction.json must be an object", 500)
    return data


def _all_tasks(data: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for track in data.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_id = track.get("id")
        track_title = track.get("title")
        for task in track.get("tasks") or []:
            if not isinstance(task, dict):
                continue
            entry = dict(task)
            entry["track_id"] = track_id
            entry["track_title"] = track_title
            tasks.append(entry)
    return tasks


def task_counts(data: dict[str, Any]) -> dict[str, int]:
    counts = {s: 0 for s in sorted(VALID_STATUS)}
    counts["total"] = 0
    for task in _all_tasks(data):
        status = str(task.get("status") or "later")
        if status not in VALID_STATUS:
            status = "later"
        counts[status] += 1
        counts["total"] += 1
    return counts


def enrich(data: dict[str, Any]) -> dict[str, Any]:
    """Return direction payload with derived summary fields for the UI."""
    payload = dict(data)
    counts = task_counts(data)
    rec = data.get("recommended_order") or []
    by_id = {t.get("id"): t for t in _all_tasks(data)}
    recommended = []
    for tid in rec:
        task = by_id.get(tid)
        if task:
            recommended.append(
                {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "status": task.get("status"),
                    "priority": task.get("priority"),
                    "track_title": task.get("track_title"),
                }
            )
    payload["task_counts"] = counts
    payload["recommended_tasks"] = recommended
    payload["source_path"] = str(DIRECTION_REL).replace("\\", "/")
    return payload
