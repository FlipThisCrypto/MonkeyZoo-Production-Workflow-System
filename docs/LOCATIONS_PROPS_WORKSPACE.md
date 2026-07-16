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
| GET | `/api/expressions` |
| GET | `/api/expressions/<slug>` |
| GET | `/api/canon-catalog/summary` |
| GET | `/media/locations/<slug>/primary-reference.png` |
| GET | `/media/props/<slug>/primary-reference.png` |
| GET | `/media/expressions/<slug>/<filename>` |

Detail payloads include `primary_image_url` when a still is filed. Expression sheets are inventoried from `03_APPROVED_CANON/approved_expressions/` (owner-managed; optional on disk).

## GitHub Pages

`docs/export_static_catalog.py` writes `docs/static/canon-catalog.json` during `sync_docs.ps1`. Static mode serves read-only list/detail snapshots (image bytes remain local-only).

## Art queue

When a panel plan lists a location or props, Art Queue resolves them against approved inventories and attaches `location_ref` / `prop_refs` (with media URLs when present) next to character references.

## Art stills

File selected stills as `primary-reference.png` in the matching folder. Priority targets are listed in `docs/ART_REFERENCE_PRIORITIES.md`. **Current season baseline:** all inventory locations and props have primary stills.
