# Project Direction — MonkeyZoo / Banana Lab

**Machine-readable source of truth:** `00_SYSTEM/project_direction.json`  
**In Studio:** open **Project Map** (separate from the home Dashboard).

This page is the human-readable companion. When priorities change, update the JSON first, then refresh this doc if needed.

---

## North star

Ship monthly **MonkeyZoo** comic issues with consistent characters, locations, props, and continuity — using a local, **evidence-gated** production pipeline that never pretends work is done without real artifacts.

| Name | Role |
|---|---|
| **The Banana Lab** | Production Studio (local app) |
| **MonkeyZoo** | Comic series / project |
| **Fiend Studios** | Owner |

## Current mode (Phase 0)

| Item | Value |
|---|---|
| Status | **Shipped for single-owner local use** |
| Start | `.\Start-BananaLab.ps1` → `http://127.0.0.1:8765` |
| Remote | RDP / Tailscale into home PC (not public write URL) |
| Pages | GitHub Pages = **read-only** demo |
| Baseline tag | `v0.9.0-local-ship` |

**Do not** port-forward writable Studio to the open internet. Phase 1 hosting requires real auth (`docs/HOSTING_PLAN.md`).

---

## How to use the task map

1. Open Studio → **Project Map**.  
2. Filter by status: **done / active / next / later / blocked**.  
3. Expand a task for full instructions and doc paths.  
4. Follow **Recommended order** for what to do next.

Statuses:

| Status | Meaning |
|---|---|
| `done` | Shipped / usable today |
| `active` | Current ongoing habit or focus |
| `next` | Recommended soon |
| `later` | Deferred intentionally |
| `blocked` | Waiting on decision/dependency |

---

## Production pipeline (every issue)

1. Intake → 2. Canon Review → 3. Outline → 4. Script → 5. Page & Panel Plan → 6. Art Prompt Pack → 7. Art Production → 8. Visual QA → 9. Release → 10. Published  

Full commands and gates: `docs/OPERATOR_RUNBOOK.md`.

---

## Recommended next work (high level)

1. **Creative proof issue** — drive Issue 01 (NeonBlue / festival) through lettered PDF/CBZ quality.  
2. **Owner merge** — promote proven season locations/props into `world_bible` when ready.  
3. **Studio UX polish** — small improvements from real production friction.  
4. **Character expression/pose expansion** — LoRA prep from local expression sheets.  
5. **Issues 02–06** — continue Signal season after Issue 01 path is proven.  
6. **Phase 1 private host** — only when browser remote without RDP is required.

---

## Phases at a glance

| Phase | Goal | Status |
|---|---|---|
| 0 Local ship | Owner produces on one PC | **Done / active mode** |
| 1 Private host | HTTPS + auth for work browser | Later |
| 2 Small team | Roles + audit | Later |
| 3 SaaS | Multi-tenant product | Out of scope for v1 |

---

## Key doc index

| Topic | Doc |
|---|---|
| Local ship | `docs/LOCAL_SHIP.md` |
| Operator path | `docs/OPERATOR_RUNBOOK.md` |
| Hosting | `docs/HOSTING_PLAN.md` |
| Season | `story-bibles/seasons/2026-emo-monkeys-the-signal-between-us/SEASON-BIBLE.md` |
| Locations/props | `docs/LOCATIONS_PROPS_WORKSPACE.md` |
| Art priorities | `docs/ART_REFERENCE_PRIORITIES.md` |
| Backups | `docs/BACKUPS.md` |
| Package exports | `docs/PACKAGE_EXPORTS.md` |

---

## Editing the map

```text
00_SYSTEM/project_direction.json   ← edit tasks/statuses/instructions here
docs/PROJECT_DIRECTION.md          ← keep this summary aligned
Studio Project Map                 ← loads JSON via GET /api/project-direction
docs/static/project-direction.json ← refreshed by docs export/sync for Pages
```
