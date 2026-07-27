# Package and export procedure

How lettered pages, PDFs, and CBZ packages enter the formal Banana Lab release gates.

## Tools

| Script | Role |
|---|---|
| `00_SYSTEM/scripts/assemble_pages.py` | Stage 8 draft lettering + web/print page PNGs + PDF drafts |
| `00_SYSTEM/scripts/build_release.py` | CBZ from web layout + export checklist; optional legacy `--archive` |
| `scripts/package_issue.py` | Operator wrapper around the above |
| Studio **Release → Publish archive** | Formal evidence-gated copy into `05_RELEASE_ARCHIVE` |

## Recommended path

1. Finish art selection for every planned panel (`generated_art/selected_panels/`).
2. Optional draft lettering assembly:

```powershell
python scripts/package_issue.py 2026-08_Issue_06 --assemble
```

3. Build CBZ and list export status:

```powershell
python scripts/package_issue.py 2026-08_Issue_06
```

4. Visually inspect `layout/web_layout`, PDFs, and the CBZ in a reader.
5. Complete CHIP-0015 metadata without `TODO` placeholders **before** QA if metadata participates in the QA evidence hash.
6. Run formal QA → PASS → promote.
7. Studio Release: approve → promote manifest → **Publish archive**.
8. Advance workflow to **Published**.
9. `.\Backup-BananaLab.ps1`.

## Cover discovery

Every surface resolves the cover through one shared contract,
`00_SYSTEM/scripts/issue_cover.py` -- the Studio release gate, the Studio
visual-QA evidence set, `validate_issue.py --cover`, `build_release.py`
(and therefore `package_issue.py`), and archive publishing.

1. `generated_art/covers/main_cover.png` -- **canonical**
2. `exports/cover.png` -- **DEPRECATED** compatibility fallback. Accepted so
   issues already using it are not stranded; every surface that accepts it warns
   and prints the migration command. Scheduled for removal once no issue relies
   on it -- check with `python 00_SYSTEM/scripts/issue_cover.py --audit`.

The former third step, "first non-empty `generated_art/**/*cover*.png`", is
**gone**. It let a preview render stand in for the deliverable, and because the
glob is case-insensitive on Windows and case-sensitive on POSIX it made the
release evidence hash differ between the dev rig and CI.

## Quality bar

- `assemble_pages.py` produces **draft-tier** lettering for review, not final print lettering.
- Print-final lettering still expects Krita/CSP polish per stage 8 agent guidance.
- Release gates require non-empty PDF bytes and a ZIP/CBZ that opens, contains members, and passes `testzip()`.

## Do not

- Do not use free-form copies into `05_RELEASE_ARCHIVE` when Studio `publish-archive` can run.
- Do not change selected panels, cover, checklist, or metadata after QA PASS without a new QA review.
