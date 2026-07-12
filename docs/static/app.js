window.BANANA_LAB_STATIC_MODE = true;
const statuses = ["canon","established","experimental","optional","dormant","retired","contradicted","unknown","reserved"];
const strengths = ["defining","strong","moderate","subtle","background"];
const frequencies = ["almost always","often","sometimes","rarely","special circumstances only","never"];

let characters = [];
let current = null;
let selectedForCompare = new Set();
let storyPreview = null;
let adventureStyles = [];

const $ = (id) => document.getElementById(id);

function badge(text, cls = "") {
  return `<span class="badge ${cls}">${escapeHtml(text)}</span>`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[ch]));
}

// Intercept API calls for static GitHub Pages preview
async function api(path, options = {}) {
  console.log("Pages Demo Mode Intercept:", path, options);
  
  const cleanPath = path.split("?")[0];
  
  // Strict write operations block: return false result and throw error
  const isWrite = cleanPath.endsWith("/trait") || 
                  cleanPath.endsWith("/field") || 
                  cleanPath.endsWith("/undo") || 
                  cleanPath === "/api/story/save" || 
                  cleanPath === "/api/story/generate-sample" ||
                  (cleanPath === "/api/issues" && (options.method || "GET").toUpperCase() !== "GET");
                  
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
    const response = await fetch("./static/characters.json");
    return response.json();
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
        "primary_image": "../media/MZ-CHAR-CLEVER/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-SUPER/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-LILDEVIL/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-PATCH/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-ZOMBIE/references/primary/primary-reference.png",
        "continuity_warnings": []
      }
    ];
  }

  if (cleanPath === "/api/issues") {
    const response = await fetch("./static/issue-workflows.json");
    return response.json();
  }

  if (cleanPath.startsWith("/api/issues/")) {
    const parts = cleanPath.split("/");
    const issueId = decodeURIComponent(parts[3] || "");
    const response = await fetch("./static/issue-workflows.json");
    const issue = (await response.json()).find(item => item.issue_id === issueId);
    if ((options.method || "GET").toUpperCase() !== "GET") {
      alert("This production action requires the local Banana Lab backend.");
      throw {ok:false, demo_mode:true, error:"Local backend required"};
    }
    if (parts[4] === "workflow") return issue?.workflow || {error:"Issue unavailable"};
    if (parts[4] === "artifacts") return issue?.artifacts || [];
    if (parts[4] === "artifact") throw {ok:false, demo_mode:true, error:"Artifact content requires the local backend"};
    return issue || {error:"Issue unavailable"};
  }
  
  if (cleanPath.startsWith("/api/characters/")) {
    const cid = cleanPath.split("/")[3];
    const response = await fetch("./static/characters.json");
    const summary = (await response.json()).find(item => item.character_id === cid);
    if (!summary) return { error: "Character unavailable" };
    return {summary, detail: {identification: {
      current_display_name: summary.display_name,
      series_name: summary.series_name,
      personal_name: summary.personal_name,
      legacy_label: summary.legacy_label,
      nationality: summary.nationality,
      country_of_origin: summary.country_of_origin,
      naming_status: summary.naming_status
    }, visual_canon: {primary_reference_image: summary.primary_image}, history: []}, traits: []};
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
        "primary_image": "../media/MZ-CHAR-CLEVER/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-SUPER/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-LILDEVIL/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-PATCH/references/primary/primary-reference.png",
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
        "primary_image": "../media/MZ-CHAR-ZOMBIE/references/primary/primary-reference.png",
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

async function loadCharacters() {
  try {
    characters = await api("/api/characters");
    if ($("statusBackend")) {
      $("statusBackend").textContent = "Connected (127.0.0.1:8765)";
      $("statusBackend").className = "status-value connected";
    }
    if ($("sidebarStatusIndicator")) {
      $("sidebarStatusIndicator").className = "status-indicator online";
    }
    if ($("sidebarStatusText")) {
      $("sidebarStatusText").textContent = "Backend connected";
    }
    await loadIssuesMetadata();
  } catch (err) {
    console.error("Backend connection failed:", err);
    if ($("statusBackend")) {
      $("statusBackend").textContent = "Backend status unavailable";
      $("statusBackend").className = "status-value disconnected";
    }
    if ($("sidebarStatusIndicator")) {
      $("sidebarStatusIndicator").className = "status-indicator offline";
    }
    if ($("sidebarStatusText")) {
      $("sidebarStatusText").textContent = "Backend status unavailable";
    }
    renderIssuesUnavailable();
  }
  
  if (!adventureStyles.length && characters.length) {
    try {
      adventureStyles = await api("/api/story/adventure-styles");
      $("storyAdventureStyle").innerHTML = adventureStyles.map(style => `<option>${escapeHtml(style)}</option>`).join("");
      $("storyAdventureStyle").value = "Low-stakes slice of life";
    } catch (e) {
      console.warn("Failed to load adventure styles:", e);
    }
  }
  
  renderCharacterList();
  renderStoryCharacterList();
  
  // Update dashboard metrics and cast
  renderDashboardMetrics();
  renderDashboardCharacters();
}

async function loadIssuesMetadata() {
  try {
    const data = await api("/api/issues");
    renderIssuesList(data);
    return true;
  } catch (err) {
    console.warn("Issues metadata unavailable:", err);
    renderIssuesUnavailable();
    return false;
  }
}

function setupIssueCreation() {
  const dialog = $("createIssueDialog"), form = $("createIssueForm");
  if (!dialog || !form) return;
  let submitting = false;
  const submitButton = form.querySelector('button[type="submit"]');
  const populate = () => {
    const options = characters.map(c => `<option value="${escapeHtml(c.character_id)}">${escapeHtml(c.display_name || c.character_id)}</option>`).join("");
    form.primary_character.innerHTML = options;
    form.guest_character.innerHTML = `<option value="">None</option>${options}`;
    updateCanonReview();
  };
  const updateCanonReview = () => {
    const selected = characters.find(c => c.character_id === form.primary_character.value);
    const review = $("issueCanonReview");
    review.replaceChildren();
    if (!selected) { review.textContent = "No character selected."; return; }
    if (selected.primary_image) {
      const portrait = document.createElement("img");
      portrait.src = selected.primary_image;
      portrait.alt = `${selected.display_name || selected.character_id} approved portrait`;
      portrait.className = "canon-review-portrait";
      review.append(portrait);
    }
    const heading = document.createElement("strong");
    heading.textContent = selected.display_name || selected.character_id;
    review.append(heading);
    const details = [
      `Legacy identity: ${selected.legacy_label || "Unavailable"}`,
      `Nationality: ${selected.nationality || "Unavailable"}`,
      `Country: ${selected.country_of_origin || "Unavailable"}`,
      "Bible: Available",
      `Image: ${selected.image_status === "approved" ? "Approved" : "Approved character image unavailable"}`,
      (selected.continuity_warnings || []).join("; ") || "No repository warnings reported."
    ];
    details.forEach(text => { const p = document.createElement("p"); p.textContent = text; review.append(p); });
  };
  $("createIssueButton").addEventListener("click", () => { form.reset(); populate(); $("issueCreateError").textContent = ""; dialog.showModal(); });
  $("cancelIssueCreate").addEventListener("click", () => dialog.close());
  form.primary_character.addEventListener("change", updateCanonReview);
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (submitting) return;
    submitting = true;
    submitButton.disabled = true;
    submitButton.textContent = "Creating…";
    $("issueCreateError").textContent = "";
    const body = Object.fromEntries(new FormData(form));
    body.output_requirements = ["cover", "metadata", "social copy", "QA"];
    try {
      const result = await api("/api/issues", {method: "POST", body: JSON.stringify(body)});
      dialog.close();
      $("issueCreateResult").textContent = `Issue created successfully: ${result.issue_id} at ${result.location}. Stage: ${result.stage}.`;
      const refreshed = await loadIssuesMetadata();
      if (!refreshed) {
        $("issueCreateResult").textContent += " Issue list refresh failed; reload Studio to see the persisted issue.";
      }
      form.reset();
    } catch (err) {
      $("issueCreateError").textContent = err.message || err.error || "Issue creation failed. No success state was recorded.";
    } finally {
      submitting = false;
      submitButton.disabled = false;
      submitButton.textContent = "Create Issue";
    }
  });
}

function renderIssuesList(issues) {
  const grid = $("issuesWorkspaceGrid");
  if (!grid) return;
  
  if (!issues || issues.length === 0) {
    renderIssuesUnavailable();
    return;
  }
  
  grid.innerHTML = issues.map(issue => {
    const isDemo = issue.is_demo;
    const tagClass = isDemo ? "tag-demo" : "tag-repo";
    const tagLabel = isDemo ? "[Demo Placeholder]" : "[Repository Metadata]";
    const borderClass = isDemo ? "demo-border" : "";
    const pillStyle = issue.stage.includes("Release") ? "background: rgba(74, 222, 128, 0.1); color: var(--ok);" : "background: rgba(56, 189, 248, 0.1); color: var(--accent);";
    const pillLabel = issue.stage.includes("Release") ? "Released" : "In Production";
    
    let stageNum = 1;
    if (issue.stage.includes("Continuity")) stageNum = 2;
    else if (issue.stage.includes("Showrunner")) stageNum = 3;
    else if (issue.stage.includes("Script")) stageNum = 4;
    else if (issue.stage.includes("Direction")) stageNum = 5;
    else if (issue.stage.includes("Generation") || issue.stage.includes("Gen")) stageNum = 6;
    else if (issue.stage.includes("Art QA")) stageNum = 7;
    else if (issue.stage.includes("Layout")) stageNum = 8;
    else if (issue.stage.includes("Final QA")) stageNum = 9;
    else if (issue.stage.includes("Release")) stageNum = 10;
    
    const barWidth = `${stageNum * 10}%`;
    const barColor = stageNum === 10 ? "var(--ok)" : "var(--accent)";
    
    return `
      <div class="issue-card ${borderClass}">
        <div class="card-header">
          <h4>${escapeHtml(issue.issue_id)} <span class="data-tag ${tagClass}">${tagLabel}</span></h4>
          <span class="status-pill" style="${pillStyle}">${pillLabel}</span>
        </div>
        <p style="margin:0; font-size:14px; font-weight:600; color:#f8fafc;">${escapeHtml(issue.title)}</p>
        <div class="progress-bar-container"><div class="progress-bar" style="width: ${barWidth}; background: ${barColor};"></div></div>
        <div class="issue-meta-grid">
          <div class="issue-meta-item"><span>Owner</span><span>${escapeHtml(issue.owner)}</span></div>
          <div class="issue-meta-item"><span>Stage</span><span>${escapeHtml(issue.stage)}</span></div>
          <div class="issue-meta-item"><span>QA Status</span><span>${escapeHtml(issue.qa_status)}</span></div>
          <div class="issue-meta-item"><span>Release Log</span><span>${escapeHtml(issue.release_log)}</span></div>
        </div>
      </div>
    `;
  }).join("");
  
  // Pick active issue to render on dashboard
  const activeIssue = issues.find(i => !i.stage.includes("Release")) || issues[0];
  if (activeIssue) {
    const isDemo = activeIssue.is_demo;
    $("dashboardIssueSource").textContent = isDemo ? "[Demo Placeholder]" : "[Repository Metadata]";
    $("dashboardIssueSource").className = `data-tag ${isDemo ? "tag-demo" : "tag-repo"}`;
    $("dashboardIssueStage").textContent = activeIssue.stage;
    $("dashboardIssueId").textContent = activeIssue.issue_id;
    $("dashboardIssueTitle").textContent = activeIssue.title;
    $("dashboardIssuePages").textContent = activeIssue.pages ? `${activeIssue.pages} Pages` : "8 Pages";
    $("dashboardIssuePanels").textContent = activeIssue.panels ? `${activeIssue.panels} Panels` : "20 Panels";
    $("pipelineProgressStageName").textContent = activeIssue.stage;
    
    let activeStageNum = 1;
    if (activeIssue.stage.includes("Continuity")) activeStageNum = 2;
    else if (activeIssue.stage.includes("Showrunner")) activeStageNum = 3;
    else if (activeIssue.stage.includes("Script")) activeStageNum = 4;
    else if (activeIssue.stage.includes("Direction")) activeStageNum = 5;
    else if (activeIssue.stage.includes("Generation") || activeIssue.stage.includes("Gen")) activeStageNum = 6;
    else if (activeIssue.stage.includes("Art QA")) activeStageNum = 7;
    else if (activeIssue.stage.includes("Layout")) activeStageNum = 8;
    else if (activeIssue.stage.includes("Final QA")) activeStageNum = 9;
    else if (activeIssue.stage.includes("Release")) activeStageNum = 10;
    
    $("pipelineProgressBar").style.width = `${activeStageNum * 10}%`;
    
    const labels = document.querySelectorAll(".progress-labels span");
    labels.forEach((el, index) => {
      el.className = "";
      el.style.fontWeight = "400";
      if (index + 1 === activeStageNum) {
        el.className = "text-accent";
        el.style.fontWeight = "700";
      }
    });
  }
}

function renderIssuesUnavailable() {
  const grid = $("issuesWorkspaceGrid");
  if (grid) {
    grid.innerHTML = `
      <div class="issue-card demo-border">
        <div class="card-header">
          <h4>No Issues Loaded <span class="data-tag tag-demo">[Demo Placeholder]</span></h4>
          <span class="status-pill status-in-progress">Inactive</span>
        </div>
        <p style="margin:0; font-size:14px; font-weight:600; color:#f8fafc;">Current issue unavailable</p>
        <div class="issue-meta-grid">
          <div class="issue-meta-item"><span>Owner</span><span>Unavailable</span></div>
          <div class="issue-meta-item"><span>Stage</span><span>Production stage unavailable</span></div>
        </div>
      </div>
    `;
  }
  
  if ($("dashboardIssueSource")) {
    $("dashboardIssueSource").textContent = "[Demo Placeholder]";
    $("dashboardIssueSource").className = "data-tag tag-demo";
    $("dashboardIssueStage").textContent = "Production stage unavailable";
    $("dashboardIssueId").textContent = "Current issue unavailable";
    $("dashboardIssueTitle").textContent = "Current issue unavailable";
    $("dashboardIssuePages").textContent = "Current issue unavailable";
    $("dashboardIssuePanels").textContent = "Current issue unavailable";
    $("pipelineProgressStageName").textContent = "Production stage unavailable";
    $("pipelineProgressBar").style.width = "0%";
    
    const labels = document.querySelectorAll(".progress-labels span");
    labels.forEach(el => {
      el.className = "";
      el.style.fontWeight = "400";
    });
  }
}

function renderCharacterList() {
  const query = $("searchBox").value.toLowerCase();
  $("characterList").innerHTML = characters
    .filter(c => `${c.display_name} ${c.series_name} ${c.character_id}`.toLowerCase().includes(query))
    .map(c => `
      <div class="character-row ${current?.summary.character_id === c.character_id ? "selected" : ""}" data-id="${c.character_id}">
        ${c.primary_image ? `<img src="${c.primary_image}" alt="${escapeHtml(c.display_name)} approved portrait">` : `<div class="missing-img">Approved character image unavailable</div>`}
        <div>
          <h3>${escapeHtml(c.display_name)}</h3>
          <p>${escapeHtml(c.series_name || "")}</p>
          <div class="mini-stats">
            ${badge(`L${c.development_level}`)}
            ${badge(`${c.canon_traits} canon`, "canon")}
            ${badge(`${c.experimental_traits} exp`, "experimental")}
            ${c.continuity_warnings.length ? badge(`${c.continuity_warnings.length} warnings`, "warning") : ""}
          </div>
        </div>
      </div>
    `).join("");
  document.querySelectorAll(".character-row").forEach(row => {
    row.addEventListener("click", () => loadCharacter(row.dataset.id));
  });
}

function renderStoryCharacterList() {
  $("storyCharacterList").innerHTML = characters.map((c, index) => `
    <div class="story-character-row">
      <label class="story-check">
        <input type="checkbox" value="${c.character_id}" ${index < 2 ? "checked" : ""}>
        ${c.primary_image ? `<img src="${c.primary_image}" alt="${escapeHtml(c.display_name)} approved portrait">` : `<span class="missing-img">Approved character image unavailable</span>`}
        <span>
          <strong>${escapeHtml(c.display_name)}</strong>
          <small>${escapeHtml(c.series_name || "")}</small>
        </span>
      </label>
      <select data-role-for="${c.character_id}">
        <option ${index === 0 ? "selected" : ""}>primary</option>
        <option ${index === 1 ? "selected" : ""}>secondary</option>
        <option ${index > 1 ? "selected" : ""}>supporting</option>
        <option>cameo</option>
      </select>
    </div>
  `).join("");
}

async function loadCharacter(characterId) {
  current = await api(`/api/characters/${characterId}`);
  $("emptyState").classList.add("hidden");
  $("detailView").classList.remove("hidden");
  $("undoBtn").disabled = false;
  
  if ($("statusCharacter")) {
    $("statusCharacter").textContent = current.summary.display_name;
  }
  
  renderCharacterList();
  renderDetail();
}

function renderDetail() {
  const s = current.summary;
  const d = current.detail;
  $("characterName").textContent = s.display_name;
  $("seriesLine").textContent = `${s.series_name || ""} | Personal name: ${s.personal_name || "blank"} | Naming: ${s.naming_status}`;
  $("appearanceLine").textContent = `Last appearance: ${s.last_comic_appearance}`;
  $("badges").innerHTML = [
    badge(`Level ${s.development_level}`),
    badge(`${s.canon_traits} canon`, "canon"),
    badge(`${s.experimental_traits} experimental`, "experimental"),
    badge(`${s.unresolved_fields} unresolved`)
  ].join("");
  $("warnings").innerHTML = s.continuity_warnings.map(w => badge(w, "warning")).join("");
  $("primaryImage").src = s.primary_image || "";
  $("primaryImage").style.display = s.primary_image ? "block" : "none";
  const images = [d.visual_canon.primary_reference_image, ...(d.visual_canon.supporting_reference_images || [])].filter(Boolean);
  $("altImages").innerHTML = images.slice(1, 9).map(path => `<img src="./media/${s.character_id}/${path}" alt="">`).join("");
  renderTraits();
  renderNaming();
  renderVisual();
  renderHistory();
  renderCompare();
}

function groupTraits() {
  const groups = {};
  current.traits.forEach(t => {
    const section = t.path.split(".")[0].replaceAll("_", " ");
    groups[section] = groups[section] || [];
    groups[section].push(t);
  });
  return groups;
}

function renderTraits() {
  const groups = groupTraits();
  $("tab-traits").innerHTML = Object.entries(groups).map(([section, traits]) => `
    <h3 class="section-heading">${escapeHtml(title(section))}</h3>
    ${traits.map(renderTraitRow).join("")}
  `).join("");
  bindTraitButtons();
}

function title(value) {
  return value.replace(/\b\w/g, c => c.toUpperCase());
}

function renderTraitRow(t) {
  return `
    <div class="trait-row">
      <div class="trait-main">
        <strong>${escapeHtml(t.name)}</strong>
        <p>${escapeHtml(t.value || "blank / intentionally unresolved")}</p>
        <div>
          ${badge(t.status, t.status === "canon" ? "canon" : t.status === "experimental" ? "experimental" : "")}
          ${badge(t.strength)}
          ${badge(t.usage_frequency)}
          ${badge(t.confidence || "no confidence")}
        </div>
        <p><small>${escapeHtml(t.rationale || "")}</small></p>
      </div>
      <div class="trait-actions" data-path="${escapeHtml(t.path)}">
        <button data-action="approve_canon">Canon</button>
        <button data-action="approve_established">Established</button>
        <button data-action="keep_experimental">Experimental</button>
        <button data-action="mark_optional">Optional</button>
        <button data-action="mark_dormant">Dormant</button>
        <button data-action="retire">Retire</button>
        <button data-action="reject" class="danger">Reject</button>
        <button data-edit="true">Edit</button>
      </div>
    </div>
  `;
}

function bindTraitButtons() {
  document.querySelectorAll("[data-action]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const path = btn.closest(".trait-actions").dataset.path;
      const note = prompt("Optional note for approval history:", "") || "";
      await api(`/api/characters/${current.summary.character_id}/trait`, {
        method: "POST",
        body: JSON.stringify({path, updates: {action: btn.dataset.action}, note})
      });
      await loadCharacter(current.summary.character_id);
    });
  });
  document.querySelectorAll("[data-edit]").forEach(btn => {
    btn.addEventListener("click", () => openEditDialog(btn.closest(".trait-actions").dataset.path));
  });
}

function findTrait(path) {
  return current.traits.find(t => t.path === path);
}

function fillSelect(select, values, selected) {
  select.innerHTML = values.map(v => `<option value="${v}" ${v === selected ? "selected" : ""}>${v}</option>`).join("");
}

function openEditDialog(path) {
  const t = findTrait(path);
  $("editTraitPath").value = path;
  $("editName").value = t.name || "";
  $("editValue").value = t.value || "";
  fillSelect($("editStatus"), statuses, t.status);
  fillSelect($("editStrength"), strengths, t.strength);
  fillSelect($("editFrequency"), frequencies, t.usage_frequency);
  $("editNote").value = t.notes || "";
  $("editContexts").value = (t.compatible_contexts || []).join(", ");
  $("editIncompatible").value = (t.incompatible_contexts || []).join(", ");
  $("editDialog").showModal();
}

async function saveTraitEdit(event) {
  event.preventDefault();
  const path = $("editTraitPath").value;
  const updates = {
    name: $("editName").value,
    value: $("editValue").value || null,
    status: $("editStatus").value,
    strength: $("editStrength").value,
    usage_frequency: $("editFrequency").value,
    notes: $("editNote").value || null,
    compatible_contexts: splitList($("editContexts").value),
    incompatible_contexts: splitList($("editIncompatible").value)
  };
  await api(`/api/characters/${current.summary.character_id}/trait`, {
    method: "POST",
    body: JSON.stringify({path, updates, note: $("editNote").value || ""})
  });
  $("editDialog").close();
  await loadCharacter(current.summary.character_id);
}

function splitList(value) {
  return value.split(",").map(v => v.trim()).filter(Boolean);
}

function renderNaming() {
  const ident = current.detail.identification;
  $("tab-naming").innerHTML = `
    <h3>Naming Controls</h3>
    <div class="form-grid">
      <label>Current display name<input id="nameDisplay" value="${escapeHtml(ident.current_display_name || "")}"></label>
      <label>Series name<input id="nameSeries" value="${escapeHtml(ident.series_name || "")}"></label>
      <label>Personal name<input id="namePersonal" value="${escapeHtml(ident.personal_name || "")}"></label>
      <label>Codename<input id="nameCode" value="${escapeHtml(ident.codename || "")}"></label>
      <label>Nicknames<input id="nameNicks" value="${escapeHtml((ident.nicknames || []).join(", "))}"></label>
      <label>Naming status
        <select id="nameStatus">
          ${["personal_name_canon","series_name_only","codename_only","nickname_only","personal_name_unresolved","unresolved","reserved"].map(v => `<option ${ident.naming_status === v ? "selected" : ""}>${v}</option>`).join("")}
        </select>
      </label>
    </div>
    <p><button id="saveNaming" class="primary">Save Naming</button></p>
  `;
  $("saveNaming").addEventListener("click", saveNaming);
}

async function saveNaming() {
  const id = current.summary.character_id;
  const changes = [
    ["identification.current_display_name", $("nameDisplay").value],
    ["identification.series_name", $("nameSeries").value || null],
    ["identification.personal_name", $("namePersonal").value || null],
    ["identification.codename", $("nameCode").value || null],
    ["identification.nicknames", splitList($("nameNicks").value)],
    ["identification.naming_status", $("nameStatus").value]
  ];
  for (const [path, value] of changes) {
    await api(`/api/characters/${id}/field`, {method: "POST", body: JSON.stringify({path, value, action: "update_naming"})});
  }
  await loadCharacter(id);
}

function renderVisual() {
  const id = current.summary.character_id;
  const visual = current.detail.visual_canon;
  const images = [visual.primary_reference_image, ...(visual.supporting_reference_images || [])].filter(Boolean);
  $("tab-visual").innerHTML = `
    <h3>Visual Controls</h3>
    <p>Clever remains the only confirmed glasses-wearing monkey unless owner review changes canon.</p>
    ${images.length ? images.map(path => `
      <div class="image-control">
        <img src="./media/${id}/${path}" alt="">
        <div><strong>${escapeHtml(path)}</strong><br><small>${path === visual.primary_reference_image ? "Primary" : "Alternate"}</small></div>
        <button data-primary="${escapeHtml(path)}">Set Primary</button>
      </div>
    `).join("") : "<p>No visual references found for this character.</p>"}
    <h3 class="section-heading">Visual Rules</h3>
    ${["features_that_must_never_change","features_that_may_vary","prohibited_visual_additions"].map(key => `
      <p><strong>${title(key.replaceAll("_", " "))}</strong>: ${(visual[key] || []).length} entries</p>
    `).join("")}
  `;
  document.querySelectorAll("[data-primary]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await api(`/api/characters/${id}/field`, {
        method: "POST",
        body: JSON.stringify({path: "visual_canon.primary_reference_image", value: btn.dataset.primary, action: "select_primary_reference"})
      });
      await loadCharacter(id);
    });
  });
}

function renderHistory() {
  const history = current.detail.history || [];
  $("tab-history").innerHTML = `
    <h3>Approval History</h3>
    ${history.length ? history.slice().reverse().map(h => `
      <div class="history-entry">
        <strong>${escapeHtml(h.action)}</strong> <code>${escapeHtml(h.field_path)}</code><br>
        <small>${escapeHtml(h.date)} ${h.note ? " | " + escapeHtml(h.note) : ""}</small>
      </div>
    `).join("") : "<p>No approval history yet.</p>"}
  `;
}

function renderCompare() {
  const options = characters.map(c => `
    <label><input type="checkbox" value="${c.character_id}" ${selectedForCompare.has(c.character_id) ? "checked" : ""}> ${escapeHtml(c.display_name)}</label>
  `).join("");
  $("tab-compare").innerHTML = `
    <h3>Comparison Mode</h3>
    <div class="form-grid">${options}</div>
    <p><button id="runCompare" class="primary">Compare Selected</button></p>
    <div id="compareResult"></div>
  `;
  $("tab-compare").querySelectorAll("input[type=checkbox]").forEach(input => {
    input.addEventListener("change", () => {
      if (input.checked) selectedForCompare.add(input.value);
      else selectedForCompare.delete(input.value);
    });
  });
  $("runCompare").addEventListener("click", runCompare);
}

async function runCompare() {
  const ids = Array.from(selectedForCompare);
  if (current) ids.push(current.summary.character_id);
  const unique = Array.from(new Set(ids));
  const data = await api("/api/compare", {method: "POST", body: JSON.stringify({character_ids: unique})});
  $("compareResult").innerHTML = `
    <div class="compare-grid">
      ${data.characters.map(item => `
        <div class="compare-column">
          <h4>${escapeHtml(item.summary.display_name)}</h4>
          <p>${escapeHtml(item.summary.series_name || "")}</p>
          <p>${badge(`${item.summary.canon_traits} canon`, "canon")} ${badge(`${item.summary.experimental_traits} experimental`, "experimental")}</p>
        </div>
      `).join("")}
    </div>
    <h4>Overlap</h4>
    <pre>${escapeHtml(JSON.stringify(data.overlap, null, 2))}</pre>
  `;
}

function storySetupFromForm() {
  const selected = Array.from($("storyCharacterList").querySelectorAll("input[type=checkbox]:checked"))
    .map(input => ({
      character_id: input.value,
      role: document.querySelector(`[data-role-for="${CSS.escape(input.value)}"]`).value
    }));
  return {
    issue_id: $("storyIssueId").value || undefined,
    characters: selected,
    page_count: $("storyPageCount").value,
    panel_count: $("storyPanelCount").value,
    panel_density: $("storyPanelDensity").value,
    topic: $("storyTopic").value,
    adventure_style: $("storyAdventureStyle").value,
    tone: $("storyTone").value,
    audience: $("storyAudience").value,
    conflict: $("storyConflict").value,
    location: $("storyLocation").value,
    lesson: $("storyLesson").value,
    required_beat: $("storyRequiredBeat").value,
    forbidden_content: $("storyForbidden").value,
    continuity_mode: $("storyContinuityMode").value,
    canon_strictness: $("storyCanonStrictness").value,
    character_growth_mode: $("storyGrowthMode").value,
    optional_story_instructions: $("storyInstructions").value
  };
}

async function previewStory() {
  storyPreview = await api("/api/story/preview", {
    method: "POST",
    body: JSON.stringify(storySetupFromForm())
  });
  renderStoryPreview(storyPreview);
}

async function saveStoryPacket() {
  const data = await api("/api/story/save", {
    method: "POST",
    body: JSON.stringify(storySetupFromForm())
  });
  storyPreview = data;
  renderStoryPreview(data);
  alert(`Saved ${data.written_files.length} story context files.`);
}

async function generateSampleIssue() {
  const data = await api("/api/story/generate-sample", {
    method: "POST",
    body: JSON.stringify(storySetupFromForm())
  });
  storyPreview = data;
  renderStoryPreview(data);
  alert(`Generated sample issue and saved ${data.written_files.length} files.`);
}

function renderStoryPreview(data) {
  const packet = data.packet;
  $("storyPreview").classList.remove("hidden");
  $("storyPreview").innerHTML = `
    <div class="story-preview-grid">
      <section>
        <h3>Selected Cast</h3>
        ${packet.selected_cast.map(renderStoryCharacterPreview).join("")}
      </section>
      <section>
        <h3>Panel Plan</h3>
        <pre>${escapeHtml(JSON.stringify(data.panel_plan, null, 2))}</pre>
        <h3>Story Structure</h3>
        <pre>${escapeHtml(JSON.stringify(data.story_structure, null, 2))}</pre>
      </section>
    </div>
    <h3>Warnings</h3>
    <div class="warnings">${data.warnings.length ? data.warnings.map(w => badge(w, "warning")).join("") : badge("No warnings", "canon")}</div>
    <h3>Compact Prompt</h3>
    <textarea class="prompt-preview" readonly rows="14">${escapeHtml(data.prompt)}</textarea>
    ${data.generated_script ? `
      <h3>Generated Sample Script</h3>
      <textarea class="prompt-preview" readonly rows="14">${escapeHtml(data.generated_script)}</textarea>
      <h3>Script Validation</h3>
      <div class="warnings">${data.script_validation_warnings.length ? data.script_validation_warnings.map(w => badge(w, "warning")).join("") : badge("No script warnings", "canon")}</div>
      <h3>Proposed Post-Issue Bible Update</h3>
      <pre>${escapeHtml(JSON.stringify(data.continuity_proposal, null, 2))}</pre>
    ` : ""}
    <p><small>Save target: ${escapeHtml(data.save_hint || "")}</small></p>
  `;
}

function renderStoryCharacterPreview(character) {
  return `
    <div class="story-character-preview">
      <h4>${escapeHtml(character.display_name)} ${badge(character.role)}</h4>
      <p>${escapeHtml(character.series_name || "")} | Personal name: ${escapeHtml(character.personal_name || "blank")} | ${escapeHtml(character.naming_status || "")}</p>
      <p><strong>Selected traits</strong></p>
      <ul>${character.selected_traits.map(trait => `<li>${escapeHtml(trait.name)}: ${escapeHtml(trait.value || "")} ${badge(trait.status, trait.status === "experimental" ? "experimental" : trait.status === "canon" ? "canon" : "")}</li>`).join("") || "<li>None</li>"}</ul>
      <p><strong>Excluded this pass</strong>: ${character.excluded_traits.length}</p>
      <p><strong>Visual</strong>: glasses ${escapeHtml(character.visual_requirements.glasses_status || "unknown")}; primary ${escapeHtml(character.primary_reference_image || "missing")}</p>
    </div>
  `;
}

function toggleStoryBuilder(forceOpen = null) {
  const open = forceOpen === null ? $("viewStoryBuilder").classList.contains("hidden") : forceOpen;
  
  // Clear active states on navigation items
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
  
  if (open) {
    document.querySelector('[data-view="storyBuilder"]').classList.add("active");
    $("activeViewLabel").textContent = "Story Builder";
    document.querySelectorAll(".workspace-view").forEach(el => el.classList.add("hidden"));
    $("viewStoryBuilder").classList.remove("hidden");
    showWizardStep(1); // Reset to step 1
  } else {
    document.querySelector('[data-view="characters"]').classList.add("active");
    $("activeViewLabel").textContent = "Characters";
    document.querySelectorAll(".workspace-view").forEach(el => el.classList.add("hidden"));
    $("viewCharacters").classList.remove("hidden");
  }
}

function renderDashboardMetrics() {
  let totalCanon = 0;
  let totalExperimental = 0;
  let totalWarnings = 0;
  
  characters.forEach(c => {
    totalCanon += c.canon_traits || 0;
    totalExperimental += c.experimental_traits || 0;
    totalWarnings += c.continuity_warnings ? c.continuity_warnings.length : 0;
  });
  
  const charCountEl = $("metricCharactersCount");
  const canonCountEl = $("metricCanonCount");
  const expCountEl = $("metricExpCount");
  const warningCountEl = $("metricWarningCount");
  
  if (charCountEl) charCountEl.textContent = characters.length;
  if (canonCountEl) canonCountEl.textContent = totalCanon;
  if (expCountEl) expCountEl.textContent = totalExperimental;
  if (warningCountEl) warningCountEl.textContent = totalWarnings;
}

function renderDashboardCharacters() {
  const container = $("dashboardCharactersList");
  if (!container) return;
  container.innerHTML = characters.map(c => `
    <div class="dashboard-character-card" data-id="${c.character_id}">
      ${c.primary_image ? `<img src="${c.primary_image}" alt="${escapeHtml(c.display_name)} approved portrait">` : `<div class="missing-img">Approved character image unavailable</div>`}
      <div class="dashboard-char-info">
        <strong>${escapeHtml(c.display_name)}</strong>
        <span>Level ${c.development_level}</span>
      </div>
    </div>
  `).join("");
  
  // Bind click handlers to load the character and route to character view
  container.querySelectorAll(".dashboard-character-card").forEach(card => {
    card.addEventListener("click", async () => {
      const cid = card.dataset.id;
      await loadCharacter(cid);
      const navItem = document.querySelector('[data-view="characters"]');
      if (navItem) navItem.click();
    });
  });
}

// Workspace Router
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const viewName = btn.dataset.view;
    if (!viewName) return;
    
    // Update active nav button
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    
    // Update breadcrumb
    const label = btn.innerText.replace(/Soon$/, "").trim();
    $("activeViewLabel").textContent = label;
    
    if ($("statusWorkspace")) {
      $("statusWorkspace").textContent = label;
    }
    
    // Hide all view containers
    document.querySelectorAll(".workspace-view").forEach(el => el.classList.add("hidden"));
    
    // Show active container
    const viewContainerMap = {
      dashboard: "viewDashboard",
      characters: "viewCharacters",
      locations: "viewLocations",
      props: "viewProps",
      storyBuilder: "viewStoryBuilder",
      issues: "viewIssues",
      canon: "viewCanon",
      timeline: "viewTimeline",
      artQueue: "viewArtQueue",
      layout: "viewLayout",
      qa: "viewQA",
      release: "viewRelease",
      settings: "viewSettings"
    };
    
    const targetId = viewContainerMap[viewName];
    if (targetId && $(targetId)) {
      $(targetId).classList.remove("hidden");
    }
  });
});

// Story Builder Wizard Stepper Logic
let activeWizardStep = 1;

function showWizardStep(step) {
  activeWizardStep = step;
  
  // Update wizard step indicator active states
  document.querySelectorAll(".wizard-step").forEach(el => {
    const s = parseInt(el.dataset.step);
    el.classList.toggle("active", s === step);
    el.classList.toggle("completed", s < step);
  });
  
  // Hide all panels, show the active one
  document.querySelectorAll(".wizard-panel-step").forEach(el => {
    const s = parseInt(el.dataset.stepPanel);
    el.classList.toggle("hidden", s !== step);
  });
}

// Bind wizard next/prev button clicks
document.querySelectorAll(".wizard-next-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    if (activeWizardStep < 5) {
      showWizardStep(activeWizardStep + 1);
    }
  });
});

document.querySelectorAll(".wizard-prev-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    if (activeWizardStep > 1) {
      showWizardStep(activeWizardStep - 1);
    }
  });
});

// Bind wizard stepper indicators so users can jump to steps directly
document.querySelectorAll(".wizard-step").forEach(el => {
  el.addEventListener("click", () => {
    const step = parseInt(el.dataset.step);
    showWizardStep(step);
  });
});

function switchTab(event) {
  const tab = event.target.dataset.tab;
  if (!tab) return;
  document.querySelectorAll(".tabs button").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
  $(`tab-${tab}`).classList.remove("hidden");
}

async function undoLast() {
  if (!current) return;
  await api(`/api/characters/${current.summary.character_id}/undo`, {method: "POST", body: "{}"});
  await loadCharacter(current.summary.character_id);
}

$("refreshBtn").addEventListener("click", loadCharacters);
$("searchBox").addEventListener("input", renderCharacterList);
$("undoBtn").addEventListener("click", undoLast);
$("editForm").addEventListener("submit", saveTraitEdit);
document.querySelector(".tabs").addEventListener("click", switchTab);
$("compareBtn").addEventListener("click", () => {
  if (!current && characters[0]) loadCharacter(characters[0].character_id).then(() => document.querySelector('[data-tab="compare"]').click());
  else document.querySelector('[data-tab="compare"]').click();
});
$("storyBuilderBtn").addEventListener("click", () => toggleStoryBuilder(true));
$("closeStoryBuilder").addEventListener("click", () => toggleStoryBuilder(false));
$("previewStoryBtn").addEventListener("click", previewStory);
$("regenerateStoryBtn").addEventListener("click", previewStory);
$("saveStoryBtn").addEventListener("click", saveStoryPacket);
$("generateSampleBtn").addEventListener("click", generateSampleIssue);

setupIssueCreation();
setupProductionDashboard();
loadCharacters();

let activeProductionIssue = null;

function renderIssuesList(issues) {
  const grid = $("issuesWorkspaceGrid");
  if (!grid) return;
  grid.innerHTML = (issues || []).map(issue => `
    <article class="issue-card ${issue.degraded ? "demo-border" : ""}">
      <div class="card-header"><h4>${escapeHtml(issue.issue_id)}</h4><span class="status-pill">${escapeHtml(issue.validation_state || "degraded")}</span></div>
      <p><strong>${escapeHtml(issue.title || "Title unavailable")}</strong></p>
      <div class="issue-meta-grid">
        <div class="issue-meta-item"><span>Current stage</span><span>${escapeHtml(issue.workflow?.current_stage?.label || "Unavailable")}</span></div>
        <div class="issue-meta-item"><span>Primary character</span><span>${escapeHtml(issue.primary_character || "Unavailable")}</span></div>
        <div class="issue-meta-item"><span>Blockers</span><span>${Number(issue.blocker_count || 0)}</span></div>
        <div class="issue-meta-item"><span>Last updated</span><span>${escapeHtml(issue.last_updated || "Unavailable")}</span></div>
      </div>
      <button type="button" class="open-production-dashboard" data-issue-id="${escapeHtml(issue.issue_id)}" ${issue.degraded ? "disabled" : ""}>Open Production Dashboard</button>
      ${issue.degraded ? `<p class="error-message">Degraded legacy issue: ${escapeHtml(issue.error || "metadata unavailable")}</p>` : ""}
    </article>`).join("");
  grid.querySelectorAll(".open-production-dashboard").forEach(button => button.addEventListener("click", () => openProductionDashboard(button.dataset.issueId)));
}

function setupProductionDashboard() {
  $("closeProductionDashboard")?.addEventListener("click", () => $("productionDashboard").classList.add("hidden"));
  $("closeArtifactDialog")?.addEventListener("click", () => $("artifactDialog").close());
  $("validateStageButton")?.addEventListener("click", () => runProductionAction("validate"));
  $("approveStageButton")?.addEventListener("click", () => runProductionAction("workflow/approve"));
  $("advanceStageButton")?.addEventListener("click", () => runProductionAction("advance"));
}

async function openProductionDashboard(issueId) {
  try {
    activeProductionIssue = await api(`/api/issues/${encodeURIComponent(issueId)}`);
    renderProductionDashboard(activeProductionIssue);
    $("productionDashboard").classList.remove("hidden");
    $("productionDashboard").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (err) { $("issueCreateResult").textContent = err.message || "Unable to load issue dashboard"; }
}

function renderProductionDashboard(issue) {
  const workflow = issue.workflow;
  const staticMode = window.BANANA_LAB_STATIC_MODE === true;
  $("productionIdentity").textContent = `${issue.title} · ${issue.issue_id}`;
  $("productionSummary").innerHTML = [["Edition",issue.edition_number],["Period",issue.period],["Primary",issue.primary_character],["Guest",issue.guest_character || "None"],["Stage",workflow.current_stage.label],["Status",issue.validation_state],["Location",issue.location],["Updated",issue.last_updated]].map(([label,value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? "Unavailable")}</strong></div>`).join("");
  $("productionStageRail").innerHTML = workflow.stages.map(stage => `<button type="button" class="stage-node stage-${escapeHtml(stage.state)}" aria-label="Stage ${stage.number}: ${escapeHtml(stage.label)}, ${escapeHtml(stage.state)}"><span>${stage.number}</span><strong>${escapeHtml(stage.label)}</strong><small>${escapeHtml(stage.state.replace("_"," "))}</small></button>`).join("");
  const current = workflow.stages.find(stage => stage.id === workflow.current_stage.id);
  $("currentStageDetail").innerHTML = `<h5>${escapeHtml(current.label)}</h5><p>Status: <strong>${escapeHtml(current.state.replaceAll("_", " "))}</strong></p>${workflow.state_notice ? `<p class="approval-notice">${escapeHtml(workflow.state_notice)}</p>` : ""}<h6>Required inputs</h6><ul>${current.required_files.map(name => `<li>${escapeHtml(name)}</li>`).join("") || "<li>No file prerequisites</li>"}</ul><h6>Validation</h6><ul>${current.validation.messages.map(message => `<li>${escapeHtml(message)}</li>`).join("") || "<li>Passed</li>"}</ul>${current.approval.required ? `<p class="approval-notice">Owner approval: ${current.approval.stale ? "stale" : current.approval.approved ? "recorded" : "required"}</p>` : ""}`;
  $("validateStageButton").disabled = staticMode;
  $("validateStageButton").textContent = staticMode ? "Validate — local backend required" : "Validate current stage";
  $("approveStageButton").classList.toggle("hidden", !current.approval.required);
  $("approveStageButton").disabled = staticMode || current.validation.status !== "passed" || current.approval.approved;
  $("approveStageButton").textContent = staticMode ? "Approve — local backend required" : current.approval.approved ? "Owner approval recorded" : "Record owner approval";
  $("advanceStageButton").disabled = staticMode || current.state !== "current_ready" || current.id === "published";
  $("advanceStageButton").textContent = staticMode ? "Advance — local backend required" : "Advance stage";
  $("artifactInventory").innerHTML = issue.artifacts.map(file => `<div class="artifact-row"><div><strong>${escapeHtml(file.name)}</strong><small>${escapeHtml(file.group)} · ${file.exists ? "Exists" : "Missing"}${file.modified ? ` · ${escapeHtml(file.modified)}` : ""}</small></div>${file.exists && file.viewable ? `<button type="button" data-artifact="${escapeHtml(file.name)}">View</button>` : ""}</div>`).join("");
  $("artifactInventory").querySelectorAll("[data-artifact]").forEach(button => button.addEventListener("click", () => viewArtifact(button.dataset.artifact)));
}

async function runProductionAction(action) {
  if (!activeProductionIssue) return;
  try {
    const stage = activeProductionIssue.workflow.current_stage.id;
    const options = {method: "POST", body: action === "advance" ? JSON.stringify({stage}) : action === "workflow/approve" ? JSON.stringify({stage, approved: true}) : "{}"};
    await api(`/api/issues/${encodeURIComponent(activeProductionIssue.issue_id)}/${action}`, options);
    await openProductionDashboard(activeProductionIssue.issue_id);
  } catch (err) { $("issueCreateResult").textContent = err.message || `${action} failed`; }
}

async function viewArtifact(path) {
  try {
    const data = await api(`/api/issues/${encodeURIComponent(activeProductionIssue.issue_id)}/artifact?path=${encodeURIComponent(path)}`);
    $("artifactTitle").textContent = data.name;
    $("artifactContent").textContent = data.type === ".json" ? JSON.stringify(JSON.parse(data.content), null, 2) : data.content;
    $("artifactDialog").showModal();
  } catch (err) { $("issueCreateResult").textContent = err.message || "Artifact unavailable"; }
}
