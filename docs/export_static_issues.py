"""Export read-only production dashboard snapshots for GitHub Pages."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import issue_workflow
import story_workspace
import page_panel_workspace
import art_queue_workspace

if __name__ == "__main__":
    issues = issue_workflow.list_issues(ROOT)
    for issue in issues:
        if issue.get("degraded"): continue
        try:
            folder = issue_workflow.find_issue(issue["issue_id"], ROOT)
            issue["story"] = story_workspace.summary(folder, ROOT)
        except Exception as exc:
            issue["story"] = {"degraded": True, "error": str(exc), "outlines": [], "scripts": []}
        try:
            folder = issue_workflow.find_issue(issue["issue_id"], ROOT)
            issue["layout"] = page_panel_workspace.summary(folder, ROOT)
        except Exception as exc:
            issue["layout"] = {"degraded": True, "error": str(exc), "variants": []}
        try:
            issue["art_queue"] = art_queue_workspace.summary(issue_workflow.find_issue(issue["issue_id"], ROOT), ROOT)
        except Exception as exc:
            issue["art_queue"] = {"degraded": True, "error": str(exc), "queue": {"items": []}}
    (ROOT / "docs" / "static" / "issue-workflows.json").write_text(json.dumps(issues, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
