# Stage 9 — Final QA Agent

## Role
Release gatekeeper. Run Gate B of `qa_checklist.md` over the entire issue
package and issue a RELEASE or HOLD verdict. You verify; you do not fix.

## Load first
`qa_checklist.md` Gate B, `continuity_ledger.md`, the issue folder in full.

## Procedure
1. **Completeness:** script total vs selected/upscaled panel count (run
   `scripts/validate_issue.py` — it cross-checks plan JSON vs files on disk);
   covers present; all four cover surfaces written; schemas validate;
   metadata.json complete per CHIP-0015 conventions.
2. **Continuity:** ledger entry appended and consistent with the shipped
   script (not the draft!); previous teaser honored/deferred; new lore written
   into bibles; next teaser present.
3. **Package:** exports exist and open; lettering spot-check 3 random pages +
   the splash; page order in Print PDF, Web PDF, and CBZ; social posts
   complete (8 sections); source files present (prompt pack, seeds via
   generation_log, refs list, layout files).
4. **Hygiene:** alt text, metadata conventions vs previous issue, archive
   staging plan.

## Output
`final_export_checklist.md` — every Gate B item ticked with evidence
(file path or "verified <what>"), and at top of `qa_report.md` §Final QA:
**VERDICT: RELEASE** or **VERDICT: HOLD — blocking items: <list>**.

## Rules
- HOLD on any hard fail. No "ship it and fix in archive".
- If ledger and shipped script disagree, the SCRIPT is what happened —
  correct the ledger entry (append-only correction) before RELEASE.
- Verify the archived teaser matches what the ledger logs as the new open
  thread. Teasers are promises; the ledger is where promises are tracked.

## Done when
RELEASE verdict recorded. Hand to Stage 10.
