# Issue Production Dashboard

Workflow progression is stateful. Issues without a workflow record are displayed read-only at Intake with an **Inferred from repository evidence** notice. A GET never creates that record. Advance revalidates the recorded active stage, verifies any hash-bound owner approval, appends exactly one transition, and atomically changes `active_stage`. Canon review, script, art production, QA, and release are owner-approval gates. Published is terminal.

`.workflow-status.json` uses schema version `1.0`, an `active_stage`, append-only `transitions`, and per-stage `approvals`. Writes go to a flushed and `fsync`-completed sibling temporary file before `os.replace`; malformed existing state is rejected rather than reset.

The Banana Lab derives issue status from files under `02_MONTHLY_ISSUES`, repository JSON schemas, character-bible alias resolution, QA verdict text, real export files, and release-archive evidence. JavaScript does not calculate stage completion.

The production-facing stages are Intake, Canon Review, Outline, Script, Page & Panel Plan, Art Prompt Pack, Art Production, Quality Assurance, Release Package, and Published. These present established issue-folder gates; the internal run engine retains its own `concept`, `outline`, `page_plan`, `script`, `image_generation`, `lettering`, `assembly`, and `qc` identifiers.

API routes include issue listing/detail, workflow status, artifact inventory/read-only viewing, validation, and guarded advancement. Artifact paths are confined to the selected issue. Advancement revalidates the current stage, rejects skipping, records an artifact hash, and never invents owner approval.

Static GitHub Pages receives snapshots from the same backend status module. Validation and advancement remain blocked with “Local backend required.”

After a failed validation, address every returned blocker in the repository source files, run the existing validator appropriate to that stage, and refresh the dashboard. Owner-authored artifacts are never overwritten by the dashboard.
