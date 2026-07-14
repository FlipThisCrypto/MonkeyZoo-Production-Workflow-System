# Local ship — current production mode

**Status:** Shipped for **local single-owner use** (Phase 0).  
**Not shipped:** Public or unauthenticated hosted writable backend.

Writable Studio binds to **loopback only** (`127.0.0.1:8765`). GitHub Pages remains a **public read-only** demo of the UI; it cannot mutate production data.

## What “shipped locally” means

| Surface | Audience | Capability |
|---|---|---|
| Your PC + `Start-BananaLab.ps1` | You (owner) | Full write: issues → publish archive |
| GitHub Pages | Anyone with the repo Pages URL | Read-only static preview |
| Hosted multi-user app | — | **Not enabled** (see `HOSTING_PLAN.md`) |

If no one else has been given a private link to your machine, **no one can write to your issue data**. That is intentional for Phase 0.

## Start (every session)

From the repo root:

```powershell
.\Start-BananaLab.ps1
```

Open: `http://127.0.0.1:8765`

Optional backup after real work:

```powershell
.\Backup-BananaLab.ps1
```

## Phase 0 remote access (work / another network)

Use one of these. **Do not** port-forward 8765 to the open internet.

### Option A — Tailscale (recommended)

1. Install Tailscale on the home machine that holds this repo.  
2. Install Tailscale on the work device (if policy allows).  
3. Ensure the home machine is running Studio (`Start-BananaLab.ps1`).  
4. From work, open `http://<tailscale-ip-of-home>:8765` **only if** you intentionally rebind the app later.

**Important:** The app currently listens on `127.0.0.1` only. For Tailscale access to the app port you must either:

- Use **Tailscale SSH / remote desktop** into the home machine and browse `http://127.0.0.1:8765` there, or  
- Later change bind to the Tailscale interface with auth (Phase 1) — not required for Phase 0.

**Phase 0 preferred path:** remote desktop (or Tailscale SSH + local browser on that machine), not a public URL.

### Option B — Windows Remote Desktop / Chrome Remote Desktop

1. Leave the home PC on with the repo available.  
2. Connect with RDP or Chrome Remote Desktop.  
3. On the home session, run `.\Start-BananaLab.ps1` and use Studio in the remote desktop browser.

### Option C — Work offline on a synced copy

- Copy or clone the repo to a work machine (private).  
- Run Studio there against that copy.  
- Merge/sync via git when home again.  
- Keep art/backups in mind (`Backup-BananaLab.ps1`); git ignores large exports/archives.

## Baseline proven at this ship point

- Live issue path intake → published (see `LIVE_APP_TEST_REPORT.md`)  
- Studio promote handles create-issue stubs  
- Release archives use unique folder paths  
- Operator runbook, backups, package helpers documented  

Git tip: `main` at local ship tag `v0.9.0-local-ship` (or later tags on the same line).

## Security rules for Phase 0

1. Keep writable Studio on **localhost** (or private remote desktop only).  
2. Do not open Windows Firewall for TCP 8765 to “public”.  
3. Do not use `0.0.0.0` bind without authentication.  
4. Treat GitHub Pages as demo-only.  
5. Run backups before bulk art deletes or machine moves.

## Continue improvements

Work from `main` as usual. Suggested next tracks:

1. Creative package quality (lettered PDF/CBZ on a full issue)  
2. Studio UX polish  
3. Phase 1 private host **only when** you want browser-native remote without RDP  

## Rollback

Local ship is just the current `main` tip + docs. No cloud deploy to roll back. Revert commits or check out an older tag if needed.
