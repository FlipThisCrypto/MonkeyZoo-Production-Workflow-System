# NFT Fusion — The Real Tech Behind FusionZoo
**Writers' room reference.** Facts sourced from monkeyzoo.net/what-is-nft-fusion/
(written by Tim Youngman, Founder & CEO of MonkeyZoo, dated March 1st, 2025).
Every claim below is from that page. The jokes are ours; the facts aren't.

**How to use this file:** when a script touches FusionZoo tech, pull the fact
from here so the satire stays true. The comedy only works because the tech is
real — we never dunk on the technology, we dunk on how monkeys *behave* around it.

---

## 1. What NFT Fusion actually is

NFT Fusion is MonkeyZoo's technology for **combining, updating, and upgrading
NFTs in a trustless, decentralized way** while keeping on-chain provenance and
the non-fungible nature of every source NFT. Built on the Chia® blockchain.

The official mental model, verbatim: **"Think of NFTs being stored inside
other NFTs."**

> Comic translation: monkeys inside monkeys. A matryoshka with a wallet.
> Nothing is destroyed, nothing is forgotten, everything is *in there
> somewhere* — which is also how Moodz would describe his feelings.

It's implemented as **CHIP-0021** (Chia Improvement Proposal 21, "the NFT
Fusion Puzzle"), written in **Chialisp®**, Chia's native smart contract
language. Spec: github.com/Chia-Network/chips (chip-0021) · code:
github.com/trgarrett/fusion-clsp

## 2. The four things fusion can do

| Operation | Official meaning | In-world flavor |
|---|---|---|
| **Fuse** | Combine multiple NFTs into new, more complex assets | Two monkeys enter, one monkey (containing two monkeys) leaves |
| **Update** | Modify existing NFTs to reflect changes or improvements | The haircut is on-chain now. No takebacks. Well—one takeback (see §5) |
| **Divide** | Split a single NFT into multiple components | The amicable breakup protocol |
| **Upgrade** | Enhance NFTs with new features or capabilities | "Wellness," as the billboard calls it |

These are "practical, on-chain actions that can be performed securely and
verifiably" — not vaporware. That matters: FusionZoo's *tech* always works in
our stories. It's the *marketing* and the *appetites* that cause plot.

## 3. The coinset model (why Chia is weird and great)

Chia doesn't use accounts like Ethereum; it uses a **coinset model**, an
evolution of Bitcoin's UTXO system. Every transaction **spends coins
(immutable objects) and creates new ones**. Benefits, per the page:

- **Parallel processing** — many transactions at once (vs EVM's sequential line)
- **Robust smart contracts** — immutable coins are solid ground to build on
- Better privacy, more secure smart contracts

> Comic translation: in Zoo City, nothing is ever edited — the old you is
> spent and a new you is minted. The universe keeps receipts. This is
> canonically why the ledger (ours AND theirs) is append-only.

## 4. The singleton — the beating heart (and our best monster)

The fusion system relies on a **singleton puzzle — a unique coin that cannot
be duplicated** — which:
- maintains the authorized state of all locked and unlocked NFTs,
- validates ownership through **cryptographic announcements**,
- enforces all fusion/de-fusion rules through its Chialisp code,
- tracks **launcher IDs**, **lineage proofs** (coin ancestry), and
  pay-to-singleton relationships.

It manages exactly **three states: Empty, A Locked, and B Locked.**
Fusion is the transition A Locked → B Locked; de-fusion is B Locked → A Locked.
Every transition is verified against DID ownership proofs, puzzle-defined
transitions, inter-puzzle announcements, and lineage proofs.

> Comic translation: there is one immortal referee coin and it has exactly
> three moods. It cannot be bribed, duplicated, or emotionally manipulated,
> which makes it the most stable character in the entire franchise.
> Story rule derived from this: a fusion state is either A, B, or Empty —
> anything *between* states is a horror story (see: The Pending, MZ-2026-08-06).

## 5. Reversibility — the undo button is real

"One of the most powerful features of NFT Fusion is the ability to **defuse**"
— and **only the owner of the asset can reverse the fusion.** De-fusion runs
through Chia **offer files** (atomic swaps):

1. User creates an offer file via wallet (offering A for B, or B for A)
2. The fusion singleton validates the offer, creates announcements
3. P2 singleton puzzles verify those announcements
4. The offer puzzle executes the atomic exchange
5. The singleton records the state change

**"All components must succeed or the entire transaction fails."** The atomic
swap flow *prevents partial de-fusion*. Official de-fusion scorecard:

| Feature | Value |
|---|---|
| Asset recovery | **Full component recovery** |
| Transaction cost | **$0.0001** (as of February 2025) |
| Transaction finality | **1 block** |
| Metadata preservation | Fully retained |
| Royalty enforcement | Puzzle-native |

> Comic translation: the undo button costs one ten-thousandth of a dollar and
> works in one block. The Emo Faction's entire creed is a real feature with a
> real price tag, and the price tag is a rounding error. "Fusion can be
> reversed. But not everything resets." (Ed.4) — the tech refunds your assets,
> not your memories. THAT gap is where every MonkeyZoo story lives.
> Also canon-critical: partial fusion is IMPOSSIBLE in the modern system.
> All-or-nothing is enforced by math. Anything half-done must predate the
> safeguards or bypass them — which is how we get ghosts.

## 6. Nesting — monkeys all the way down

Official gaming example of multi-layer asset nesting (FusionZoo):

```
Layer 0: Base Character (NFT A)
 └─ Layer 1: Armor (NFT B)
    └─ Layer 2: Hat (NFT C)
       └─ Layer 3: Chest plate (NFT D)
          └─ Layer 4: Weapon (NFT E)
             └─ Layer 5: Enchantment (NFT F)
```

- Composition depth: **recursive, theoretically infinite** ("as a fused NFT
  can then be fused inside of another NFT the upgradability… becomes infinite")
- Each layer keeps **independent ownership proofs**
- **Partial updates possible without full recomposition**
- Parent NFTs maintain Merkle proofs of child assets
- Royalty streams split using Chia Offers

> Comic translation: a monkey can wear a hat that owns its own paperwork.
> The hat can be repossessed without undressing the monkey. Infinite nesting
> = infinite "one more upgrade" = the Stayed's origin story is literally a
> supported feature used irresponsibly.

## 7. The security stack (why nobody hacks the zoo)

Per the page, CHIP-0021 addresses security via:
- **Ownership Proof** — cryptographic signatures from ALL input NFTs
- **Atomic Swaps** — all-or-nothing P2P completion
- **Immutable Contracts** — puzzle code immutable after deployment
- **DID Verification** — mandates authorized minting
- **BLS Signature Verification** — 256-bit security (vs ECDSA's 128-bit on EVM chains)
- **Reorg Resistance** — 32-block finality threshold
- **Formal Verification** — the Chialisp fusion logic is formally verified

And the chain underneath: **50,000+ full nodes** (one of the most
decentralized blockchains), **Proof of Space and Time** consensus
(energy-efficient), transactions costing **fractions of a cent**, trustless
P2P trading via offer files, **no oracles needed** — validation is pure
on-chain logic, unlike EVM dynamic NFTs that lean on external oracles
(which can be manipulated).

> Comic translation: the vault is fine. The vault is FORMALLY VERIFIED fine.
> Every heist story in MonkeyZoo must therefore target the only unverified
> component in the system: the monkey.

## 8. Metadata & identity

- Fusion extends **CHIP-0015** off-chain metadata (schema.org standard) so
  display services can show historical relationships between fused NFTs and
  their components. (This is why OUR issue metadata.json is CHIP-0015.)
- Chia's **NFT1** standard: updatable URIs, usage licenses, on-chain royalties.
- Creators can embed a **DID** for proven provenance with no centralized service.
- Official authenticity check: **"Always check for the MonkeyZoo DID to know
  it's authentic!"** → `did:chia:16ydm8lppl2k7ewdj6j4063frmzk55sehy97pm92etatpmhnzl7lslxvzg8`

> Comic translation: in Zoo City, everyone's papers are self-proving. Forging
> a monkey is computationally embarrassing. Impostor plots must be social
> engineering, never chain fraud.

## 9. The future (V2) — canon runway

MonkeyZoo is "conceptually working on a **V2**" featuring:
- **DataLayer® integration** for metadata and layer validation
- **Pick-and-replace fusion/de-fusion** — swap one layer "without having to
  completely defuse the puzzle every time a minor change is made"
- Future standards on the roadmap: CHIP-35
- Scaling concepts: "secure the bag" transaction batching, Layer 2 solutions

> Comic translation: coming soon to FusionZoo — changing your hat without
> legally dissolving your entire self. The Stayed would have LOVED that.
> Keep V2 as a background billboard gag until it's real.

## 10. Fact → story mapping (quick reference for Stage 2/3/4)

| Real fact | Established world beat |
|---|---|
| Nothing destroyed; stored inside | "They say nothing is destroyed. Everything is stored safely inside." (Ed.4) |
| De-fusion = full clean recovery | The Annex creed; Ed.2 climax de-fusion |
| Only the owner can reverse | Consent theme: change on YOUR terms (Ed.4/5) |
| Atomic all-or-nothing | The Pending (pre-atomic prototype victims) are impossible under modern rules — that's the point |
| Singleton: Empty / A Locked / B Locked | Chamber state screens; "between states" = forbidden zone |
| The chain records without judgment | "FusionZoo logs the run and powers down without judgment." (Ed.3) |
| Infinite nesting / one more upgrade | The Stayed chanting MORE (Issue 05) |
| $0.0001 undo | Joke seed: the exit was always affordable; courage is the expensive part |

## Fair-use notes
- "Chia is a trademark of Chia Network, Inc. in the United States and worldwide."
  ChiaLisp and DataLayer likewise. MonkeyZoo builds ON Chia and is not
  affiliated with Chia Network Inc. Keep the ® on first use in published text.
- Never present in-world FusionZoo marketing (the satire) as real MonkeyZoo
  claims. The real tech works; the fictional corporation is the villain-ish one.
