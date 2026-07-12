# MonkeyZoo Studio Static Pages Sync Script
# Run this script to export primary static frontend files to docs/ and apply GitHub Pages adjustments.

$StaticDir = "character-bibles/_review_app/static"
$DocsDir = "docs"

# Ensure source files exist - fail clearly if missing
if (-not (Test-Path "$StaticDir/index.html")) { throw "Source index.html is missing at $StaticDir/index.html" }
if (-not (Test-Path "$StaticDir/styles.css")) { throw "Source styles.css is missing at $StaticDir/styles.css" }
if (-not (Test-Path "$StaticDir/app.js")) { throw "Source app.js is missing at $StaticDir/app.js" }

# 1. Clean and recreate directories (preserve docs/media which is tracked in git)
if (-not (Test-Path "$DocsDir/static")) {
    New-Item -ItemType Directory -Path "$DocsDir/static" | Out-Null
}

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

# 3. Generate issues_metadata.json from 02_MONTHLY_ISSUES
$Issues = @()
$IssueDirs = Get-ChildItem -Path "02_MONTHLY_ISSUES" -Directory -ErrorAction SilentlyContinue
if ($IssueDirs) {
    foreach ($dir in $IssueDirs) {
        $metaPath = Join-Path $dir.FullName "metadata.json"
        if (Test-Path $metaPath) {
            $meta = Get-Content -Path $metaPath -Raw | ConvertFrom-Json
            
            $title = $meta.name
            if (-not $title) { $title = $meta.title }
            
            $issueId = $meta.issue_id
            if (-not $issueId) { $issueId = $dir.Name }
            
            $stage = "10. Release"
            $completion = "100%"
            $owner = "Lead Writer"
            $qa = "Passed"
            $log = "Compiled PDF & CBZ"
            
            if ($meta.status -eq "in_production") {
                $stage = "4. Script"
                $completion = "40%"
                $owner = "Art Director"
                $qa = "Pending"
                $log = "Draft Outline"
            } elseif ($issueId -like "*06*") {
                $stage = "1. Intake"
                $completion = "10%"
                $owner = "Editor"
                $qa = "Pending"
                $log = "Concept Brief"
            }
            
            $pages = 8
            if ($meta.page_count) { $pages = $meta.page_count }
            
            $panels = 20
            if ($meta.panel_count) { $panels = $meta.panel_count }
            
            $Issues += @{
                issue_id = $issueId
                title = $title
                stage = $stage
                completion = $completion
                owner = $owner
                qa_status = $qa
                release_log = $log
                pages = $pages
                panels = $panels
                is_demo = $false
            }
        }
    }
}

# Add a demo issue explicitly labeled as demo
$Issues += @{
    issue_id = "MZ-DEMO-ISSUE-01"
    title = "Calibration Test"
    stage = "6. Art Generation"
    completion = "60%"
    owner = "AI Generator"
    qa_status = "Pending"
    release_log = "Progress demonstration only"
    pages = 10
    panels = 30
    is_demo = $true
}

$IssuesJson = $Issues | ConvertTo-Json -Depth 5
Set-Content -Path "$StaticDir/issues_metadata.json" -Value $IssuesJson -NoNewline
Copy-Item -Path "$StaticDir/issues_metadata.json" -Destination "$DocsDir/static/issues_metadata.json" -Force

# 4. Copy HTML and convert asset links + inject banner
$HtmlContent = Get-Content -Path "$StaticDir/index.html" -Raw
$HtmlContent = $HtmlContent -replace '/static/styles.css', './static/styles.css'
$HtmlContent = $HtmlContent -replace '/static/app.js', './static/app.js'

# Pages static indicator overrides (online -> offline class, change text)
$HtmlContent = $HtmlContent -replace '<span class="status-indicator" id="sidebarStatusIndicator"></span>', '<span class="status-indicator offline" id="sidebarStatusIndicator"></span>'
$HtmlContent = $HtmlContent -replace '<span class="status-text" id="sidebarStatusText">Backend status: checking</span>', '<span class="status-text" id="sidebarStatusText">Local backend required</span>'

# Status bar overrides
$HtmlContent = $HtmlContent -replace '<span id="statusBackend" class="status-value disconnected">Backend status: checking</span>', '<span id="statusBackend" class="status-value disconnected">Local backend required</span>'

$BannerDiv = @"
    <div class="studio-main-panel">
      <!-- Demo Preview Banner -->
      <div class="demo-preview-banner" role="alert">
        ⚡ GitHub Pages Demo Preview — Connect the local MonkeyZoo Studio backend for full production functionality.
      </div>
"@
$HtmlContent = $HtmlContent -replace '    <div class="studio-main-panel">', $BannerDiv
Set-Content -Path "$DocsDir/index.html" -Value $HtmlContent -NoNewline

# 5. Copy JS and replace API fetch + media path hooks
$JsContent = Get-Content -Path "$StaticDir/app.js" -Raw

# Replace the api function
$ApiTarget = 'async function api\(path, options = \{\}\) \{[\s\S]*?return data;\s*\}'
$ApiMock = @'
// Intercept API calls for static GitHub Pages preview
async function api(path, options = {}) {
  console.log("Pages Demo Mode Intercept:", path, options);
  
  const cleanPath = path.split("?")[0];
  
  // Strict write operations block: return false result and throw error
  const isWrite = cleanPath.endsWith("/trait") || 
                  cleanPath.endsWith("/field") || 
                  cleanPath.endsWith("/undo") || 
                  cleanPath === "/api/story/save" || 
                  cleanPath === "/api/story/generate-sample";
                  
  if (isWrite) {
    alert("This action is unavailable in the GitHub Pages demo. Run MonkeyZoo Studio locally to modify production data.");
    throw {
      "ok": false,
      "demo_mode": true,
      "error": "Local backend required"
    };
  }
  
  // Mock read data mapping
  if (cleanPath === "/api/characters") {
    return [
      {
        "character_id": "MZ-CHAR-CLEVER",
        "display_name": "Clever [Demo Placeholder]",
        "series_name": "Clever Monkey [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 6,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-CLEVER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-SUPER",
        "display_name": "Super [Demo Placeholder]",
        "series_name": "Super Monkey [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 5,
        "experimental_traits": 0,
        "unresolved_fields": 1,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-SUPER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-LILDEVIL",
        "display_name": "Lil Devil [Demo Placeholder]",
        "series_name": "Lil Devil Monkey [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 4,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-LILDEVIL/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-PATCH",
        "display_name": "Patch [Demo Placeholder]",
        "series_name": "Patch Monkey [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 2,
        "experimental_traits": 0,
        "unresolved_fields": 3,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-PATCH/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      {
        "character_id": "MZ-CHAR-ZOMBIE",
        "display_name": "Zombie [Demo Placeholder]",
        "series_name": "Zombie Monkey [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 3,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
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
  
  if (cleanPath === "/api/compare") {
    const ids = JSON.parse(options.body).character_ids || [];
    return {
      characters: ids.map(id => ({
        summary: { display_name: id.replace("MZ-CHAR-", "") + " [Demo Placeholder]", series_name: id, canon_traits: 5, experimental_traits: 0 }
      })),
      overlap: {
        "personality": "Low overlap (traits are distinct) [Demo Placeholder]",
        "speech": "Intellectual tone vs. heroic tone [Demo Placeholder]",
        "visual_identity": "Visual comparison placeholder [Demo Placeholder]"
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
        "display_name": "Clever [Demo Placeholder]",
        "series_name": "Clever Monkey [Demo Placeholder]",
        "personal_name": "unresolved [Demo Placeholder]",
        "naming_status": "unresolved [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 6,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-CLEVER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Clever [Demo Placeholder]",
          "series_name": "Clever Monkey [Demo Placeholder]",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved [Demo Placeholder]"
        },
        "visual_canon": {
          "primary_reference_image": "references/primary/primary-reference.png",
          "supporting_reference_images": ["references/alternate/alternate-pose-01.png"],
          "features_that_must_never_change": ["glasses"],
          "features_that_may_vary": [],
          "prohibited_visual_additions": []
        },
        "history": [
          { "action": "History unavailable [Demo Placeholder]", "date": "History unavailable [Demo Placeholder]", "note": "History unavailable [Demo Placeholder]" }
        ]
      },
      "traits": [
        { "path": "personality.intelligence", "name": "Trait data unavailable in static preview [Demo Placeholder]", "value": "Trait data unavailable in static preview [Demo Placeholder]", "status": "unknown [Demo Placeholder]", "strength": "defining", "usage_frequency": "almost always", "confidence": "high" }
      ]
    },
    "MZ-CHAR-SUPER": {
      "summary": {
        "character_id": "MZ-CHAR-SUPER",
        "display_name": "Super [Demo Placeholder]",
        "series_name": "Super Monkey [Demo Placeholder]",
        "personal_name": "unresolved [Demo Placeholder]",
        "naming_status": "unresolved [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 5,
        "experimental_traits": 0,
        "unresolved_fields": 1,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-SUPER/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Super [Demo Placeholder]",
          "series_name": "Super Monkey [Demo Placeholder]",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved [Demo Placeholder]"
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
        { "path": "personality.temperament", "name": "Trait data unavailable in static preview [Demo Placeholder]", "value": "Trait data unavailable in static preview [Demo Placeholder]", "status": "unknown [Demo Placeholder]", "strength": "defining", "usage_frequency": "almost always", "confidence": "high" }
      ]
    },
    "MZ-CHAR-LILDEVIL": {
      "summary": {
        "character_id": "MZ-CHAR-LILDEVIL",
        "display_name": "Lil Devil [Demo Placeholder]",
        "series_name": "Lil Devil Monkey [Demo Placeholder]",
        "personal_name": "unresolved [Demo Placeholder]",
        "naming_status": "unresolved [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 4,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-LILDEVIL/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Lil Devil [Demo Placeholder]",
          "series_name": "Lil Devil Monkey [Demo Placeholder]",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved [Demo Placeholder]"
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
        { "path": "personality.temperament", "name": "Trait data unavailable in static preview [Demo Placeholder]", "value": "Trait data unavailable in static preview [Demo Placeholder]", "status": "unknown [Demo Placeholder]", "strength": "defining", "usage_frequency": "often", "confidence": "high" }
      ]
    },
    "MZ-CHAR-PATCH": {
      "summary": {
        "character_id": "MZ-CHAR-PATCH",
        "display_name": "Patch [Demo Placeholder]",
        "series_name": "Patch Monkey [Demo Placeholder]",
        "personal_name": "unresolved [Demo Placeholder]",
        "naming_status": "unresolved [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 2,
        "experimental_traits": 0,
        "unresolved_fields": 3,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-PATCH/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Patch [Demo Placeholder]",
          "series_name": "Patch Monkey [Demo Placeholder]",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved [Demo Placeholder]"
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
        { "path": "personality.temperament", "name": "Trait data unavailable in static preview [Demo Placeholder]", "value": "Trait data unavailable in static preview [Demo Placeholder]", "status": "unknown [Demo Placeholder]", "strength": "moderate", "usage_frequency": "sometimes", "confidence": "moderate" }
      ]
    },
    "MZ-CHAR-ZOMBIE": {
      "summary": {
        "character_id": "MZ-CHAR-ZOMBIE",
        "display_name": "Zombie [Demo Placeholder]",
        "series_name": "Zombie Monkey [Demo Placeholder]",
        "personal_name": "unresolved [Demo Placeholder]",
        "naming_status": "unresolved [Demo Placeholder]",
        "development_level": 1,
        "canon_traits": 3,
        "experimental_traits": 1,
        "unresolved_fields": 0,
        "last_comic_appearance": "Last appearance unavailable [Demo Placeholder]",
        "primary_image": "./media/MZ-CHAR-ZOMBIE/references/primary/primary-reference.png",
        "continuity_warnings": []
      },
      "detail": {
        "identification": {
          "current_display_name": "Zombie [Demo Placeholder]",
          "series_name": "Zombie Monkey [Demo Placeholder]",
          "personal_name": "",
          "codename": "",
          "nicknames": [],
          "naming_status": "unresolved [Demo Placeholder]"
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
        { "path": "personality.temperament", "name": "Trait data unavailable in static preview [Demo Placeholder]", "value": "Trait data unavailable in static preview [Demo Placeholder]", "status": "unknown [Demo Placeholder]", "strength": "moderate", "usage_frequency": "often", "confidence": "moderate" }
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
      "Page_1": { "panels": 1, "description": "Cover page: [Demo Placeholder] " + (setup.topic || "Observed signal") },
      "Page_2": { "panels": 4, "description": "Story page: introduction of characters in [Demo Placeholder] " + (setup.location || "Observatory") },
      "Page_12": { "panels": 1, "description": "Back cover: [Demo Placeholder] " + (setup.lesson || "learning lesson") }
    },
    "story_structure": {
      "arc": "Emo Monkeys Season Arc 2026 [Demo Placeholder]",
      "beat_progression": [
        "Beat 1: Group gathers [Demo Placeholder]",
        "Beat 2: Discovery of topic [Demo Placeholder]"
      ]
    },
    "warnings": [],
    "prompt": `### MonkeyZoo Comic Script Generation Prompt [Demo Placeholder]`,
    "generated_script": `#### Page 1: Front Cover [Demo Placeholder]
Narrative Box: THE SIGNAL BETWEEN US [Demo Placeholder]`,
    "script_validation_warnings": [],
    "continuity_proposal": {
      "new_established_traits": [],
      "lessons_learned": [ (setup.lesson || "listening yields clarity") + " [Demo Placeholder]" ]
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
