# Backend hosting plan (online use at work)

Goal: use Banana Lab / MonkeyZoo production workflows from a browser at work without exposing an unauthenticated write API to the public internet.

This is a **plan only**. Do not deploy a public writable Flask `app.run` as-is.

## Current security boundary [CONFIRMED]

| Surface | Mode | Auth |
|---|---|---|
| GitHub Pages (`docs/`) | Public read-only static preview | None |
| Local Flask (`127.0.0.1:8765`) | Full write: issues, art, QA, release | None (single owner trust) |

Writable endpoints mutate the filesystem under the repo (`02_MONTHLY_ISSUES`, archives, bibles). Public exposure without auth is a **critical** risk.

## Requirements for work use

1. Access from office browser over HTTPS  
2. Authentication (you only, or small team)  
3. Authorization on every mutating route  
4. CSRF protection for cookie sessions  
5. Upload limits and request size caps  
6. Production WSGI (not Flask debug server)  
7. Secrets not in git  
8. Backups of issue art + archives  
9. Optional: VPN or private network only  

## Recommended phases

### Phase 0 — Local ship (current production mode)

**This is the active ship mode.** Writable Studio is single-owner and local.

- Primary: `.\Start-BananaLab.ps1` → `http://127.0.0.1:8765`  
- Work access: remote desktop (or Tailscale) **into the home machine**, then use localhost there  
- Do **not** port-forward 8765 to the public internet  
- GitHub Pages stays read-only; no public write URL is required or published  
- Operator details: `docs/LOCAL_SHIP.md`  

**[ASSUMPTION]** No third party has remote desktop or Tailscale access to the owner machine.

### Phase 1 — Private hosted single-user (target for first online ship)

**Architecture**

```
Browser (work) --HTTPS--> Reverse proxy (Caddy/Nginx)
                              |
                              v
                     Auth gate (SSO or basic auth + app session)
                              |
                              v
                     Gunicorn/Uvicorn WSGI + Flask app
                              |
                              v
                     Persistent volume (issues, art, archives)
```

**Hosting options (pick one)**

| Option | Pros | Cons |
|---|---|---|
| **Fly.io / Railway / Render private service** | Simple container deploy | Need volume for art; cost |
| **Small VPS (Hetzner/DigitalOcean)** | Full control, cheap | You operate OS |
| **Home PC + Tailscale Funnel / reverse proxy** | Uses existing machine | Home uptime/power |

**App changes required before Phase 1**

1. Auth middleware (session cookie + login)  
2. CSRF tokens for POST/PUT  
3. Disable Flask `debug=True` in production  
4. Bind only behind proxy; trust `X-Forwarded-*` carefully  
5. Config via env: `SECRET_KEY`, `WORKSPACE_ROOT`, `MAX_UPLOAD_MB`  
6. Structured access logs without secrets  
7. Health endpoint: `GET /healthz` (no FS mutation)  
8. Rate limit create/upload endpoints  

**Do not**

- Open `0.0.0.0:8765` on a public IP without auth  
- Commit production secrets  
- Point GitHub Pages at a writable backend  

### Phase 2 — Small team

- Role-based auth (owner vs reviewer)  
- Per-issue locks already exist for some workspaces; extend consistency  
- Audit log of approvals/promotes  
- Object storage for art (S3-compatible) optional  

### Phase 3 — Productized SaaS (out of scope for v1)

- Multi-tenant isolation  
- Hosted AI providers  
- Billing / analytics  

## Minimal Phase 1 implementation sketch

**New files (future PR)**

- `character-bibles/_review_app/auth.py` — login, session, require_user  
- `character-bibles/_review_app/wsgi.py` — production entry  
- `Dockerfile` + `docker-compose.yml` (app + volume)  
- `.env.example` (never commit real secrets)  

**Env**

```text
BANANA_LAB_SECRET_KEY=...
BANANA_LAB_PASSWORD_HASH=...   # or OIDC config
BANANA_LAB_WORKSPACE=/data/monkeyzoo
BANANA_LAB_COOKIE_SECURE=1
```

**Proxy example (Caddy)**

```text
bananalab.example.com {
  reverse_proxy app:8000
}
```

**Process**

```text
gunicorn -b 0.0.0.0:8000 --workers 2 wsgi:app
```

## Data & backup when hosted

- Mount persistent volume at workspace root  
- Nightly: `python scripts/backup_production.py --dest /backups`  
- Offsite copy of `06_BACKUPS` / volume snapshots  

## Acceptance criteria for “online at work”

- [ ] HTTPS only  
- [ ] Login required for any non-static page and all APIs  
- [ ] Logout ends session  
- [ ] CSRF blocked without token  
- [ ] Upload > limit rejected  
- [ ] Create issue → publish archive works against volume  
- [ ] Restore from backup tested once  
- [ ] Security note in README: not multi-tenant  

## Decision for now

**Shipped:** Phase 0 local single-owner Studio (`docs/LOCAL_SHIP.md`, tag `v0.9.0-local-ship`).  
**Deferred:** Phase 1+ hosted writable backend until auth is implemented.  
**Work use:** remote into the home machine; no public app link.

[DEPENDENCY APPROVAL REQUIRED] if introducing OIDC libraries, Redis sessions, or object storage SDKs.
