# MonkeyZoo Production Workflow System — Agent Guide

Monthly comic factory: idea in → finished issue out. Read this first, then
take orders from `00_SYSTEM/` — it is the source of truth.

## Orientation (read in this order)
1. `README.md` — how the whole factory works, folder map, pipeline table.
2. `00_SYSTEM/monkeyzoo_master_bible.md` — franchise facts, canon hierarchy,
   the ten hard rules. **Canon hierarchy: continuity_ledger > character_bible
   > world_bible > visual_style_bible > prompt_rules.**
3. `00_SYSTEM/continuity_ledger.md` — append-only. Check the last issue's
   OPEN THREADS before writing anything new.

## Skills (in `.claude/skills/`)
- **mz-new-issue** — Stages 1–5: idea → brief → outline → script → prompt pack
- **mz-art-run** — Stages 6–7: ComfyUI generation (Z-Image recipe) + Art QA
- **mz-package** — Stages 8–10: layout/lettering, exports, Final QA, release
- **mz-char-refs** — standardized character variant sets from minted canon

## Non-negotiables
- Personalities and published events are LOCKED; visual specs are LOCKED at
  character_bible v1.1+ (creator-ref-derived). No redesigns without an
  explicit redesign issue.
- Character identity in art = HAIR + card color (see character bible §template).
- Nothing generated is canon until it passes QA (Gate A) — and canon
  approval (anything entering `03_APPROVED_CANON/`) is HUMAN-ONLY.
- Every issue appends a ledger entry before Final QA passes.
- Byte-exact values (sha256, IPFS CIDs, the MonkeyZoo DID, seeds) are read
  from disk commands at write time, never transcribed from context
  (`00_SYSTEM/automation_rules.md` §6).
- Ledger is append-only: corrections are new `[ERR-...]` entries.

## Local rig facts (this machine)
- ComfyUI portable at `I:\ai\ComfyUI`, launched via `run_zluda.bat`
  (AMD RX 6800 through ZLUDA). Output: `I:\ai\nft\output\`.
- Art engine: Z-Image Turbo (see mz-art-run for the full recipe and the
  hang-recovery procedure).
- Python scripts in `00_SYSTEM/scripts/` run with system `python`; the page
  assembler needs Pillow — use `I:\ai\ComfyUI\python_embeded\python.exe`.

## Git discipline
- Commit per stage gate: `MZ-YYYY-MM-##: <stage> done`. Canon changes in
  their own `canon:` commits. Releases tagged `issue-##`.
- Heavy art is gitignored (reproducible from packs + seeds); only QA-selected
  art and web layouts are tracked.
