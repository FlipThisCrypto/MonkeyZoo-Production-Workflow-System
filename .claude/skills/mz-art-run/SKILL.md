---
name: mz-art-run
description: Run the MonkeyZoo art stages (6–7) — ComfyUI generation via Z-Image and adversarial Art QA — for an issue whose prompt pack is ready. Use when the user says "run the art stage", "generate the panels", or after mz-new-issue completes.
---

# MonkeyZoo: Art Run (Stages 6–7)

Generate panels with ComfyUI (Z-Image Turbo via ZLUDA) and QA them to
selected_panels. Calibrated on this rig (RX 6800 16GB, ~90s/image warm).

## Engine facts (hard-won — do not rediscover)
- **Engine: Z-Image Turbo bf16** (`z_image_turbo_bf16.safetensors` +
  `qwen_3_4b.safetensors` CLIP type `lumina2` + `z_image_ae.safetensors`).
  8 steps, cfg 1.0, res_multistep/simple, AuraFlow shift 3.0.
- **cfg 1.0 ⇒ negative prompts are INERT.** All guard language must be
  positive-phrased. The batch runner handles this.
- RealVisXL = photorealism (fails style lock). Animagine XL = tag-trained
  (grid-collapses on prose). Both already tried and rejected — see Issue 06
  `generation_log.md`.
- The runner (`00_SYSTEM/scripts/run_art_batch.py --engine zimage`) auto-fixes
  three cfg-1 hazards: lettering clauses render as literal balloons; the words
  "MonkeyZoo house style" render as logo text; characterless panels draw the
  style-lock's monkey (auto plate-style).

## Steps
1. **Server:** `Invoke-WebRequest http://127.0.0.1:8188/system_stats`. If
   down: launch `I:\ai\ComfyUI\run_zluda.bat` in background; first gen after
   cold start takes ~7 min (19GB model load + ZLUDA kernel compile).
2. **Batch:** plates + panels, 2 variants first pass:
   `python 00_SYSTEM/scripts/run_art_batch.py <issue-folder> --engine zimage --variants 2`
   Monitor queue in a background loop (poll `/prompt` → `queue_remaining`).
3. **HANG RECOVERY (ZLUDA):** if queue count freezes >15 min, the GPU is
   wedged. `/interrupt` will NOT free it. Kill the ComfyUI python process
   (`Get-Process python | Where Path -like "I:\ai\ComfyUI*" | Stop-Process
   -Force`) — the run_zluda.bat loop auto-relaunches in ~90s. Requeue ONLY
   missing items (diff output files vs expected, use `--only`).
   **VRAM-LEAK TRAP:** the relaunch can come up with the dead process's VRAM
   still held — server log shows `loaded partially; 0.00 MB usable` and the
   sampler sits at 0% forever. ALWAYS verify recovery: (a) `/system_stats`
   `vram_free` ≈ 15.8GB, and (b) one render actually completes (watch the
   output dir), before trusting a requeued batch. If leaked: kill and
   relaunch again — second restart claims the memory.
4. **Collect:** copy outputs from `I:\ai\nft\output\<ISSUE-ID>/` into
   `generated_art/raw_panels/`.
5. **Art QA (Gate A, `00_SYSTEM/qa_checklist.md`):** build 3×3 contact sheets
   (System.Drawing) to triage cheaply; full-res read only contenders. Judge
   against the bible, not "looks cool". Verify per-character QA checklists
   (hair is identity: white fringe=Ash, black slick=Static, cyan spike
   crown=NeonBlue, red-streak white=Scarline, blue beanie/streak=Moodz,
   black-white split=TwoTone).
6. **Select:** exactly one file per panel → `selected_panels/<panel_id>.png`.
   Rejects → `04_REJECTED_OUTPUTS/rejected_art/` with reasons in qa_report.md.
7. **Reroll** failed panels (fix the producing stage first if the failure is
   systematic — never brute-force seeds). Two failed rerolls → escalate to a
   layout-crop instruction or composition control.
8. **Validate:** `validate_issue.py <folder> --art` must PASS. Update
   `qa_report.md` (per-panel verdict table) + `generation_log.md`. Commit.

## Known residuals & escalation paths
- Rear/back views: Z-Image refuses them — use over-shoulder framing instead.
- Giant-foreground-monkey scale bug in high wide shots: crop at layout;
  long-term fix is Z-Image Fun ControlNet (`ZImageFunControlnet` node exists).
- TwoTone's split hair needs image conditioning; his minted ref is
  `03_APPROVED_CANON/approved_characters/factions/twotone.webp`.
- LoRA training threshold: 20+ approved refs per character (Kohya SS).

## Character-integration compositing (alternative to monolithic generation)
If a panel is a character standing in an *already-approved* location plate
(not a new scene needing full ComfyUI generation), you can composite
instead of generating: `00_SYSTEM/scripts/integration/compositor.py` scales
and grounds a character layer onto the plate via a `scene_blocking.json` +
`pose_spec.json` pair (ground-plane calibration, light sources, foot
anchor), then applies contact shadow, environmental relighting, and
foreground occlusion in sequence. Run
`validate_integration.py <panel.png> <foot_x> <foot_y>` afterward — it
fails on leftover reference/card colors or a missing contact shadow. See
`00_SYSTEM/automation_rules.md` §6A and
`00_SYSTEM/integration_upgrade/CYCLE_LEDGER.md` for the full build record
and current limitations (no bespoke pose generation yet; this uses
existing reference poses).
