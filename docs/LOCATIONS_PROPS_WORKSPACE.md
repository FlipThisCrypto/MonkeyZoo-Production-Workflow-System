# Locations and Props workspaces

Read-only foundation browsers for approved canon inventories.

## Source of truth

| Kind | Inventory | Index | Folders |
|---|---|---|---|
| Locations | `03_APPROVED_CANON/approved_locations/locations-inventory.json` | `LOCATION_INDEX.md` | `approved_locations/<slug>/bible.md` |
| Props | `03_APPROVED_CANON/approved_props/props-inventory.json` | `PROP_INDEX.md` | `approved_props/<slug>/bible.md` |

Season mapping: `story-bibles/seasons/2026-emo-monkeys-the-signal-between-us/location-and-prop-tracker.md`

## Studio

- **Locations** and **Props** nav items are **Foundation** (browse + bible read).
- No mutations yet — editing remains file-based with owner approval for world merges.

## API (local)

| Method | Path |
|---|---|
| GET | `/api/locations` |
| GET | `/api/locations/<location_id>` |
| GET | `/api/props` |
| GET | `/api/props/<prop_id>` |
| GET | `/api/canon-catalog/summary` |

## GitHub Pages

`docs/export_static_catalog.py` writes `docs/static/canon-catalog.json` during `sync_docs.ps1`. Static mode serves read-only list/detail snapshots.

## Art next step

File selected stills as `primary-reference.png` in the matching folder. Priority targets are listed in `docs/ART_REFERENCE_PRIORITIES.md`.
