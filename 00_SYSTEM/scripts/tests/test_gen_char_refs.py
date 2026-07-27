"""Characterization of the character-reference workflow builder (gen_char_refs).

build() generates the standardized pose/expression plates that accumulate toward
the LoRA-training threshold, so its graph must stay correct. It was untested;
these pin the behaviours that are specific to this builder (distinct from the
Stage-6 panel builder): the txt2img vs img2img latent wiring, the denoise
pass-through, and the composed prompt (base identity + hair + variant + colour
background + no-text tail). Reproducibility invariants (seed in sampler,
seeded filename_prefix, zeroed negative) are pinned too.
"""
from __future__ import annotations

import sys
import types
import urllib.error
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]  # 00_SYSTEM/scripts
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import gen_char_refs as gcr  # noqa: E402

CHAR = {"hair": "HAIR-DESCRIPTOR", "bg": "flat solid warm orange background", "seed": 100001}


def _build(**over):
    kw = dict(name="ash", char=CHAR, vkey="01_neutral", vdesc="standing facing viewer",
              seed=100001, denoise=1.0, init=None)
    kw.update(over)
    return gcr.build(**kw)


def test_prompt_composes_identity_hair_variant_background_and_no_text_tail():
    text = _build()["4"]["inputs"]["text"]
    assert text.startswith(gcr.BASE)
    assert "HAIR-DESCRIPTOR" in text
    assert "standing facing viewer" in text
    assert "flat solid warm orange background" in text
    assert text.endswith(gcr.TAIL)
    assert "no text" in text and "no logo anywhere" in text


def test_seed_and_seeded_filename_prefix():
    wf = _build(seed=100015)
    assert wf["8"]["inputs"]["seed"] == 100015
    assert wf["10"]["inputs"]["filename_prefix"] == "MZ-REFS/ash_01_neutral_seed100015"


def test_negative_is_zeroed_conditioning():
    wf = _build()
    assert wf["5"]["class_type"] == "ConditioningZeroOut"
    assert wf["8"]["inputs"]["negative"] == ["5", 0]


def test_txt2img_uses_empty_latent_and_no_image_load_nodes():
    wf = _build(init=None)
    assert wf["6"]["class_type"] == "EmptySD3LatentImage"
    assert (wf["6"]["inputs"]["width"], wf["6"]["inputs"]["height"]) == (832, 1216)
    assert "11" not in wf and "12" not in wf          # no LoadImage / ImageScale
    assert wf["8"]["inputs"]["latent_image"] == ["6", 0]


def test_img2img_wires_init_through_scale_and_encode():
    wf = _build(init="ash.png", denoise=0.70)
    assert wf["11"]["class_type"] == "LoadImage"
    assert wf["11"]["inputs"]["image"] == "ash.png"
    assert wf["12"]["class_type"] == "ImageScale"
    assert wf["12"]["inputs"]["image"] == ["11", 0]
    assert wf["6"]["class_type"] == "VAEEncode"        # latent comes from the init, not empty
    assert wf["6"]["inputs"]["pixels"] == ["12", 0]
    assert wf["8"]["inputs"]["latent_image"] == ["6", 0]


def test_denoise_is_passed_to_the_sampler():
    assert _build(init="ash.png", denoise=0.85)["8"]["inputs"]["denoise"] == 0.85
    assert _build(init=None, denoise=1.0)["8"]["inputs"]["denoise"] == 1.0


def test_turbo_recipe_constants_are_locked():
    # Z-Image Turbo: 8 steps, cfg 1, AuraFlow shift 3 — the calibrated recipe.
    wf = _build()
    assert wf["8"]["inputs"]["steps"] == 8
    assert wf["8"]["inputs"]["cfg"] == 1.0
    assert wf["7"]["inputs"]["shift"] == 3.0


# ---- queue + run_batch: connection resilience and submission accounting -------

def _bargs(**over):
    base = dict(dry_run=False, img2img=False, denoise=0.0, host="127.0.0.1:8188")
    base.update(over)
    return types.SimpleNamespace(**base)


def test_queue_returns_node_errors_instead_of_crashing_on_connection_failure(monkeypatch):
    def boom(req, timeout=None):
        raise urllib.error.URLError("Connection refused")
    monkeypatch.setattr(gcr.urllib.request, "urlopen", boom)
    resp = gcr.queue("127.0.0.1:9", {"1": {}})
    assert "node_errors" in resp                 # degrades to an error response, no traceback
    assert "connection" in resp["node_errors"]


def test_run_batch_counts_all_ok():
    def q(host, wf): return {}
    out = gcr.run_batch(["ash", "moodz"], ["01_neutral"], _bargs(), queue_fn=q)
    assert out == {"ok": 2, "failed": 0}         # 2 characters x 1 selected variant


def test_run_batch_counts_failures_separately():
    def q(host, wf): return {"node_errors": {"connection": "refused"}}
    out = gcr.run_batch(["ash"], ["01_neutral", "02_threeqtr"], _bargs(), queue_fn=q)
    assert out == {"ok": 0, "failed": 2}


def test_run_batch_dry_run_submits_nothing():
    called = {"n": 0}
    def q(host, wf): called["n"] += 1; return {}
    out = gcr.run_batch(["ash"], ["01_neutral"], _bargs(dry_run=True), queue_fn=q)
    assert out == {"ok": 0, "failed": 0}
    assert called["n"] == 0
