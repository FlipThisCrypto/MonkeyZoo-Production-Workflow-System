# Art Prompt Pack and Queue Workspace

Studio **Art Queue** view covers both the Art Prompt Pack stage and panel queue production.

## Art Prompt Pack (stage `art_prompts`)

1. Select an issue in the Art Queue workspace.
2. **Build pack from page plan** creates a schema-valid variant from `page_panel_plan.json`.
3. **Approve pack**, then **Promote pack** to `art_prompt_pack.json`.
4. Advance the workflow to Art Production.

API and rules: `docs/ART_PROMPT_PACK_WORKSPACE.md`.

## Panel queue (stages `art_prompts` / `art_production`)

The Art Queue derives one item per canonical `page_panel_plan.json` panel. Prompt export is available at `art_prompts` and `art_production`; image import and preferred selection require `art_production`.

Prompt packages are manual-provider records bound to the plan hash. They include canonical character IDs, individual primary references, visual constraints, location, props, action, and continuity. Missing individual references block prompt export; group artwork is never substituted.

Manual PNG, JPEG, and WebP imports are decoded and validated, limited to 25 MB, stored as immutable attempts, and labeled `manual_import`. Rejected and archived attempts remain in history. Owner selection records `project_owner` and atomically writes a normalized PNG to `generated_art/selected_panels/<panel_id>.png`. No image is fabricated and no stage advances automatically. Static snapshots are read-only.

Studio controls start **disabled** until a trusted local runtime capability is proven.
