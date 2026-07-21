window.BANANA_LAB_STATIC_MODE = true;
const statuses = ["canon","established","experimental","optional","dormant","retired","contradicted","unknown","reserved"];
const strengths = ["defining","strong","moderate","subtle","background"];
const frequencies = ["almost always","often","sometimes","rarely","special circumstances only","never"];

let characters = [];
let current = null;
let selectedForCompare = new Set();
let storyPreview = null;
let adventureStyles = [];
let productionStory = null;
let storyImportKind = "outline";
let runtimeCapability = {resolved: false, writable: false, reason: "unresolved"};

const MUTATION_SELECTOR = [
  "[data-mutation]", "#createIssueButton", "#saveStoryBtn", "#generateSampleBtn",
  "#outlinePromptBtn", "#outlineImportBtn", "#scriptPromptBtn", "#scriptImportBtn",
  "#storyImportSubmit", "#createPlanVariant", "#buildArtQueue", "#createArtPromptPack",
  "#artAttemptFile",
  "#createQAReview", "#releaseManifest", "#releaseApprove", "#releasePromote",
  "#releasePublishArchive",
  "#validateStageButton", "#approveStageButton", "#advanceStageButton", "#saveTraitBtn", "#undoBtn",
  "#createIssueForm button[type='submit']", "#settingsForm button[type='submit']",
  "[data-approve-variant]", "[data-promote-variant]", "[data-layout-approve]",
  "[data-layout-promote]", "[data-art-select]", "[data-art-reject]", "[data-art-prompt]",
  "[data-art-import]", "[data-art-pack-approve]", "[data-art-pack-promote]",
  "[data-qa-finalize]", "[data-qa-promote]"
].join(",");

function canMutate() { return runtimeCapability.resolved && runtimeCapability.writable === true; }
function isTrustedRuntimeCapability(data) {
  return Boolean(data && data.schema_version === "1.0" && data.runtime === "monkeyzoo-local" &&
    data.capability === "monkeyzoo-production-write-v1" && data.writable === true);
}
function enforceMutationCapability(root = document) {
  if (canMutate()) return;
  root.querySelectorAll(MUTATION_SELECTOR).forEach(control => {
    control.disabled = true;
    control.title = "Trusted writable local runtime required";
  });
}
async function resolveRuntimeCapability() {
  // Static Pages sets this flag before the bundle runs. Stay fail-closed without probing a missing API.
  if (window.BANANA_LAB_STATIC_MODE === true) {
    runtimeCapability = {resolved: true, writable: false, reason: "static-preview"};
    console.info(`MonkeyZoo read-only mode: ${runtimeCapability.reason}`);
    enforceMutationCapability();
    return runtimeCapability;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 2000);
  try {
    const response = await fetch("/api/runtime-capabilities", {signal: controller.signal, cache: "no-store"});
    const data = response.ok ? await response.json() : null;
    const trusted = isTrustedRuntimeCapability(data);
    runtimeCapability = {resolved: true, writable: trusted, reason: trusted ? "trusted-local-runtime" : "untrusted-capability"};
  } catch (_error) {
    runtimeCapability = {resolved: true, writable: false, reason: "capability-unavailable"};
  } finally { clearTimeout(timer); }
  if (canMutate()) document.querySelectorAll(MUTATION_SELECTOR).forEach(control => { control.disabled = false; control.title = ""; });
  else {
    console.info(`MonkeyZoo read-only mode: ${runtimeCapability.reason}`);
    enforceMutationCapability();
  }
  return runtimeCapability;
}

const $ = (id) => document.getElementById(id);

function badge(text, cls = "") {
  return `<span class="badge ${cls}">${escapeHtml(text)}</span>`;
}

const HTML_ESCAPE_MAP = {
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => HTML_ESCAPE_MAP[ch]);
}


// Intercept API calls for static GitHub Pages preview
async function api(path, options = {}) {
  const cleanPath = path.split("?")[0];
  const method = String(options.method || "GET").toUpperCase();
  const readOnlyPost = new Set(["/api/compare", "/api/story/preview", "/api/story/validate-script"]);
  const isWrite = method !== "GET" && !readOnlyPost.has(cleanPath);
                  
  if (isWrite) {
    alert("This action is unavailable in the GitHub Pages demo. Run MonkeyZoo Studio locally to modify production data.");
    throw {
      "ok": false,
      "demo_mode": true,
      "error": "Local backend required"
    };
  }

  if (cleanPath === "/api/runtime-capabilities") {
    return {schema_version:"1.0", runtime:"static-preview", capability:null, writable:false};
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

  if (cleanPath === "/api/locations" || cleanPath === "/api/props" || cleanPath === "/api/canon-catalog/summary") {
    const response = await fetch("./static/canon-catalog.json");
    const catalog = await response.json();
    if (cleanPath === "/api/locations") return catalog.locations || [];
    if (cleanPath === "/api/props") return catalog.props || [];
    return catalog.summary || {};
  }

  if (cleanPath === "/api/project-direction") {
    const response = await fetch("./static/project-direction.json");
    return response.json();
  }

  if (cleanPath === "/api/expressions") {
    const response = await fetch("./static/canon-catalog.json");
    const catalog = await response.json();
    return catalog.expressions || [];
  }

  if (cleanPath.startsWith("/api/expressions/")) {
    const slug = decodeURIComponent(cleanPath.slice("/api/expressions/".length));
    const response = await fetch("./static/canon-catalog.json");
    const catalog = await response.json();
    const item = (catalog.expressions || []).find(e => e.slug === slug);
    if (!item) return { error: "Expression set unavailable", slug };
    return item;
  }

  if (cleanPath.startsWith("/api/locations/")) {
    const id = decodeURIComponent(cleanPath.split("/")[3] || "");
    const response = await fetch("./static/canon-catalog.json");
    const catalog = await response.json();
    const summary = (catalog.locations || []).find(item => item.location_id === id);
    if (!summary) return {error:"Location unavailable"};
    return {summary, bible_markdown:`# ${summary.display_name || id}\n\n${summary.season_role || ""}\n`, has_primary_image:!!summary.has_primary_image};
  }

  if (cleanPath.startsWith("/api/props/")) {
    const id = decodeURIComponent(cleanPath.split("/")[3] || "");
    const response = await fetch("./static/canon-catalog.json");
    const catalog = await response.json();
    const summary = (catalog.props || []).find(item => item.prop_id === id);
    if (!summary) return {error:"Prop unavailable"};
    return {summary, bible_markdown:`# ${summary.display_name || id}\n\n${summary.notes || ""}\n`, has_primary_image:!!summary.has_primary_image};
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
    if (parts[4] === "story") return issue?.story || {error:"Story snapshot unavailable", outlines:[], scripts:[]};
    if (parts[4] === "layout") return issue?.layout || {error:"Layout snapshot unavailable", variants:[]};
    if (parts[4] === "art-prompts") return issue?.art_prompts || {error:"Art Prompt Pack snapshot unavailable", variants:[], canonical_pack_exists:false, plan:{exists:false}};
    if (parts[4] === "art-queue") return issue?.art_queue || {error:"Art Queue snapshot unavailable", queue:{items:[]}};
    if (parts[4] === "qa") return issue?.qa || {error:"QA snapshot unavailable", evidence:{panels:[],blockers:[]}, reviews:[]};
    if (parts[4] === "release") return issue?.release || {error:"Release snapshot unavailable", evidence:{files:[],blockers:[],archive:{path:"05_RELEASE_ARCHIVE",exists:false,publication_files:[]}}, approval_current:false, release_ready:false, publication_ready:false};
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
  const canonical = characters.find(item => item.character_id === cid);
  if (canonical) return {
    summary: canonical,
    detail: {identification: {
      current_display_name: canonical.display_name,
      series_name: canonical.series_name,
      personal_name: canonical.personal_name,
      naming_status: canonical.naming_status
    }, visual_canon: {primary_reference_image: canonical.primary_image}, history: []},
    traits: []
  };
  return {
    summary: {character_id:cid, display_name:`Unresolved character (${cid})`, series_name:"Unresolved character", personal_name:null, naming_status:"unresolved", primary_image:null},
    detail: {identification:{current_display_name:`Unresolved character (${cid})`, naming_status:"unresolved"}, visual_canon:{primary_reference_image:null}, history:[]},
    traits: [], unresolved:true
  };
}

function getMockStoryPreview(setup) {
  const castIds = (setup.characters || []).map(c => c.character_id);
  const unresolved = castIds.filter(id => getMockCharacterDetail(id).unresolved);
  
  return {
    "packet": {
      "selected_cast": castIds.map(id => {
        const detail = getMockCharacterDetail(id);
        return {
          "character_id": id,
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
    "warnings": unresolved.map(id => `Unresolved character ID: ${id}`),
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
      $("statusBackend").textContent = canMutate() ? "Trusted writable local runtime" : "Read-only static preview";
      $("statusBackend").className = `status-value ${canMutate() ? "connected" : "disconnected"}`;
    }
    if ($("sidebarStatusIndicator")) {
      $("sidebarStatusIndicator").className = `status-indicator ${canMutate() ? "online" : "offline"}`;
    }
    if ($("sidebarStatusText")) {
      $("sidebarStatusText").textContent = canMutate() ? "Writable local runtime" : "Read-only static preview";
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
      submitButton.disabled = !canMutate();
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
  $("undoBtn").disabled = !canMutate();
  
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
      projectMap: "viewProjectMap",
      characters: "viewCharacters",
      locations: "viewLocations",
      props: "viewProps",
      expressions: "viewExpressions",
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

let catalogExpressions = [];
let selectedExpressionSlug = null;

function setupCanonCatalogs() {
  $("locationFilter")?.addEventListener("change", () => renderLocationsList());
  $("propFilter")?.addEventListener("change", () => renderPropsList());
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const view = btn.getAttribute("data-view");
      if ((view === "locations" || view === "props") && !catalogLocations.length) loadCanonCatalogs();
      if (view === "expressions" && !catalogExpressions.length) loadExpressionCatalog();
      if (view === "projectMap" && !projectDirectionData) loadProjectDirection();
    });
  });
}

let projectDirectionData = null;

function setupProjectMap() {
  $("projectMapStatusFilter")?.addEventListener("change", () => renderProjectMap());
  $("projectMapTrackFilter")?.addEventListener("change", () => renderProjectMap());
  $("projectMapRefresh")?.addEventListener("click", () => loadProjectDirection(true));
}

async function loadProjectDirection(force = false) {
  if (projectDirectionData && !force) {
    renderProjectMap();
    return;
  }
  if ($("projectMapStatus")) $("projectMapStatus").textContent = "Loading project direction…";
  try {
    projectDirectionData = await api("/api/project-direction");
    renderProjectMap();
  } catch (err) {
    if ($("projectMapStatus")) {
      $("projectMapStatus").textContent = err.message || "Project direction unavailable";
    }
  }
}

function renderProjectMap() {
  const data = projectDirectionData;
  if (!data || !$("projectMapTracks")) return;
  const statusFilter = $("projectMapStatusFilter")?.value || "all";
  const trackFilter = $("projectMapTrackFilter")?.value || "all";
  const counts = data.task_counts || {};

  if ($("projectMapTrackFilter") && $("projectMapTrackFilter").options.length <= 1) {
    for (const track of data.tracks || []) {
      const opt = document.createElement("option");
      opt.value = track.id;
      opt.textContent = track.title;
      $("projectMapTrackFilter").appendChild(opt);
    }
  }

  if ($("projectMapSummary")) {
    $("projectMapSummary").innerHTML = [
      ["Total tasks", counts.total || 0],
      ["Done", counts.done || 0],
      ["Active", counts.active || 0],
      ["Next", counts.next || 0],
      ["Later", counts.later || 0],
      ["Blocked", counts.blocked || 0]
    ].map(([k, v]) => `<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
  }

  if ($("projectMapNorthStar")) {
    $("projectMapNorthStar").innerHTML = `
      <h3>${escapeHtml(data.title || "Project Direction")}</h3>
      <p class="project-map-subtitle">${escapeHtml(data.subtitle || "")}</p>
      <p><strong>North star:</strong> ${escapeHtml(data.north_star || "")}</p>
      <ul class="project-map-howto">${(data.how_to_use_this_map || []).map(line => `<li>${escapeHtml(line)}</li>`).join("")}</ul>
      <p class="project-map-meta">Updated ${escapeHtml(data.updated || "—")} · Source <code>${escapeHtml(data.source_path || "00_SYSTEM/project_direction.json")}</code></p>`;
  }

  const mode = data.current_mode || {};
  if ($("projectMapMode")) {
    $("projectMapMode").innerHTML = `
      <h4>Current mode</h4>
      <div class="project-map-mode-card">
        <span class="status-pill status-${escapeHtml(mode.status || "active")}">${escapeHtml(mode.phase || "—")}</span>
        <p>${escapeHtml(mode.summary || "")}</p>
        <p><strong>Start:</strong> <code>${escapeHtml(mode.start_command || "")}</code> → <code>${escapeHtml(mode.studio_url || "")}</code></p>
      </div>`;
  }

  if ($("projectMapRecommended")) {
    const rec = data.recommended_tasks || data.recommended_order || [];
    const items = Array.isArray(rec) && rec.length && typeof rec[0] === "object"
      ? rec
      : (data.recommended_order || []).map(id => ({id, title: id}));
    $("projectMapRecommended").innerHTML = `
      <h4>Recommended order</h4>
      <ol class="project-map-rec-list">${items.map((t, i) => `
        <li><span class="rec-index">${i + 1}</span>
          <strong>${escapeHtml(t.title || t.id)}</strong>
          <span class="task-status badge-${escapeHtml(t.status || "next")}">${escapeHtml(t.status || "")}</span>
          <span class="muted">${escapeHtml(t.track_title || "")}</span>
        </li>`).join("")}</ol>`;
  }

  if ($("projectMapPhases")) {
    $("projectMapPhases").innerHTML = `
      <h4>Hosting / ship phases</h4>
      <div class="project-map-phase-grid">${(data.phases || []).map(p => `
        <article class="project-map-phase status-${escapeHtml(p.status || "later")}">
          <header><strong>${escapeHtml(p.name)}</strong>
          <span class="task-status badge-${escapeHtml(p.status || "later")}">${escapeHtml(p.status || "")}</span></header>
          <p>${escapeHtml(p.goal || "")}</p>
          <p class="project-map-instructions">${escapeHtml(p.instructions || "")}</p>
        </article>`).join("")}</div>`;
  }

  if ($("projectMapPipeline")) {
    $("projectMapPipeline").innerHTML = `
      <h4>Issue production pipeline</h4>
      <ol class="project-map-pipeline-list">${(data.pipeline_stages || []).map(s => `
        <li><strong>${escapeHtml(s.label || s.stage)}</strong>
          <span>${escapeHtml(s.evidence || "")}</span>
          <em>${s.approval ? "Owner approval" : "No approval gate"}</em>
        </li>`).join("")}</ol>`;
  }

  if ($("projectMapTracks")) {
    const tracks = (data.tracks || []).filter(t => trackFilter === "all" || t.id === trackFilter);
    $("projectMapTracks").innerHTML = tracks.map(track => {
      const tasks = (track.tasks || []).filter(t => statusFilter === "all" || t.status === statusFilter);
      if (!tasks.length && statusFilter !== "all") return "";
      return `<section class="project-map-track">
        <h4>${escapeHtml(track.title || track.id)}</h4>
        <div class="project-map-task-list">${tasks.map(task => `
          <details class="project-map-task status-${escapeHtml(task.status || "later")}" id="task-${escapeHtml(task.id || "")}">
            <summary>
              <span class="task-status badge-${escapeHtml(task.status || "later")}">${escapeHtml(task.status || "")}</span>
              <span class="task-priority">${escapeHtml(task.priority || "")}</span>
              <strong>${escapeHtml(task.title || task.id)}</strong>
            </summary>
            <div class="project-map-task-body">
              <p class="project-map-instructions">${escapeHtml(task.instructions || "")}</p>
              ${(task.docs && task.docs.length) ? `<p><strong>Docs:</strong> ${task.docs.map(d => `<code>${escapeHtml(d)}</code>`).join(" · ")}</p>` : ""}
              <p class="muted">Task id: <code>${escapeHtml(task.id || "")}</code></p>
            </div>
          </details>`).join("") || "<p class=\"workspace-help\">No tasks match this filter.</p>"}
      </section>`;
    }).join("") || "<p class=\"workspace-help\">No tracks match this filter.</p>";
  }

  if ($("projectMapLinks")) {
    $("projectMapLinks").innerHTML = `
      <h4>Quick links (repo paths)</h4>
      <ul>${(data.quick_links || []).map(l => `<li><strong>${escapeHtml(l.label)}</strong> — <code>${escapeHtml(l.path)}</code></li>`).join("")}</ul>`;
  }

  if ($("projectMapStatus")) {
    $("projectMapStatus").textContent = `${counts.total || 0} tasks · ${counts.done || 0} done · ${counts.next || 0} next · mode: ${mode.phase || "—"}`;
  }
}

function mediaUrl(url) {
  if (!url) return "";
  return String(url).split("/").map(encodeURIComponent).join("/").replace(/%2F/gi, "/");
}

async function loadCanonCatalogs() {
  try {
    const [locations, props, summary] = await Promise.all([
      api("/api/locations"),
      api("/api/props"),
      api("/api/canon-catalog/summary")
    ]);
    catalogLocations = Array.isArray(locations) ? locations : [];
    catalogProps = Array.isArray(props) ? props : [];
    if ($("locationsSummary")) {
      $("locationsSummary").innerHTML = [
        ["Locations", summary.locations_count || catalogLocations.length],
        ["With primary", summary.locations_with_primary || 0],
        ["Proposed", summary.locations_proposed || 0],
        ["Season", summary.season || "—"]
      ].map(([k, v]) => `<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
    }
    if ($("propsSummary")) {
      $("propsSummary").innerHTML = [
        ["Props", summary.props_count || catalogProps.length],
        ["With primary", summary.props_with_primary || 0],
        ["Proposed", summary.props_proposed || 0],
        ["Season", summary.season || "—"]
      ].map(([k, v]) => `<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
    }
    if ($("locationsStatus")) $("locationsStatus").textContent = `${catalogLocations.length} locations loaded from approved canon.`;
    if ($("propsStatus")) $("propsStatus").textContent = `${catalogProps.length} props loaded from approved canon.`;
    renderLocationsList();
    renderPropsList();
  } catch (err) {
    if ($("locationsStatus")) $("locationsStatus").textContent = err.message || "Locations unavailable";
    if ($("propsStatus")) $("propsStatus").textContent = err.message || "Props unavailable";
  }
}

async function loadExpressionCatalog() {
  try {
    const [sets, summary] = await Promise.all([
      api("/api/expressions"),
      api("/api/canon-catalog/summary")
    ]);
    catalogExpressions = Array.isArray(sets) ? sets : [];
    if ($("expressionsSummary")) {
      $("expressionsSummary").innerHTML = [
        ["Sets", summary.expression_sets_count || catalogExpressions.length],
        ["Images", summary.expression_images_count || 0]
      ].map(([k, v]) => `<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
    }
    if ($("expressionsStatus")) {
      $("expressionsStatus").textContent = catalogExpressions.length
        ? `${catalogExpressions.length} expression sets loaded from approved_expressions.`
        : "No local expression sets found (folder optional; owner-managed).";
    }
    renderExpressionsList();
  } catch (err) {
    if ($("expressionsStatus")) $("expressionsStatus").textContent = err.message || "Expressions unavailable";
  }
}

function renderLocationsList() {
  if (!$("locationsList")) return;
  const filter = $("locationFilter")?.value || "all";
  const rows = catalogLocations.filter(item => filter === "all" || item.status === filter);
  $("locationsList").innerHTML = rows.length
    ? rows.map(item => {
        const active = item.location_id === selectedLocationId ? "active" : "";
        const img = item.has_primary_image ? " · image" : " · no image";
        return `<button type="button" class="catalog-row ${active}" data-location-id="${escapeHtml(item.location_id)}">
          <strong>${escapeHtml(item.display_name || item.location_id)}</strong>
          <small>${escapeHtml(item.location_id)} · ${escapeHtml(item.status || "unknown")}${img}</small>
          <span>${escapeHtml(item.month || item.first_issue || "world")}</span>
        </button>`;
      }).join("")
    : "<p class=\"workspace-help\">No locations match this filter.</p>";
  $("locationsList").querySelectorAll("[data-location-id]").forEach(btn => {
    btn.addEventListener("click", () => openLocationDetail(btn.dataset.locationId));
  });
}

function renderPropsList() {
  if (!$("propsList")) return;
  const filter = $("propFilter")?.value || "all";
  const rows = catalogProps.filter(item => filter === "all" || item.status === filter);
  $("propsList").innerHTML = rows.length
    ? rows.map(item => {
        const active = item.prop_id === selectedPropId ? "active" : "";
        const img = item.has_primary_image ? " · image" : " · no image";
        return `<button type="button" class="catalog-row ${active}" data-prop-id="${escapeHtml(item.prop_id)}">
          <strong>${escapeHtml(item.display_name || item.prop_id)}</strong>
          <small>${escapeHtml(item.prop_id)} · ${escapeHtml(item.category || "prop")} · ${escapeHtml(item.status || "unknown")}${img}</small>
          <span>${escapeHtml(item.first_issue || "world")}</span>
        </button>`;
      }).join("")
    : "<p class=\"workspace-help\">No props match this filter.</p>";
  $("propsList").querySelectorAll("[data-prop-id]").forEach(btn => {
    btn.addEventListener("click", () => openPropDetail(btn.dataset.propId));
  });
}

function renderExpressionsList() {
  if (!$("expressionsList")) return;
  $("expressionsList").innerHTML = catalogExpressions.length
    ? catalogExpressions.map(item => {
        const active = item.slug === selectedExpressionSlug ? "active" : "";
        const thumb = item.base_image_url
          ? `<img class="catalog-row-thumb" src="${escapeHtml(mediaUrl(item.base_image_url))}" alt="" loading="lazy">`
          : "";
        // data-slug holds the exact slug; avoid dataset camelCase issues with spaces
        return `<button type="button" class="catalog-row catalog-row-with-thumb ${active}" data-expression-slug="${escapeHtml(item.slug)}">
          ${thumb}
          <span class="catalog-row-text">
            <strong>${escapeHtml(item.display_name || item.slug)}</strong>
            <small>${escapeHtml(item.slug)} · ${item.image_count || 0} plates</small>
            <span>${item.static_media ? "static media" : "local sheet"}</span>
          </span>
        </button>`;
      }).join("")
    : "<p class=\"workspace-help\">No expression sets available in this build.</p>";
  $("expressionsList").querySelectorAll("[data-expression-slug]").forEach(btn => {
    btn.addEventListener("click", () => openExpressionDetail(btn.getAttribute("data-expression-slug") || ""));
  });
}

function primaryImageBlock(url, label) {
  if (!url) return `<p><strong>Primary image:</strong> Not yet filed</p>`;
  return `<p><strong>Primary image:</strong> Present</p>
    <figure class="catalog-primary-figure">
      <img class="catalog-primary-image" src="${escapeHtml(mediaUrl(url))}" alt="${escapeHtml(label || "Primary reference")}" loading="lazy">
    </figure>`;
}

async function openLocationDetail(locationId) {
  selectedLocationId = locationId;
  renderLocationsList();
  if (!$("locationDetail")) return;
  $("locationDetail").innerHTML = "<p class=\"workspace-help\">Loading…</p>";
  try {
    const data = await api(`/api/locations/${encodeURIComponent(locationId)}`);
    const s = data.summary || {};
    $("locationDetail").innerHTML = `
      <header><h4>${escapeHtml(s.display_name || locationId)}</h4>
      <p><code>${escapeHtml(s.location_id || locationId)}</code> · ${escapeHtml(s.status || "")}</p></header>
      <p><strong>Season role:</strong> ${escapeHtml(s.season_role || "—")}</p>
      <p><strong>Folder:</strong> <code>${escapeHtml(s.folder || "")}</code></p>
      ${primaryImageBlock(data.primary_image_url || s.primary_image_url, s.display_name)}
      <pre class="catalog-bible">${escapeHtml(data.bible_markdown || "No bible.md found.")}</pre>`;
  } catch (err) {
    $("locationDetail").innerHTML = `<p class="workspace-help">${escapeHtml(err.message || "Unavailable")}</p>`;
  }
}

async function openPropDetail(propId) {
  selectedPropId = propId;
  renderPropsList();
  if (!$("propDetail")) return;
  $("propDetail").innerHTML = "<p class=\"workspace-help\">Loading…</p>";
  try {
    const data = await api(`/api/props/${encodeURIComponent(propId)}`);
    const s = data.summary || {};
    $("propDetail").innerHTML = `
      <header><h4>${escapeHtml(s.display_name || propId)}</h4>
      <p><code>${escapeHtml(s.prop_id || propId)}</code> · ${escapeHtml(s.category || "prop")} · ${escapeHtml(s.status || "")}</p></header>
      <p><strong>Notes:</strong> ${escapeHtml(s.notes || "—")}</p>
      <p><strong>Folder:</strong> <code>${escapeHtml(s.folder || "")}</code></p>
      ${primaryImageBlock(data.primary_image_url || s.primary_image_url, s.display_name)}
      <pre class="catalog-bible">${escapeHtml(data.bible_markdown || "No bible.md found.")}</pre>`;
  } catch (err) {
    $("propDetail").innerHTML = `<p class="workspace-help">${escapeHtml(err.message || "Unavailable")}</p>`;
  }
}

async function openExpressionDetail(slug) {
  selectedExpressionSlug = slug;
  renderExpressionsList();
  if (!$("expressionDetail")) return;
  $("expressionDetail").innerHTML = "<p class=\"workspace-help\">Loading…</p>";
  try {
    let data = null;
    try {
      data = await api(`/api/expressions/${encodeURIComponent(slug)}`);
    } catch (_err) {
      data = null;
    }
    // Static/demo fallback: use list payload when detail endpoint is sparse
    if (!data || data.error || !Array.isArray(data.images) || !data.images.length) {
      const cached = catalogExpressions.find(item => item.slug === slug);
      if (cached) data = { ...cached, ...(data && !data.error ? data : {}) };
    }
    if (!data || data.error) {
      throw new Error((data && data.error) || "Expression set unavailable");
    }
    const images = Array.isArray(data.images) ? data.images : [];
    $("expressionDetail").innerHTML = `
      <header><h4>${escapeHtml(data.display_name || slug)}</h4>
      <p><code>${escapeHtml(data.slug || slug)}</code> · ${images.length || data.image_count || 0} plates</p></header>
      <p><strong>Folder:</strong> <code>${escapeHtml(data.folder || "")}</code></p>
      ${images.length ? `<div class="expression-grid">
        ${images.map(img => `<figure class="expression-tile">
          <img src="${escapeHtml(mediaUrl(img.url))}" alt="${escapeHtml(img.filename)}" loading="lazy">
          <figcaption>${escapeHtml(img.filename)}</figcaption>
        </figure>`).join("")}
      </div>` : `<p class="workspace-help">No plate previews in this static build. Open local Studio for full expression files under <code>approved_expressions</code>.</p>`}`;
  } catch (err) {
    $("expressionDetail").innerHTML = `<p class="workspace-help">${escapeHtml(err.message || "Unavailable")}</p>`;
  }
}

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

async function initializeApplication() {
  enforceMutationCapability();
  await resolveRuntimeCapability();
  setupIssueCreation();
  setupProductionDashboard();
  setupProductionStoryWorkspace();
  setupLayoutWorkspace();
  setupArtQueue();
  setupQAWorkspace();
  setupReleaseWorkspace();
  setupCanonCatalogs();
  setupProjectMap();
  await loadCharacters();
  await loadCanonCatalogs();
  enforceMutationCapability();
}
initializeApplication();

let activeProductionIssue = null;
let activeLayout = null;
let activeArtQueue = null;
let activeArtPrompts = null;
let artUploadPanel = null;
let activeQA = null;
let activeRelease = null;
let catalogLocations = [];
let catalogProps = [];
let selectedLocationId = null;
let selectedPropId = null;

function renderIssuesList(issues) {
  const selector = $("storyProductionIssue");
  if (selector) selector.innerHTML = '<option value="">Choose an issue</option>' + issues.filter(issue => !issue.degraded).map(issue => `<option value="${escapeHtml(issue.issue_id)}">${escapeHtml(issue.issue_id)} — ${escapeHtml(issue.title)}</option>`).join("");
  const layoutSelect = $("layoutIssueSelect");
  if (layoutSelect) layoutSelect.innerHTML = '<option value="">Choose an issue</option>' + issues.filter(i=>!i.degraded).map(i=>`<option value="${escapeHtml(i.issue_id)}">${escapeHtml(i.issue_id)} — ${escapeHtml(i.title)}</option>`).join("");
  const artSelect=$("artQueueIssue"); if(artSelect)artSelect.innerHTML='<option value="">Choose an issue</option>'+issues.filter(i=>!i.degraded).map(i=>`<option value="${escapeHtml(i.issue_id)}">${escapeHtml(i.issue_id)} — ${escapeHtml(i.title)}</option>`).join("");
  const qaSelect=$("qaIssueSelect");if(qaSelect)qaSelect.innerHTML='<option value="">Choose an issue</option>'+issues.filter(i=>!i.degraded).map(i=>`<option value="${escapeHtml(i.issue_id)}">${escapeHtml(i.issue_id)} — ${escapeHtml(i.title)}</option>`).join("");
  const releaseSelect=$("releaseIssueSelect");if(releaseSelect)releaseSelect.innerHTML='<option value="">Choose an issue</option>'+issues.filter(i=>!i.degraded).map(i=>`<option value="${escapeHtml(i.issue_id)}">${escapeHtml(i.issue_id)} — ${escapeHtml(i.title)}</option>`).join("");
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

function setupProductionStoryWorkspace() {
  $("storyProductionIssue")?.addEventListener("change", event => loadProductionStory(event.target.value));
  $("outlinePromptBtn")?.addEventListener("click", () => exportStoryPrompt("outline"));
  $("scriptPromptBtn")?.addEventListener("click", () => exportStoryPrompt("script"));
  $("outlineImportBtn")?.addEventListener("click", () => openStoryImport("outline"));
  $("scriptImportBtn")?.addEventListener("click", () => openStoryImport("script"));
  $("storyImportSubmit")?.addEventListener("click", importStoryVariant);
  $("closeVariantDialog")?.addEventListener("click", () => $("variantDialog").close());
}

async function loadProductionStory(issueId) {
  if (!issueId) return;
  try { productionStory = await api(`/api/issues/${encodeURIComponent(issueId)}/story`); renderProductionStory(); }
  catch (error) { $("storyProductionStatus").textContent = error.message; }
}

function renderProductionStory() {
  const staticMode = !canMutate();
  const {issue, workflow, canon} = productionStory;
  $("storyProductionStatus").textContent = `Active stage: ${workflow.current_stage.label}. ${workflow.blockers.join(" ") || "Stage evidence is ready."}`;
  $("storyIssueContext").innerHTML = [["Issue",issue.issue_id],["Title",issue.title],["Period",issue.month],["Primary",issue.primary_character],["Guest",issue.guest_character || "None"],["Workflow",workflow.current_stage.label],["Outline",productionStory.outline_approval ? "Approved" : "Not approved"],["Script",productionStory.script_approval ? "Approved" : "Not approved"],["Drafts",`${productionStory.draft_counts.outlines} outline · ${productionStory.draft_counts.scripts} script`]].map(([k,v])=>`<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
  $("storyCanonContext").innerHTML = `<p><strong>Snapshot:</strong> ${escapeHtml(canon.snapshot_hash)} · ${canon.warnings.length ? "Warnings present" : "Current"}</p><div class="canon-character-strip">${canon.characters.map(c=>`<article><strong>${escapeHtml(c.display_name || c.character_id)}</strong><small>${escapeHtml(c.character_id)} · ${escapeHtml(c.role)} · ${escapeHtml(c.canon_status || "status unavailable")}</small></article>`).join("")}</div><h5>Warnings</h5><ul>${canon.warnings.map(w=>`<li>${escapeHtml(w)}</li>`).join("") || "<li>None detected</li>"}</ul><h5>Excluded material</h5><ul>${canon.excluded.map(x=>`<li>${escapeHtml(x.source)} — ${escapeHtml(x.reason)}</li>`).join("") || "<li>None</li>"}</ul>`;
  renderStoryVariants("outline", productionStory.outlines, staticMode);
  renderStoryVariants("script", productionStory.scripts, staticMode);
  ["outlinePromptBtn","outlineImportBtn","scriptPromptBtn","scriptImportBtn"].forEach(id => { $(id).disabled = staticMode; $(id).title = staticMode ? "Local backend required" : ""; });
}

function renderStoryVariants(kind, items, staticMode) {
  $(`${kind}Variants`).innerHTML = items.length ? items.map(v=>`<article class="variant-card ${v.approval_current ? "approved" : ""}"><header><strong>${escapeHtml(v.variant_id)}</strong><span>${escapeHtml(v.validation.status)}</span></header><p>${escapeHtml(v.provider)} · ${escapeHtml(v.model)} · ${escapeHtml(v.created_at)}</p><p>${v.canon_stale ? "Canon changed since generation" : "Canon snapshot current"}${v.approval_current ? " · Approved" : ""}</p><div><button type="button" data-view-variant="${escapeHtml(v.variant_id)}">Open full view</button><button type="button" data-approve-variant="${escapeHtml(v.variant_id)}" ${staticMode || v.approval ? "disabled" : ""}>Approve</button><button type="button" data-promote-variant="${escapeHtml(v.variant_id)}" ${staticMode || !v.approval_current ? "disabled" : ""}>Promote</button></div></article>`).join("") : "<p>No variants yet.</p>";
  $(`${kind}Variants`).querySelectorAll("[data-view-variant]").forEach(b=>b.addEventListener("click",()=>viewStoryVariant(kind,b.dataset.viewVariant)));
  $(`${kind}Variants`).querySelectorAll("[data-approve-variant]").forEach(b=>b.addEventListener("click",()=>storyVariantAction(kind,b.dataset.approveVariant,"approve")));
  $(`${kind}Variants`).querySelectorAll("[data-promote-variant]").forEach(b=>b.addEventListener("click",()=>storyVariantAction(kind,b.dataset.promoteVariant,"promote")));
}

function openStoryImport(kind) { storyImportKind=kind; $("storyImportTitle").textContent=`Import ${kind} Markdown`; $("storyImportContent").value=""; $("storyImportDialog").showModal(); }
async function importStoryVariant() { try { await api(`/api/issues/${encodeURIComponent(productionStory.issue.issue_id)}/story/${storyImportKind}s/import`,{method:"POST",body:JSON.stringify({content:$("storyImportContent").value,provider:$("storyImportProvider").value})}); $("storyImportDialog").close(); await loadProductionStory(productionStory.issue.issue_id); } catch(e){ $("storyProductionStatus").textContent=e.message; } }
async function exportStoryPrompt(kind) { try { const data=await api(`/api/issues/${encodeURIComponent(productionStory.issue.issue_id)}/story/${kind}s/prompt`,{method:"POST",body:"{}"}); $("variantDialogTitle").textContent=`${kind} manual prompt package`; $("variantDialogContent").textContent=data.prompt; $("variantDialog").showModal(); } catch(e){ $("storyProductionStatus").textContent=e.message; } }
function viewStoryVariant(kind,id) { const variant=productionStory[`${kind}s`].find(v=>v.variant_id===id); $("variantDialogTitle").textContent=id; $("variantDialogContent").textContent=variant.content; $("variantDialog").showModal(); }
async function storyVariantAction(kind,id,action) {
  try {
    // create_issue writes stub outline/script files; promote must replace them intentionally.
    const replace = action === "promote" && Boolean(productionStory?.existing_files?.[`issue_${kind}.md`]);
    await api(`/api/issues/${encodeURIComponent(productionStory.issue.issue_id)}/story/${kind}s/${encodeURIComponent(id)}/${action}`,{
      method:"POST",
      body:JSON.stringify(action==="promote"?{replace}:{note:"Approved in The Banana Lab"})
    });
    await loadProductionStory(productionStory.issue.issue_id);
  } catch(e){ $("storyProductionStatus").textContent=e.message; }
}

function setupLayoutWorkspace(){
  $("layoutIssueSelect")?.addEventListener("change",e=>loadLayout(e.target.value));
  $("createPlanVariant")?.addEventListener("click",()=>layoutAction("variants"));
}
async function loadLayout(issueId){if(!issueId)return;try{activeLayout=await api(`/api/issues/${encodeURIComponent(issueId)}/layout`);renderLayout()}catch(e){$("layoutStatus").textContent=e.message}}
function renderLayout(){
  const staticMode=!canMutate(),w=activeLayout.workflow;
  $("layoutStatus").textContent=`Active stage: ${w.current_stage.label}. ${w.blockers.join(" ")||"Stage evidence is ready."}`;
  $("layoutSummary").innerHTML=[["Issue",activeLayout.issue_id],["Stage",w.current_stage.label],["Script",activeLayout.script.exists?"Loaded":"Missing"],["Canonical plan",activeLayout.canonical_plan_exists?"Exists":"Not promoted"],["Variants",activeLayout.variants.length]].map(([k,v])=>`<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
  $("createPlanVariant").disabled=staticMode||w.active_stage!=="page_plan"; $("createPlanVariant").title=staticMode?"Local backend required":"";
  $("layoutVariants").innerHTML=activeLayout.variants.length?activeLayout.variants.map(v=>`<article class="layout-variant"><header><strong>${escapeHtml(v.variant_id)}</strong><span>${escapeHtml(v.validation.status)}</span></header><p>${v.script_stale?"Canonical script changed":"Script current"} · ${v.plan.page_count} pages</p><div class="page-strip">${v.plan.pages.map(p=>`<button type="button" aria-label="Page ${p.page_number}, ${p.panels.length} panels">Page ${p.page_number}<small>${p.panels.length} panels</small></button>`).join("")}</div>${v.plan.pages.map(p=>`<details><summary>Page ${p.page_number}: ${escapeHtml(p.page_purpose)}</summary>${p.panels.map(panel=>`<article class="panel-detail"><strong>${escapeHtml(panel.panel_id)}</strong><span>${escapeHtml(panel.location)} · ${escapeHtml(panel.characters.join(", ")||"No characters")}</span><p>${escapeHtml(panel.action)}</p><small>Dialogue: ${escapeHtml(panel.dialogue||"None")} · Caption: ${escapeHtml(panel.caption||"None")} · Props: ${escapeHtml((panel._props||[]).join(", ")||"None")}</small><p>Continuity: ${escapeHtml(panel.continuity_notes||"None")}</p></article>`).join("")}</details>`).join("")}<ul>${v.validation.findings.map(f=>`<li>${escapeHtml(f.level)}: ${escapeHtml(f.message)}</li>`).join("")||"<li>Schema and numbering valid</li>"}</ul><div><button data-layout-approve="${escapeHtml(v.variant_id)}" ${staticMode||v.approval?"disabled":""}>Approve</button><button data-layout-promote="${escapeHtml(v.variant_id)}" ${staticMode||!v.approval_current?"disabled":""}>Promote</button></div></article>`).join(""):"<p>No plan variants yet.</p>";
  $("layoutVariants").querySelectorAll("[data-layout-approve]").forEach(b=>b.addEventListener("click",()=>layoutAction(`variants/${b.dataset.layoutApprove}/approve`)));
  $("layoutVariants").querySelectorAll("[data-layout-promote]").forEach(b=>b.addEventListener("click",()=>layoutAction(`variants/${b.dataset.layoutPromote}/promote`)));
}
async function layoutAction(path){
  try{
    const isPromote = path.includes("/promote");
    const body = isPromote && activeLayout?.canonical_plan_exists ? {replace:true} : {};
    await api(`/api/issues/${encodeURIComponent(activeLayout.issue_id)}/layout/${path}`,{method:"POST",body:JSON.stringify(body)});
    await loadLayout(activeLayout.issue_id);
  }catch(e){$("layoutStatus").textContent=e.message}
}

function setupArtQueue(){
  $("artQueueIssue")?.addEventListener("change",e=>{loadArtQueue(e.target.value);loadArtPrompts(e.target.value)});
  $("buildArtQueue")?.addEventListener("click",()=>artQueuePost("build"));
  $("createArtPromptPack")?.addEventListener("click",()=>artPromptPackAction("variants"));
  $("artAttemptFile")?.addEventListener("change",uploadArtAttempt);
}
async function loadArtQueue(issueId){if(!issueId)return;try{activeArtQueue=await api(`/api/issues/${encodeURIComponent(issueId)}/art-queue`);renderArtQueue()}catch(e){$("artQueueStatus").textContent=e.message}}
async function loadArtPrompts(issueId){
  if(!issueId)return;
  try{
    activeArtPrompts=await api(`/api/issues/${encodeURIComponent(issueId)}/art-prompts`);
    renderArtPrompts();
  }catch(e){
    if($("artPromptPackSummary")) $("artPromptPackSummary").innerHTML=`<div><span>Pack</span><strong>${escapeHtml(e.message)}</strong></div>`;
  }
}
function renderArtPrompts(){
  if(!activeArtPrompts||!$("artPromptPackSummary")) return;
  const staticMode=!canMutate();
  const w=activeArtPrompts.workflow||{active_stage:"",current_stage:{label:"Unknown"}};
  const variants=activeArtPrompts.variants||[];
  $("artPromptPackSummary").innerHTML=[
    ["Issue",activeArtPrompts.issue_id],
    ["Stage",w.current_stage?.label||w.active_stage||"Unknown"],
    ["Plan",activeArtPrompts.plan?.exists?"Present":"Missing"],
    ["Canonical pack",activeArtPrompts.canonical_pack_exists?"Promoted":"Not promoted"],
    ["Variants",variants.length]
  ].map(([k,v])=>`<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
  if($("createArtPromptPack")){
    $("createArtPromptPack").disabled=staticMode||w.active_stage!=="art_prompts";
    $("createArtPromptPack").title=staticMode?"Local backend required":(w.active_stage!=="art_prompts"?"Requires art_prompts stage":"");
  }
  if(!$("artPromptPackVariants")) return;
  $("artPromptPackVariants").innerHTML=variants.length?variants.map(v=>`<article class="layout-variant"><header><strong>${escapeHtml(v.variant_id)}</strong><span>${escapeHtml(v.validation?.status||"unknown")}</span></header><p>${v.plan_stale?"Page plan changed":"Plan current"} · ${v.pack?.panels?.length||0} panels · ${v.approval_current?"Approved":"Not approved"}</p><ul>${(v.validation?.findings||[]).slice(0,5).map(f=>`<li>${escapeHtml(f.level||"error")}: ${escapeHtml(f.message)}</li>`).join("")||"<li>Schema valid</li>"}</ul><div><button type="button" data-art-pack-approve="${escapeHtml(v.variant_id)}" ${staticMode||v.approval?"disabled":""}>Approve pack</button><button type="button" data-art-pack-promote="${escapeHtml(v.variant_id)}" ${staticMode||!v.approval_current?"disabled":""}>Promote pack</button></div></article>`).join(""):"<p>No art prompt pack variants yet. Build one when the workflow is on Art Prompt Pack.</p>";
  $("artPromptPackVariants").querySelectorAll("[data-art-pack-approve]").forEach(b=>b.addEventListener("click",()=>artPromptPackAction(`variants/${b.dataset.artPackApprove}/approve`)));
  $("artPromptPackVariants").querySelectorAll("[data-art-pack-promote]").forEach(b=>b.addEventListener("click",()=>artPromptPackAction(`variants/${b.dataset.artPackPromote}/promote`)));
}
async function artPromptPackAction(path){
  const issueId=activeArtPrompts?.issue_id||$("artQueueIssue")?.value;
  if(!issueId)return;
  try{
    const replace = path.endsWith("/promote") && Boolean(activeArtPrompts?.canonical_pack_exists);
    const body = path.endsWith("/promote")
      ? JSON.stringify({replace})
      : JSON.stringify({note:"Approved in The Banana Lab"});
    await api(`/api/issues/${encodeURIComponent(issueId)}/art-prompts/${path}`,{method:"POST",body});
    await loadArtPrompts(issueId);
    if(activeArtQueue?.issue_id===issueId) await loadArtQueue(issueId);
  }catch(e){
    if($("artQueueStatus")) $("artQueueStatus").textContent=e.message;
  }
}
function renderArtQueue(){
  const staticMode=!canMutate(),q=activeArtQueue.queue,w=activeArtQueue.workflow,items=q.items||[];
  $("artQueueStatus").textContent=q.error||`Active stage: ${w.current_stage.label}. ${w.blockers.join(" ")||"Queue evidence ready."}`;
  $("artQueueSummary").innerHTML=[["Issue",activeArtQueue.issue_id],["Stage",w.current_stage.label],["Panels",items.length],["Approved",items.filter(i=>i.status==="approved").length],["Missing",items.filter(i=>i.status!=="approved").length],["Provider","Manual prompt/import"]].map(([k,v])=>`<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
  $("buildArtQueue").disabled=staticMode||!["art_prompts","art_production"].includes(w.active_stage);$("buildArtQueue").title=staticMode?"Local backend required":"";
  $("artQueueItems").innerHTML=items.map(i=>`<article class="art-queue-item"><header><strong>${escapeHtml(i.panel_id)}</strong><span>${escapeHtml(i.status)}</span></header><p>${escapeHtml(i.location||"Location missing")} · ${escapeHtml(i.characters.join(", ")||"No characters")}</p><p>${escapeHtml(i.action||"Action missing")}</p><small>Props: ${escapeHtml((i.props||[]).join(", ")||"None")} · Attempts: ${i.attempt_count}</small><div class="reference-strip">${[...(i.references||[]).map(r=>({label:r.display_name||r.character_id,detail:r.error||"character",url:null})),...(i.location_ref?[({label:i.location_ref.display_name||i.location||"Location",detail:i.location_ref.error||"location",url:i.location_ref.primary_image_url})]:[]),...(i.prop_refs||[]).map(r=>({label:r.display_name||r.prop_id||"Prop",detail:r.error||"prop",url:r.primary_image_url}))].map(r=>`<span>${escapeHtml(r.label)} · ${escapeHtml(r.detail)}${r.url?` · <a href="${escapeHtml(mediaUrl(r.url))}" target="_blank" rel="noopener">ref</a>`:""}</span>`).join("")}</div><div class="attempt-list">${(i.attempts||[]).map(a=>`<span>${escapeHtml(a.attempt_id)} · ${escapeHtml(a.format)} ${a.width}×${a.height} · ${escapeHtml(a.status)} <button data-art-select="${escapeHtml(i.panel_id)}|${escapeHtml(a.attempt_id)}" ${staticMode||a.status==="rejected"||a.status==="archived"?"disabled":""}>Select</button><button data-art-reject="${escapeHtml(i.panel_id)}|${escapeHtml(a.attempt_id)}" ${staticMode||a.status==="preferred"?"disabled":""}>Reject</button></span>`).join("")}</div><div><button data-art-prompt="${escapeHtml(i.panel_id)}" ${staticMode?"disabled":""}>Export prompt</button><button data-art-import="${escapeHtml(i.panel_id)}" ${staticMode||w.active_stage!=="art_production"?"disabled":""}>Import image</button></div></article>`).join("")||"<p>No queue items. Build the queue after the art prompt pack is promoted, or when art production is active.</p>";
  $("artQueueItems").querySelectorAll("[data-art-prompt]").forEach(b=>b.addEventListener("click",()=>artQueuePost(`${b.dataset.artPrompt}/prompt`,true)));
  $("artQueueItems").querySelectorAll("[data-art-import]").forEach(b=>b.addEventListener("click",()=>{artUploadPanel=b.dataset.artImport;$("artAttemptFile").click()}));
  $("artQueueItems").querySelectorAll("[data-art-select]").forEach(b=>b.addEventListener("click",()=>artAttemptAction(b.dataset.artSelect,"select")));
  $("artQueueItems").querySelectorAll("[data-art-reject]").forEach(b=>b.addEventListener("click",()=>artAttemptAction(b.dataset.artReject,"status")));
}
async function artQueuePost(path,show=false){try{const data=await api(`/api/issues/${encodeURIComponent(activeArtQueue.issue_id)}/art-queue/${path}`,{method:"POST",body:"{}"});if(show){$("artifactTitle").textContent=`Prompt ${data.panel_id}`;$("artifactContent").textContent=JSON.stringify(data,null,2);$("artifactDialog").showModal()}await loadArtQueue(activeArtQueue.issue_id)}catch(e){$("artQueueStatus").textContent=e.message}}
async function uploadArtAttempt(){const file=$("artAttemptFile").files[0];if(!file||!artUploadPanel)return;const form=new FormData();form.append("image",file);form.append("provider","manual import");try{const response=await fetch(`/api/issues/${encodeURIComponent(activeArtQueue.issue_id)}/art-queue/${encodeURIComponent(artUploadPanel)}/attempts`,{method:"POST",body:form});const data=await response.json();if(!response.ok)throw new Error(data.error);await loadArtQueue(activeArtQueue.issue_id)}catch(e){$("artQueueStatus").textContent=e.message}finally{$("artAttemptFile").value=""}}
async function artAttemptAction(value,action){const [panel,attempt]=value.split("|");try{await api(`/api/issues/${encodeURIComponent(activeArtQueue.issue_id)}/art-queue/${encodeURIComponent(panel)}/attempts/${encodeURIComponent(attempt)}/${action}`,{method:"POST",body:action==="status"?JSON.stringify({status:"rejected"}):"{}"});await loadArtQueue(activeArtQueue.issue_id)}catch(e){$("artQueueStatus").textContent=e.message}}

function setupQAWorkspace(){$("qaIssueSelect")?.addEventListener("change",e=>loadQA(e.target.value));$("createQAReview")?.addEventListener("click",()=>qaPost("reviews",{}))}
async function loadQA(id){if(!id)return;try{activeQA=await api(`/api/issues/${encodeURIComponent(id)}/qa`);renderQA()}catch(e){$("qaStatus").textContent=e.message}}
function renderQA(){
 const staticMode=!canMutate(),e=activeQA.evidence,w=activeQA.workflow;
 $("qaStatus").textContent=e.blockers?.join(" ")||`Active stage: ${w.current_stage.label}. No automated evidence blockers.`;
 $("qaSummary").innerHTML=[["Issue",activeQA.issue_id],["Stage",w.current_stage.label],["Planned",e.planned_panel_count||0],["Selected",e.selected_panel_count||0],["Blockers",e.blockers?.length||0],["Reviews",activeQA.reviews.length]].map(([k,v])=>`<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
 $("createQAReview").disabled=staticMode||w.active_stage!=="qa";$("createQAReview").title=staticMode?"Local backend required":"";
 $("qaPanels").innerHTML=(e.panels||[]).map(p=>`<article class="qa-panel-row"><strong>${escapeHtml(p.panel_id)}</strong><span>${p.exists?`${escapeHtml(p.format)} · ${p.width}×${p.height}`:"Missing art"}</span><small>Characters: ${escapeHtml(p.characters.join(", ")||"Missing")} · Dialogue/caption: ${p.dialogue||p.caption?"Present":"None"} · Continuity: ${escapeHtml(p.continuity_notes||"Missing")}</small></article>`).join("");
 $("qaReviews").innerHTML=activeQA.reviews.map(r=>`<article class="qa-review"><header><strong>${escapeHtml(r.review_id)}</strong><span>${escapeHtml(r.verdict||"Draft")}${r.evidence_stale?" · Evidence changed":""}</span></header><p>${escapeHtml(r.owner_notes||"No owner notes")}</p><div><button data-qa-finalize="${escapeHtml(r.review_id)}|pass" ${staticMode||r.approval||r.evidence.blockers.length?"disabled":""}>Pass</button><button data-qa-finalize="${escapeHtml(r.review_id)}|hold" ${staticMode||r.approval?"disabled":""}>Hold</button><button data-qa-finalize="${escapeHtml(r.review_id)}|fail" ${staticMode||r.approval?"disabled":""}>Fail</button><button data-qa-promote="${escapeHtml(r.review_id)}" ${staticMode||!r.approval_current?"disabled":""}>Promote report</button></div></article>`).join("")||"<p>No QA reviews.</p>";
 $("qaReviews").querySelectorAll("[data-qa-finalize]").forEach(b=>b.addEventListener("click",()=>{const [id,verdict]=b.dataset.qaFinalize.split("|");qaPost(`reviews/${id}/finalize`,{verdict,notes:$("qaOwnerNotes").value,continuity_checks:$("qaContinuityNote").value?[$("qaContinuityNote").value]:[]})}));$("qaReviews").querySelectorAll("[data-qa-promote]").forEach(b=>b.addEventListener("click",()=>qaPost(`reviews/${b.dataset.qaPromote}/promote`,{})));
}
async function qaPost(path,body){
  try{
    const payload = {...(body||{})};
    if(path.includes("/promote") && payload.replace === undefined){
      // Existing owner qa_report.md stubs from issue creation require explicit replace.
      payload.replace = true;
    }
    await api(`/api/issues/${encodeURIComponent(activeQA.issue_id)}/qa/${path}`,{method:"POST",body:JSON.stringify(payload)});
    await loadQA(activeQA.issue_id);
  }catch(e){$("qaStatus").textContent=e.message}
}

function setupReleaseWorkspace(){
  $("releaseIssueSelect")?.addEventListener("change",e=>loadRelease(e.target.value));
  $("releaseManifest")?.addEventListener("click",()=>releasePost("manifest",{}));
  $("releaseApprove")?.addEventListener("click",()=>releasePost("approve",{note:$("releaseOwnerNote").value}));
  $("releasePromote")?.addEventListener("click",()=>releasePost("promote-manifest",{}));
  $("releasePublishArchive")?.addEventListener("click",()=>releasePost("publish-archive",{replace:false}));
}
async function loadRelease(id){if(!id)return;try{activeRelease=await api(`/api/issues/${encodeURIComponent(id)}/release`);renderRelease()}catch(e){$("releaseStatus").textContent=e.message}}
function renderRelease(){
 const staticMode=!canMutate(),e=activeRelease.evidence,w=activeRelease.workflow;
 $("releaseStatus").textContent=e.blockers.join(" ")||`Evidence complete. ${activeRelease.approval_current?"Owner approval current.":"Owner approval required."}`;
 $("releaseSummary").innerHTML=[["Issue",activeRelease.issue_id],["Stage",w.current_stage.label],["QA",e.qa_verdict],["Covers",e.covers.length],["PDFs",e.pdfs.length],["Packages",e.packages.length],["Release ready",activeRelease.release_ready?"Yes":"No"],["Published evidence",activeRelease.publication_ready?"Complete":"Incomplete"]].map(([k,v])=>`<div><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join("");
 const stageOK=["release","published"].includes(w.active_stage);
 const canPublish=stageOK&&activeRelease.approval_current&&!e.blockers.length;
 $("releaseManifest").disabled=staticMode||!stageOK;
 $("releaseApprove").disabled=staticMode||!stageOK||e.blockers.length>0||activeRelease.approval_current;
 $("releasePromote").disabled=staticMode||!activeRelease.approval_current;
 if($("releasePublishArchive")){
   $("releasePublishArchive").disabled=staticMode||!canPublish;
   $("releasePublishArchive").title=staticMode?"Local backend required":(canPublish?"":"Requires current approval and no blockers");
 }
 ["releaseManifest","releaseApprove","releasePromote"].forEach(id=>$(id).title=staticMode?"Local backend required":"");
 $("releaseEvidence").innerHTML=`<h4>Exact blockers</h4><ul>${e.blockers.map(x=>`<li>${escapeHtml(x)}</li>`).join("")||"<li>None</li>"}</ul><h4>CHIP-0015 metadata</h4><p>Format: ${escapeHtml(e.metadata.format||"Missing")} · Missing: ${escapeHtml(e.metadata.missing_fields.join(", ")||"None")} · Placeholders: ${escapeHtml(e.metadata.placeholders.join(", ")||"None")}</p><h4>File hash manifest</h4><div class="release-files">${e.files.map(f=>`<span>${escapeHtml(f.path)} · ${f.size} bytes · ${escapeHtml(f.sha256)}</span>`).join("")}</div><h4>Archive</h4><p>${escapeHtml(e.archive.path)} · ${e.archive.exists?"Exists":"Missing"} · ${escapeHtml(e.archive.publication_files.join(", ")||"No publication evidence")}</p><p class="workspace-help">Publish archive copies verified PDF/CBZ/ZIP and evidence into <code>05_RELEASE_ARCHIVE</code>. Then advance the workflow stage to Published.</p>`;
}
async function releasePost(path,body){
  try{
    const payload = {...(body||{})};
    if(path === "promote-manifest" && payload.replace === undefined) payload.replace = true;
    if(path === "publish-archive" && payload.replace === undefined) payload.replace = false;
    await api(`/api/issues/${encodeURIComponent(activeRelease.issue_id)}/release/${path}`,{method:"POST",body:JSON.stringify(payload)});
    await loadRelease(activeRelease.issue_id);
  }catch(e){$("releaseStatus").textContent=e.message}
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
  const staticMode = !canMutate();
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
