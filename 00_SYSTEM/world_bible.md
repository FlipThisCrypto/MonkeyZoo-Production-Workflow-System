# MonkeyZoo World Bible
**Version:** 1.0 · **Last updated:** 2026-07-02

How the MonkeyZoo world works. New locations, tech, or rules invented in an
issue MUST be added here (and logged in `continuity_ledger.md`) before release.

---

## 1. The World in One Paragraph

Zoo City is a dark cartoon sci-fi/cyberpunk city populated by plush-stitched
monkeys. It rains a lot. Neon is the main light source. Corporations sell
self-improvement the way street vendors sell fruit. The biggest of them is
**FusionZoo**, whose technology can combine, upgrade, and (allegedly always)
reverse what you are. The comedy is loud; the loneliness underneath is real.

## 2. Canon Locations

### Zoo City streets
- Wet pavement, neon reflections, black-and-grey buildings, lamp posts,
  picket-fence courtyards in older blocks (see Emo ref #973 backdrop).
- Weather default: night rain or post-rain sheen. Daytime exists but is rare
  and should feel slightly wrong.

### FusionZoo Public Facility (Ed.4)
- Tall glass walls; glowing signage: **"FUSIONZOO – UPGRADE YOURSELF."**
- Sterile lobby: glowing floor lines, floating explainer screens, seating area.
- Long corridor of numbered fusion-chamber doors, soft hum.
- **Fusion chamber:** circular room, central platform, energy lines pulsing
  under the floor. Control screen states: "FUSION READY."

### The Fusion Lab / The Annex (Ed.2)
- A forgotten corner of the original Fusion Lab. Cluttered, older tech,
  archival — where the Emo Faction recorded the De-Fusion Tapes.
- The Annex is where the *truth* about the tech lives; the Public Facility is
  where the *marketing* lives. Keep this contrast.

### The Slope (Ed.3)
- Winter run outside the city. One slope, same rules for everyone: no resets,
  no shortcuts. FusionZoo terminals log runs and power down without judgment.

### Chamber 0 (Issue 05 — resolves the Ed.4 teaser)
- The cracked chamber, located: a disused Annex-wing chamber leaking **green
  light**, orbited by the Stayed. Door deliberately left open (squad's choice).
- Green glow remains RESERVED for this chamber and zombie contexts.

### The Old Quarter (Issue 06)
- Zoo City's pre-neon first draft: rounder low-rise architecture, dead cable
  bundles sagging like vines, faded analog signage. The city never tore it
  down; it just stopped looking. Only light: Relay 1's mast, blinking red in
  a stuttering, WRONG rhythm.

### FusionZoo Relay 1 (Issue 06)
- Abandoned relay station in the Old Quarter. Control room: wall of dead
  consoles, ONE screen alive with a slow amber heartbeat waveform. Behind it,
  the prototype chamber hall — bulky riveted first-generation fusion chambers
  with porthole windows, amber emergency floor strips.
- **Signal palette: amber/red** (never green — the Pending are not zombies).
- Evidence of the Keeper: fresh power splices, new cable ties, a folded tarp
  bed. Identity: OPEN THREAD.
- After Issue 06: console reads "SIGNAL ACKNOWLEDGED — RETURN PROTOCOL
  INITIATED"; Patch's crumpled Issue-05 recall notice lies beside the screen.

### Season locations (proposed — Signal Between Us, Aug 2026–Jan 2027)

Full IDs, bibles, and art folders live in `03_APPROVED_CANON/approved_locations/`.  
Tracker: `story-bibles/seasons/2026-emo-monkeys-the-signal-between-us/location-and-prop-tracker.md`.

| Month | Headline setpiece locations (IDs) |
|---|---|
| August | Festival grounds, main stage, service corridor, control node |
| September | Storm/routine nodes, transit hub, school PA zone, **old relay junction** |
| October | Haunted attraction, false-choice gallery, old access path |
| November | Community meal hall, auto-harmony seating grid |
| December | Winter emergency shelter, heating infrastructure node |
| January | New Year civic prep district, **central Echo relay** |

These remain **proposed story canon** until owner approval and a continuity-ledger entry.

## 3. FusionZoo Technology (world logic — LOCKED)

Fusion is the in-world mirror of Chia NFT mechanics. Keep the mapping intact
but never lecture; the story must work for readers who don't know the tech.
Full real-tech reference (CHIP-0021, singleton states, atomicity, de-fusion
costs): `nft_fusion_reference.md` — scripts citing tech MUST pull from it.

| World rule | Real-world mirror |
|---|---|
| Fusion combines traits/skills/identities of monkeys into something new | Combining/nesting NFTs (FusionZoo tech on Chia) |
| Nothing is destroyed; everything is stored inside | On-chain provenance, singletons |
| De-fusion cleanly restores every asset to its original state | Reversible unwrapping (Ed.2 climax) |
| "You can always go back" — technically true, emotionally not | The undo button exists; regret still costs |
| Fusion begins by *syncing* — you feel everything at once | State sync before commit |
| The system logs and powers down without judgment | The chain doesn't care; it just records |
| Fusion is optional. Until it isn't. | FOMO / social pressure as soft coercion |

**Hard tech rules:**
1. Fusion requires standing on a chamber platform; it cannot happen ambiently.
2. A subject can abort during sync (Moodz proved it, Ed.4). After commit,
   only a proper de-fusion reverses it.
3. De-fusion is always *technically* clean. What it can't reset is memory and
   feeling ("Fusion can be reversed. But not everything resets.").
4. The system never lies with data; the *marketing around it* lies constantly.
5. New tech capabilities require a continuity ledger entry + this file updated.

## 4. Factions & Groups

- **Emo Faction (the leads):** skeptics of permanence; trust the undo button;
  archive truth in the Annex.
- **Zombie Faction — the Stayed (Issue 05, canon):** monkeys who never
  stopped fusing; shamble in orbit around Chamber 0 chanting "MORE." Not
  hostile; hungry for upgrades, not monkeys. Tragic-funny, never horror.
  Named member: **Patch** (bitten ear, bone stump; NeonBlue's old friend) —
  crossed the threshold after Issue 05 and now travels WITH the squad.
- **The Pending (Issue 06, canon):** survivors of pre-atomicity prototype
  fusion experiments (~13 years ago; DAY 4,749 counter), stuck mid-state.
  NOT zombies: no brains, no green, no decay. **Canon look (adopted from
  production): blank-white uncolored monkeys with clean outlines.** They
  speak normally, refuse interference ("Don't. Touch. The state."), and want
  company, not fixing. Attention visibly stabilizes them. Modern fusion's
  atomicity makes new Pending impossible (see nft_fusion_reference.md §5).
- **The Keeper (Issue 06, unseen):** someone maintains Relay 1's power —
  vigil, not abandonment. Identity: OPEN THREAD.
- **Super, Clever, Cheeky, Lil Devil:** archetype communities in Zoo City
  (designs validated by The Fusion Squad PDF — see character bible table).
  A red-masked Super watcher has shadowed the squad since Issue 05.

## 5. Tone & World-Logic Guardrails

- Physics are cartoon-elastic, stakes are emotionally real. No gore, no death
  on-page; zombies are tragic-funny, not horror.
- Corporations are absurd but never cartoonishly evil-mustached — the menace
  is bureaucratic cheerfulness.
- Nobody has money problems solved by magic; the city runs on hustle.
- Speech: monkeys talk like tired internet-native adults, PG-13 max.
- Narration captions are the series' voice: short, wry, second-person-adjacent
  ("They say you can always go back.").

## 6. Recurring Signage / Props (approved set)

- "FUSIONZOO – UPGRADE YOURSELF" sign · "FUSION READY" screen ·
  floating explainer screens · numbered chamber doors · energy floor lines ·
  MonkeyZoo script watermark · Fiend Studios cover stamp.
- New recurring props must be added to `03_APPROVED_CANON/approved_props/`.

### Season props (proposed — Signal Between Us)

See `03_APPROVED_CANON/approved_props/PROP_INDEX.md` and the season
`location-and-prop-tracker.md`. Headline recurring mystery props:

- **Echo Symbol (six segments)** — incomplete until January; hideable in scenery  
- **Cyan relay marker** — August/September frequency thread  
- **Six-tone interference motif** — audio/visual from September onward  
- **Old wall marking / residue** — October witness evidence  
- **Auto-harmony seating UI** — November forced-unity system  
- **Heating sequence plate** — December activation phrase  
- **Two-path display + central relay console** — January finale
