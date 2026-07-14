# Live App Test Report

- Generated: 2026-07-14T17:35:37+00:00
- Issue under test: `MZ-2026-10-01`
- Base URL: `http://127.0.0.1:8765`
- Results: **65 passed**, **0 failed**

## Chronology

- **PASS** `server_ready` — runtime-capabilities writable
- **PASS** `runtime_capabilities` — {"capability": "monkeyzoo-production-write-v1", "runtime": "monkeyzoo-local", "schema_version": "1.0", "writable": true}
- **PASS** `list_characters` — count=11
- **PASS** `create_issue` — {"files_created": ["cover_prompt.md", "final_export_checklist.md", "generation_log.md", "issue_brief.json", "issue_brief.md", "issue_outline.md", "issue_script.md", "metadata.json", "qa_report.md", "s
- **PASS** `workflow_after_create` — intake
- **PASS** `advance:intake` — canon_review
- **PASS** `after_intake` — canon_review
- **PASS** `workflow_approve:canon_review` — 
- **PASS** `advance:canon_review` — outline
- **PASS** `outline_prompt` — outline-20260714T173521Z-83ce4c
- **PASS** `outline_import` — 
- **PASS** `outline_approve` — 
- **PASS** `outline_promote_replace_false` — status=409 err=issue_outline.md already exists; explicit replacement confirmation is required (stub overwrite behavior)
- **PASS** `outline_promote_replace_true` — 
- **PASS** `advance:outline` — script
- **PASS** `script_prompt` — 
- **PASS** `script_import` — 
- **PASS** `script_approve` — 
- **PASS** `script_promote_replace_false` — blocked as expected: issue_script.md already exists; explicit replacement confirmation is required
- **PASS** `script_promote` — 
- **PASS** `workflow_approve:script` — 
- **PASS** `advance:script` — page_plan
- **PASS** `layout_create` — 
- **PASS** `layout_approve` — 
- **PASS** `layout_promote` — 
- **PASS** `advance:page_plan` — art_prompts
- **PASS** `art_prompt_pack_create` — 
- **PASS** `art_prompt_pack_approve` — 
- **PASS** `art_prompt_pack_promote` — 
- **PASS** `advance:art_prompts` — art_production
- **PASS** `art_queue_build` — items=2 err=None
- **PASS** `art_prompt_export:MZ-2026-10-01_P01_PANEL01` — 
- **PASS** `art_import:MZ-2026-10-01_P01_PANEL01` — 
- **PASS** `art_select:MZ-2026-10-01_P01_PANEL01` — 
- **PASS** `art_prompt_export:MZ-2026-10-01_P02_PANEL01` — 
- **PASS** `art_import:MZ-2026-10-01_P02_PANEL01` — 
- **PASS** `art_select:MZ-2026-10-01_P02_PANEL01` — 
- **PASS** `pre_qa_deliverables` — cover/pdf/zip/metadata written
- **PASS** `workflow_approve:art_production` — 
- **PASS** `advance:art_production` — qa
- **PASS** `qa_create` — qa-20260714T173527Z-637bde
- **PASS** `qa_blockers` — []
- **PASS** `qa_finalize_pass` — 
- **PASS** `qa_promote` — 
- **PASS** `workflow_approve:qa` — 
- **PASS** `advance:qa` — release
- **PASS** `release_readiness` — []
- **PASS** `release_approve` — 
- **PASS** `release_promote_manifest` — 
- **PASS** `release_publish_archive` — 05_RELEASE_ARCHIVE/2026/Issue_01
- **PASS** `workflow_approve:release` — 
- **PASS** `advance:release` — published
- **PASS** `final_stage_published` — published
- **PASS** `publication_ready` — True
- **PASS** `ui_create_issue_enabled` — enabled=True
- **PASS** `ui_nav:dashboard` — clicked
- **PASS** `ui_nav:issues` — clicked
- **PASS** `ui_nav:storyBuilder` — clicked
- **PASS** `ui_nav:layout` — clicked
- **PASS** `ui_nav:artQueue` — clicked
- **PASS** `ui_nav:qa` — clicked
- **PASS** `ui_nav:release` — clicked
- **PASS** `ui_art_prompt_pack_control` — present
- **PASS** `ui_release_publish_control` — present
- **PASS** `ui_console_severe` — []

## Interpretation notes

- HTTP steps exercise the same Flask routes the Studio UI calls.
- `outline_promote_replace_false` / script equivalent document whether create-issue stubs block first promote without `replace=true`.
- UI steps verify navigation and control presence under a writable local runtime.

## Follow-up fixes from this run

See `docs/SHIP_READINESS_ASSESSMENT.md`.

1. **Studio promote** now sends `replace:true` when stub/canonical targets already exist (story/layout/pack/QA).
2. **Archive path** now uses `05_RELEASE_ARCHIVE/YYYY/<issue-folder>` to prevent month/edition collisions; legacy `YYYY/Issue_NN` still validates.

Hosting plan for online work use: `docs/HOSTING_PLAN.md`.

