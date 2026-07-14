# Release Workspace

Evidence-backed release readiness, owner approval, hash manifests, and archive publication.

## Readiness blockers

- exact current QA `VERDICT: PASS` with matching evidence hash
- final cover under `generated_art/**/*cover*.png`
- CHIP-0015 metadata with required fields and no `TODO` placeholders
- social copy, final checklist, cover prompt
- non-empty PDF under `exports/`
- valid non-empty CBZ or ZIP package under `exports/`

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/issues/<id>/release` | Readiness + evidence + approval state |
| POST | `/api/issues/<id>/release/manifest` | Persist a hash manifest snapshot |
| POST | `/api/issues/<id>/release/approve` | Owner approve current evidence |
| POST | `/api/issues/<id>/release/promote-manifest` | Write `release_hash_manifest.json` |
| POST | `/api/issues/<id>/release/publish-archive` | Copy verified artifacts to `05_RELEASE_ARCHIVE` |

## Publication flow

1. Reach stage `release` with all release blockers cleared.
2. Approve release (evidence-bound).
3. Promote `release_hash_manifest.json`.
4. Publish archive (`publish-archive`).
5. Owner-approve the release workflow gate.
6. Advance to `published`.
7. Confirm `publication_ready` is true.

Archive path:

```text
05_RELEASE_ARCHIVE/YYYY/Issue_NN/
```

Git ignores the archive tree. Run `.\Backup-BananaLab.ps1` after publication.
