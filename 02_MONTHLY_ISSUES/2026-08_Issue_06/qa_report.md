# MZ-2026-08-06 QA Report

## Art QA (Gate A) — Batch 1 reviewed 2026-07-03 (44 images, Z-Image Turbo, text-only identity tier)

**Result: 11/22 panel-groups selected (3 clean + 8 with edit notes), 11 rejected → reroll queued with systematic fixes.**

| Panel | Verdict | Selected variant | Notes |
|---|---|---|---|
| P00_PLATE01 | **APPROVE** | seed60002 | Old Quarter: cable-vines, red mast, empty, on-style. Both variants passed; picked stronger mast read |
| P00_PLATE02 | **APPROVE** | seed60002 | Relay room: single amber heartbeat CRT, rusted door, hanging bulb — brief exactly |
| P00_PLATE03 | **APPROVE** | seed60004 | Prototype hall: porthole chambers + amber floor strips |
| P01_PANEL01 | REJECT ×2 | — | Walk-cycle line instead of turned-back staging; TwoTone split + Ash hood missing; envelope→balloon. Super cameo landed perfectly (keep beat in reroll) |
| P01_PANEL02 | REJECT ×2 | — | Content miss: single generic monkey instead of notice close-up + 3 faces. Characterless-prompt fix applies |
| P02_PANEL01 | REJECT ×2 | — | HARD FAIL: index finger on NeonBlue point. TwoTone panda-blotch not vertical split. Balloons |
| P02_PANEL02 | **APPROVE (edit)** | seed100001 (smoke) | Moodz wary side-eye, fringe+blue streak, studded cuffs. Edits: bubble artifact lower-right; face tan not pale (waived this issue) |
| P02_PANEL03 | REJECT ×2 | — | "MOZOZO"/"ZOO" logo hallucination; Patch de-zombified; NeonBlue rendered as blue humanoid |
| P03_PANEL01 | REJECT ×2 | — | Environment good, squad scale/count chaos, shadow-blob figures |
| P03_PANEL02 | **APPROVE (edit)** | seed60303 | Static (headphones, shake lines) + Ash face-off at amber-seam door. Edits: remove 2 balloons; Ash hood missing (waived — flag for lettering crop) |
| P03_PANEL03 | REJECT ×2 | — | Moodz fringe missing (identity); full figure instead of mitt close-up; touching console (script says hovering) |
| P04_PANEL01 | REJECT ×2 | — | SPLASH: Pending-as-white-monkeys concept STRONG but "ZOZO" text + collage framing instead of hall composition. seed60402 flagged as possible promo/variant material |
| P05_PANEL01 | REJECT ×2 | — | White Pending reads beautifully; NeonBlue rendered as blue humanoid (identity) |
| P05_PANEL02 | REJECT ×2 | — | v2 close (brown monkey in blue jacket ✓) but recoil/flicker absent, balloon cluster |
| P05_PANEL03 | REJECT ×2 | — | Patch got brain+mint skin (best Patch face yet) but console/grief staging absent; popcorn artifact |
| P06_PANEL01 | **APPROVE (edit)** | seed60601 | Keeper's nest: Static peering over console, TwoTone-ish at fresh red wiring, tarp bed. Edit: balloons out |
| P06_PANEL02 | **APPROVE (edit)** | seed60602 | THE composition: Moodz (blue-streak) facing white Pending cluster, zombie bg. Edit: balloons out |
| P07_PANEL01 | **APPROVE (edit)** | seed60701 | Mingled squad + white Pending + zombies in warm amber — "company" reads. Edit: balloon out |
| P07_PANEL02 | **APPROVE (edit)** | seed60703 | Moodz (blue streak) + Scarline (scarf + brow scar!) at threshold, door light between. Edit: red balloon out |
| P07_PANEL03 | **APPROVE (edit)** | seed60704 | Patch's mint mitts smoothing the pastel envelope beside heartbeat screen — the beat lands. Waiver: face visible (script said body-exiting); body brown not full pale-green |
| P08_PANEL01 | **APPROVE (edit)** | seed60802 | Dawn walk-out, Patch INSIDE the group (arc beat ✓). Edit: balloon out; mixed facing waived |
| P08_PANEL02 | REJECT ×2 | — | HARD FAIL: monkey present in the mandatory-empty room (style-lock-describes-a-monkey failure; characterless fix applies) |

**Systematic failure diagnosis (fixed in `run_art_batch.py` before reroll):**
1. Lettering clauses ("clear for two balloons") rendered as literal balloons — cfg 1.0 makes negatives inert. Fix: clause-filter at send time.
2. "MonkeyZoo house style:" rendered as logo text ("ZOZO", "MOZOZO"). Fix: strip brand words, keep style description.
3. Characterless panels (P01_PANEL02, P08_PANEL02) drew the style-lock's monkey. Fix: auto plate-style treatment when `character_tokens` is empty.
4. Identity misses (TwoTone split, Ash hood, NeonBlue jacket-vs-body, Patch full design) — inherent to text-only tier; approved panels from this batch now seed `03_APPROVED_CANON` for IPAdapter/LoRA next issue.

**Art-direction adoption:** the model consistently renders the Pending as
blank-white uncolored monkeys — clearer and more reproducible than the
scripted lineart-with-missing-fills. ADOPTED as the canon Pending look
(ledger + world bible to be updated at release).

## Art QA (Gate A) — Batch 2 (reroll, 22 images) reviewed 2026-07-03

**Result: all 11 rerolled panels now have selections — 22/22 panel-groups
complete.** Balloon and logo-text hallucinations: ZERO in batch 2 (runner
fixes confirmed effective).

| Panel | Verdict | Selected | Notes |
|---|---|---|---|
| P01_PANEL01 | APPROVE (edit) | seed60102 (b2) | Signature reads improved (pale-face Moodz, headphones, blue flick, scarf, notice in hand); Super-watcher cameo present. Walk-line staging waived |
| P01_PANEL02 | **APPROVE** | seed60103 (b2) | Clean skyline + wrong-rhythm mast, no characters — brief exactly |
| P02_PANEL01 | APPROVE (edit) | seed60202 (b2) | No fingers this time; TwoTone greyscale split improving; balloons gone |
| P02_PANEL03 | APPROVE (edit) | seed60204 (b2) | Olive stitched Patch walking; red horizon; logo text gone. NeonBlue-behind still humanoid-ish — crop tighter at layout |
| P03_PANEL01 | CONDITIONAL | seed60302 (b2) | Scale chaos persists (giant foreground monkey) after 2 attempts → escalated per rules: LAYOUT CROP instruction (crop right ⅔: small squad + architecture). ControlNet/depth needed for this shot type next issue |
| P03_PANEL03 | CONDITIONAL | seed60303 (b2) | Fringe still absent → LAYOUT CROP to mitt + heartbeat screen (script wanted close-up anyway; crop restores intent AND hides identity miss) |
| P04_PANEL01 | **APPROVE** | seed60401 (b2) | SPLASH: monumental white Pending figure, white queue behind, colored squad small below. Composition change from scripted orbit ADOPTED (showrunner sign-off) — caption unchanged |
| P05_PANEL01 | CONDITIONAL | seed60502 (b2) | The Pending reads perfectly; NeonBlue humanoid again (2 attempts) → LAYOUT CROP to Pending solo, dialogue tail from off-panel |
| P05_PANEL02 | APPROVE (edit) | seed60503 (b2) | NeonBlue reaching, white Pending recoiling — the consent beat lands |
| P05_PANEL03 | APPROVE (edit) | seed60504 (b2) | Patch (mint + brain + stitches) grieving at console; best TwoTone split of the run beside him; humanoid bg figure to crop/inpaint |
| P08_PANEL02 | **APPROVE** | seed60802 (b2) | Empty room, DOUBLED heartbeat waveform, envelope beside console. The final beat, exactly as scripted |

**Batch 2 summary:** 22 generated, 11 panels resolved (4 clean approvals,
4 approve-with-edits, 3 conditional with layout-crop instructions).
Recurring residual: NeonBlue renders humanoid in two-shots with the Pending
(white monkey pulls the palette); TwoTone's split needs reference
conditioning. Both are identity-stack limitations, not prompt bugs —
resolution path is IPAdapter/LoRA from this issue's approved panels.

**STAGE 7 DISPOSITION: COMPLETE.** 22/22 panel-groups selected
(validate_issue --art: PASS). Ready for Stage 8 (upscale → layout →
lettering) with 3 crop instructions and 8 balloon/artifact edits carried in
the notes above.

Pre-flagged for extra scrutiny (from prompt pack):
- **THE PENDING (all panels P4–P7):** issue-scoped DECLARED ART EXCEPTION —
  lineart with missing color fills + doubled outline. QA must verify (a) the
  exception applies ONLY to Pending figures, never leaks onto leads; (b) the
  Pending never acquire brains/green/decay (they are NOT zombies); (c) the
  P04 splash gets approved FIRST and becomes the look-lock reference for every
  later Pending panel.
- **NO GREEN GLOW anywhere this issue** — signal palette is amber/red. Any
  green = hard reject (green is zombie-chamber-reserved; the one zombie in
  this issue, Patch, carries no glow).
- **P01_PANEL01:** Static's ONE headphone cup lifted — sanctioned beat; both
  cups on ears or headphones removed = reject. Deep-background Super cameo
  must stay tiny and undetailed.
- **P07_PANEL03 / P08_PANEL02:** the recall notice prop must match Issue 05's
  pastel envelope (crumpled + rain-spotted variant); blank — no generated text.
- **P08_PANEL02 vs P03_PANEL03:** framing must match (panel rhyme) — generate
  P03_PANEL03 first, reuse its depth map.
- **Keeper evidence (P06_PANEL01):** NO figure, shadow, or silhouette may
  appear. Model loves adding lurkers to "hidden nest" prompts — watch for it.
- **Patch group placement:** P01 line's END → P08 group's MIDDLE. Wrong
  placement breaks the issue's visual arc — check both panels together.

## Script QA (advisory, Stage 4 self-check) — PASS
- Voice lock: Ash 2 lines ("Generous." / "They waved." — 1+2 words) ✓ ·
  Scarline exactly one sentence ✓ · Moodz max line 5 words ✓ · Patch
  fragments only ✓ · Static meter lines within cadence ✓
- One splash (P4) ✓ · Balloon counts ≤2 everywhere (P1.2 n/a — single) ✓
- Silent panels used deliberately: P1.2, P7.1, P7.3, P8.2 ✓ (franchise
  signature honored)
- Issue 05 threshold thread resolved (Patch with squad, P1.1) ✓ ·
  Super teaser explicitly deferred with cameo ✓ · Rear-cover teaser = idea's
  exact beat ✓
- Tech grounding: "the state", atomicity-era framing, DAY 4,749 all trace to
  nft_fusion_reference.md §4–5 ✓

## Final QA (Gate B)
VERDICT: PENDING — awaiting Stages 6–8 (generation, art QA, layout).
Blocking items: generated art, lettered layouts, exports, IPFS uploads.

Non-art items satisfied: script complete ✓ · plan + pack JSONs validate ✓ ·
covers written ✓ · social posts ready ✓ · ledger entry drafted ✓ · next-issue
teaser present ("IT HEARD") ✓ · new lore staged for world bible on release ✓


## Art QA (Gate A) — Batch 3 (bible v1.1 design corrections, 30 images) reviewed 2026-07-06

Context: ERR-2026-07-06 — creator reference images revealed v1.0 character
specs were wrong. Pack/plan/script patched to v1.1 descriptors (hair-based
identity); 15 character panels regenerated.

**Result: all 15 panels re-selected with v1.1 designs. Hair-based identity is
a step-change: leads are now distinguishable even at silhouette scale.**

Highlights vs the v1.0 batch:
- Static: black slicked hair + grey eye-rings render reliably (door, nest) — the
  headphones/spikes problem is gone because the design no longer contains them.
- Ash: silver-white fringe reads instantly beside Static at the Relay door.
- NeonBlue: FIXED his humanoid problem — white-and-cyan spike crown + black
  vest renders as an on-model monkey in P02/P05; the recoil beat (P05_PANEL02
  seed60503) is the best two-shot of the issue.
- Splash (60401): white Pending monumental + squad row with readable per-lead
  hair at small scale.
- P03_PANEL01 wide: every tiny figure identifiable by hair — including a red
  streak read for Scarline.

Residuals (edit-stage notes, carried to layout):
1. P07_PANEL02 Scarline: jacket/pale face correct, scarlet streak ABSENT —
   paint red streak viewer-left at edit stage (small op).
2. TwoTone's half-black/half-white hair split renders as plain dark hair in
   2-shots (P02_PANEL01, P06_PANEL01) — needs reference conditioning
   (webp #1195 via IPAdapter) or LoRA; acceptable at current draft tier.
3. P08_PANEL01 group faces camera; mast visible RECEDING BEHIND them, so the
   walking-home beat still reads — reframe accepted, noted.
4. P03_PANEL01 giant-foreground-monkey scale issue persists (3rd occurrence)
   — layout crop retained; this shot type is the #1 argument for wiring
   Z-Image Fun ControlNet next issue.

Pages, PDFs, CBZ, and social crops rebuilt from the corrected selects.
