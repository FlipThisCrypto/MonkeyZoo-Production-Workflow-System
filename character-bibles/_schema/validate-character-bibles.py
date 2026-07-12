import argparse
import json
import os
import sys
from pathlib import Path

import yaml

TRAIT_STATUSES = {
    "canon", "established", "experimental", "optional", "dormant",
    "retired", "contradicted", "unknown", "reserved",
}
TRAIT_STRENGTHS = {"defining", "strong", "moderate", "subtle", "background"}
USAGE_FREQUENCIES = {
    "almost always", "often", "sometimes", "rarely",
    "special circumstances only", "never",
}
NAMING_STATUSES = {
    "personal_name_canon", "series_name_only", "codename_only",
    "nickname_only", "personal_name_unresolved", "unresolved", "reserved",
}
UNRESOLVED_NAME_STATUSES = {"series_name_only", "codename_only", "personal_name_unresolved", "unresolved", "reserved"}


def load_file(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def iter_bible_files(root):
    for path in root.rglob("*"):
        if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
            continue
        if path.name not in {"bible.json", "bible.yaml", "bible.yml"}:
            continue
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] in {"_schema", "_inventory"}:
            continue
        yield path


def walk_traits(value, location=""):
    if isinstance(value, dict):
        if {"name", "status", "strength", "usage_frequency"}.issubset(value.keys()):
            yield location, value
        for key, child in value.items():
            yield from walk_traits(child, f"{location}.{key}" if location else key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_traits(child, f"{location}[{index}]")


def validate_image(path_value, workspace_root, bible_path, errors):
    if not path_value:
        return
    raw = Path(path_value)
    candidates = [raw] if raw.is_absolute() else [bible_path.parent / raw, workspace_root / raw]
    if not any(candidate.exists() for candidate in candidates):
        errors.append(f"{bible_path}: image reference does not exist: {path_value}")


def collect_character_ids(bibles):
    ids = set()
    for _, data in bibles:
        ident = (data or {}).get("identification", {})
        character_id = ident.get("character_id")
        if character_id:
            ids.add(character_id)
    return ids


def validate_bible(path, data, workspace_root, known_ids):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return [f"{path}: Bible file must contain an object/map"], warnings

    identification = data.get("identification")
    if not isinstance(identification, dict):
        return [f"{path}: missing identification section"], warnings

    for field in ["current_display_name", "naming_status", "character_id", "development_level", "canon_status"]:
        if field not in identification:
            errors.append(f"{path}: missing identification.{field}")

    character_id = identification.get("character_id")
    if not character_id:
        errors.append(f"{path}: every Bible must have a character ID")

    naming_status = identification.get("naming_status")
    if naming_status not in NAMING_STATUSES:
        errors.append(f"{path}: unsupported naming_status: {naming_status}")

    personal_name = identification.get("personal_name")
    if naming_status in UNRESOLVED_NAME_STATUSES and personal_name:
        errors.append(f"{path}: personal_name must remain blank/null while naming_status is {naming_status}")

    level = identification.get("development_level")
    if not isinstance(level, int) or not 1 <= level <= 5:
        errors.append(f"{path}: development_level must be an integer from 1 to 5")

    visual = data.get("visual_canon")
    if not isinstance(visual, dict):
        errors.append(f"{path}: missing visual_canon section")
    else:
        validate_image(visual.get("primary_reference_image"), workspace_root, path, errors)
        for image_path in visual.get("supporting_reference_images", []) or []:
            validate_image(image_path, workspace_root, path, errors)
        if level and level >= 3:
            if not visual.get("features_that_must_never_change"):
                errors.append(f"{path}: Level {level} characters must define visual_canon.features_that_must_never_change")
            if not visual.get("prohibited_visual_additions"):
                errors.append(f"{path}: Level {level} characters must define visual_canon.prohibited_visual_additions")

    for location, trait in walk_traits(data):
        status = trait.get("status")
        strength = trait.get("strength")
        frequency = trait.get("usage_frequency")
        if status not in TRAIT_STATUSES:
            errors.append(f"{path}: unsupported trait status at {location}: {status}")
        if strength not in TRAIT_STRENGTHS:
            errors.append(f"{path}: unsupported trait strength at {location}: {strength}")
        if frequency not in USAGE_FREQUENCIES:
            errors.append(f"{path}: unsupported usage frequency at {location}: {frequency}")

    usage = data.get("issue_level_usage")
    if not isinstance(usage, dict):
        errors.append(f"{path}: missing issue_level_usage section")
    else:
        max_defining = usage.get("maximum_defining_traits_per_issue")
        max_quirks = usage.get("maximum_minor_quirks_per_issue")
        if not isinstance(max_defining, int) or not 0 <= max_defining <= 3:
            errors.append(f"{path}: issue_level_usage.maximum_defining_traits_per_issue must be 0-3")
        if not isinstance(max_quirks, int) or not 0 <= max_quirks <= 4:
            errors.append(f"{path}: issue_level_usage.maximum_minor_quirks_per_issue must be 0-4")
        for cooldown_name in ["catchphrase_cooldown", "running_gag_cooldown"]:
            cooldown = usage.get(cooldown_name)
            if cooldown:
                minimum = cooldown.get("minimum_issues_between_uses")
                if not isinstance(minimum, int) or minimum < 0:
                    errors.append(f"{path}: {cooldown_name}.minimum_issues_between_uses must be a non-negative integer")

    for index, relationship in enumerate(data.get("relationships", []) or []):
        target_id = relationship.get("target_character_id")
        if target_id and target_id not in known_ids:
            warnings.append(f"{path}: relationship[{index}] target ID not found among loaded Bibles: {target_id}")
        status = relationship.get("relationship_status")
        if status and status not in TRAIT_STATUSES:
            errors.append(f"{path}: relationship[{index}] unsupported relationship_status: {status}")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate MonkeyZoo Character Bible YAML/JSON files.")
    parser.add_argument("--root", default="character-bibles", help="Character bibles root directory.")
    parser.add_argument("--workspace-root", default=".", help="Workspace root for relative image paths.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace_root = Path(args.workspace_root).resolve()
    bible_files = list(iter_bible_files(root))
    loaded = []
    errors = []
    warnings = []

    for path in bible_files:
        try:
            loaded.append((path, load_file(path)))
        except Exception as exc:
            errors.append(f"{path}: failed to parse: {exc}")

    known_ids = collect_character_ids(loaded)
    for path, data in loaded:
        file_errors, file_warnings = validate_bible(path, data, workspace_root, known_ids)
        errors.extend(file_errors)
        warnings.extend(file_warnings)

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    print(f"Validated {len(loaded)} Character Bible file(s).")
    if errors:
        print(f"FAILED with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1
    print(f"PASSED with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
