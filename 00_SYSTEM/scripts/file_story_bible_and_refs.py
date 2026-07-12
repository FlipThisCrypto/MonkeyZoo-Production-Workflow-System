from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = REPO_ROOT.parent
APPROVED_ROOT = REPO_ROOT / "03_APPROVED_CANON" / "approved_characters"
SEASON_DIR = REPO_ROOT / "story-bibles" / "seasons" / "2026-emo-monkeys-the-signal-between-us"
CHARACTER_BIBLES_ROOT = WORKSPACE_ROOT / "character-bibles"


CHARACTERS = [
    {
        "id": "MZ-CHAR-001",
        "name": "Moodz",
        "slug": "moodz",
        "role": "Emo Monkey lead; guarded emotional center",
        "status": "approved lead",
        "folder": "03_APPROVED_CANON/approved_characters/moodz/",
    },
    {
        "id": "MZ-CHAR-002",
        "name": "TwoTone",
        "slug": "twotone",
        "role": "Emo Monkey lead; balance analyst",
        "status": "approved lead",
        "folder": "03_APPROVED_CANON/approved_characters/twotone/",
    },
    {
        "id": "MZ-CHAR-003",
        "name": "Static",
        "slug": "static",
        "role": "Emo Monkey lead; signal and code alarm",
        "status": "approved lead",
        "folder": "03_APPROVED_CANON/approved_characters/static/",
    },
    {
        "id": "MZ-CHAR-004",
        "name": "Ash",
        "slug": "ash",
        "role": "Emo Monkey lead; quiet conscience",
        "status": "approved lead",
        "folder": "03_APPROVED_CANON/approved_characters/ash/",
    },
    {
        "id": "MZ-CHAR-005",
        "name": "NeonBlue",
        "slug": "neonblue",
        "role": "Emo Monkey lead; rescuer and believer",
        "status": "approved lead",
        "folder": "03_APPROVED_CANON/approved_characters/neonblue/",
    },
    {
        "id": "MZ-CHAR-006",
        "name": "Scarline",
        "slug": "scarline",
        "role": "Emo Monkey lead; experienced observer-mentor",
        "status": "approved lead",
        "folder": "03_APPROVED_CANON/approved_characters/scarline/",
    },
    {
        "id": "MZ-CHAR-LILDEVIL",
        "name": "Lil Devil",
        "slug": "lil devil",
        "role": "August guest; pressure toward immediate force",
        "status": "guest / faction archetype",
        "folder": "03_APPROVED_CANON/approved_characters/lil devil/",
    },
    {
        "id": "MZ-CHAR-CLEVER",
        "name": "Clever",
        "slug": "clever",
        "role": "September guest; technical validator",
        "status": "guest / faction archetype; only confirmed glasses-wearing monkey",
        "folder": "03_APPROVED_CANON/approved_characters/clever/",
    },
    {
        "id": "MZ-CHAR-ZOMBIE",
        "name": "Zombie",
        "slug": "zombie",
        "role": "October guest; old FusionZoo witness",
        "status": "guest / faction archetype",
        "folder": "03_APPROVED_CANON/approved_characters/zombie/",
    },
    {
        "id": "MZ-CHAR-CHEEKY",
        "name": "Cheeky",
        "slug": "cheeky",
        "role": "November guest; humor and crowd redirection",
        "status": "guest / faction archetype",
        "folder": "03_APPROVED_CANON/approved_characters/cheeky/",
    },
    {
        "id": "MZ-CHAR-SUPER",
        "name": "Super Monkey",
        "slug": "super",
        "role": "December guest; visible physical rescue with limits",
        "status": "guest / faction archetype",
        "folder": "03_APPROVED_CANON/approved_characters/super/",
    },
    {
        "id": "MZ-CHAR-PATCH",
        "name": "Patch",
        "slug": "patch",
        "role": "NeonBlue/Pending/FusionZoo open thread",
        "status": "issue-derived supporting character; visual reference requires owner review",
        "folder": "character-bibles/MZ-CHAR-PATCH/references/",
    },
    {
        "id": "MZ-CHAR-EMO-GENERIC",
        "name": "Generic Emo Monkey",
        "slug": "emo",
        "role": "Faction/background reference, not one of the six named leads",
        "status": "faction archetype",
        "folder": "03_APPROVED_CANON/approved_characters/emo/",
    },
]


SOURCE_IMAGE_MAP = {
    "cheeky": [
        "cheeky.png",
        "Cartoon Monkey #51 in Teal Shorts.png",
        "Cartoon_Monkey__51_in_Teal_Shorts-removebg-preview.png",
    ],
    "clever": [
        "clever.png",
        "Cool Cartoon Monkey Character.png",
        "Cool_Cartoon_Monkey_Character-removebg-preview.png",
        "Cartoon Monkey with Pi Shirt.png",
        "Cartoon_Monkey_with_Pi_Shirt-removebg-preview.png",
    ],
    "emo": ["emo.png"],
    "lil devil": [
        "lil devil.png",
        "Devilish Monkey #424.png",
        "Devilish_Monkey__424-removebg-preview.png",
    ],
    "super": [
        "super.png",
        "Superhero Monkey with Red Mask.png",
        "Superhero_Monkey_with_Red_Mask-removebg-preview.png",
        "cape.png",
        "cape-removebg-preview.png",
    ],
    "zombie": [
        "zombie.png",
        "Zombie Monkey in Tattered Clothing.png",
        "Zombie_Monkey_in_Tattered_Clothing-removebg-preview.png",
    ],
    "_groups": ["Fusion Squad.png"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(WORKSPACE_ROOT).as_posix()


def copy_if_present(src: Path, dest: Path) -> dict | None:
    if not src.exists():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or sha256(src) != sha256(dest):
        shutil.copy2(src, dest)
    return {
        "source_path": rel(src),
        "filed_path": rel(dest),
        "sha256": sha256(dest),
        "bytes": dest.stat().st_size,
    }


def file_season_bible() -> None:
    SEASON_DIR.mkdir(parents=True, exist_ok=True)
    source = REPO_ROOT / "MonkeyZoo_Emo_Monkeys_Season_Bible.md"
    filed = SEASON_DIR / "SEASON-BIBLE.md"
    if source.exists():
        source_text = source.read_text(encoding="utf-8")
        source_is_pointer = "Canonical filed copy:" in source_text
        if not source_is_pointer:
            filed.write_text(source_text, encoding="utf-8")
            source.write_text(
                "# MonkeyZoo Emo Monkeys Season Bible\n\n"
                "Canonical filed copy:\n\n"
                "`story-bibles/seasons/2026-emo-monkeys-the-signal-between-us/SEASON-BIBLE.md`\n\n"
                "This root-level file is a pointer so the story bible is not maintained in two places.\n",
                encoding="utf-8",
            )
        elif not filed.exists():
            raise RuntimeError(
                "Root season bible is already a pointer, but the filed SEASON-BIBLE.md is missing."
            )
    metadata = {
        "season_id": "2026-emo-monkeys-the-signal-between-us",
        "title": "Emo Monkeys: The Signal Between Us",
        "span": "August 2026 through January 2027",
        "format": "six connected monthly comic issues",
        "canon_status": "story-development document; new facts remain proposed until approved",
        "primary_cast": ["Moodz", "TwoTone", "Static", "Ash", "NeonBlue", "Scarline"],
        "guest_characters": ["Lil Devil", "Clever", "Zombie", "Cheeky", "Super Monkey"],
        "open_threads": ["Patch", "The Echo", "Relay 1", "The Pending", "the Keeper"],
        "character_source_of_truth": "character-bibles/MZ-CHAR-*/bible.yaml",
        "image_source_of_truth": "MonkeyZoo_Comic_Factory/03_APPROVED_CANON/approved_characters/",
        "continuity_source_of_truth": "MonkeyZoo_Comic_Factory/00_SYSTEM/continuity_ledger.md",
        "official_external_sources": [
            "https://monkeyzoo.net/",
            "https://monkeyzoo.net/what-is-nft-fusion/",
            "https://monkeyzoo.net/learn/",
        ],
    }
    (SEASON_DIR / "season-metadata.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (SEASON_DIR / "README.md").write_text(
        "# Emo Monkeys: The Signal Between Us\n\n"
        "This folder is the filed home for the August 2026-January 2027 Emo Monkeys season bible.\n\n"
        "- `SEASON-BIBLE.md` is the narrative season plan.\n"
        "- `season-metadata.yaml` is the machine-readable season header.\n"
        "- `CHARACTER-AND-REFERENCE-INDEX.md` lists who each character is and where production should find references.\n"
        "- `continuity-map.md`, `echo-mystery-tracker.md`, `character-growth-tracker.md`, and `guest-appearance-tracker.md` give production quick-reference views.\n"
        "- `issue-01-neonblue.md` through `issue-06-twotone.md` are the per-issue working stubs.\n"
        "- Character canon still lives in `character-bibles/MZ-CHAR-*/bible.yaml`.\n"
        "- Official website context is summarized in `source_of_truth/official-monkeyzoo-web-sources.md`.\n"
        "- Production canon and hard rules still live in `00_SYSTEM/`.\n",
        encoding="utf-8",
    )


def file_source_images() -> list[dict]:
    filed: list[dict] = []
    for slug, names in SOURCE_IMAGE_MAP.items():
        target_dir = APPROVED_ROOT / slug / "source_images"
        if slug == "_groups":
            target_dir = APPROVED_ROOT / "_groups" / "source_images"
        for name in names:
            src = WORKSPACE_ROOT / name
            dest = target_dir / safe_name(name)
            record = copy_if_present(src, dest)
            if record:
                record["character_or_group"] = slug
                record["source_type"] = "loose local source image copied for provenance"
                filed.append(record)
    return filed


def safe_name(name: str) -> str:
    return (
        name.replace("#", "No")
        .replace(" ", "_")
        .replace("__", "_")
        .replace(",", "")
    )


def file_patch_reference() -> dict | None:
    src = WORKSPACE_ROOT / "zombie.png"
    dest = CHARACTER_BIBLES_ROOT / "MZ-CHAR-PATCH" / "references" / "primary" / "primary-reference.png"
    record = copy_if_present(src, dest)
    if not record:
        return None
    record.update({
        "character_id": "MZ-CHAR-PATCH",
        "character": "Patch",
        "confidence": "medium-high",
        "source_evidence": [
            "MonkeyZoo_Comic_Factory/02_MONTHLY_ISSUES/2026-07_Issue_05/page_panel_plan.json",
            "MonkeyZoo_Comic_Factory/02_MONTHLY_ISSUES/2026-07_Issue_05/issue_script.md",
            "MonkeyZoo_Comic_Factory/02_MONTHLY_ISSUES/2026-08_Issue_06/issue_script.md",
        ],
        "notes": "Issue plans identify `zombie.png (#1997 = Patch)`. This is filed as Patch's issue-derived reference, not as permission to treat every zombie image as Patch.",
    })
    source_map_path = CHARACTER_BIBLES_ROOT / "MZ-CHAR-PATCH" / "references" / "source-map.json"
    source_map_path.write_text(
        json.dumps({"character_id": "MZ-CHAR-PATCH", "character": "Patch", "sources": [record]}, indent=2),
        encoding="utf-8",
    )
    patch_bible = CHARACTER_BIBLES_ROOT / "MZ-CHAR-PATCH" / "bible.yaml"
    if patch_bible.exists():
        data = yaml.safe_load(patch_bible.read_text(encoding="utf-8"))
        visual = data.setdefault("visual_canon", {})
        visual["primary_reference_image"] = "references/primary/primary-reference.png"
        visual["supporting_reference_images"] = visual.get("supporting_reference_images") or []
        visual["glasses_status"] = visual.get("glasses_status") or "unknown"
        notes = data.setdefault("source_notes", [])
        patch_note = "Patch primary reference filed from issue evidence: `zombie.png (#1997 = Patch)`. Owner should review whether this is final individual art or a faction-derived placeholder."
        if patch_note not in notes:
            notes.append(patch_note)
        patch_bible.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110),
            encoding="utf-8",
        )
    return record


def write_character_index(source_records: list[dict], patch_record: dict | None) -> None:
    manifest = {
        "schema_version": "1.0",
        "purpose": "Character identity and image reference map for the actual MonkeyZoo production workflow.",
        "characters": [],
        "filed_loose_source_images": source_records,
        "patch_reference": patch_record,
        "notes": [
            "Character Bibles remain the character canon source of truth.",
            "03_APPROVED_CANON/approved_characters is the production image reference source for IPAdapter/LoRA and prompt packs.",
            "source_images folders preserve loose local source cards; use numbered pose files for production identity unless source evidence says otherwise.",
            "Patch uses an issue-derived reference and remains owner-review for final individual visual identity.",
        ],
    }
    lines = [
        "# MonkeyZoo Character And Image Reference Index",
        "",
        "This page marks who each character is and where production should find their images.",
        "",
        "Canon rule: Character Bibles define personality and continuity. `03_APPROVED_CANON/approved_characters/` defines image references for generation. `source_images/` preserves original loose cards and source art for provenance.",
        "",
        "| Character | ID | Role in current workflow | Status | Production image folder | Primary production ref | Source images |",
        "|---|---|---|---|---|---|---|",
    ]
    for char in CHARACTERS:
        folder = REPO_ROOT / char["folder"]
        if char["folder"].startswith("character-bibles/"):
            folder = WORKSPACE_ROOT / char["folder"]
        primary = first_primary(folder, char["slug"])
        source_count = len([r for r in source_records if r.get("character_or_group") == char["slug"]])
        if char["id"] == "MZ-CHAR-PATCH" and patch_record:
            primary = patch_record["filed_path"]
            source_count += 1
        manifest["characters"].append({
            **char,
            "primary_reference": primary,
            "source_image_count": source_count,
        })
        lines.append(
            f"| {char['name']} | `{char['id']}` | {char['role']} | {char['status']} | `{char['folder']}` | `{primary or 'missing / owner review'}` | {source_count} |"
        )
    lines.extend([
        "",
        "## Patch Filing Note",
        "",
        "Patch comes from Issue 05/06 continuity. The issue plan names `zombie.png (#1997 = Patch)`, so that image is copied into `character-bibles/MZ-CHAR-PATCH/references/primary/primary-reference.png` with source-map notes. This does not mean every Zombie or Stayed image is Patch.",
        "",
        "## Workflow Use",
        "",
        "1. Story planning reads `story-bibles/seasons/.../SEASON-BIBLE.md` plus Character Bibles.",
        "2. Continuity checks read `00_SYSTEM/continuity_ledger.md` and proposed post-issue updates.",
        "3. Art direction reads this index and the approved character folders.",
        "4. Generation uses approved pose/reference files, not unreviewed loose images.",
        "5. QA writes corrections back into the ledger and Character Bible review system; nothing becomes canon automatically.",
    ])
    (APPROVED_ROOT / "CHARACTER_IMAGE_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (APPROVED_ROOT / "character-image-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (SEASON_DIR / "CHARACTER-AND-REFERENCE-INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def first_primary(folder: Path, slug: str) -> str | None:
    candidates = [
        folder / f"{folder.name}_00_clean_base.png",
        folder / f"{slug}_00_clean_base.png",
        folder / f"{slug}.webp",
        folder / f"{slug}.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return rel(candidate)
    if folder.exists():
        for candidate in sorted(folder.glob("*.png")) + sorted(folder.glob("*.webp")):
            return rel(candidate)
    return None


def main() -> None:
    file_season_bible()
    source_records = file_source_images()
    patch_record = file_patch_reference()
    write_character_index(source_records, patch_record)
    print(json.dumps({
        "season_folder": rel(SEASON_DIR),
        "source_images_filed": len(source_records),
        "patch_reference_filed": bool(patch_record),
        "character_index": rel(APPROVED_ROOT / "CHARACTER_IMAGE_INDEX.md"),
    }, indent=2))


if __name__ == "__main__":
    main()
