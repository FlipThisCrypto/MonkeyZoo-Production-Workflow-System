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

`build_release.py` looks for a cover in this order:

1. `exports/cover.png`
2. `generated_art/covers/main_cover.png`
3. first non-empty `generated_art/**/*cover*.png`

## Quality bar

- `assemble_pages.py` produces **draft-tier** lettering for review, not final print lettering.
- Print-final lettering still expects Krita/CSP polish per stage 8 agent guidance.
- Release gates require non-empty PDF bytes and a ZIP/CBZ that opens, contains members, and passes `testzip()`.

## Do not

- Do not use free-form copies into `05_RELEASE_ARCHIVE` when Studio `publish-archive` can run.
- Do not change selected panels, cover, checklist, or metadata after QA PASS without a new QA review.
