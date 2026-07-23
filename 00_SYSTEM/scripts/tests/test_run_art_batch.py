"""Characterization of the Stage-6 ComfyUI workflow builder (run_art_batch).

build_workflow() turns one panel of a promoted art_prompt_pack into a ComfyUI
API graph. It drives every generated panel of every issue and was untested, so a
refactor could silently break reproducibility or overwrite outputs. These pin the
load-bearing invariants:
  * the reroll seed lands in the sampler node (seed, seed+1, ... per variant),
  * the SaveImage filename_prefix is <issue_id>/<panel_id>_seed<seed> so distinct
    seeds never overwrite each other,
  * resolution parses (default + explicit WxH),
  * SDXL keeps a real negative prompt (with optional suffix),
  * the Z-Image Turbo path strips the character lock's logo-prone prefix, drops
    lettering/SFX clauses that cfg=1 would render literally, appends the no-text
    guard, and zeroes the negative via ConditioningZeroOut.
The prompt slicing here assumes prompts lead with the style lock — which the
art-prompt validator (iterations 36/37) now guarantees.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_art_batch as rab  # noqa: E402

LOCK = ("MonkeyZoo house style: chibi cartoon monkey, thick outlines, "
        "dark cartoon sci-fi cyberpunk backdrop")


def _args(**over):
    base = dict(plate_style="", style_prefix="", neg_suffix="", engine="sdxl",
                steps=28, cfg=6.0, checkpoint="animagine-xl-4.0.safetensors",
                variants=1, dry_run=False, host="127.0.0.1:8188")
    base.update(over)
    return types.SimpleNamespace(**base)


def _pack(**over):
    p = {"issue_id": "MZ-2026-08-06", "style_lock_phrase": LOCK}
    p.update(over)
    return p


def _panel(**over):
    pa = {"panel_id": "MZ-2026-08-06_P03_PANEL02", "page_number": 3, "panel_number": 2,
          "character_tokens": ["MZ-CHAR-001"], "prompt": LOCK + ", Moodz at the mast",
          "negative_prompt": "photorealistic, extra limbs"}
    pa.update(over)
    return pa


# ---- SDXL path -------------------------------------------------------------

def test_sdxl_seed_and_filename_prefix():
    wf = rab.build_workflow(_panel(), _pack(), _args(), seed=774)
    assert wf["5"]["inputs"]["seed"] == 774
    assert wf["7"]["inputs"]["filename_prefix"] == "MZ-2026-08-06/MZ-2026-08-06_P03_PANEL02_seed774"


def test_sdxl_default_resolution_and_steps_cfg():
    wf = rab.build_workflow(_panel(), _pack(), _args(steps=30, cfg=7.5), seed=1)
    assert (wf["4"]["inputs"]["width"], wf["4"]["inputs"]["height"]) == (1216, 832)
    assert wf["5"]["inputs"]["steps"] == 30
    assert wf["5"]["inputs"]["cfg"] == 7.5


def test_sdxl_explicit_resolution():
    wf = rab.build_workflow(_panel(resolution="832x1216"), _pack(), _args(), seed=1)
    assert (wf["4"]["inputs"]["width"], wf["4"]["inputs"]["height"]) == (832, 1216)


def test_sdxl_positive_and_negative_prompt_wired():
    wf = rab.build_workflow(_panel(), _pack(), _args(neg_suffix="blurry"), seed=1)
    assert wf["2"]["inputs"]["text"].startswith(LOCK)
    assert wf["3"]["inputs"]["text"] == "photorealistic, extra limbs, blurry"


def test_sdxl_style_prefix_inserted_after_lock():
    wf = rab.build_workflow(_panel(), _pack(), _args(style_prefix="masterpiece, anime"), seed=1)
    text = wf["2"]["inputs"]["text"]
    assert text.startswith(LOCK + ", masterpiece, anime")  # lock preserved, prefix after it


def test_variants_produce_distinct_prefixes():
    prefixes = {rab.build_workflow(_panel(), _pack(), _args(), seed=100 + v)["7"]["inputs"]["filename_prefix"]
                for v in range(3)}
    assert len(prefixes) == 3  # no collisions across the reroll variants


# ---- Z-Image Turbo path ----------------------------------------------------

def test_zimage_seed_steps_cfg_and_prefix():
    wf = rab.build_workflow(_panel(), _pack(), _args(engine="zimage"), seed=42)
    assert wf["8"]["inputs"]["seed"] == 42
    assert wf["8"]["inputs"]["steps"] == 8
    assert wf["8"]["inputs"]["cfg"] == 1.0
    assert wf["10"]["inputs"]["filename_prefix"].endswith("_seed42")


def test_zimage_strips_lock_prefix_and_adds_no_text_guard():
    wf = rab.build_workflow(_panel(), _pack(), _args(engine="zimage"), seed=1)
    text = wf["4"]["inputs"]["text"]
    assert "MonkeyZoo house style:" not in text     # logo-prone prefix removed
    assert "no text, no letters, no words" in text  # anti-lettering guard appended


def test_zimage_drops_lettering_and_sfx_clauses():
    panel = _panel(prompt=LOCK + ", Moodz shouts, clear for two balloons, SFX BOOM, tense")
    wf = rab.build_workflow(panel, _pack(), _args(engine="zimage"), seed=1)
    text = wf["4"]["inputs"]["text"]
    assert "clear for" not in text
    assert "balloon" not in text.lower()
    assert "SFX" not in text
    assert "tense" in text  # legitimate content survives


def test_zimage_negative_is_zeroed_not_textual():
    wf = rab.build_workflow(_panel(), _pack(), _args(engine="zimage"), seed=1)
    # turbo ignores negatives: node 5 zeroes the positive conditioning and the
    # sampler's negative points at it, rather than encoding negative_prompt text.
    assert wf["5"]["class_type"] == "ConditioningZeroOut"
    assert wf["8"]["inputs"]["negative"] == ["5", 0]


def test_zimage_characterless_panel_uses_plate_lock():
    panel = _panel(character_tokens=[], prompt=LOCK + ", empty relay courtyard at dusk")
    wf = rab.build_workflow(panel, _pack(), _args(engine="zimage"), seed=1)
    text = wf["4"]["inputs"]["text"]
    assert "chibi cartoon monkey" not in text            # monkey-describing lock dropped
    assert "empty relay courtyard at dusk" in text        # scene body retained


# ---- run_batch: submission accounting (observability / exit-code correctness) --

def _panels(n):
    return [_panel(panel_id=f"P{i:02d}", panel_number=i, seed=100 + i) for i in range(n)]


def test_run_batch_counts_all_ok():
    calls = []
    def q(host, wf): calls.append(host); return {}          # empty response = accepted
    out = rab.run_batch(_pack(), _panels(3), _args(variants=2), queue_fn=q)
    assert out == {"ok": 6, "failed": 0}
    assert len(calls) == 6


def test_run_batch_counts_submission_failures_separately():
    def q(host, wf): return {"node_errors": {"connection": "refused"}}
    out = rab.run_batch(_pack(), _panels(2), _args(variants=1), queue_fn=q)
    assert out == {"ok": 0, "failed": 2}                     # errors are NOT counted as queued


def test_run_batch_mixed_ok_and_failed():
    seen = {"n": 0}
    def q(host, wf):
        seen["n"] += 1
        return {} if seen["n"] % 2 else {"node_errors": {"x": "y"}}
    out = rab.run_batch(_pack(), _panels(2), _args(variants=2), queue_fn=q)  # 4 submissions
    assert out["ok"] + out["failed"] == 4
    assert out["failed"] == 2


def test_run_batch_dry_run_submits_nothing():
    called = {"n": 0}
    def q(host, wf): called["n"] += 1; return {}
    out = rab.run_batch(_pack(), _panels(3), _args(variants=2, dry_run=True), queue_fn=q)
    assert out == {"ok": 0, "failed": 0}
    assert called["n"] == 0                                  # dry-run never contacts ComfyUI


# ---- load_pack: clean operator-facing errors instead of tracebacks ------------

def _issue_with_pack(tmp_path, content):
    d = tmp_path / "02_MONTHLY_ISSUES" / "2026-08_Issue_06"
    d.mkdir(parents=True)
    if content is not None:
        (d / "art_prompt_pack.json").write_text(content, encoding="utf-8")
    return tmp_path


def test_load_pack_missing_pack_is_actionable(tmp_path):
    factory = _issue_with_pack(tmp_path, None)  # folder exists, pack does not
    with pytest.raises(SystemExit, match="No art_prompt_pack.json"):
        rab.load_pack("2026-08_Issue_06", factory)


def test_load_pack_missing_issue_folder_is_clean(tmp_path):
    with pytest.raises(SystemExit, match="No art_prompt_pack.json"):
        rab.load_pack("2099-01_Issue_99", tmp_path)


def test_load_pack_malformed_json_is_clean(tmp_path):
    factory = _issue_with_pack(tmp_path, "{not valid json")
    with pytest.raises(SystemExit, match="Malformed art_prompt_pack.json"):
        rab.load_pack("2026-08_Issue_06", factory)


def test_load_pack_no_panels_is_clean(tmp_path):
    factory = _issue_with_pack(tmp_path, json.dumps({"issue_id": "x", "panels": []}))
    with pytest.raises(SystemExit, match="no panels"):
        rab.load_pack("2026-08_Issue_06", factory)


def test_load_pack_valid_returns_pack(tmp_path):
    factory = _issue_with_pack(tmp_path, json.dumps({"issue_id": "x", "panels": [{"panel_id": "P1"}]}))
    pack = rab.load_pack("2026-08_Issue_06", factory)
    assert pack["panels"][0]["panel_id"] == "P1"
