# Story and Script Workspace

The Banana Lab Story Builder extends the existing story-context system with an issue-local production workspace. It reads the active stage from `.workflow-status.json`; outline operations require `outline`, script operations require `script`, and promotions never advance the workflow.

## Canon snapshots and storage

Each manual prompt or import freezes a compact canon snapshot under `.story-workspace/canon-snapshots/`. Snapshots contain repository-relative source references, SHA-256 hashes, canonical character IDs, alias resolutions, issue-brief and season-plan hashes, warnings, and excluded sources. Variants compare that frozen hash with current approved sources and display **Canon changed since generation** when stale.

Outline and script records live separately under `.story-workspace/{outlines,scripts}/{variants,approvals,promotions}`. Approved variants are immutable. Approvals bind the owner, content hash, and canon snapshot hash. Promotions are atomic, provenance-recorded, duplicate-protected, and require explicit replacement confirmation plus a backup when a canonical file already exists.

## Provider and manual workflow

The provider boundary currently exposes the always-safe `manual_prompt` provider. It exports task instructions, issue brief, frozen canon context, output contract, validation expectations, and a generation ID. Externally produced Markdown is imported with `source_type: manual_import`; the application never calls it direct model output. Future local CLI or OpenAI-compatible adapters can implement the same record contract without exposing credentials. Local settings may use `config/generation.local.json`, already excluded by the repository's `*.local.*` ignore rule.

Validation reports structural errors separately from heuristic warnings. Errors block approval. Outline checks cover identity, required sections, placeholders, and prohibited-material warnings. Script checks add panel presence and duplicate panel IDs. These checks do not claim semantic canon perfection.

Generation/import failures never create approved output or touch production files. Generation events record safe provenance without credentials or absolute paths. Recovery is to correct the input/provider and create a new variant; history is preserved.
