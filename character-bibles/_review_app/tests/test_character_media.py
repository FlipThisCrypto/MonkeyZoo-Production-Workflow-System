import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "character-bibles" / "_review_app"
sys.path.insert(0, str(APP))
import app as review_app
import bible_store

EXPECTED = {
    "MZ-CHAR-ZOMBIE": ("Patch", "Zombie", "American", "United States of America"),
    "MZ-CHAR-CLEVER": ("Lily", "Clever", "Scottish", "Scotland"),
    "MZ-CHAR-LILDEVIL": ("Sasha", "Lil Devil", "Russian", "Russia"),
    "MZ-CHAR-SUPER": ("Maxx", "Super", "Canadian", "Canada"),
    "MZ-CHAR-CHEEKY": ("Japes", "Cheeky", "British", "United Kingdom"),
}


def test_owner_approved_identity_and_portrait_mapping():
    records = {cid: bible_store.character_summary(cid, data) for cid, data in bible_store.load_all(ROOT / "character-bibles")}
    assert "MZ-CHAR-PATCH" not in records
    assert len(records) == 11
    for cid, expected in EXPECTED.items():
        record = records[cid]
        assert (record["display_name"], record["legacy_label"], record["nationality"], record["country_of_origin"]) == expected
        assert record["image_status"] == "approved"
        assert "group-fusion-squad" not in record["primary_image"].lower()


def test_patch_alias_is_canonical_and_manifest_is_resolved():
    bibles = ROOT / "character-bibles"
    assert bible_store.resolve_character_id("MZ-CHAR-PATCH", bibles) == "MZ-CHAR-ZOMBIE"
    assert bible_store.resolve_character_id("Patch", bibles) == "MZ-CHAR-ZOMBIE"
    assert bible_store.resolve_character_id("Zombie", bibles) == "MZ-CHAR-ZOMBIE"
    alias = __import__("yaml").safe_load((bibles / "MZ-CHAR-PATCH" / "bible.yaml").read_text(encoding="utf-8"))
    assert alias["visual_canon"]["primary_reference_image"] is None
    assert bible_store.load_bible("MZ-CHAR-PATCH", bibles)["identification"]["character_id"] == "MZ-CHAR-ZOMBIE"
    manifest = json.loads((ROOT / "03_APPROVED_CANON" / "approved_characters" / "character-image-manifest.json").read_text(encoding="utf-8"))
    independent = [item for item in manifest["characters"] if not item.get("canonical_id") and item["id"] != "MZ-CHAR-EMO-GENERIC"]
    assert len(independent) == 11
    text = json.dumps(manifest).casefold()
    assert "patch uses an issue-derived reference" not in text
    assert "patch" not in " ".join(part for part in ("requires owner review", "unresolved visual identity") if part in text)


def test_local_portraits_return_correct_mime_and_bytes():
    client = review_app.app.test_client()
    records = client.get("/api/characters").get_json()
    assert len({item["character_id"] for item in records}) == len(records)
    for record in records:
        assert record["primary_image"] or record["image_status"] == "unavailable"
        if record["primary_image"]:
            response = client.get(record["primary_image"])
            assert response.status_code == 200
            assert response.mimetype in {"image/png", "image/webp"}
            assert response.data
    alias_response = client.get("/api/characters/MZ-CHAR-PATCH")
    assert alias_response.status_code == 200
    assert alias_response.get_json()["summary"]["character_id"] == "MZ-CHAR-ZOMBIE"


def test_static_export_matches_local_inventory(tmp_path):
    spec = importlib.util.spec_from_file_location("export_static_characters", ROOT / "docs" / "export_static_characters.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workspace = tmp_path / "workspace"
    (workspace / "character-bibles").mkdir(parents=True)
    for source in (ROOT / "character-bibles").glob("MZ-CHAR-*"):
        import shutil
        shutil.copytree(source, workspace / "character-bibles" / source.name)
    (workspace / "docs" / "static").mkdir(parents=True)
    records = module.export(workspace)
    assert {item["character_id"] for item in records} == {cid for cid, _ in bible_store.load_all(ROOT / "character-bibles")}
    for item in records:
        url = item["primary_image"]
        assert not url or (url.startswith("./media/") and ":\\" not in url and not url.startswith("/media/") and "Fusion" not in url)
        if url:
            assert (workspace / "docs" / url.removeprefix("./")).is_file()
