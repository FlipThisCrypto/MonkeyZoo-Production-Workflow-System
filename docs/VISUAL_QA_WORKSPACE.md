# Visual QA Workspace

The QA workspace inventories every planned panel against `generated_art/selected_panels`, validates PNG readability, dimensions, duplicate bytes, panel mapping, character presence, dialogue/caption requirements, continuity notes, cover evidence, metadata, and the final export checklist.

Reviews freeze a hash of the plan, metadata, cover inputs/images, checklist, and selected panel bytes. Evidence changes stale a review. The owner explicitly finalizes Pass, Hold, or Fail; Pass is unavailable while objective blockers remain. Missing or invalid selected panels, duplicate art, dimension mismatches, missing identity metadata, unmapped art, missing issue metadata, a missing cover prompt, a missing final export checklist, and blank per-panel continuity notes are blockers. A missing cover image is an explicit QA advisory because Release owns the blocking cover-deliverable requirement. Hold and Fail remain available with blockers.

Finalized reviews are immutable. Promotion renders and validates the exact report before mutation, runs under an exclusive lock, writes the report and provenance atomically, verifies their review ID, evidence hash, and verdict agreement, and rolls back the report, provenance, and replacement backup on any failure. Explicit replacement confirmation remains required.

Promoted reports use the canonical `VERDICT:` format consumed by the stateful QA workflow gate. Hold and Fail therefore continue to block Release; promotion itself never advances the workflow. Static QA snapshots are read-only.
