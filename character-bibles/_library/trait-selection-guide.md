# Character Trait Selection Guide

This library is a suggestion resource, not a random assignment table.

Use `trait-library.yaml` or `trait-library.json` when a character needs a small, story-useful addition. Do not fill every category for every character. A strong MonkeyZoo character can stay sparse.

## Selection Rules

Only propose a trait when it:

- Fits the character's visual design.
- Fits owner-approved canon and documented evidence.
- Creates useful contrast with the rest of the cast.
- Supports future stories, not only one gag.
- Does not duplicate another character too closely.
- Does not overload the character's current development level.

Never recommend `canon` from this library. Valid suggestion statuses are:

- `experimental`: test once with owner review.
- `optional`: available when useful, not defining.
- `reserved`: hold for later development or continuity.

## Recommended Workflow

1. Open the character's Bible and review current canon, established traits, visuals, and continuity warnings.
2. Check the cast for overlap in speech, role, visual identity, relationship function, and running elements.
3. Choose at most one or two library suggestions for a review pass.
4. Add source notes explaining why the suggestion fits.
5. Keep the trait experimental, optional, or reserved until the owner approves it.
6. After comic use, record whether the trait helped the story before promoting or retiring it.

## Development Level Guidance

Level 1 characters usually need visual clarity before deep personality. Prefer:

- Signature pose.
- Physical tick.
- Specific talent.
- One relationship clue, if evidence exists.

Level 2 characters can support a little more contrast. Consider:

- A weakness that creates growth.
- A relationship dynamic.
- A restrained catchphrase or speech pattern.
- A personal rule that can be tested.

Level 3+ characters can carry continuity. Consider:

- Personal mission.
- Recurring mystery.
- Unusual luck pattern.
- Long-running relationship tension.

## Recommendation Tool

Run:

```powershell
python character-bibles/_library/trait_library_tools.py recommend MZ-CHAR-CLEVER
```

The tool returns five suggestions with fit rationale, possible cast overlap, risks, and a suggested status. It never returns `canon`.
