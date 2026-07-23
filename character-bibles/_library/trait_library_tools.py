from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

LIBRARY_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = LIBRARY_ROOT.parents[1]
BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"

CATEGORIES = [
    "catchphrase",
    "physical_tick",
    "running_prop",
    "entrance_style",
    "exit_style",
    "favorite_word",
    "speech_pattern",
    "personal_rule",
    "unusual_fear",
    "lucky_charm",
    "theme_music_or_audio_cue",
    "color_preference_or_aversion",
    "signature_pose",
    "favorite_snack",
    "mini_celebration",
    "specific_talent",
    "specific_weakness",
    "imaginary_or_unseen_companion",
    "bad_timing_habit",
    "narrator_awareness",
    "personal_sound_effect",
    "literal_misunderstanding_tendency",
    "collection_or_obsession",
    "unexpected_hobby",
    "emotional_tell",
    "personal_mission",
    "unusual_luck_pattern",
    "relationship_dynamic",
    "signature_mistake",
    "recurring_mystery",
]

CATEGORY_META = {
    "catchphrase": ("dialogue", "moderate", "rarely", ["dialogue", "comedy", "emotional-button"], ["catchphrase-overuse"]),
    "physical_tick": ("behavioral", "subtle", "sometimes", ["visual-storytelling", "acting", "emotion"], ["busy-acting"]),
    "running_prop": ("visual", "moderate", "sometimes", ["visual-storytelling", "continuity", "mystery"], ["prop-clutter"]),
    "entrance_style": ("behavioral", "moderate", "rarely", ["adventure", "panel-reveal", "comedy"], ["scene-stealing"]),
    "exit_style": ("behavioral", "subtle", "rarely", ["button-panel", "comedy", "emotion"], ["formulaic-exit"]),
    "favorite_word": ("dialogue", "subtle", "sometimes", ["voice", "dialogue"], ["voice-tic-overuse"]),
    "speech_pattern": ("dialogue", "moderate", "often", ["voice", "dialogue", "contrast"], ["samey-dialogue"]),
    "personal_rule": ("behavioral", "strong", "sometimes", ["growth", "team-conflict", "ethics"], ["moralizing"]),
    "unusual_fear": ("behavioral", "moderate", "rarely", ["comedy", "vulnerability", "adventure"], ["cheap-fear-gag"]),
    "lucky_charm": ("visual", "subtle", "rarely", ["continuity", "mystery", "emotion"], ["prop-clutter"]),
    "theme_music_or_audio_cue": ("dialogue", "moderate", "rarely", ["audio-gag", "entrance", "mood"], ["noisy-page"]),
    "color_preference_or_aversion": ("visual", "moderate", "sometimes", ["visual-storytelling", "art-direction"], ["palette-drift"]),
    "signature_pose": ("visual", "moderate", "sometimes", ["recognition", "acting", "covers"], ["pose-repetition"]),
    "favorite_snack": ("visual", "subtle", "rarely", ["comedy", "comfort", "worldbuilding"], ["snack-filler"]),
    "mini_celebration": ("behavioral", "subtle", "rarely", ["comedy", "reward", "team-bonding"], ["victory-spam"]),
    "specific_talent": ("behavioral", "strong", "sometimes", ["adventure", "mystery", "team-role"], ["solves-everything"]),
    "specific_weakness": ("behavioral", "moderate", "sometimes", ["growth", "conflict", "emotion"], ["punishing-character"]),
    "imaginary_or_unseen_companion": ("dialogue", "moderate", "rarely", ["comedy", "mystery", "emotion"], ["confusing-canon"]),
    "bad_timing_habit": ("behavioral", "moderate", "sometimes", ["comedy", "team-conflict"], ["interrupts-drama"]),
    "narrator_awareness": ("dialogue", "subtle", "rarely", ["narration", "satire", "comedy"], ["breaks-immersion"]),
    "personal_sound_effect": ("dialogue", "subtle", "rarely", ["lettering", "comedy", "acting"], ["sfx-clutter"]),
    "literal_misunderstanding_tendency": ("dialogue", "moderate", "rarely", ["comedy", "dialogue", "team-conflict"], ["makes-character-dim"]),
    "collection_or_obsession": ("behavioral", "moderate", "sometimes", ["continuity", "mystery", "comedy"], ["one-note-obsession"]),
    "unexpected_hobby": ("behavioral", "subtle", "rarely", ["contrast", "emotion", "downtime"], ["random-quirk"]),
    "emotional_tell": ("visual", "subtle", "sometimes", ["emotion", "acting", "silent-panel"], ["overexplaining-emotion"]),
    "personal_mission": ("behavioral", "strong", "sometimes", ["growth", "continuity", "adventure"], ["plot-tunnel-vision"]),
    "unusual_luck_pattern": ("behavioral", "moderate", "rarely", ["comedy", "mystery", "adventure"], ["deus-ex-machina"]),
    "relationship_dynamic": ("behavioral", "strong", "sometimes", ["team-conflict", "emotion", "continuity"], ["forced-pairing"]),
    "signature_mistake": ("behavioral", "moderate", "rarely", ["comedy", "growth", "team-conflict"], ["same-mistake-loop"]),
    "recurring_mystery": ("behavioral", "strong", "special circumstances only", ["mystery", "continuity", "long-term"], ["mystery-bloat"]),
}

STOPWORDS = {
    "with", "that", "this", "when", "from", "into", "while", "before", "after", "character", "story",
    "visual", "dialogue", "behavioral", "trait", "support", "without", "become", "becoming", "panel",
    "once", "pressure", "contrast", "choice", "canon", "issue", "team", "scene", "uses", "useful",
}

BASE_OPTIONS = {
    "catchphrase": ["Hold the bananas", "Small problem, big eyebrows", "That was almost a plan", "Put a pin in the chaos", "One vine at a time", "Nobody panic professionally", "I heard the quiet part", "Still counts as teamwork", "Let the weird breathe", "Not my first mango", "Permission to improvise", "We can fix the fix", "Tiny nope", "Interesting in a bad way", "Good news with teeth"],
    "physical_tick": ["ear flick before risk", "tail counts beats", "straightens tiny detail", "blinks twice at lies", "paws tap panel rhythm", "leans toward clues", "freezes during praise", "rubs wrist when unsure", "checks exit path", "tilts head at half-truths", "brushes dust off nothing", "mirrors teammate posture", "touches emblem for courage", "squints at patterns", "sits lower when overwhelmed"],
    "running_prop": ["folded map with wrong corner", "tiny repair sticker sheet", "emergency mango pouch", "blank label maker", "mismatched walkie", "lucky bottle cap", "mini flashlight with mood beam", "notebook of almost-clues", "thread spool for routes", "old arcade token", "tiny weather flag", "collapsible sign", "pocket magnifier", "snack wrapper evidence bag", "rubber stamp that says later"],
    "entrance_style": ["already in the background", "drops from wrong height", "arrives mid-sentence", "slides in with evidence", "peeks around signage", "bursts through harmless curtain", "steps from shadow calmly", "rides in on prop mishap", "appears after sound cue", "enters carrying consequence", "waves before landing", "comes in backward reading", "arrives too prepared", "sneaks in loudly", "walks in like a verdict"],
    "exit_style": ["backs away still talking", "vanishes behind foreground object", "leaves a useful clue", "exits through wrong door", "moonwalks from embarrassment", "salutes too late", "gets pulled by off-panel task", "fades into crowd", "turns exit into button joke", "leaves prop behind", "quiet nod and go", "runs back for one word", "slides out of panel edge", "exits with tiny bow", "walks off following noise"],
    "favorite_word": ["technically", "meanwhile", "tiny", "probably", "permission", "behold", "allegedly", "steady", "nope", "curious", "again", "objection", "sparkly", "borrowed", "almost"],
    "speech_pattern": ["three-word verdicts", "question before answer", "soft correction first", "lists two options", "echoes last key word", "starts with tiny disclaimer", "uses stage directions aloud", "understates danger", "over-formal under stress", "pauses before names", "answers with comparisons", "says emotion as weather", "half-whispered confidence", "rhyming only when nervous", "turns plans into labels"],
    "personal_rule": ["ask before fixing", "never leave the smallest one", "jokes stop at fear", "measure twice, leap once", "no shortcuts through feelings", "share credit first", "tell the hard part plainly", "protect the quiet clue", "never trust perfect signs", "keep one hand free", "do not mock old mistakes", "carry the map back", "try kindness before cleverness", "leave room for no", "repair what you rename"],
    "unusual_fear": ["too-perfect symmetry", "silent applause", "empty trophy shelves", "maps without edges", "freshly polished buttons", "unlabeled switches", "automatic doors that wait", "crowds chanting wrong name", "friendly countdowns", "costumes with no eye holes", "bananas cut lengthwise", "music that stops early", "spotlights looking back", "tiny locked boxes", "weather indoors"],
    "lucky_charm": ["cracked arcade token", "button from first costume", "blue thread knot", "tiny paper umbrella", "old bus ticket", "polished pebble with stripe", "folded apology note", "banana sticker star", "toy compass that points home", "bent spoon badge", "friendship receipt", "tiny red ribbon", "shell from mystery beach", "plastic crown piece", "half of a puzzle charm"],
    "theme_music_or_audio_cue": ["three off-key notes", "tiny drumroll fail", "distant elevator ding", "mango maraca shake", "hero chord too small", "soft record scratch", "mysterious triangle ping", "sneaker squeak rhythm", "wind-up toy whirr", "page-turn chime", "radio static hello", "low bass banana boom", "tap-tap pause", "whistle that answers itself", "one-note fanfare"],
    "color_preference_or_aversion": ["avoids perfect white rooms", "trusts teal markers", "gets calmer near warm yellow", "hates red warning lights", "chooses blue for hard truths", "collects purple labels", "uses green to mark safe paths", "goes still around silver", "likes mismatched stripes", "refuses invisible ink", "prefers sunset orange in endings", "reads black borders as serious", "uses pink for brave notes", "mistrusts gold trophies", "keeps grey for uncertain clues"],
    "signature_pose": ["one foot on clue", "both hands behind back", "pointing without looking", "chin up tiny courage", "crouched detective lean", "arms wide to block chaos", "finger raised then lowered", "sits on panel border", "leans against speech bubble space", "tiny salute with serious face", "shoulder turn toward exit", "hands framing mystery", "knees bent before sprint", "palms open peace offer", "looks up while everyone looks down"],
    "favorite_snack": ["freeze-dried mango chips", "tiny pretzel knots", "sour banana buttons", "midnight trail mix", "emergency crackers", "peanut-butter moon bites", "seaweed crunch squares", "blueberry evidence muffins", "spicy popcorn kernels", "cocoa pebble clusters", "warm cinnamon toast sticks", "lemon cloud candies", "quiet apple slices", "pickle chips of courage", "marshmallow compass points"],
    "mini_celebration": ["two-finger victory tap", "silent fist bloom", "tiny cape swish", "one-second dance loop", "checks imaginary scoreboard", "high-fives nearest object", "under-breath yes", "victory sticker placement", "tail spiral flourish", "bows to nobody", "mango toast gesture", "draws a small star", "polishes badge once", "does not smile until alone", "whispers teamwork"],
    "specific_talent": ["reads crowd temperature", "spots reused props", "maps escape routes fast", "turns jokes into distractions", "hears machinery moods", "remembers exact promises", "finds missing labels", "calms one teammate at a time", "builds tools from scraps", "notices who is absent", "translates panic into tasks", "solves by asking the quiet person", "turns failure into cover", "tracks footprints in glitter", "knows when not to speak"],
    "specific_weakness": ["overprotects the plan", "needs applause to feel useful", "trusts labels too much", "freezes after being thanked", "turns discomfort into jokes", "avoids asking for help", "pushes mystery past safety", "mistakes calm for agreement", "cannot leave puzzle unfinished", "confuses speed with bravery", "takes blame too fast", "hides fear behind precision", "forgets quiet teammates", "keeps old promise too rigidly", "overcorrects after one mistake"],
    "imaginary_or_unseen_companion": ["the committee under the hat", "off-panel cousin Maybe", "a suspicious wind named Greg", "future self with notes", "the tiny judge", "invisible stage manager", "pocket weather advisor", "the old machine voice", "a backpack audience", "banana peel oracle", "the fourth wall intern", "imaginary safety inspector", "memory of a mentor", "the echo in the vents", "unseen rival who keeps score"],
    "bad_timing_habit": ["compliments during alarm", "opens snack at reveal", "asks big question after answer", "arrives right after courage", "laughs one beat late", "starts repair during speech", "names the danger too soon", "waves during stealth", "uses catchphrase in silence", "tests prop during tension", "confesses after group hug", "solves clue while leaving", "misreads dramatic pause", "celebrates decoy victory", "starts countdown at two"],
    "narrator_awareness": ["notices panel borders", "argues with caption tone", "hears page turn coming", "counts panels under breath", "knows splash page means trouble", "asks why the camera is low", "objects to recap boxes", "points at off-panel noise", "uses gutter as hiding place", "waits for next page reveal", "reads title as clue", "complains about tiny lettering", "trusts silent panels", "knows cover promises drama", "spots when narration dodges truth"],
    "personal_sound_effect": ["plink of realization", "fwip of sudden plan", "mrrp of doubt", "tik-tik focus noise", "bloop of embarrassment", "zzzt before idea", "hmph with punctuation", "sproing of bad impulse", "whuff of courage", "eep kept tiny", "clack of decision", "poff of exit", "ding with suspicion", "grrk of restraint", "tada but lowercase"],
    "literal_misunderstanding_tendency": ["takes signs as commands", "believes metaphor needs map", "answers rhetorical questions", "waits for actual green light", "looks for real elephant", "brings table to table talk", "treats cold case as chilly box", "packs ladder for higher stakes", "searches for plot hole", "expects cliffhanger cliff", "counts skeleton crew bones", "polishes rough draft", "guards running joke from running", "measures long story", "tries to bottle suspense"],
    "collection_or_obsession": ["almost-identical warning labels", "lost button caps", "maps of places already known", "tiny apology notes", "misprinted tickets", "background sign photos", "broken countdown clocks", "unclaimed trophies", "oddly shaped keys", "snack wrappers with clues", "weather reports from indoors", "matching socks from mysteries", "unused name tags", "strange elevator music tapes", "lists of things not to touch"],
    "unexpected_hobby": ["repairs music boxes", "studies cloud handwriting", "makes tiny dioramas", "practices dramatic lighting", "folds emergency origami", "keeps a smell journal", "does silent improv", "restores old arcade cabinets", "paints invisible signs", "learns polite lockpicking", "bakes clue-shaped snacks", "curates found buttons", "draws maps from memory", "collects almost-rhymes", "records harmless echoes"],
    "emotional_tell": ["smile becomes too square", "ears flatten on guilt", "tail stills before truth", "eyes track exits", "voice gets extra polite", "hands hide in sleeves", "laugh cuts off early", "leans toward trusted friend", "checks prop for comfort", "stands between danger and child", "over-explains when scared", "goes quiet at praise", "looks at floor during apology", "straightens badge before lie", "forgets favorite word"],
    "personal_mission": ["prove change can be chosen", "make scary systems understandable", "protect jokes from becoming cruelty", "find who got left behind", "turn panic into teamwork", "keep promises from becoming traps", "learn when to stop fixing", "make room for quiet courage", "help the team disagree safely", "restore a forgotten place", "name the cost before winning", "find a home signal", "save the tiny evidence", "make bravery less loud", "leave every place kinder"],
    "unusual_luck_pattern": ["bad luck near trophies", "finds exits by tripping", "wins only practice rounds", "lucky when honest", "unlucky after boasting", "always draws the decoy map", "rain stops for apologies", "machines work when ignored", "snacks reveal clues accidentally", "doors open to wrong truth", "loses props that needed losing", "breaks only fake things", "falls toward evidence", "gets help after asking badly", "luck flips at sunset"],
    "relationship_dynamic": ["translator for teammate feelings", "friendly rivalry over plans", "protective of the quiet one", "skeptical of the flashy one", "shares blame too quickly", "trust is earned through small tasks", "comforts by fixing objects", "argues only when scared", "pairs well with opposite tempo", "becomes brave when watched kindly", "needs permission to lead", "tests friends with small honesty", "keeps old guilt private", "learns to accept backup", "rivalry becomes repair"],
    "signature_mistake": ["fixes symptom not cause", "uses wrong name tag", "trusts the cleanest clue", "overcommits to first theory", "forgets audience is watching", "brings prop for previous problem", "turns left at emotional crossroads", "reads warning upside down", "answers before listening", "hides useful fear", "makes joke one panel early", "assumes silence means yes", "saves decoy first", "packs everything except courage", "confuses winning with helping"],
    "recurring_mystery": ["who wrote the old labels", "why the arcade token returns", "what the quiet signal means", "where the missing panel went", "who keeps repairing damage overnight", "why maps disagree near water", "what Patch remembers", "why the music knows names", "who owns the empty trophy", "why the same door moves", "what happened before issue one", "who watches from signage", "why bananas point north", "what the sealed costume hides", "why one spotlight follows truth"],
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:48]


def load_bible(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def walk_traits(data: Any):
    if isinstance(data, dict):
        if data.get("category") in CATEGORIES and data.get("name"):
            yield data
        for value in data.values():
            yield from walk_traits(value)
    elif isinstance(data, list):
        for value in data:
            yield from walk_traits(value)


def harvested_project_options(bibles_root: Path = BIBLES_ROOT) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {category: [] for category in CATEGORIES}
    seen: set[tuple[str, str, str]] = set()
    for bible_path in sorted(bibles_root.glob("MZ-CHAR-*/bible.yaml")):
        data = load_bible(bible_path)
        ident = data.get("identification", {})
        character_id = bible_path.parent.name          # e.g. "MZ-CHAR-001"
        for trait in walk_traits(data):

            key = (trait["category"], str(trait.get("name")), str(trait.get("value")))
            if key in seen:
                continue
            seen.add(key)
            found[trait["category"]].append({
                "short_name": str(trait.get("name")),
                "description": str(trait.get("value") or trait.get("name")),
                "source": f"Existing {ident.get('current_display_name') or character_id} Bible trait",
                "source_character_id": character_id,
                "source_status": trait.get("status"),
            })
    return found


def build_library(bibles_root: Path = BIBLES_ROOT) -> dict[str, Any]:
    harvested = harvested_project_options(bibles_root)
    entries = []
    for category in CATEGORIES:
        source_options = harvested[category] + [
            {"short_name": name, "description": default_description(category, name), "source": "Curated suggestion option"}
            for name in BASE_OPTIONS[category]
        ]
        seen_names: set[str] = set()
        index = 1
        for option in source_options:
            name = option["short_name"].strip()
            if not name or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            entries.append(make_entry(category, index, option))
            index += 1
    return {
        "schema_version": "1.0",
        "purpose": "Suggestion library only. Entries are not random assignments and never become canon automatically.",
        "selection_rule": "Propose a trait only when it fits visual design, established canon, useful contrast, future stories, and character load.",
        "categories": CATEGORIES,
        "entries": entries,
    }


def default_description(category: str, name: str) -> str:
    label = category.replace("_", " ")
    return f"{name} as a {label} that can support story contrast without becoming a mandatory gag."


def make_entry(category: str, index: int, option: dict[str, Any]) -> dict[str, Any]:
    modality, intensity, frequency, tags, conflicts = CATEGORY_META[category]
    short_name = option["short_name"]
    return {
        "trait_id": f"MZLIB-{slug(category).upper()}-{index:03d}-{slug(short_name).upper()}",
        "category": category,
        "short_name": short_name,
        "description": option["description"],
        "possible_story_uses": story_uses(category),
        "suitable_archetypes": suitable_archetypes(category),
        "unsuitable_archetypes": unsuitable_archetypes(category),
        "visual_or_dialogue_or_behavioral": modality,
        "intensity": intensity,
        "recommended_frequency": frequency,
        "possible_downside": downside(category),
        "compatibility_tags": tags + [slug(short_name)],
        "conflict_tags": conflicts,
        "requires_owner_approval": True,
        "example_usage": example_usage(category, short_name),
        "overuse_warning": overuse_warning(category),
        "source": option.get("source"),
        "source_character_id": option.get("source_character_id"),
        "source_status": option.get("source_status"),
    }


def story_uses(category: str) -> list[str]:
    uses = {
        "catchphrase": ["button line", "emotional callback", "voice contrast"],
        "specific_talent": ["problem solving", "team role clarity", "mystery breakthrough"],
        "specific_weakness": ["growth beat", "team conflict", "earned vulnerability"],
        "recurring_mystery": ["long-term continuity", "issue hook", "background clue"],
        "relationship_dynamic": ["pairing contrast", "ensemble tension", "repair scene"],
    }
    return uses.get(category, ["comedy beat", "visual storytelling", "character differentiation"])


def suitable_archetypes(category: str) -> list[str]:
    if category in {"specific_talent", "personal_mission", "personal_rule"}:
        return ["developing lead", "mentor", "problem solver", "reluctant hero"]
    if category in {"catchphrase", "personal_sound_effect", "bad_timing_habit"}:
        return ["comic relief", "high-energy lead", "scene spark", "supporting character"]
    if category in {"recurring_mystery", "unusual_luck_pattern", "collection_or_obsession"}:
        return ["mystery carrier", "quiet observer", "lore-linked character"]
    return ["lead", "supporting character", "visual character", "ensemble foil"]


def unsuitable_archetypes(category: str) -> list[str]:
    if category in {"catchphrase", "personal_sound_effect"}:
        return ["intentionally sparse character", "solemn emotional anchor"]
    if category in {"recurring_mystery", "personal_mission"}:
        return ["one-panel cameo", "background-only character"]
    if category in {"specific_weakness", "unusual_fear"}:
        return ["character already overloaded with flaws"]
    return ["character whose canon already covers the same function"]


def downside(category: str) -> str:
    return {
        "catchphrase": "Can flatten the voice if used as filler.",
        "specific_talent": "Can make the character solve too many scenes.",
        "specific_weakness": "Can feel punitive if not balanced by agency.",
        "recurring_mystery": "Can bloat continuity if every appearance adds clues.",
        "relationship_dynamic": "Can force pairings when the plot does not need them.",
    }.get(category, "Can become noise if it does not serve the scene.")


def example_usage(category: str, short_name: str) -> str:
    return f"In a story-relevant moment, use '{short_name}' once to reveal character pressure, contrast, or choice."


def overuse_warning(category: str) -> str:
    return {
        "catchphrase": "Limit to once per issue unless repetition is the joke.",
        "physical_tick": "Do not describe it in every panel.",
        "signature_pose": "Rotate poses so references do not become stiff.",
        "specific_talent": "Let other characters contribute solutions.",
        "specific_weakness": "Do not make the character fail the same way every issue.",
        "recurring_mystery": "Resolve or rest mysteries before adding new ones.",
    }.get(category, "Use only when it adds story value.")


def validate_library(library: dict[str, Any]) -> list[str]:
    errors = []
    entries = library.get("entries", [])
    required = {
        "trait_id", "category", "short_name", "description", "possible_story_uses", "suitable_archetypes",
        "unsuitable_archetypes", "visual_or_dialogue_or_behavioral", "intensity", "recommended_frequency",
        "possible_downside", "compatibility_tags", "conflict_tags", "requires_owner_approval", "example_usage",
        "overuse_warning",
    }
    ids = set()
    for entry in entries:
        missing = required - set(entry)
        if missing:
            errors.append(f"{entry.get('trait_id', 'unknown')} missing {sorted(missing)}")
        if entry.get("trait_id") in ids:
            errors.append(f"Duplicate trait_id {entry.get('trait_id')}")
        ids.add(entry.get("trait_id"))
        if entry.get("category") not in CATEGORIES:
            errors.append(f"Invalid category {entry.get('category')}")
        if entry.get("requires_owner_approval") is not True:
            errors.append(f"{entry.get('trait_id')} must require owner approval")
    for category in CATEGORIES:
        count = sum(1 for entry in entries if entry.get("category") == category)
        if count < 15:
            errors.append(f"{category} has {count} entries; expected at least 15")
    return errors


def load_library(path: Path | None = None) -> dict[str, Any]:
    path = path or LIBRARY_ROOT / "trait-library.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_library(library: dict[str, Any], root: Path = LIBRARY_ROOT) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "trait-library.yaml").write_text(yaml.safe_dump(library, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    (root / "trait-library.json").write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding="utf-8")


def recommend_traits(character_id: str, top_n: int = 5, bibles_root: Path = BIBLES_ROOT,
                     library: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    library = library or load_library()
    character = load_bible(bibles_root / character_id / "bible.yaml")
    all_bibles = {path.parent.name: load_bible(path) for path in bibles_root.glob("MZ-CHAR-*/bible.yaml")}
    existing_terms = existing_trait_terms(character)
    cast_terms = {cid: existing_trait_terms(data) for cid, data in all_bibles.items() if cid != character_id}
    visual_text = json.dumps(character.get("visual_canon", {}), ensure_ascii=False).lower()
    development_level = character.get("identification", {}).get("development_level") or 1
    candidates = []
    for entry in library.get("entries", []):
        if entry.get("source_character_id") == character_id:
            continue
        if entry["short_name"].lower() in existing_terms:
            continue
        overlap = overlap_with_cast(entry, cast_terms)
        score = recommendation_score(entry, existing_terms, visual_text, development_level, overlap, character_id)
        candidates.append((score, entry, overlap))
    candidates.sort(key=lambda item: item[0], reverse=True)
    results = []
    category_counts: dict[str, int] = {}
    for _, entry, overlap in candidates:
        if category_counts.get(entry["category"], 0) >= 1 and len(category_counts) < top_n:
            continue
        results.append({
            "trait_id": entry["trait_id"],
            "category": entry["category"],
            "short_name": entry["short_name"],
            "why_it_may_fit": why_it_may_fit(entry, character),
            "possible_overlap_with_other_characters": overlap,
            "risks": [entry["possible_downside"], entry["overuse_warning"]],
            "suggested_status": suggested_status(entry, development_level),
        })
        category_counts[entry["category"]] = category_counts.get(entry["category"], 0) + 1
        if len(results) >= top_n:
            break
    return results


def existing_trait_terms(data: dict[str, Any]) -> set[str]:
    terms = set()
    for trait in walk_traits(data):
        terms.add(str(trait.get("name", "")).lower())
        terms.update(re.findall(r"[a-z]{4,}", str(trait.get("value", "")).lower()))
    return terms


def overlap_with_cast(entry: dict[str, Any], cast_terms: dict[str, set[str]]) -> list[str]:
    words = set(re.findall(r"[a-z]{4,}", f"{entry['short_name']} {entry['description']}".lower())) - STOPWORDS
    overlaps = []
    for character_id, terms in cast_terms.items():
        if words & terms:
            overlaps.append(character_id)
    return overlaps[:5]


def recommendation_score(entry: dict[str, Any], existing_terms: set[str], visual_text: str, development_level: int,
                         overlap: list[str], character_id: str) -> int:
    score = 50
    if entry["visual_or_dialogue_or_behavioral"] == "visual" and any(word in visual_text for word in re.findall(r"[a-z]{4,}", entry["description"].lower())):
        score += 20
    if development_level <= 1 and entry["category"] in {"signature_pose", "physical_tick", "specific_talent"}:
        score += 16
    if development_level >= 2 and entry["category"] in {"specific_weakness", "relationship_dynamic", "personal_mission"}:
        score += 14
    if entry["category"] in missing_story_roles(existing_terms):
        score += 18
    score -= len(overlap) * 18
    if entry.get("source_character_id") and entry.get("source_character_id") != character_id:
        score -= 100
    if entry["category"] in {"catchphrase", "personal_sound_effect"} and "catchphrase" in existing_terms:
        score -= 20
    return score


def missing_story_roles(existing_terms: set[str]) -> set[str]:
    missing = set()
    if not ({"mission", "goal", "growth"} & existing_terms):
        missing.add("personal_mission")
    if not ({"weakness", "fear", "struggle"} & existing_terms):
        missing.add("specific_weakness")
    if not ({"pose", "gesture", "stands"} & existing_terms):
        missing.add("signature_pose")
    return missing


def why_it_may_fit(entry: dict[str, Any], character: dict[str, Any]) -> str:
    ident = character.get("identification", {})
    level = ident.get("development_level")
    return (
        f"Could give {ident.get('current_display_name')} a {entry['visual_or_dialogue_or_behavioral']} "
        f"tool at development level {level} without making it canon."
    )


def suggested_status(entry: dict[str, Any], development_level: int) -> str:
    if entry["category"] in {"recurring_mystery", "personal_mission"}:
        return "reserved"
    if development_level <= 1 and entry["intensity"] in {"strong", "moderate"}:
        return "optional"
    return "experimental"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build, validate, and recommend MonkeyZoo trait suggestions.")
    parser.add_argument("command", choices=["build", "validate", "recommend"])
    parser.add_argument("character_id", nargs="?")
    args = parser.parse_args()
    if args.command == "build":
        library = build_library()
        errors = validate_library(library)
        if errors:
            print("\n".join(errors))
            return 1
        save_library(library)
        print(f"Wrote {len(library['entries'])} trait suggestions.")
        return 0
    if args.command == "validate":
        errors = validate_library(load_library())
        if errors:
            print("\n".join(errors))
            return 1
        print("Trait library validation passed.")
        return 0
    if not args.character_id:
        parser.error("recommend requires character_id")
    print(json.dumps(recommend_traits(args.character_id), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
