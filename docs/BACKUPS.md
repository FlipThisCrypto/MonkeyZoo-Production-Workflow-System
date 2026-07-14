# Production backups

Git tracks scripts, schemas, selected panels, and text/JSON issue artifacts. It does **not** replace offline backups for:

- untracked raw/upscaled/edited art
- gitignored PDF/CBZ/ZIP exports
- `05_RELEASE_ARCHIVE` publication packages
- owner-managed assets under `03_APPROVED_CANON/approved_expressions/`
- local workspace state (`.story-workspace`, `.art-workspace`, `.qa-workspace`, `.release-workspace`, `.art-prompt-workspace`)

## One-command backup

```powershell
.\Backup-BananaLab.ps1
```

Optional:

```powershell
.\Backup-BananaLab.ps1 -Dest D:\Backups\MonkeyZoo
.\Backup-BananaLab.ps1 -DryRun
python scripts/backup_production.py --dest D:\Backups\MonkeyZoo
```

Default destination: `06_BACKUPS/monkeyzoo-backup-<UTC timestamp>/` (gitignored).

## What is copied

| Path | Why |
|---|---|
| `02_MONTHLY_ISSUES` | Working packages, selected art, workspace state |
| `03_APPROVED_CANON` | Approved character/location references |
| `05_RELEASE_ARCHIVE` | Published package evidence |
| `character-bibles` | Character Bibles + Studio app |
| `01_IDEAS_INBOX` | Intake ideas |
| `story-bibles` | Season plans |
| `04_REJECTED_OUTPUTS` | Rejection history for diagnosis |

Each backup includes:

- `BACKUP_MANIFEST.json` — per-file size + SHA-256
- `BACKUP_README.md` — restore notes

## Recommended cadence

- After every successful release approval / archive publication
- Before major canon refactors or bulk art deletes
- Weekly while actively producing an issue

## Restore outline

1. Copy trees from the backup into a MonkeyZoo workspace root.
2. Confirm Python deps (`.\Start-BananaLab.ps1` or manual venv).
3. Run `python -m pytest character-bibles/_review_app/tests -q`.
4. Open Studio and confirm the issue workflow stage and blockers.

## Security note

Backups can contain unpublished art and local paths. Store them offline or on encrypted media; do not commit them to the public repository.
