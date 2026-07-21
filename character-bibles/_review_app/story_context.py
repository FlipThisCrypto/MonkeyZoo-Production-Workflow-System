from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

__all__ = ["build_story_context", "StoryContextError", "ADVENTURE_STYLES"]


import bible_store as store


ADVENTURE_STYLES = [
    "Superhero adventure",
    "Mystery",
    "Treasure hunt",
    "Rescue mission",
    "Science-fiction adventure",
    "Fantasy quest",
    "Comedy of errors",
    "Survival adventure",
    "Exploration",
    "Heist",
    "Competition",
    "Monster encounter",
    "Time-travel story",
    "Social lesson",
    "Emotional character story",
    "Team-building story",
    "Holiday special",
    "Satire",
    "Educational adventure",
    "Low-stakes slice of life",
]

CANON_STATUSES = {"canon", "established", "optional"}
REVIEWABLE_STATUSES = CANON_STATUSES | {"experimental"}
ROLE_LIMITS = {
    "primary": {"traits": 7, "catchphrases": 1, "quirks": 2, "relationships": 2},
    "secondary": {"traits": 5, "catchphrases": 1, "quirks": 1, "relationships": 1},
    "supporting": {"traits": 3, "catchphrases": 0, "quirks": 1, "relationships": 1},
    "cameo": {"traits": 1, "catchphrases": 0, "quirks": 0, "relationships": 0},
}


class StoryContextError(ValueError):
    pass


# issue_id from the request body becomes a filesystem folder name in
# issue_output_dir(), so it must be a single safe path component. This accepts
# the MZ-DRAFT-... default, real MZ-YYYY-MM-NN ids, and freeform labels
# (e.g. MZ-TEST), but rejects any path separator, parent ref ("..") , drive
# letter, or dot -- otherwise a POST to /api/story/save|generate-sample could
# drive an arbitrary-location mkdir + file write (path traversal).
_SAFE_ISSUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def safe_issue_id(value: Any) -> str:
    text = str(value or "").strip()
    if not _SAFE_ISSUE_ID.fullmatch(text):
        raise StoryContextError(
            "issue_id must be a simple identifier (letters, digits, '-', '_') "
            "with no path separators or '..'"
        )
    return text


def default_setup() -> dict[str, Any]:
    return {
        "issue_id": f"MZ-DRAFT-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "characters": [],
        "page_count": 4,
        "panel_count": 12,
        "panel_density": "automatic",
        "topic": "",
        "adventure_style": "Low-stakes slice of life",
        "tone": "warm funny adventure",
        "audience": "all ages",
        "conflict": "",
        "location": "",
        "lesson": "",
        "required_beat": "",
        "forbidden_content": "",
        "continuity_mode": "current canon only",
        "canon_strictness": "balanced",
        "character_growth_mode": "small reversible beat",
        "optional_story_instructions": "",
    }


def build_preview(body: dict[str, Any], bibles_root: Path, workspace_root: Path) -> dict[str, Any]:
    setup = normalize_setup(body)
    if not setup["characters"]:
        raise StoryContextError("Select at least one character for the story context.")
    packet = build_context_packet(setup, bibles_root)
    prompt = build_script_prompt(packet)
    warnings = list(packet["warnings"]) + validate_packet(packet)
    continuity = propose_continuity_update(packet)
    return {
        "packet": packet,
        "prompt": prompt,
        "warnings": warnings,
        "panel_plan": packet["panel_plan"],
        "story_structure": packet["story_structure"],
        "continuity_proposal": continuity,
        "save_hint": str(issue_output_dir(setup["issue_id"], workspace_root)),
    }


def save_preview(body: dict[str, Any], bibles_root: Path, workspace_root: Path) -> dict[str, Any]:
    preview = build_preview(body, bibles_root, workspace_root)
    issue_id = preview["packet"]["issue_id"]
    out_dir = issue_output_dir(issue_id, workspace_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "character-context.json": json.dumps(preview["packet"], indent=2, ensure_ascii=False),
        "character-context.md": render_context_markdown(preview["packet"]),
        "script-generation-prompt.md": preview["prompt"],
        "post-generation-validation.md": render_validation_markdown(preview["warnings"]),
        "proposed-continuity-update.json": json.dumps(preview["continuity_proposal"], indent=2, ensure_ascii=False),
        "proposed-continuity-update.md": render_continuity_markdown(preview["continuity_proposal"]),
    }
    written = []
    for name, text in files.items():
        path = out_dir / name
        path.write_text(text, encoding="utf-8")
        written.append(str(path))
    return {**preview, "written_files": written}


def generate_sample_issue(body: dict[str, Any], bibles_root: Path, workspace_root: Path,
                          save: bool = True) -> dict[str, Any]:
    preview = build_preview(body, bibles_root, workspace_root)
    script = build_sample_script(preview["packet"])
    script_warnings = validate_script_text(script, preview["packet"])
    continuity = propose_continuity_update(preview["packet"], script)
    result = {
        **preview,
        "generated_script": script,
        "script_validation_warnings": script_warnings,
        "continuity_proposal": continuity,
    }
    if save:
        issue_id = preview["packet"]["issue_id"]
        out_dir = issue_output_dir(issue_id, workspace_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "character-context.json": json.dumps(preview["packet"], indent=2, ensure_ascii=False),
            "character-context.md": render_context_markdown(preview["packet"]),
            "script-generation-prompt.md": preview["prompt"],
            "generated-script.md": script,
            "script-validation.json": json.dumps({"warnings": script_warnings}, indent=2, ensure_ascii=False),
            "script-validation.md": render_validation_markdown(preview["warnings"] + script_warnings),
            "proposed-continuity-update.json": json.dumps(continuity, indent=2, ensure_ascii=False),
            "proposed-continuity-update.md": render_continuity_markdown(continuity),
        }
        written = []
        for name, text in files.items():
            path = out_dir / name
            path.write_text(text, encoding="utf-8")
            written.append(str(path))
        result["written_files"] = written
    return result


def normalize_setup(body: dict[str, Any]) -> dict[str, Any]:
    setup = default_setup()
    setup.update({key: value for key, value in body.items() if value is not None})
    setup["issue_id"] = safe_issue_id(setup.get("issue_id"))
    setup["page_count"] = clamp_int(setup.get("page_count"), 1, 64, 4)
    setup["panel_count"] = clamp_int(setup.get("panel_count"), 1, 240, setup["page_count"] * 3)
    setup["adventure_style"] = setup["adventure_style"] if setup["adventure_style"] in ADVENTURE_STYLES else ADVENTURE_STYLES[-1]
    setup["characters"] = normalize_characters(setup.get("characters", []))
    return setup


def normalize_characters(items: Any) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []
    normalized = []
    for item in items:
        if isinstance(item, str):
            character_id = item
            role = "primary" if not normalized else "supporting"
        else:
            character_id = item.get("character_id")
            role = item.get("role", "supporting")
        if character_id:
            normalized.append({"character_id": character_id, "role": role if role in ROLE_LIMITS else "supporting"})
    return normalized


def clamp_int(value: Any, low: int, high: int, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(low, min(high, parsed))


def build_context_packet(setup: dict[str, Any], bibles_root: Path) -> dict[str, Any]:
    selected_characters = []
    warnings: list[str] = []
    for selected in setup["characters"]:
        character_id = store.resolve_character_id(selected["character_id"], bibles_root)
        data = store.load_bible(character_id, bibles_root)
        selected_characters.append(select_character_context(character_id, data, selected["role"], setup, warnings))
    packet = {
        "schema_version": "1.0",
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "issue_id": setup["issue_id"],
        "story_setup": {key: setup[key] for key in setup if key != "characters"},
        "selected_cast": selected_characters,
        "panel_plan": panel_plan(setup["page_count"], setup["panel_count"], selected_characters),
        "story_structure": story_structure(setup, selected_characters),
        "selection_rules": {
            "full_bible_injected": False,
            "experimental_traits_are_reviewable_only": True,
            "saturation_max": {
                "catchphrase": 1,
                "signature_entrance_or_exit": 1,
                "recurring_gag": 1,
                "visible_quirks": 2,
                "flaw": 1,
                "strength": 1,
                "growth_beat": 1,
                "cameo_behavior": 1,
            },
        },
        "warnings": warnings,
    }
    return packet


def select_character_context(character_id: str, data: dict[str, Any], role: str, setup: dict[str, Any],
                             warnings: list[str]) -> dict[str, Any]:
    ident = data.get("identification", {})
    visual = data.get("visual_canon", {})
    issue_usage = data.get("issue_level_usage", {}) or {}
    strict = setup.get("canon_strictness") == "strict"
    allowed_statuses = CANON_STATUSES if strict else REVIEWABLE_STATUSES
    panel_cap = panel_trait_cap(setup["panel_count"], role)
    role_cap = ROLE_LIMITS[role]["traits"]
    max_traits = min(panel_cap, role_cap)
    traits = collect_eligible_traits(data, issue_usage, allowed_statuses)
    selected, excluded = select_traits(traits, max_traits, role, setup)
    catchphrases = select_limited_traits(data.get("voice_and_dialogue", {}).get("catchphrase", []), 1, allowed_statuses)
    running = select_limited_traits(data.get("running_elements", {}).get("running_gags", []), 1, allowed_statuses)
    if role in {"supporting", "cameo"}:
        catchphrases = []
    if role == "cameo":
        running = []
    catchphrases, catch_excluded = apply_cooldown(catchphrases, issue_usage.get("catchphrase_cooldown"), setup["issue_id"])
    running, running_excluded = apply_cooldown(running, issue_usage.get("running_gag_cooldown"), setup["issue_id"])
    excluded.extend(catch_excluded + running_excluded)
    visual_requirements = visual_rules(character_id, ident, visual, warnings)
    if role == "cameo":
        selected = cameo_traits(selected)
    experimental = [trait for trait in selected + catchphrases + running if trait["status"] == "experimental"]
    return {
        "character_id": character_id,
        "display_name": ident.get("current_display_name"),
        "series_name": ident.get("series_name"),
        "personal_name": ident.get("personal_name") if ident.get("naming_status") == "personal_name_canon" else None,
        "naming_status": ident.get("naming_status"),
        "role": role,
        "primary_reference_image": visual.get("primary_reference_image"),
        "alternate_reference_images": (visual.get("supporting_reference_images") or [])[:4],
        "visual_requirements": visual_requirements,
        "selected_traits": selected,
        "catchphrases_allowed": catchphrases[:ROLE_LIMITS[role]["catchphrases"]],
        "running_elements_allowed": running[:1],
        "relationships": select_relationships(data.get("relationships", []), setup["characters"], ROLE_LIMITS[role]["relationships"]),
        "continuity_notes": select_continuity(data.get("growth_and_continuity", {}), role),
        "excluded_traits": excluded,
        "experimental_review_required": experimental,
        "source_bible": f"character-bibles/{character_id}/bible.yaml",
    }


def collect_eligible_traits(data: dict[str, Any], issue_usage: dict[str, Any], allowed_statuses: set[str]) -> list[dict[str, Any]]:
    pool = issue_usage.get("traits_eligible_for_selection") or []
    if not pool:
        pool = [trait for _, trait in store.walk_traits(data)]
    seen = set()
    result = []
    for path, trait in store.walk_traits({"traits": pool}):
        if not isinstance(trait, dict) or trait.get("status") not in allowed_statuses:
            continue
        key = (trait.get("name"), trait.get("value"), trait.get("category"))
        if key in seen:
            continue
        seen.add(key)
        result.append(compact_trait(trait, path.replace("traits.", "")))
    return result


def compact_trait(trait: dict[str, Any], path: str | None = None) -> dict[str, Any]:
    return {
        "name": trait.get("name"),
        "value": trait.get("value"),
        "category": trait.get("category"),
        "status": trait.get("status"),
        "strength": trait.get("strength"),
        "usage_frequency": trait.get("usage_frequency"),
        "compatible_contexts": trait.get("compatible_contexts") or [],
        "incompatible_contexts": trait.get("incompatible_contexts") or [],
        "last_used_issue": trait.get("last_used_issue"),
        "review_note": "Requires owner approval before becoming canon." if trait.get("status") == "experimental" else None,
        "source_path": path,
    }


def select_traits(traits: list[dict[str, Any]], max_traits: int, role: str, setup: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if max_traits <= 0:
        return [], traits
    scored = sorted(traits, key=lambda trait: score_trait(trait, setup), reverse=True)
    selected = []
    category_limits = {"specific_weakness": 1, "specific_talent": 1, "signature_pose": 1}
    category_counts: dict[str, int] = {}
    for trait in scored:
        category = trait.get("category") or ""
        if category_counts.get(category, 0) >= category_limits.get(category, 99):
            continue
        selected.append(trait)
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(selected) >= max_traits:
            break
    excluded = [trait | {"reason": "outside role or panel budget"} for trait in scored if trait not in selected]
    if role == "cameo":
        excluded.extend([trait | {"reason": "cameo saturation limit"} for trait in selected[1:]])
        selected = selected[:1]
    return selected, excluded


def score_trait(trait: dict[str, Any], setup: dict[str, Any]) -> int:
    score = 0
    score += {"defining": 40, "strong": 30, "moderate": 20, "subtle": 10, "background": 0}.get(trait.get("strength"), 0)
    score += {"canon": 35, "established": 30, "optional": 15, "experimental": 5}.get(trait.get("status"), 0)
    score += {"almost always": 20, "often": 16, "sometimes": 10, "rarely": 3}.get(trait.get("usage_frequency"), 0)
    haystack = " ".join(str(setup.get(key, "")) for key in ["topic", "adventure_style", "conflict", "location", "lesson"]).lower()
    contexts = " ".join(trait.get("compatible_contexts") or []).lower()
    if contexts and any(word in haystack for word in re.findall(r"[a-z]{4,}", contexts)):
        score += 20
    if trait.get("last_used_issue"):
        score -= 12
    return score


def panel_trait_cap(panel_count: int, role: str) -> int:
    if role == "cameo":
        return 1
    if panel_count <= 4:
        return 2
    if panel_count <= 10:
        return 3
    if panel_count <= 20:
        return 5
    return 7


def select_limited_traits(items: Any, limit: int, allowed_statuses: set[str]) -> list[dict[str, Any]]:
    if not isinstance(items, list) or limit <= 0:
        return []
    return [compact_trait(item) for item in items if isinstance(item, dict) and item.get("status") in allowed_statuses][:limit]


def apply_cooldown(traits: list[dict[str, Any]], cooldown: Any, issue_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not traits or not isinstance(cooldown, dict):
        return traits, []
    minimum = cooldown.get("minimum_issues_between_uses") or 0
    last = cooldown.get("last_used_issue")
    if minimum and last:
        return [], [trait | {"reason": f"cooldown active after {last}; minimum gap {minimum} issue(s)"} for trait in traits]
    return traits, []


def cameo_traits(traits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visuals = [trait for trait in traits if trait.get("category") == "visual_feature"]
    return (visuals or traits)[:1]


def visual_rules(character_id: str, ident: dict[str, Any], visual: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    glasses = visual.get("glasses_status")
    display_name = ident.get("current_display_name") or character_id
    if glasses == "confirmed_glasses" and character_id != "MZ-CHAR-CLEVER":
        warnings.append(f"{display_name} appears to have confirmed glasses; review conflict with Clever-only glasses rule.")
    if character_id != "MZ-CHAR-CLEVER" and glasses not in {"confirmed_no_glasses", "unknown", None}:
        warnings.append(f"{display_name} has eyewear ambiguity; do not add glasses without owner approval.")
    never = [compact_trait(t) for t in visual.get("features_that_must_never_change", []) if isinstance(t, dict)]
    prohibited = [compact_trait(t) for t in visual.get("prohibited_visual_additions", []) if isinstance(t, dict)]
    return {
        "glasses_status": glasses,
        "must_keep": never[:4],
        "may_vary": [compact_trait(t) for t in visual.get("features_that_may_vary", []) if isinstance(t, dict)][:2],
        "prohibited": prohibited[:4],
    }


def select_relationships(relationships: Any, selected_characters: list[dict[str, str]], limit: int) -> list[dict[str, Any]]:
    if not isinstance(relationships, list) or limit <= 0:
        return []
    selected_ids = {item["character_id"] for item in selected_characters}
    compact = []
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        target = rel.get("target_character_id") or rel.get("character_id")
        if target in selected_ids or not target:
            compact.append({key: rel.get(key) for key in ["target_character_id", "relationship_type", "status", "notes"]})
        if len(compact) >= limit:
            break
    return compact


def select_continuity(growth: dict[str, Any], role: str) -> list[str]:
    if role in {"cameo", "supporting"}:
        return []
    notes = []
    for key in ["current_emotional_state", "open_character_arcs", "lessons_learned"]:
        values = growth.get(key) or []
        for value in values[:1]:
            if isinstance(value, dict):
                notes.append(f"{key}: {value.get('value') or value.get('name')}")
            else:
                notes.append(f"{key}: {value}")
    return notes[:2]


def panel_plan(page_count: int, panel_count: int, cast: list[dict[str, Any]]) -> dict[str, Any]:
    if page_count == 12:
        # Enforce Cover and Back Cover (1 panel each)
        pages = [{"page": 1, "panel_count": 1}]
        story_panels = panel_count - 2
        base = story_panels // 10
        extra = story_panels % 10
        for index in range(10):
            pages.append({"page": index + 2, "panel_count": base + (1 if index < extra else 0)})
        pages.append({"page": 12, "panel_count": 1})
    else:
        base = panel_count // page_count
        extra = panel_count % page_count
        pages = [{"page": index + 1, "panel_count": base + (1 if index < extra else 0)} for index in range(page_count)]
    return {
        "page_count": page_count,
        "total_panels": panel_count,
        "pages": pages,
        "cast_density": "tight" if panel_count / max(len(cast), 1) <= 3 else "roomy",
        "note": "Keep max three named characters per generated panel.",
    }



def story_structure(setup: dict[str, Any], cast: list[dict[str, Any]]) -> dict[str, Any]:
    leads = [item["display_name"] for item in cast if item["role"] == "primary"] or [cast[0]["display_name"]]
    return {
        "opening": f"Establish {setup.get('location') or 'the setting'} and the selected cast.",
        "middle": f"Use {setup.get('adventure_style')} pressure around {setup.get('topic') or 'the chosen topic'}.",
        "turn": setup.get("required_beat") or "Let one selected trait matter without crowding the panel.",
        "ending": setup.get("lesson") or "Resolve the conflict while leaving continuity changes proposed, not canon.",
        "focus_characters": leads,
    }


def validate_packet(packet: dict[str, Any]) -> list[str]:
    warnings = []
    functions: dict[str, list[str]] = {}
    for character in packet["selected_cast"]:
        name = character["display_name"]
        for trait in character["selected_traits"]:
            if trait["status"] == "experimental":
                warnings.append(f"{name}: experimental trait '{trait['name']}' is reviewable, not canon.")
            if trait.get("category") == "role":
                functions.setdefault(trait.get("value") or trait.get("name"), []).append(name)
        if character["character_id"] != "MZ-CHAR-CLEVER" and character["visual_requirements"].get("glasses_status") == "confirmed_glasses":
            warnings.append(f"{name}: possible Clever-only glasses conflict.")
        if character["naming_status"] != "personal_name_canon" and character["personal_name"]:
            warnings.append(f"{name}: unresolved personal name must remain blank.")
    for function, names in functions.items():
        if len(names) > 1:
            warnings.append(f"Duplicate story function '{function}' assigned to {', '.join(names)}.")
    names = {item["display_name"]: item for item in packet["selected_cast"]}
    if "Clever" in names and len(names["Clever"]["selected_traits"]) > 4:
        warnings.append("Clever has a heavy problem-solving load; make sure other characters contribute.")
    if "Super Monkey" in names:
        warnings.append("Do not let Super Monkey physically solve every conflict.")
    if "Zombie" in names:
        warnings.append("Do not use Zombie only as a joke; give the cameo or role a story purpose.")
    return warnings


def validate_script_text(script_text: str, packet: dict[str, Any]) -> list[str]:
    text = script_text or ""
    warnings = []
    for character in packet["selected_cast"]:
        name = character["display_name"]
        if name and name.lower() not in text.lower():
            warnings.append(f"{name} is selected but not mentioned in the script.")
        for phrase in character.get("catchphrases_allowed", []):
            value = phrase.get("value") or phrase.get("name") or ""
            if value and text.lower().count(value.lower()) > 1:
                warnings.append(f"{name} catchphrase '{value}' appears more than once.")
    if re.search(r"\b(glasses|spectacles|goggles)\b", text, re.I):
        for character in packet["selected_cast"]:
            if character["character_id"] != "MZ-CHAR-CLEVER":
                pattern = rf"{re.escape(character['display_name'])}.{{0,40}}\b(glasses|spectacles|goggles)\b"
                match = re.search(pattern, text, re.I)
                segment = match.group(0).lower() if match else ""
                negated = any(phrase in segment for phrase in [
                    "no glasses",
                    "without glasses",
                    "not wearing glasses",
                    "do not add glasses",
                    "unresolved eyewear",
                ])
                if match and not negated:
                    warnings.append(f"{character['display_name']} may have incorrect glasses.")
    for character in packet["selected_cast"]:
        for trait in character.get("experimental_review_required", []):
            if (trait.get("name") or "").lower() in text.lower():
                warnings.append(f"{character['display_name']} uses experimental trait '{trait['name']}'; keep as review item.")
    return warnings


def build_script_prompt(packet: dict[str, Any]) -> str:
    setup = packet["story_setup"]
    lines = [
        f"# Script Prompt: {packet['issue_id']}",
        "",
        "Use only this compact character context packet and approved project rules. Do not load or paste full Character Bibles into the prompt.",
        "",
        "## Story Setup",
    ]
    for key in ["topic", "adventure_style", "tone", "audience", "conflict", "location", "lesson", "required_beat", "forbidden_content", "continuity_mode", "canon_strictness", "character_growth_mode", "optional_story_instructions"]:
        value = setup.get(key)
        if value:
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.extend(["", "## Cast Context"])
    for character in packet["selected_cast"]:
        lines.append(f"### {character['display_name']} ({character['role']})")
        if character.get("personal_name"):
            lines.append(f"- Personal name: {character['personal_name']}")
        lines.append(f"- Series name: {character.get('series_name') or 'blank'}")
        lines.append(f"- Naming status: {character.get('naming_status')}")
        lines.append(f"- Primary reference: {character.get('primary_reference_image') or 'missing'}")
        lines.append(f"- Glasses status: {character['visual_requirements'].get('glasses_status')}")
        for trait in character["selected_traits"]:
            marker = " [REVIEW]" if trait["status"] == "experimental" else ""
            lines.append(f"- Trait{marker}: {trait['name']} - {trait.get('value')}")
        for phrase in character.get("catchphrases_allowed", []):
            lines.append(f"- Catchphrase max once: {phrase.get('value') or phrase.get('name')}")
        for rule in character["visual_requirements"].get("must_keep", []):
            lines.append(f"- Must keep visually: {rule.get('value') or rule.get('name')}")
        for rule in character["visual_requirements"].get("prohibited", []):
            lines.append(f"- Prohibited visual addition: {rule.get('value') or rule.get('name')}")
    lines.extend([
        "",
        "## Panel Plan",
        json.dumps(packet["panel_plan"], indent=2),
        "",
        "## Validation Targets",
        "- Do not canonize experimental traits.",
        "- Do not give glasses to anyone except Clever unless the packet explicitly says confirmed_glasses.",
        "- Keep catchphrases, quirks, flaws, strengths, and running elements within packet limits.",
        "- Flag any new continuity fact as a proposed update requiring owner approval.",
    ])
    return "\n".join(lines) + "\n"


def build_sample_script(packet: dict[str, Any]) -> str:
    setup = packet["story_setup"]
    pages = packet["panel_plan"]["pages"]
    cast = packet["selected_cast"]
    lead = next((character for character in cast if character["role"] == "primary"), cast[0])
    support = [character for character in cast if character["character_id"] != lead["character_id"]]
    used_catchphrases: set[str] = set()
    lines = [
        f"# Generated Sample Issue: {packet['issue_id']}",
        "",
        f"Topic: {setup.get('topic') or 'untitled MonkeyZoo test'}",
        f"Adventure style: {setup.get('adventure_style')}",
        f"Tone: {setup.get('tone')}",
        "",
        "This is a QA sample script generated from compact character context only. It is not canon.",
        "",
    ]
    global_panel = 1
    for page in pages:
        lines.append(f"## Page {page['page']}")
        for panel_index in range(1, page["panel_count"] + 1):
            present = panel_characters(cast, lead, support, global_panel)
            speaker = present[(global_panel - 1) % len(present)]
            action_trait = first_trait(speaker)
            dialogue = sample_dialogue(speaker, setup, used_catchphrases)
            lines.extend([
                f"### Panel {panel_index}",
                f"- Location: {setup.get('location') or 'MonkeyZoo test setting'}",
                f"- Characters present: {', '.join(character['display_name'] for character in present)}",
                f"- Camera angle: medium readable panel",
                f"- Action: {sample_action(speaker, action_trait, global_panel, setup)}",
                f"- Emotion: {sample_emotion(global_panel, setup)}",
                f"- Dialogue: {dialogue}",
                f"- Caption text: {'A proposed growth beat appears here.' if is_growth_panel(global_panel, packet) else '-'}",
                f"- SFX: -",
                f"- Visual notes: {visual_note(present)}",
                f"- Continuity notes: Uses selected context only; any new facts remain proposed.",
                "",
            ])
            global_panel += 1
    return "\n".join(lines)


def panel_characters(cast: list[dict[str, Any]], lead: dict[str, Any], support: list[dict[str, Any]],
                     panel_number: int) -> list[dict[str, Any]]:
    if not support:
        return [lead]
    partner = support[(panel_number - 1) % len(support)]
    if partner["role"] == "cameo" and panel_number % 3 != 0:
        partner = support[0]
    present = [lead, partner]
    if panel_number % 5 == 0 and len(support) > 1:
        present.append(support[1])
    return list({character["character_id"]: character for character in present}.values())[:3]


def first_trait(character: dict[str, Any]) -> dict[str, Any] | None:
    traits = character.get("selected_traits") or []
    return traits[0] if traits else None


def sample_action(character: dict[str, Any], trait: dict[str, Any] | None, panel_number: int,
                  setup: dict[str, Any]) -> str:
    trait_text = trait.get("value") if trait else "keeps the scene readable"
    if panel_number == 1:
        return f"{character['display_name']} notices the {setup.get('topic') or 'test problem'} and {trait_text}."
    if panel_number % 4 == 0:
        return f"{character['display_name']} makes room for another character to help instead of solving everything."
    return f"{character['display_name']} uses {trait.get('name') if trait else 'a restrained beat'} in a story-relevant way."


def sample_dialogue(character: dict[str, Any], setup: dict[str, Any], used_catchphrases: set[str]) -> str:
    for phrase in character.get("catchphrases_allowed", []):
        value = phrase.get("value") or phrase.get("name")
        if value and value not in used_catchphrases:
            used_catchphrases.add(value)
            return f"{character['display_name']}: \"{value}\""
    role = character.get("role")
    if role == "primary":
        return f"{character['display_name']}: \"We handle one piece at a time.\""
    if role == "secondary":
        return f"{character['display_name']}: \"I see the part we missed.\""
    if role == "cameo":
        return "-"
    return f"{character['display_name']}: \"I can help without taking over.\""


def sample_emotion(panel_number: int, setup: dict[str, Any]) -> str:
    if panel_number == 1:
        return "curiosity"
    if panel_number % 6 == 0:
        return "comic pressure with control"
    if setup.get("character_growth_mode") != "no growth beat" and panel_number % 9 == 0:
        return "small reversible growth"
    return "forward motion"


def visual_note(present: list[dict[str, Any]]) -> str:
    notes = []
    for character in present:
        glasses = character["visual_requirements"].get("glasses_status")
        if character["character_id"] == "MZ-CHAR-CLEVER":
            notes.append("Clever keeps round black-rimmed glasses")
        elif glasses == "confirmed_no_glasses":
            notes.append(f"{character['display_name']} has no glasses")
        elif glasses == "unknown":
            notes.append(f"{character['display_name']} has unresolved eyewear; do not add glasses")
    return "; ".join(notes) or "Follow primary references."


def is_growth_panel(panel_number: int, packet: dict[str, Any]) -> bool:
    mode = packet["story_setup"].get("character_growth_mode")
    return mode not in {"no growth beat", None} and panel_number == max(1, packet["panel_plan"]["total_panels"] // 2)


def propose_continuity_update(packet: dict[str, Any], script_text: str | None = None) -> dict[str, Any]:
    growth_notes = []
    if packet["story_setup"].get("character_growth_mode") not in {"no growth beat", None}:
        lead = next((character for character in packet["selected_cast"] if character["role"] == "primary"), packet["selected_cast"][0])
        growth_notes.append({
            "character_id": lead["character_id"],
            "display_name": lead["display_name"],
            "proposal": f"Review whether {lead['display_name']} showed a small reversible growth beat in {packet['issue_id']}.",
            "status": "proposed_owner_review_required",
        })
    return {
        "issue_id": packet["issue_id"],
        "status": "proposed_owner_review_required",
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "traits_used": [
            {
                "character_id": character["character_id"],
                "display_name": character["display_name"],
                "traits": character["selected_traits"],
                "catchphrases": character.get("catchphrases_allowed", []),
                "running_elements": character.get("running_elements_allowed", []),
            }
            for character in packet["selected_cast"]
        ],
        "new_facts": [],
        "relationship_changes": [],
        "lessons_learned": [],
        "unresolved_questions": [],
        "growth_notes": growth_notes,
        "suggested_bible_updates": [],
        "script_reviewed": bool(script_text),
        "canonization_note": "Nothing in this proposal becomes canon until approved in the Character Bible review interface.",
    }


def issue_output_dir(issue_id: str, workspace_root: Path) -> Path:
    issue_id = safe_issue_id(issue_id)  # never build a path from an unvalidated id at the sink
    factory_issue = workspace_root / "MonkeyZoo_Comic_Factory" / "02_MONTHLY_ISSUES" / issue_id
    if factory_issue.exists():
        return factory_issue
    return workspace_root / "issues" / issue_id


def render_context_markdown(packet: dict[str, Any]) -> str:
    lines = [f"# Character Context Packet: {packet['issue_id']}", "", "## Selected Cast"]
    for character in packet["selected_cast"]:
        lines.append(f"### {character['display_name']} ({character['role']})")
        lines.append(f"- Bible: `{character['source_bible']}`")
        lines.append(f"- Primary reference: `{character.get('primary_reference_image') or 'missing'}`")
        lines.append(f"- Naming status: {character.get('naming_status')}; personal name: {character.get('personal_name') or 'blank'}")
        for trait in character["selected_traits"]:
            suffix = " (review required)" if trait["status"] == "experimental" else ""
            lines.append(f"- {trait['name']}: {trait.get('value')} [{trait['status']}]{suffix}")
        if character["excluded_traits"]:
            lines.append(f"- Excluded this pass: {len(character['excluded_traits'])} trait(s)")
    lines.extend(["", "## Warnings"])
    lines.extend([f"- {warning}" for warning in packet.get("warnings", [])] or ["- None"])
    return "\n".join(lines) + "\n"


def render_validation_markdown(warnings: list[str]) -> str:
    lines = ["# Post-Generation Validation Checklist", ""]
    checks = [
        "OOC dialogue",
        "Visual canon violations",
        "Catchphrase overuse",
        "Too many quirks",
        "Duplicate story functions",
        "Forgotten selected characters",
        "Unapproved traits",
        "Continuity conflicts",
        "Cooldown traits",
        "Incorrect glasses",
        "Similar voices",
    ]
    lines.extend([f"- [ ] {check}" for check in checks])
    lines.extend(["", "## Current Warnings"])
    lines.extend([f"- {warning}" for warning in warnings] or ["- None"])
    return "\n".join(lines) + "\n"


def render_continuity_markdown(proposal: dict[str, Any]) -> str:
    lines = [
        f"# Proposed Continuity Update: {proposal['issue_id']}",
        "",
        f"Status: {proposal['status']}",
        "",
        proposal["canonization_note"],
        "",
        "## Traits Used",
    ]
    for item in proposal["traits_used"]:
        lines.append(f"### {item['display_name']}")
        for trait in item["traits"]:
            lines.append(f"- {trait['name']} [{trait['status']}]")
    return "\n".join(lines) + "\n"
