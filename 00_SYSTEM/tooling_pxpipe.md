# pxpipe — Token-Cost Proxy for Factory Claude Sessions
**Ingested:** 2026-07-04 · Source: github.com/teamchong/pxpipe (MIT) ·
npm: `pxpipe-proxy@0.8.0` (verified on registry)

## What it is

A local proxy for Claude Code that cuts input-token costs by rendering bulky
context (tool results, collapsed history, big JSON) as PNG images before
requests leave the machine. Text costs ~1 char/token; images cost fixed
tokens by pixel size — pxpipe exploits the gap (~3.1 chars per image-token on
real traffic). It only images content when the math wins (profitability gate),
keeps streaming intact, and logs every conversion with counterfactual token
counts to `~/.pxpipe/events.jsonl`.

**Verified claims (their benchmarks, FINDINGS.md 2026-07-01):**
- ~59–70% lower end-to-end billing on dense traffic; ~68% input savings
- SWE-bench Lite 10/10 with −65% tokens; gist recall 98/98 on Fable 5
- Dashboard at `http://127.0.0.1:47821/` with kill switch + live savings
- Default model allowlist is already Fable 5 (what this factory runs on)

## Why the factory cares

Factory sessions are exactly pxpipe's target profile: long runs that re-read
big JSON (`page_panel_plan.json`, `art_prompt_pack.json` are 30–60KB each),
bibles, ledgers, and QA transcripts. Stages 1–5, 7, and 9 are text-dense.
Yesterday's Stage 6–8 run burned most of its input tokens re-reading pack
JSON and QA context — the kind of spend pxpipe cuts by half or more.

## ⚠ THE RISK THAT MATTERS HERE (read before enabling)

**pxpipe is explicitly lossy on byte-exact values, and it fails silently.**
Their audit: 12-char hex strings read back 13/15 on Fable 5 (87%) — misses
are confident single-glyph confabulations ("5a7373…" → "5a7973…"), not
errors. 0/15 on Opus.

This factory's release path is FULL of byte-exact values:
- `metadata.json` **sha256** hashes (CHIP-0015 — a wrong hash = broken NFT)
- **IPFS CIDs** (Qm… strings — one glyph off = dead link)
- The MonkeyZoo **DID** (`did:chia:16ydm8…` — the authenticity anchor)
- Generation **seeds** (reproducibility contract in the prompt packs)

**Standing rule (added to automation_rules): any byte-exact value that ends
up in a released file must be read from DISK at the moment of writing, never
transcribed from conversation context.** This was already good practice; with
pxpipe active it is mandatory. Stage 9 verifies hashes by recomputing
(`Get-FileHash` / `sha256sum`), never by eyeballing.

## How to enable (per session, opt-in)

```powershell
# terminal 1 — start the proxy (dashboard: http://127.0.0.1:47821/)
npx pxpipe-proxy

# terminal 2 — launch Claude Code through it
$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:47821"
claude
```

- Kill switch: dashboard toggle, or `PXPIPE_MODELS=off`
- Default allowlist already = `claude-fable-5` — no config needed
- To make permanent: set `ANTHROPIC_BASE_URL` user env var (do this only
  after a few supervised sessions confirm savings on this machine)

## Recommended factory posture

| Session type | pxpipe? | Why |
|---|---|---|
| Stages 1–5 (brief→script→pack writing) | ON | Dense JSON/bible context, no byte-exact outputs |
| Stage 7 Art QA | ON | Already image-heavy; text context is the bulk |
| Stage 8 layout | ON | Same |
| Stage 9/10 release + metadata | ON, with the disk-read rule enforced | sha256/CID/DID must come from disk commands, never context |
| Anything touching wallet/minting | OFF | Zero tolerance for confabulated identifiers |

## Notes

- It's a request-side proxy: responses stream normally; nothing is sent
  anywhere except api.anthropic.com (code is MIT, local, auditable).
- English prose loses money in the readable zone — savings come from dense
  structured content, which is most of what this factory re-reads.
- Escape hatch for byte-exact work: `CLAUDE_CODE_SUBAGENT_MODEL` per their
  docs, or just the kill switch.
