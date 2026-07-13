# Release Workspace

Release readiness is derived from a passing canonical QA verdict, final cover evidence, CHIP-0015 metadata without TODO placeholders, social copy, the export checklist, a non-empty PDF, and a valid CBZ or ZIP package. ZIP-family packages must be readable, contain at least one file, and pass an integrity check; corrupt, truncated, encrypted-inaccessible, and empty packages are blockers. Every included file receives a SHA-256 entry.

The owner explicitly approves one evidence hash. Any release-file change stales approval and removes the ready state. Manifest creation and approval are concurrency-locked and atomic. Promotion of `release_hash_manifest.json` uses the same exclusive lock, requires current approval and explicit replacement confirmation, verifies the approved manifest and current evidence before replacement, and restores the prior canonical bytes if write verification fails.

Published readiness additionally requires a recognizable, non-empty PDF, CBZ, or ZIP release artifact in the release archive; unrelated files alone do not satisfy publication readiness. The workspace does not fabricate publication, create external infrastructure, or advance workflow stages. GitHub Pages exports a read-only readiness snapshot.
