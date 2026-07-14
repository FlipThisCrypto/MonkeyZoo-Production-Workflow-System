# Art reference priorities (locations & props)

Use these when generating ComfyUI/Z-Image stills for approved canon folders.  
Save selected results as:

```text
03_APPROVED_CANON/approved_locations/<slug>/primary-reference.png
03_APPROVED_CANON/approved_props/<slug>/primary-reference.png
```

Style lock: MonkeyZoo house style (chibi monkeys optional for empty plates — prefer characterless environment plates where noted).

## Priority A — season setpieces

| Rank | ID | Folder slug | Plate type | Notes |
|---:|---|---|---|---|
| 1 | `MZ-LOC-FESTIVAL-GROUNDS` | `festival-grounds` | Characterless night festival | Neon, food stands, wet pavement |
| 2 | `MZ-LOC-OLD-RELAY-JUNCTION` | `old-relay-junction` | Characterless tech node | Ancient FusionZoo infrastructure |
| 3 | `MZ-LOC-HAUNTED-ATTRACTION` | `haunted-attraction` | Exterior attraction | Halloween facade over old systems |
| 4 | `MZ-LOC-CENTRAL-ECHO-RELAY` | `central-echo-relay` | Interior relay chamber | Finale; incomplete emblem ok |
| 5 | `MZ-LOC-COMMUNITY-MEAL-HALL` | `community-meal-hall` | Interior hall | Warm communal table space |
| 6 | `MZ-LOC-WINTER-EMERGENCY-SHELTER` | `winter-emergency-shelter` | Interior shelter | Holiday lights + storm dark |

## Priority B — recurring props

| Rank | ID | Folder slug | Notes |
|---:|---|---|---|
| 1 | `MZ-PROP-ECHO-SYMBOL` | `echo-symbol` | Six incomplete segments; B/W readable |
| 2 | `MZ-PROP-CYAN-RELAY-MARKER` | `cyan-relay-marker` | Small frequency tag |
| 3 | `MZ-PROP-TWO-PATH-DISPLAY` | `two-path-display` | Dual future UI |
| 4 | `MZ-PROP-HEATING-SEQUENCE-PLATE` | `heating-sequence-plate` | Dormant phrase panel |
| 5 | `MZ-PROP-MISDIRECT-EXIT-SIGN` | `misdirect-exit-sign` | False choice signage |

## Prompt sketch (environment plate)

```text
MonkeyZoo house style: dark cartoon sci-fi cyberpunk, thick black outlines,
flat color fills, soft cel shading, wet neon reflections, EMPTY BACKGROUND
PLATE, no characters, no speech balloons, no logos.
Scene: <location season role from bible.md>
```

Negative: photoreal, text watermarks, speech balloons, extra limbs, horror gore.
