# Contributing to the MonkeyZoo Production Workflow System

Thanks for your interest! This repo is a **monthly comic production pipeline** —
idea in → finished, canon-safe, QA'd issue out — plus the local **Banana Lab
Studio** app for running it. Read `README.md` and
`00_SYSTEM/monkeyzoo_master_bible.md` first for orientation.

## Development setup

Python 3.10+ (CI runs 3.12). From the repo root:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt      # runtime + tooling + test deps
```

`requirements-dev.txt` is the single source of truth for dependencies, shared by CI
and this guide.

## Before you open a PR — run the gates locally

CI (`.github/workflows/validate.yml`) runs exactly these; run them first:

```bash
ruff check .        # static-analysis gate (config in ruff.toml: pyflakes F + syntax E9)
pytest              # full suite (excludes backup/archive trees via pytest.ini)
```

Both must be green. If you add or change behaviour, add or update tests alongside it —
the suite is the project's safety net and grows with every change.

## Project layout (where things live)

| Path | What |
|---|---|
| `00_SYSTEM/` | The source of truth: master bible, continuity ledger, automation rules, and the pipeline scripts in `00_SYSTEM/scripts/`. |
| `character-bibles/_review_app/` | The Banana Lab Studio (Flask app) — the writable local production UI. |
| `03_APPROVED_CANON/` | Human-approved canon assets. **Writes here are human-only** (see below). |
| `02_MONTHLY_ISSUES/` | Per-issue production folders. |
| `docs/` | Read-only GitHub Pages catalog + its static exporters. |
| `.claude/skills/` | The staged pipeline skills (mz-new-issue, mz-art-run, mz-package, mz-char-refs). |

Run the studio locally (loopback only):

```powershell
.\Start-BananaLab.ps1            # http://127.0.0.1:8765  (or -Port / $env:PORT)
```

Health check: `GET /api/health` returns `{"status":"ok", ...}` (503 if the data root
is unreachable).

## Non-negotiables (please don't break these)

These come from `00_SYSTEM/monkeyzoo_master_bible.md` and `CLAUDE.md`:

- **Canon approval is human-only.** Nothing generated is canon until it passes QA
  (Gate A), and anything entering `03_APPROVED_CANON/` must be approved by a human —
  never automate a write into that tree.
- **Locked specs.** Character personalities and published events are locked; visual
  specs are locked at `character_bible` v1.1+. Redesigns need an explicit redesign
  issue.
- **Character identity in art = hair + card colour** (see the character bible template).
- **Byte-exact values** (sha256, IPFS CIDs, the MonkeyZoo DID, seeds) are read from
  disk at write time, never transcribed from memory (`automation_rules.md` §6).
- **The continuity ledger is append-only** — corrections are new `[ERR-...]` entries,
  never edits to existing ones. Append a ledger entry before Final QA passes.

## Commit & PR conventions

- Keep each commit focused; write a clear message describing the change and its
  verification. Stage-gate commits in this repo use `MZ-YYYY-MM-##: <stage> done`;
  canon changes go in their own `canon:` commits; releases are tagged `issue-##`.
- Open PRs against `main`. CI must be green (ruff + pytest).
- Heavy generated art is gitignored (reproducible from prompt packs + seeds); only
  QA-selected art and web layouts are tracked. Don't commit large regenerable binaries.

## Reporting issues

Include what you did, what you expected, what happened, and (for pipeline problems)
the issue folder and stage. For the app, the server logs the real cause of any 5xx
(the client response is intentionally sanitized) — include that server-side log.
