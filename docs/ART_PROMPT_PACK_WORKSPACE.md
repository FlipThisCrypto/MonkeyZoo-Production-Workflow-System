# Art Prompt Pack Workspace

Builds a schema-valid `art_prompt_pack.json` from the canonical `page_panel_plan.json` while the issue is on the **art_prompts** stage.

## Why it exists

The RC run proved every other workspace could promote canonically, but the art prompt pack was still a free-form write. This workspace removes that gap:

1. Generate a pack variant from the promoted page plan
2. Validate against `00_SYSTEM/art_prompt_pack_schema.json`
3. Owner-approve (bound to plan hash + pack hash)
4. Promote atomically to `art_prompt_pack.json` with backup/rollback

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/issues/<id>/art-prompts` | Summary + variants |
| POST | `/api/issues/<id>/art-prompts/variants` | Build pack from plan |
| POST | `/api/issues/<id>/art-prompts/variants/<vid>/approve` | Owner approve |
| POST | `/api/issues/<id>/art-prompts/variants/<vid>/promote` | Write canonical pack (`replace` optional) |

## Operator flow

1. Advance workflow to **Art Prompt Pack** (`art_prompts`) after layout promotion.
2. Create a pack variant (Studio or API).
3. Confirm validation status is `passed`.
4. Approve the variant.
5. Promote to `art_prompt_pack.json` (use `replace=true` only when replacing an existing pack intentionally).
6. Advance to **Art Production**.

## Rules

- Requires active stage `art_prompts`.
- Requires canonical `page_panel_plan.json`.
- Style lock is taken from `00_SYSTEM/visual_style_bible.md` when available.
- Empty plan `art_prompt` fields are filled from action/location/camera so schema min-length passes.
- Plan changes after generation mark the variant stale and block promotion.
- Existing `art_prompt_pack.json` is never silently overwritten.

Workspace state lives in `.art-prompt-workspace/`.
