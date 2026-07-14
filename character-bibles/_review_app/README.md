# MonkeyZoo Character Bible Review App

This is a local review interface for the Character Bible files in `character-bibles/MZ-CHAR-*/bible.yaml`.

It is intentionally separate from the comic-generation pipeline. Reviewing a trait here does not generate comics or change published canon by itself.
The Story Builder integrates approved Bibles into issue planning by creating compact character-context packets. It does not paste full Bibles into prompts.

## Start The App

Preferred (workspace root):

```powershell
.\Start-BananaLab.ps1
```

Manual:

```powershell
python character-bibles/_review_app/app.py
```

Open:

```text
http://127.0.0.1:8765
```

Operator docs: `docs/OPERATOR_RUNBOOK.md`. Workspace docs live under `docs/*_WORKSPACE.md`.

## Review A Character

1. Select a character from the browser.
2. Check the primary image, naming status, warning badges, and trait counts.
3. Open the `Traits`, `Naming`, `Visual`, `History`, or `Compare` tabs.
4. Use buttons and short fields instead of editing YAML directly.

The character browser shows canon trait count, experimental trait count, unresolved fields, last appearance, and continuity warnings.

## Approve Traits

Each trait has review buttons:

- `Canon`: promote to immutable canon.
- `Established`: approve as reliable but not immutable.
- `Experimental`: keep reviewable.
- `Optional`: available when useful, not defining.
- `Dormant`: previously used but inactive.
- `Retire`: should no longer appear.
- `Reject`: records rejection and marks the trait retired/never.
- `Edit`: change text, strength, frequency, notes, story contexts, or incompatible traits.

Every saved change writes an `approval-history.json` entry in that character folder with date, previous value, new value, approval status, and note.

## Keep A Character Sparse

Sparse is valid. Do not approve filler traits just because a field exists.

For Level 1 or unresolved characters:

- Keep unknown fields blank, `unknown`, or `reserved`.
- Prefer one visual identity marker and one role.
- Avoid adding flaws, habits, or catchphrases without evidence.
- Use `reserved` when the owner intentionally wants future room.

Patch is currently an example of an intentionally sparse character.

## Add Traits After A Comic Release

After a comic release:

1. Add the new trait in the character Bible YAML or through a future add-trait control.
2. Set status based on evidence: `experimental` for a first test, `established` after repeated reliable use, `canon` only when owner-approved.
3. Add source evidence in the trait.
4. Add or update continuity notes.
5. Use the review app to approve or defer the trait.

Do not promote a trait simply because it appeared once unless the owner marks it canon.

## Compare Characters

Use the `Compare` tab:

1. Select two or more characters.
2. Click `Compare Selected`.
3. Review overlap groups for personality, speech, story role, visual identity, relationships, and quirks.
4. If two characters overlap too much, adjust one through motivation, flaw, speech style, or story function rather than adding random quirks.

## Update Naming Later

Use the `Naming` tab to:

- Keep current series name.
- Add a personal name.
- Add a codename.
- Add nicknames.
- Mark naming unresolved.
- Mark a personal name as canon.

Do not require a personal name. Series-named characters such as Clever, Super Monkey, and Zombie may remain unresolved until owner review.

## Visual Review

Use the `Visual` tab to select primary references and inspect visual rules.

Important current rule: Clever is the only confirmed glasses-wearing monkey. Do not add glasses to other characters unless the owner approves a canon change.

## Build Story Context

Click `Story Builder` to prepare an issue before script generation.

1. Select characters and choose a role for each: `primary`, `secondary`, `supporting`, or `cameo`.
2. Set page count, panel count, topic, adventure style, tone, audience, conflict, location, lesson, required beat, forbidden content, continuity mode, canon strictness, and growth mode.
3. Click `Preview Context`.
4. Review selected traits, excluded traits, panel allocation, story structure, warnings, and the compact prompt.
5. Click `Regenerate Trait Selection` after changing roles or story setup.
6. Click `Save Packet` when the preview looks right.

Saved packets are written to the matching `MonkeyZoo_Comic_Factory/02_MONTHLY_ISSUES/<issue-id>/` folder when it already exists. Otherwise they are written to `issues/<issue-id>/`.

The saved files are:

- `character-context.json`
- `character-context.md`
- `script-generation-prompt.md`
- `post-generation-validation.md`
- `proposed-continuity-update.json`
- `proposed-continuity-update.md`

## Approve Traits For Stories

The Story Builder may include experimental traits when canon strictness is `balanced`, but every experimental trait is marked as review-required. It never changes a trait status and never makes an experimental trait canon.

Use `strict` canon mode when a script should use only `canon`, `established`, or `optional` traits.

## Keep A Character Sparse In Stories

Sparse characters can still appear. Assign them as `supporting` or `cameo`, then let the packet use visual identity plus at most one behavior. Do not fill missing personality, naming, or relationship fields just to make a larger packet.

## Add Traits After Release

After a comic release, use the saved `proposed-continuity-update.*` files as a review checklist. Add new facts, relationships, lessons, or growth notes only after owner review. A used trait remains proposed until approved through the Character Bible controls.

## Compare Before Generation

Use the regular `Compare` tab to check overlap before opening Story Builder. In the Story Builder preview, watch for duplicate story-function warnings and adjust roles or story setup so Clever, Super Monkey, Zombie, and the rest of the cast do not collapse into one repeated function.

## Update Naming Later For Stories

The Story Builder leaves personal names blank unless the Bible says `personal_name_canon`. Series names remain valid display names, so characters can be used without forcing a personal name.
