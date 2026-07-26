# Silent Failure Audit Report

**Source enumeration:** `git-tracked`

## Summary

Total handlers scanned: 163

| Classification | Count |
|----------------|-------|
| cleanup-suppression | 30 |
| intentional-fallback | 66 |
| likely-swallowed | 14 |
| re-raised | 53 |

## All Findings

| File | Line | Handler | Classification | Detail |
|------|------|---------|----------------|--------|
| 00_SYSTEM/scripts/assemble_pages.py | 42 | `OSError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| 00_SYSTEM/scripts/assemble_pages.py | 45 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| 00_SYSTEM/scripts/build_release.py | 87 | `BaseException` | re-raised | Exception is re-raised or wrapped. |
| 00_SYSTEM/scripts/gen_char_refs.py | 159 | `urllib.error.URLError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| 00_SYSTEM/scripts/genesis/genesis_charart.py | 418 | `Exception` | likely-swallowed | Broad handler with no raise, logging, or fallback. |
| 00_SYSTEM/scripts/genesis/genesis_release.py | 142 | `ValueError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| 00_SYSTEM/scripts/integration/assemble_issue_preview.py | 27 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| 00_SYSTEM/scripts/new_issue.py | 61 | `(TypeError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| 00_SYSTEM/scripts/new_issue.py | 103 | `(ImportError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| 00_SYSTEM/scripts/new_issue.py | 203 | `IssueCreationError` | re-raised | Exception is re-raised or wrapped. |
| 00_SYSTEM/scripts/new_issue.py | 205 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| 00_SYSTEM/scripts/run_art_batch.py | 119 | `urllib.error.URLError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| 00_SYSTEM/scripts/run_art_batch.py | 133 | `json.JSONDecodeError` | re-raised | Exception is re-raised or wrapped. |
| 00_SYSTEM/scripts/validate_issue.py | 41 | `FileNotFoundError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| 00_SYSTEM/scripts/validate_issue.py | 43 | `json.JSONDecodeError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| 00_SYSTEM/scripts/validate_issue.py | 54 | `ImportError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| 00_SYSTEM/scripts/validate_ledger.py | 83 | `(OSError, ValueError)` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| 00_SYSTEM/scripts/validate_ledger.py | 109 | `(OSError, ValueError)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/app.py | 109 | `(TypeError, ValueError)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/app.py | 118 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/app.py | 126 | `ValueError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/app.py | 273 | `(BadRequest, UnsupportedMediaType)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/app.py | 548 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_prompt_workspace.py | 75 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_prompt_workspace.py | 78 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_prompt_workspace.py | 92 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_prompt_workspace.py | 95 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_prompt_workspace.py | 109 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_prompt_workspace.py | 119 | `FileExistsError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_prompt_workspace.py | 129 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_prompt_workspace.py | 436 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_queue_workspace.py | 23 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_queue_workspace.py | 25 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_queue_workspace.py | 31 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_queue_workspace.py | 36 | `FileExistsError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_queue_workspace.py | 42 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_queue_workspace.py | 66 | `ValueError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| character-bibles/_review_app/art_queue_workspace.py | 111 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_queue_workspace.py | 168 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/art_queue_workspace.py | 171 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_queue_workspace.py | 176 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/art_queue_workspace.py | 184 | `ArtQueueError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/bible_store.py | 80 | `BaseException` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/bible_store.py | 83 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/bible_store.py | 94 | `yaml.YAMLError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/bible_store.py | 280 | `(ValueError, IndexError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/bible_store.py | 285 | `KeyError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/bible_store.py | 303 | `(KeyError, IndexError, ValueError, TypeError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/bible_store.py | 319 | `json.JSONDecodeError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/canon_catalog.py | 38 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/canon_catalog.py | 46 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/canon_catalog.py | 70 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/canon_catalog.py | 348 | `ValueError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/issue_workflow.py | 92 | `(OSError, ValueError)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/issue_workflow.py | 139 | `ValueError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| character-bibles/_review_app/issue_workflow.py | 179 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/issue_workflow.py | 195 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/issue_workflow.py | 197 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/issue_workflow.py | 257 | `Exception` | likely-swallowed | Broad handler with no raise, logging, or fallback. |
| character-bibles/_review_app/issue_workflow.py | 266 | `ValueError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/page_panel_workspace.py | 47 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/page_panel_workspace.py | 49 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/page_panel_workspace.py | 60 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/page_panel_workspace.py | 62 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/page_panel_workspace.py | 70 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/page_panel_workspace.py | 86 | `FileExistsError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/page_panel_workspace.py | 91 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/page_panel_workspace.py | 93 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/page_panel_workspace.py | 136 | `ValueError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| character-bibles/_review_app/page_panel_workspace.py | 288 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/project_direction.py | 33 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/project_direction.py | 41 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/release_workspace.py | 18 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/release_workspace.py | 20 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/release_workspace.py | 27 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/release_workspace.py | 29 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/release_workspace.py | 35 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/release_workspace.py | 44 | `FileExistsError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/release_workspace.py | 48 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/release_workspace.py | 50 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/release_workspace.py | 71 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/release_workspace.py | 84 | `(OSError, EOFError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/release_workspace.py | 93 | `visual_qa_workspace.VisualQAError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/release_workspace.py | 156 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/release_workspace.py | 159 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/release_workspace.py | 221 | `BaseException` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/story_context.py | 28 | `BaseException` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/story_context.py | 31 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/story_context.py | 220 | `(TypeError, ValueError)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/story_workspace.py | 39 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/story_workspace.py | 49 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/story_workspace.py | 51 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/story_workspace.py | 154 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/story_workspace.py | 181 | `ValueError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| character-bibles/_review_app/story_workspace.py | 309 | `(KeyError, StoryWorkspaceError)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_review_app/tests/test_bible_store.py | 327 | `Exception` | likely-swallowed | Broad handler with no raise, logging, or fallback. |
| character-bibles/_review_app/visual_qa_workspace.py | 20 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/visual_qa_workspace.py | 22 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 29 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/visual_qa_workspace.py | 31 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 37 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/visual_qa_workspace.py | 45 | `FileExistsError` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/visual_qa_workspace.py | 49 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 51 | `OSError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 67 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| character-bibles/_review_app/visual_qa_workspace.py | 151 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| character-bibles/_review_app/visual_qa_workspace.py | 154 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 158 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 163 | `FileNotFoundError` | cleanup-suppression | Empty handler on narrow exception type; likely intentional suppression. |
| character-bibles/_review_app/visual_qa_workspace.py | 170 | `VisualQAError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| character-bibles/_schema/validate-character-bibles.py | 223 | `Exception` | likely-swallowed | Broad handler with no raise, logging, or fallback. |
| docs/export_static_catalog.py | 48 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| docs/export_static_catalog.py | 61 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_catalog.py | 92 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| docs/export_static_catalog.py | 103 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_catalog.py | 148 | `Exception` | likely-swallowed | Broad handler with no raise, logging, or fallback. |
| docs/export_static_issues.py | 22 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_issues.py | 30 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_issues.py | 34 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_issues.py | 38 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_issues.py | 42 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_issues.py | 46 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/export_static_issues.py | 50 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| docs/verify_static_site.py | 62 | `ValueError` | likely-swallowed | Narrow handler with no raise, logging, or fallback. |
| scripts/backup_production.py | 115 | `(OSError, ValueError)` | re-raised | Exception is re-raised or wrapped. |
| scripts/compose_issue01_draft_panels.py | 101 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/compose_issue01_draft_panels.py | 114 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/compose_issue01_draft_panels.py | 156 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/compose_issue01_draft_panels.py | 160 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/compose_issue01_draft_panels.py | 175 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/compose_issue01_draft_panels.py | 179 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_01_neonblue_story.py | 36 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/drive_issue_01_neonblue_story.py | 40 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_01_neonblue_story.py | 43 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_01_neonblue_story.py | 372 | `SystemExit` | re-raised | Exception is re-raised or wrapped. |
| scripts/drive_issue_01_neonblue_story.py | 374 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| scripts/drive_issue_02_pipeline.py | 39 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/drive_issue_02_pipeline.py | 43 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_02_pipeline.py | 182 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_02_pipeline.py | 194 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_02_pipeline.py | 232 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/drive_issue_02_pipeline.py | 236 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_02_pipeline.py | 414 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_02_static_story.py | 31 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/drive_issue_02_static_story.py | 35 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_02_static_story.py | 38 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/drive_issue_03_scarline_scaffold.py | 31 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/drive_issue_03_scarline_scaffold.py | 35 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/live_app_test_issue.py | 62 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/live_app_test_issue.py | 66 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/live_app_test_issue.py | 69 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/live_app_test_issue.py | 387 | `Exception` | likely-swallowed | Broad handler with no raise, logging, or fallback. |
| scripts/live_app_test_issue.py | 428 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| scripts/prepare_issue01_release_assets.py | 36 | `urllib.error.HTTPError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/prepare_issue01_release_assets.py | 40 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/prepare_issue01_release_assets.py | 75 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/rc_real_issue_run.py | 80 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/rc_real_issue_run.py | 471 | `Exception` | re-raised | Exception is re-raised or wrapped. |
| scripts/tests/test_pytest_collection_integrity.py | 105 | `(OSError, subprocess.CalledProcessError)` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/workflow_engine.py | 47 | `OSError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/workflow_engine.py | 563 | `ValueError` | intentional-fallback | Narrow handler with fallback assignment/return. |
| scripts/workflow_engine.py | 629 | `Exception` | intentional-fallback | Broad handler with fallback assignment/return (review for adequacy). |
| scripts/workflow_engine.py | 752 | `(WorkflowError, bible_store.BibleStoreError, story_context.StoryContextError)` | intentional-fallback | Narrow handler with fallback assignment/return. |

## Action Required

The following handlers require human review:

- **00_SYSTEM/scripts/assemble_pages.py:42** `OSError` — Narrow handler with no raise, logging, or fallback.
- **00_SYSTEM/scripts/genesis/genesis_charart.py:418** `Exception` — Broad handler with no raise, logging, or fallback.
- **00_SYSTEM/scripts/validate_issue.py:41** `FileNotFoundError` — Narrow handler with no raise, logging, or fallback.
- **00_SYSTEM/scripts/validate_issue.py:43** `json.JSONDecodeError` — Narrow handler with no raise, logging, or fallback.
- **character-bibles/_review_app/art_queue_workspace.py:66** `ValueError` — Narrow handler with no raise, logging, or fallback.
- **character-bibles/_review_app/issue_workflow.py:139** `ValueError` — Narrow handler with no raise, logging, or fallback.
- **character-bibles/_review_app/issue_workflow.py:257** `Exception` — Broad handler with no raise, logging, or fallback.
- **character-bibles/_review_app/page_panel_workspace.py:136** `ValueError` — Narrow handler with no raise, logging, or fallback.
- **character-bibles/_review_app/story_workspace.py:181** `ValueError` — Narrow handler with no raise, logging, or fallback.
- **character-bibles/_review_app/tests/test_bible_store.py:327** `Exception` — Broad handler with no raise, logging, or fallback.
- **character-bibles/_schema/validate-character-bibles.py:223** `Exception` — Broad handler with no raise, logging, or fallback.
- **docs/export_static_catalog.py:148** `Exception` — Broad handler with no raise, logging, or fallback.
- **docs/verify_static_site.py:62** `ValueError` — Narrow handler with no raise, logging, or fallback.
- **scripts/live_app_test_issue.py:387** `Exception` — Broad handler with no raise, logging, or fallback.
