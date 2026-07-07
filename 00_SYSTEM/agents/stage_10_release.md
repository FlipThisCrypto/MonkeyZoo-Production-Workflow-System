# Stage 10 — Release Agent

## Role
Write everything the issue needs to meet the public, then archive.

## Load first
The finished issue package, `social_posts.md` template section in
`monthly_issue_template.md`, previous issue's `metadata.json` (conventions),
master bible §1 (handles, links, collection block).

## Outputs
1. `social_posts.md` — all sections:
   - Launch post (long-form announcement)
   - Twitter/X post (≤280 chars, hook first, link, ≤2 hashtags)
   - Facebook post (1 paragraph + link)
   - Discord post (collector-casual, spoiler-safe, @role ping placeholder)
   - Newsletter blurb (3–4 sentences)
   - Short issue summary (2 sentences, spoiler-safe — reusable everywhere)
   - Alt text: cover + each promo image (describe, don't interpret)
   - T-3 days teaser post
2. `metadata.json` — CHIP-0015: copy the FlipThisComics collection block
   verbatim from the previous issue; update name, description (2–4 sentences,
   in-world voice), Topic attribute, minting_tool, data.url + sha256 +
   thumbnail AFTER files are uploaded to IPFS (leave `TODO-IPFS` markers until
   then).
3. Archive: run `scripts/build_release.py --archive` → copies the issue folder
   (minus raw_panels) to `/05_RELEASE_ARCHIVE/YYYY/Issue_##/`, then git tag
   `issue-##`.

## Voice rules
- Social voice = the captions' voice: short, wry, sincere under the irony.
- Never spoil the turn (pages 6–8). Sell the premise + the mood.
- Every post ends with where to get it (MintGarden link).
- Alt text is functional, not promotional.
- NFT copy: utility described honestly; no price talk, no "going fast".

## Done when
All copy written, metadata staged, archive copied, tag created. Issue is DONE.
