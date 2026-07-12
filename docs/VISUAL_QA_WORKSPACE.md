# Visual QA Workspace

The QA workspace inventories every planned panel against `generated_art/selected_panels`, validates PNG readability, dimensions, duplicate bytes, panel mapping, character presence, dialogue/caption requirements, continuity notes, cover evidence, metadata, and the final export checklist.

Reviews freeze a hash of the plan, metadata, cover inputs/images, checklist, and selected panel bytes. Evidence changes stale a review. The owner explicitly finalizes Pass, Hold, or Fail; Pass is unavailable while objective blockers remain. Finalized reviews are immutable and promotion is concurrency-locked, atomic, provenance-recorded, and overwrite-protected.

Promoted reports use the canonical `VERDICT:` format consumed by the stateful QA workflow gate. Hold and Fail therefore continue to block Release; promotion itself never advances the workflow. Static QA snapshots are read-only.
