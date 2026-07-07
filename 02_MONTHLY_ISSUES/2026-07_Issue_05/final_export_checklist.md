# MZ-2026-07-05 Final Export Checklist (Gate B evidence sheet)

Status legend: [x] done · [ ] pending · [~] drafted, needs final pass

## Completeness
- [x] Script complete (issue_script.md — 8 pages, 20 panels, 4 cover surfaces)
- [x] page_panel_plan.json written (validates: run `validate_issue.py 2026-07_Issue_05`)
- [x] art_prompt_pack.json written (22 entries: 2 plates + 20 panels)
- [ ] Every scripted panel has approved, upscaled image
- [ ] Main cover generated + approved
- [ ] Variant cover generated + approved
- [~] metadata.json (CHIP-0015 complete except TODO-IPFS url/sha256 fields)

## Continuity
- [~] continuity_ledger.md entry appended (DRAFT — flip to released at Stage 10)
- [x] Previous teaser honored (Ed.4 zombie teaser → resolved on-page)
- [ ] New lore written into world_bible §2/§4 final pass (the Stayed, Chamber 0,
      Wellness Recall, Patch — currently in ledger draft; copy on release)
- [x] No character redesigns
- [x] Next-issue teaser present (rear outside cover + P08_PANEL02)

## Package
- [ ] MonkeyZoo_Issue_05_Print.pdf
- [ ] MonkeyZoo_Issue_05_Web.pdf
- [ ] MonkeyZoo_Issue_05_CBZ.zip (`build_release.py 2026-07_Issue_05`)
- [ ] cover.png + promo_images/
- [ ] Lettering pass (no bubble covers a face; margins ≥100px safe area)
- [ ] Page order verified in all three formats
- [x] Social posts ready (social_posts.md — all 8 sections)
- [x] Source files present (prompt pack, seeds, refs lists; generation_log pending art)

## Release hygiene
- [x] Alt text written (cover, variant, splash promo)
- [x] NFT metadata conventions match Ed.3 (CHIP-0015, Sage Wallet, collection block verbatim)
- [ ] Archive staged (`build_release.py 2026-07_Issue_05 --archive` after RELEASE)

## VERDICT
HOLD — art pipeline (Stages 6–8) not yet run. Everything upstream of ComfyUI
is complete and validated; this is the expected state of the worked example.
