# Page and Panel Planning Workspace

The Layout workspace converts the canonical `issue_script.md` into reviewable, schema-validated plan variants. It is available only while the recorded workflow stage is `page_plan`.

The parser retains page purpose, panel size, canonical character IDs, location, action, dialogue, captions, sound effects, visual notes, continuity notes, and issue-local prop observations. Alias records resolve through the shared character identity index. Validation checks page and panel sequencing, duplicate IDs, unknown characters, required production fields, and the repository `page_panel_plan_schema.json`.

Variants live under `.layout-workspace/variants`. Approval is explicit, immutable, and bound to both the plan hash and canonical script hash. Script changes stale the approval. Promotion writes `page_panel_plan.json` atomically, records provenance, refuses duplicate promotion, and requires explicit replacement with a backup for an existing canonical plan. Promotion never advances the workflow.

GitHub Pages exports read-only summaries. All create, approve, and promote controls require the local backend.
