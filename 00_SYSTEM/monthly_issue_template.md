# Monthly Issue Template
Copy this checklist into each new issue folder's workflow. File templates below
are the canonical formats — `scripts/new_issue.py` scaffolds them automatically.

## Issue Folder Contents (all required before Final QA)

```
/02_MONTHLY_ISSUES/YYYY-MM_Issue_##/
  issue_brief.md              ← Stage 1–2 output
  issue_outline.md            ← Stage 3 output
  issue_script.md             ← Stage 4 output
  page_panel_plan.json        ← Stage 4 output (machine-readable)
  art_prompt_pack.json        ← Stage 5 output
  cover_prompt.md             ← Stage 5 output
  social_posts.md             ← Stage 10 output
  metadata.json               ← Stage 10 output (CHIP-0015)
  qa_report.md                ← Stages 7 & 9 output
  final_export_checklist.md   ← Stage 9 output
  /references/{character_refs,background_refs,pose_refs,previous_issue_refs}
  /generated_art/{raw_panels,selected_panels,upscaled,edited}
  /layout/{print_layout,web_layout,social_crops}
  /exports/  → MonkeyZoo_Issue_##_Print.pdf · _Web.pdf · _CBZ.zip · cover.png · promo_images/
```

---

## ISSUE BRIEF TEMPLATE (issue_brief.md)

```
Issue ID: MZ-YYYY-MM-##
Issue Month: YYYY-MM
Issue Number: ##
Working Title:
Core Idea:
Theme:
Satire Target:
Emotional Core:
Main Character:
Supporting Characters:
Conflict:
Antagonist or Problem:
Setting:
Running Joke:
Ending:
Next Issue Teaser:
Required Visuals:
Forbidden Changes:
Continuity Risks:
Release Assets Needed:
```

## ISSUE OUTLINE TEMPLATE (issue_outline.md)

```
# MZ-YYYY-MM-## — <Title>
Logline: <one sentence>
Theme: <one line>
Page count: <n> story pages + 4 covers
Emotional arc: <start state → turn → end state, per main character>
Comedy arc: <the joke engine and how it escalates>
Conflict: <want vs obstacle>
Ending: <the image/line we land on>
Teaser: <rear-cover hook for next month>

## Page map
Page 1 — <purpose> — <beat>
Page 2 — ...
```

## ISSUE SCRIPT TEMPLATE (issue_script.md) — per panel

```
### Page N — <page purpose>
**Panel N.M (<size: Half/Third/Full/Splash>)**
- Location:
- Characters:
- Camera: <angle + shot size>
- Action:
- Emotion:
- Dialogue: <SPEAKER: "line"> (or —)
- Caption: <narration> (or —)
- SFX: (or —)
- Visual notes:
- Continuity notes:
```

## PAGE/PANEL PLAN — see issue_brief_schema.json siblings
`page_panel_plan.json` must validate against `page_panel_plan_schema.json`.
`art_prompt_pack.json` must validate against `art_prompt_pack_schema.json`.

## COVER PROMPT TEMPLATE (cover_prompt.md)

```
# Main cover
Concept: <one sentence, the issue in a single image>
Composition: <staging>
Prompt: <assembled per prompt_rules.md>
Negative: <base + appends>
Identity stack: <LoRA/IPAdapter/refs>
Card mode or scene mode: <which>

# Variant cover
Concept / Composition / Prompt / Negative / Identity stack
Variant rule: same issue moment, different lens (parody, minimal, faction POV)
```

## SOCIAL POSTS TEMPLATE (social_posts.md)

```
## Launch post (long)     — announcement, 2–3 paragraphs
## Twitter/X (≤280)       — hook + link + 2 hashtags max
## Facebook               — 1 short paragraph + link
## Discord                — @collectors ping, casual voice, spoiler-safe
## Newsletter blurb       — 3–4 sentences
## Issue summary (spoiler-safe, 2 sentences)
## Alt text               — cover alt + 1 promo panel alt
## Teaser post (T-3 days) — cropped panel + one line, no spoilers
```

## METADATA TEMPLATE (metadata.json)
CHIP-0015, FlipThisComics collection block copied verbatim from previous issue;
update: name, description, Topic attribute, data.url, sha256, thumbnail.

## QA REPORT + FINAL EXPORT CHECKLIST
Use `qa_checklist.md` sections A (Art QA) and B (Final QA) — copy results in.
