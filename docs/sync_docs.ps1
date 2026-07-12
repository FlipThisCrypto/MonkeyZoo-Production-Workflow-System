# MonkeyZoo Studio Static Pages Sync Script
# Run this script to export primary static frontend files to docs/ and apply GitHub Pages adjustments.

$StaticDir = "character-bibles/_review_app/static"
$DocsDir = "docs"

# 1. Clean and recreate directories
New-Item -ItemType Directory -Force -Path "$DocsDir/static" | Out-Null

# 2. Copy Stylesheet and inject pages overrides
Copy-Item -Path "$StaticDir/styles.css" -Destination "$DocsDir/static/styles.css" -Force
$BannerStyle = @"

.demo-preview-banner {
  background: #f59e0b; /* Amber 500 */
  color: #0f172a; /* Slate 900 */
  font-weight: 700;
  font-size: 13px;
  text-align: center;
  padding: 8px 16px;
  letter-spacing: 0.02em;
  z-index: 99;
  flex-shrink: 0;
}
"@
Add-Content -Path "$DocsDir/static/styles.css" -Value $BannerStyle

# 3. Copy HTML and convert asset links + inject banner
$HtmlContent = Get-Content -Path "$StaticDir/index.html" -Raw
$HtmlContent = $HtmlContent -replace '/static/styles.css', './static/styles.css'
$HtmlContent = $HtmlContent -replace '/static/app.js', './static/app.js'

$BannerDiv = @"
    <div class="studio-main-panel">
      <!-- Demo Preview Banner -->
      <div class="demo-preview-banner" role="alert">
        ⚡ GitHub Pages Demo Preview — Connect the local MonkeyZoo Studio backend for full production functionality.
      </div>
"@
$HtmlContent = $HtmlContent -replace '    <div class="studio-main-panel">', $BannerDiv
Set-Content -Path "$DocsDir/index.html" -Value $HtmlContent -NoNewline

# 4. Copy JS and replace API fetch + media path hooks
$JsContent = Get-Content -Path "$StaticDir/app.js" -Raw

# Replace the api function
$ApiTarget = 'async function api\(path, options = \{\}\) \{[\s\S]*?return data;\s*\}'
$ApiMock = @'
// Intercept API calls for static GitHub Pages preview
async function api(path, options = {}) {
  console.log("Pages Demo Mode Intercept:", path, options);
  
  // Clean path by stripping query params
  const cleanPath = path.split("?")[0];
  
  // Mock data mapping
  if (cleanPath === "/api/characters") {
    return [
      {
        "character_id": "MZ-CHAR-CLEVER",
        "display_name": "Clever",
        "series_name": "Clever Monkey",
        "development_level": 1,
        "canon_traits": 6,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "MZ-2026-07-05",
        "primary_image": "./media/MZ-CHAR-CLEVER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-SUPER",
        "display_name": "Super",
        "series_name": "Super Monkey",
        "development_level": 1,
        "canon_traits": 5,
        "experimental_traits": 0,
        "unresolved_fields": 1,
        "last_comic_appearance": "MZ-2026-07-05",
        "primary_image": "./media/MZ-CHAR-SUPER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-LILDEVIL",
        "display_name": "Lil Devil",
        "series_name": "Lil Devil Monkey",
        "development_level": 1,
        "canon_traits": 4,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "MZ-2026-06-12",
        "primary_image": "./media/MZ-CHAR-LILDEVIL/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-PATCH",
        "display_name": "Patch",
        "series_name": "Patch Monkey",
        "development_level": 1,
        "canon_traits": 2,
        "experimental_traits": 0,
        "unresolved_fields": 3,
        "last_comic_appearance": "MZ-2026-07-05",
        "primary_image": "./media/MZ-CHAR-PATCH/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-ZOMBIE",
        "display_name": "Zombie",
        "series_name": "Zombie Monkey",
        "development_level": 1,
        "canon_traits": 3,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "MZ-2026-05-30",
        "primary_image": "./media/MZ-CHAR-ZOMBIE/references/primary/primary-reference.png",
        "continuity_warnings": []
      }
    ];
  }
  
  if (cleanPath.startsWith("/api/characters/")) {
    const cid = cleanPath.split("/")[3];
    return getMockCharacterDetail(cid);
  }
  
  if (cleanPath === "/api/story/adventure-styles") {
    return [
      "Low-stakes slice of life",
      "High-stakes action adventure",
      "Character-driven mystery",
      "Comedic misadventure",
      "Philosophical dialogue"
    ];
  }
  
  if (cleanPath === "/api/story/preview") {
    return getMockStoryPreview(JSON.parse(options.body));
  }
  
  if (cleanPath === "/api/story/save") {
    alert("Demo Mode Preview: Saving packets requires a running local MonkeyZoo Studio backend.");
    return { ok: false, error: "Local backend required", written_files: [] };
  }
  
  if (cleanPath === "/api/story/generate-sample") {
    alert("Demo Mode Preview: Generation workflow scripts require a running local MonkeyZoo Studio backend.");
    return { ok: false, error: "Local backend required", written_files: [] };
  }
  
  if (cleanPath.endsWith("/undo")) {
    alert("Demo Mode Preview: Undo changes requires a running local MonkeyZoo Studio backend.");
    return { ok: true, undone: false };
  }
  
  if (cleanPath.endsWith("/trait") || cleanPath.endsWith("/field")) {
    alert("Demo Mode Preview: Modifying traits or fields is disabled in this hosted preview. Connect your local studio backend to edit character YAML files.");
    return { ok: true };
  }
  
  if (cleanPath === "/api/compare") {
    const ids = JSON.parse(options.body).character_ids || [];
    return {
      characters: ids.map(id => ({
        summary: { display_name: id.replace("MZ-CHAR-", ""), series_name: id, canon_traits: 5, experimental_traits: 0 }
      })),
      overlap: {
        "personality": "Low overlap (traits are distinct)",
        "speech": "Clever uses intellectual syntax; Super speaks in heroic tones.",
        "visual_identity": "Glasses visual rule is locked to Clever."
      }
    };
  }
  
  return { error: "Unknown endpoint in demo mode" };
}

function getMockCharacterDetail(cid) {
  const charactersMap = {
    "MZ-CHAR-CLEVER": {
      "summary": {
        "character_id": "MZ-CHAR-CLEVER",
        "display_name": "Clever",
        "series_name": "Clever Monkey",
        "personal_name": "unresolved",
        "naming_status": "unresolved",
        "development_level": 1,
        "canon_traits": 6,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "MZ-2026-07-05",
        "primary_image": "./media/MZ-CHAR-CLEVER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Clever",
          "series_name": "Clever Monkey",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved"
        },
        "visual_canon": {
          "primary_reference_image": "references/primary/primary-reference.png",
          "supporting_reference_images": ["references/alternate/alternate-pose-01.png"],
          "features_that_must_never_change": ["glasses"],
          "features_that_may_vary": [],
          "prohibited_visual_additions": []
        },
        "history": [
          { "action": "promote_canon", "field_path": "visual_canon.primary_reference_image", "date": "2026-07-12", "note": "Verified initial base design" }
        ]
      },
      "traits": [
        { "path": "personality.intelligence", "name": "Logical Analytical", "value": "Solve problems using formulas and instruments.", "status": "canon", "strength": "defining", "usage_frequency": "almost always", "confidence": "high" },
        { "path": "visual.glasses", "name": "Wears Glasses", "value": "The only monkey in the cast who wears glasses.", "status": "canon", "strength": "defining", "usage_frequency": "almost always", "confidence": "high" }
      ]
    },
    "MZ-CHAR-SUPER": {
      "summary": {
        "character_id": "MZ-CHAR-SUPER",
        "display_name": "Super",
        "series_name": "Super Monkey",
        "personal_name": "unresolved",
        "naming_status": "unresolved",
        "development_level": 1,
        "canon_traits": 5,
        "experimental_traits": 0,
        "unresolved_fields": 1,
        "last_comic_appearance": "MZ-2026-07-05",
        "primary_image": "./media/MZ-CHAR-SUPER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Super",
          "series_name": "Super Monkey",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved"
        },
        "visual_canon": {
          "primary_reference_image": "references/primary/primary-reference.png",
          "supporting_reference_images": ["references/alternate/alternate-pose-01.png"],
          "features_that_must_never_change": ["cape"],
          "features_that_may_vary": [],
          "prohibited_visual_additions": ["glasses"]
        },
        "history": []
      },
      "traits": [
        { "path": "personality.temperament", "name": "Heroic Bold", "value": "Acts with confidence and steps in first.", "status": "canon", "strength": "defining", "usage_frequency": "almost always", "confidence": "high" }
      ]
    },
    "MZ-CHAR-LILDEVIL": {
      "summary": {
        "character_id": "MZ-CHAR-LILDEVIL",
        "display_name": "Lil Devil",
        "series_name": "Lil Devil Monkey",
        "personal_name": "unresolved",
        "naming_status": "unresolved",
        "development_level": 1,
        "canon_traits": 4,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "MZ-2026-06-12",
        "primary_image": "./media/MZ-CHAR-LILDEVIL/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Lil Devil",
          "series_name": "Lil Devil Monkey",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved"
        },
        "visual_canon": {
          "primary_reference_image": "references/primary/primary-reference.png",
          "supporting_reference_images": [],
          "features_that_must_never_change": [],
          "features_that_may_vary": [],
          "prohibited_visual_additions": ["glasses"]
        },
        "history": []
      },
      "traits": [
        { "path": "personality.temperament", "name": "Mischievous", "value": "Loves pranking Clever and distracting others.", "status": "canon", "strength": "defining", "usage_frequency": "often", "confidence": "high" }
      ]
    },
    "MZ-CHAR-PATCH": {
      "summary": {
        "character_id": "MZ-CHAR-PATCH",
        "display_name": "Patch",
        "series_name": "Patch Monkey",
        "personal_name": "unresolved",
        "naming_status": "unresolved",
        "development_level": 1,
        "canon_traits": 2,
        "experimental_traits": 0,
        "unresolved_fields": 3,
        "last_comic_appearance": "MZ-2026-07-05",
        "primary_image": "./media/MZ-CHAR-PATCH/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Patch",
          "series_name": "Patch Monkey",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved"
        },
        "visual_canon": {
          "primary_reference_image": "references/primary/primary-reference.png",
          "supporting_reference_images": [],
          "features_that_must_never_change": ["eye patch"],
          "features_that_may_vary": [],
          "prohibited_visual_additions": []
        },
        "history": []
      },
      "traits": [
        { "path": "personality.temperament", "name": "Quiet Observer", "value": "Intentionally sparse and calm.", "status": "established", "strength": "moderate", "usage_frequency": "sometimes", "confidence": "moderate" }
      ]
    },
    "MZ-CHAR-ZOMBIE": {
      "summary": {
        "character_id": "MZ-CHAR-ZOMBIE",
        "display_name": "Zombie",
        "series_name": "Zombie Monkey",
        "personal_name": "unresolved",
        "naming_status": "unresolved",
        "development_level": 1,
        "canon_traits": 3,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "MZ-2026-05-30",
        "primary_image": "./media/MZ-CHAR-ZOMBIE/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Zombie",
          "series_name": "Zombie Monkey",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved"
        },
        "visual_canon": {
          "primary_reference_image": "references/primary/primary-reference.png",
          "supporting_reference_images": [],
          "features_that_must_never_change": [],
          "features_that_may_vary": [],
          "prohibited_visual_additions": ["glasses"]
        },
        "history": []
      },
      "traits": [
        { "path": "personality.temperament", "name": "Sleepy / Slow", "value": "Responds slowly to calls, often sleeps in.", "status": "experimental", "strength": "moderate", "usage_frequency": "often", "confidence": "moderate" }
      ]
    }
  };
  
  return charactersMap[cid] || charactersMap["MZ-CHAR-CLEVER"];
}

function getMockStoryPreview(setup) {
  const castIds = (setup.characters || []).map(c => c.character_id);
  const selectedCastNames = castIds.map(id => id.replace("MZ-CHAR-", ""));
  
  return {
    "packet": {
      "selected_cast": castIds.map(id => {
        const detail = getMockCharacterDetail(id);
        return {
          "display_name": detail.summary.display_name,
          "series_name": detail.summary.series_name,
          "personal_name": detail.summary.personal_name,
          "naming_status": detail.summary.naming_status,
          "role": (setup.characters.find(c => c.character_id === id) || {}).role || "supporting",
          "selected_traits": detail.traits,
          "excluded_traits": [],
          "visual_requirements": {
            "glasses_status": id === "MZ-CHAR-CLEVER" ? "locked" : "prohibited"
          },
          "primary_reference_image": detail.summary.primary_image
        };
      })
    },
    "panel_plan": {
      "Page_1": { "panels": 1, "description": "Cover page: " + (setup.topic || "Observed signal") },
      "Page_2": { "panels": 4, "description": "Story page: introduction of characters in " + (setup.location || "Observatory") },
      "Page_3": { "panels": 4, "description": "Story page: development of conflict: " + (setup.conflict || "disagreement") },
      "Page_12": { "panels": 1, "description": "Back cover: " + (setup.lesson || "learning lesson") }
    },
    "story_structure": {
      "arc": "Emo Monkeys Season Arc 2026",
      "beat_progression": [
        "Beat 1: Group gathers at " + (setup.location || "Observatory"),
        "Beat 2: Discovery of topic: " + (setup.topic || "mystery"),
        "Beat 3: Conflict resolving beat: " + (setup.lesson || "mutual support")
      ]
    },
    "warnings": [],
    "prompt": `### MonkeyZoo Comic Script Generation Prompt
Active Issue: ${setup.issue_id || "MZ-2026-07-05"}
Location: ${setup.location || "Observatory"}
Cast: ${selectedCastNames.join(", ")}
Topic: ${setup.topic || "Mystery frequency"}
Lesson: ${setup.lesson || "Listening to each other"}`,
    "generated_script": `#### Page 1: Front Cover
[Composition: Single wide panel. ${selectedCastNames[0] || "Clever"} looking through a telescope at the night sky.]
Narrative Box: THE SIGNAL BETWEEN US

#### Page 2
Panel 1: Clever stands excited by the observatory console.
Clever: "I found it! An active transmission frequency!"
Panel 2: Super walks in wearing his cape.
Super: "Outstanding! Let's build the decoder antenna."`,
    "script_validation_warnings": [],
    "continuity_proposal": {
      "new_established_traits": [],
      "lessons_learned": [ setup.lesson || "listening yields clarity" ]
    },
    "save_hint": "Issues/" + (setup.issue_id || "MZ-2026-07-05")
  };
}
'@

$JsContent = [regex]::Replace($JsContent, $ApiTarget, $ApiMock)

# Replace absolute media path references with relative ones
$JsContent = $JsContent -replace '/media/', './media/'

Set-Content -Path "$DocsDir/static/app.js" -Value $JsContent -NoNewline

Write-Output "MonkeyZoo Studio Pages Sync Complete!"
