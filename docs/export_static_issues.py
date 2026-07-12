"""Export read-only production dashboard snapshots for GitHub Pages."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import issue_workflow

if __name__ == "__main__":
    issues = issue_workflow.list_issues(ROOT)
    (ROOT / "docs" / "static" / "issue-workflows.json").write_text(json.dumps(issues, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
