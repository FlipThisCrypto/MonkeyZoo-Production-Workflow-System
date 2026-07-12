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
    // Return detailed mock data for each character
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
    // Return a mocked story builder preview
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

async function loadCharacters() {
  characters = await api("/api/characters");
  if (!adventureStyles.length) {
    adventureStyles = await api("/api/story/adventure-styles");
    $("storyAdventureStyle").innerHTML = adventureStyles.map(style => `<option>${escapeHtml(style)}</option>`).join("");
    $("storyAdventureStyle").value = "Low-stakes slice of life";
  }
  renderCharacterList();
  renderStoryCharacterList();
  
  // Update dashboard metrics and cast
  renderDashboardMetrics();
  renderDashboardCharacters();
}

function renderCharacterList() {
  const query = $("searchBox").value.toLowerCase();
  $("characterList").innerHTML = characters
    .filter(c => `${c.display_name} ${c.series_name} ${c.character_id}`.toLowerCase().includes(query))
    .map(c => `
      <div class="character-row ${current?.summary.character_id === c.character_id ? "selected" : ""}" data-id="${c.character_id}">
        ${c.primary_image ? `<img src="${c.primary_image}" alt="">` : `<div class="missing-img"></div>`}
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
        ${c.primary_image ? `<img src="${c.primary_image}" alt="">` : `<span class="missing-img"></span>`}
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
      ${c.primary_image ? `<img src="${c.primary_image}" alt="${escapeHtml(c.display_name)}">` : `<div class="missing-img"></div>`}
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
    
    // Hide all view containers
    document.querySelectorAll(".workspace-view").forEach(el => el.classList.add("hidden"));
    
    // Show active container
    const viewContainerMap = {
      dashboard: "viewDashboard",
      characters: "viewCharacters",
      storyBuilder: "viewStoryBuilder",
      issues: "viewIssues",
      canon: "viewCanon",
      timeline: "viewTimeline",
      artQueue: "viewArtQueue",
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

loadCharacters();
