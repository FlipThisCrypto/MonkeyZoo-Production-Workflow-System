# Ship readiness assessment (live app test)

Generated from a real run against `http://127.0.0.1:8765` using `scripts/live_app_test_issue.py`.

Evidence labels follow the Master Prompt (7-14-26) convention.

## Environment context

| Item | Evidence |
|---|---|
| Language | Python 3 (local: 3.14) |
| Framework | Flask review app (`character-bibles/_review_app/app.py`) |
| Frontend | Static HTML/JS Banana Lab Studio |
| OS | Windows |
| Test tools | urllib HTTP client + Selenium headless Chrome + pytest |
| Deployment model | Local single-owner writable runtime; GitHub Pages read-only |

## Scope

| Area | Status |
|---|---|
| Live issue `MZ-2026-10-01` | Created and driven intake → published via app APIs |
| UI navigation / controls | Selenium smoke under writable capability |
| pytest suite | Regression after fixes |
| Intentionally not claimed | Production visual lettering quality, multi-user hosting readiness |

## Findings

### Works [CONFIRMED]

- Runtime capability contract enables mutations only for exact local trusted response
- Create issue via API persists folder + stubs
- Workflow advance/approve gates enforce stage order and owner approvals
- Story outline/script import/approve/promote (with replace when stubs exist)
- Layout parse → approve → promote
- Art prompt pack build → approve → promote
- Art queue build → prompt export → multipart import → preferred select
- QA create → PASS finalize → promote report
- Release approve → manifest promote → publish archive → published
- UI: create issue enabled when writable; nav to issues/story/layout/art/qa/release; pack + publish controls present; zero console SEVERE in smoke

### Broken / ship blockers found in live run [CONFIRMED]

1. **Studio promote used `replace:false` always**  
   - **Location:** `static/app.js` story/layout/pack/QA promote paths  
   - **Problem:** `create_issue` writes stub `issue_outline.md`, `issue_script.md`, `qa_report.md`  
   - **Impact:** First operator promote fails with 409 “already exists; replacement confirmation required”  
   - **Severity:** High (blocks normal Studio path without undocumented recovery)  
   - **Fix (implemented):** promote sends `replace:true` when a canonical/stub target already exists (or always for QA promote stubs)

2. **Release archive path collision across months**  
   - **Location:** `release_workspace._archive`, `issue_workflow` published check, `build_release.py --archive`  
   - **Problem:** Path was `05_RELEASE_ARCHIVE/YYYY/Issue_NN` only  
   - **Impact:** `2026-09_Issue_01` and `2026-10_Issue_01` both publish to `2026/Issue_01` and overwrite  
   - **Severity:** High (data loss / wrong archive identity)  
   - **Evidence:** Live test published to `05_RELEASE_ARCHIVE/2026/Issue_01` for edition folder `2026-10_Issue_01`  
   - **Fix (implemented):** unique path `05_RELEASE_ARCHIVE/YYYY/<issue-folder-name>` with legacy path still accepted for read/validation

### Improvements (non-blocking, planned or partial)

| Item | Severity | Status |
|---|---|---|
| No in-app PDF lettering generator (operator tools only) | Medium | Documented in PACKAGE_EXPORTS |
| Create-issue stubs could be empty markers instead of files | Low | Mitigated by smart replace |
| Publish archive replace confirm dialog in UI | Low | API supports replace; UI defaults false for first publish |
| Hosted multi-user backend | High for “use at work” | See HOSTING_PLAN.md (not implemented this round) |

## Edge-case map (applicable)

- Stub file already present → promote requires replace (now handled in UI)
- Duplicate edition numbers in different months → archive path uniqueness (fixed)
- Capability missing → mutations stay disabled
- Concurrent release lock → 409
- Stale QA after metadata/cover change → release blocked (by design)

## Baseline

- Workflow is evidence-gated, not button-fabricated
- Local single-owner security model (no auth)
- Live API path for new issue reached `publication_ready=true`
- Full automated unit suite remains the regression baseline after each change

## Refactoring plan executed this round

| Change | Problem | Solution | Behavior | Compatibility |
|---|---|---|---|---|
| UI promote replace logic | Stub blocks | Conditional/always-safe replace | Studio first promote succeeds | API contract unchanged; still requires explicit replace server-side |
| Archive destination unique | Month collision | `year/folder.name` + legacy read | New publishes unique | Old `year/Issue_NN` still validates as published |
| Docs + live report | Evidence trail | LIVE_APP_TEST_REPORT + this assessment + HOSTING_PLAN | Operator clarity | N/A |

## Verification

- `python scripts/live_app_test_issue.py` (app running) — see LIVE_APP_TEST_REPORT.md  
- pytest after fixes  
- Re-run live test expecting archive path containing full issue folder name  

## Local ship decision

Phase 0 is accepted for production use on the owner machine (`docs/LOCAL_SHIP.md`).  
No public writable URL is deployed. Remote work uses RDP/Tailscale to the home PC.

## Rollback

- Revert commit; legacy archives remain readable via `_resolve_archive` / dual published check until next unique publish.
