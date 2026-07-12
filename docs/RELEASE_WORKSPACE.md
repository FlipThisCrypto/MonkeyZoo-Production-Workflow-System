# Release Workspace

Release readiness is derived from a passing canonical QA verdict, final cover evidence, CHIP-0015 metadata without TODO placeholders, social copy, the export checklist, a PDF, and a CBZ or ZIP package. Every included file receives a SHA-256 entry.

The owner explicitly approves one evidence hash. Any release-file change stales approval and removes the ready state. Manifest creation and approval are concurrency-locked and atomic. Promotion of `release_hash_manifest.json` requires current approval and explicit replacement confirmation.

Published readiness additionally requires release-archive evidence. The workspace does not fabricate publication, create external infrastructure, or advance workflow stages. GitHub Pages exports a read-only readiness snapshot.
