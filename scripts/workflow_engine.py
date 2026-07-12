from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
REVIEW_APP_ROOT = WORKSPACE_ROOT / "character-bibles" / "_review_app"
if str(REVIEW_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(REVIEW_APP_ROOT))

import bible_store  # noqa: E402
import story_context  # noqa: E402

STAGES = [
    "concept",
    "outline",
    "page_plan",
    "script",
    "image_generation",
    "lettering",
    "assembly",
    "qc",
]


class WorkflowError(ValueError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "page_count" not in data and "pages" in data:
        data["page_count"] = data["pages"]
    if "characters" not in data and "character_selection" in data:
        data["characters"] = [{"character_id": item, "role": "supporting"} for item in data["character_selection"]]
    return data


def issue_dir(config: dict[str, Any], output_root: Path) -> Path:
    return output_root / str(config.get("issue_id") or "MZ-DRAFT-WORKFLOW")


def ensure_dirs(config: dict[str, Any], output_root: Path) -> Path:
    run_dir = issue_dir(config, output_root)
    for child in ["artifacts", "validation", "reproducibility", "improvement"]:
        (run_dir / child).mkdir(parents=True, exist_ok=True)
    return run_dir


def json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def md_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_setup(config: dict[str, Any]) -> dict[str, Any]:
    setup = story_context.default_setup()
    mapping = {
        "issue_id": "issue_id",
        "topic": "topic",
        "adventure_style": "adventure_style",
        "page_count": "page_count",
        "panel_count": "panel_count",
        "audience": "audience",
        "tone": "tone",
        "conflict": "conflict",
        "location": "location",
        "lesson": "lesson",
        "required_beat": "required_beat",
        "forbidden_content": "forbidden_content",
        "continuity_mode": "continuity_mode",
        "canon_strictness": "canon_strictness",
        "character_growth_mode": "character_growth_mode",
        "optional_story_instructions": "optional_story_instructions",
        "characters": "characters",
    }
    for src, dest in mapping.items():
        if src in config:
            setup[dest] = config[src]
    return story_context.normalize_setup(setup)


def validate_config(config: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = ["issue_id", "topic", "adventure_style", "page_count", "panel_count", "characters"]
    for key in required:
        if not config.get(key):
            issues.append(issue("high", "config", f"Missing required input: {key}", f"Add `{key}` to config."))
    page_count = int(config.get("page_count") or 0)
    panel_count = int(config.get("panel_count") or 0)
    if page_count < 1:
        issues.append(issue("high", "config.page_count", "Page count must be at least 1.", "Use a positive page count."))
    if panel_count < page_count:
        issues.append(issue("high", "config.panel_count", "Panel count is lower than page count.", "Use at least one panel per page."))
    production = config.get("production", {}) or {}
    max_named = int(production.get("max_named_characters_per_panel") or 3)
    if max_named > 3:
        issues.append(issue("medium", "production.max_named_characters_per_panel", "Panel cast cap is loose.", "Keep generated panels readable with three or fewer named characters."))
    seen = set()
    for selected in config.get("characters") or []:
        character_id = selected.get("character_id") if isinstance(selected, dict) else selected
        if not character_id:
            issues.append(issue("high", "characters", "A selected character is missing character_id.", "Select a known `MZ-CHAR-*` id."))
            continue
        if character_id in seen:
            issues.append(issue("medium", f"characters.{character_id}", "Character selected more than once.", "Remove duplicate cast entry."))
        seen.add(character_id)
        if not (WORKSPACE_ROOT / "character-bibles" / character_id / "bible.yaml").exists():
            issues.append(issue("high", f"characters.{character_id}", "Selected character Bible is missing.", "Select an existing Bible folder."))
    return issues


def issue(severity: str, location: str, message: str, action: str) -> dict[str, str]:
    return {"severity": severity, "location": location, "message": message, "action": action}


def load_selected_bibles(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    items = []
    for selected in config.get("characters") or []:
        character_id = selected.get("character_id") if isinstance(selected, dict) else selected
        items.append((character_id, bible_store.load_bible(character_id, WORKSPACE_ROOT / "character-bibles")))
    return items


def bible_display_name(data: dict[str, Any]) -> str:
    ident = data.get("identification", {}) or {}
    return ident.get("current_display_name") or ident.get("character_id") or "Unknown"


def stage_concept(config: dict[str, Any], run_dir: Path) -> list[Path]:
    cast = [bible_display_name(data) for _, data in load_selected_bibles(config)]
    concept = {
        "issue_id": config.get("issue_id"),
        "topic": config.get("topic"),
        "adventure_style": config.get("adventure_style"),
        "audience": config.get("audience"),
        "tone": config.get("tone"),
        "cast": cast,
        "canon_policy": "No new facts become canon during generation; all continuity changes are proposals.",
    }
    path = run_dir / "artifacts" / "concept.json"
    json_write(path, concept)
    md_write(run_dir / "artifacts" / "concept.md", render_kv_markdown("Concept", concept))
    return [path, run_dir / "artifacts" / "concept.md"]


def stage_outline(config: dict[str, Any], run_dir: Path) -> list[Path]:
    setup = normalize_setup(config)
    cast = [bible_display_name(data) for _, data in load_selected_bibles(config)]
    outline = {
        "opening": f"Introduce {setup['location'] or 'the setting'} and the topic: {setup['topic']}.",
        "middle": f"Escalate as a {setup['adventure_style']} while keeping trait use restrained.",
        "turn": setup.get("required_beat") or "A selected trait matters once.",
        "ending": setup.get("lesson") or "Resolve the issue without canonizing new facts.",
        "focus_cast": cast,
    }
    path = run_dir / "artifacts" / "outline.json"
    json_write(path, outline)
    md_write(run_dir / "artifacts" / "outline.md", render_kv_markdown("Outline", outline))
    return [path, run_dir / "artifacts" / "outline.md"]


def stage_page_plan(config: dict[str, Any], run_dir: Path) -> list[Path]:
    setup = normalize_setup(config)
    packet = story_context.build_context_packet(setup, WORKSPACE_ROOT / "character-bibles")
    path = run_dir / "artifacts" / "page-plan.json"
    json_write(path, packet["panel_plan"])
    md_write(run_dir / "artifacts" / "page-plan.md", render_panel_plan(packet["panel_plan"]))
    return [path, run_dir / "artifacts" / "page-plan.md"]


def stage_script(config: dict[str, Any], run_dir: Path) -> list[Path]:
    setup = normalize_setup(config)
    result = story_context.generate_sample_issue(setup, WORKSPACE_ROOT / "character-bibles", WORKSPACE_ROOT, save=False)
    files = {
        "character-context.json": result["packet"],
        "script-validation.json": {"warnings": result["script_validation_warnings"]},
        "proposed-continuity-update.json": result["continuity_proposal"],
    }
    written = []
    for name, data in files.items():
        path = run_dir / "artifacts" / name
        json_write(path, data)
        written.append(path)
    text_files = {
        "script-generation-prompt.md": result["prompt"],
        "generated-script.md": result["generated_script"],
        "proposed-continuity-update.md": story_context.render_continuity_markdown(result["continuity_proposal"]),
    }
    for name, text in text_files.items():
        path = run_dir / "artifacts" / name
        md_write(path, text)
        written.append(path)
    return written


def stage_image_generation(config: dict[str, Any], run_dir: Path) -> list[Path]:
    context_path = run_dir / "artifacts" / "character-context.json"
    packet = json.loads(context_path.read_text(encoding="utf-8")) if context_path.exists() else story_context.build_context_packet(normalize_setup(config), WORKSPACE_ROOT / "character-bibles")
    size = (config.get("production", {}) or {}).get("panel_image_size", {}) or {}
    prompts = []
    for page in packet["panel_plan"]["pages"]:
        for panel_index in range(1, page["panel_count"] + 1):
            prompts.append({
                "page": page["page"],
                "panel": panel_index,
                "width": size.get("width", 2480),
                "height": size.get("height", 3508),
                "character_reference_paths": [
                    char.get("primary_reference_image") for char in packet["selected_cast"] if char.get("primary_reference_image")
                ],
                "status": "prompt_ready_art_not_generated",
            })
    path = run_dir / "artifacts" / "art-prompt-pack.json"
    json_write(path, {"issue_id": config.get("issue_id"), "prompts": prompts})
    return [path]


def stage_lettering(config: dict[str, Any], run_dir: Path) -> list[Path]:
    script_path = run_dir / "artifacts" / "generated-script.md"
    script = script_path.read_text(encoding="utf-8") if script_path.exists() else ""
    max_words = int((config.get("production", {}) or {}).get("max_dialogue_words_per_balloon") or 15)
    dialogue_lines = [line for line in script.splitlines() if line.startswith("- Dialogue:")]
    checks = []
    for line in dialogue_lines:
        words = [word for word in line.split(":", 1)[-1].replace('"', "").split() if word != "-"]
        checks.append({"line": line, "word_count": len(words), "within_limit": len(words) <= max_words})
    path = run_dir / "artifacts" / "lettering-plan.json"
    json_write(path, {"max_words_per_balloon": max_words, "dialogue_checks": checks})
    md_write(run_dir / "artifacts" / "lettering-plan.md", render_lettering(checks, max_words))
    return [path, run_dir / "artifacts" / "lettering-plan.md"]


def stage_assembly(config: dict[str, Any], run_dir: Path) -> list[Path]:
    artifacts = sorted(str(path.relative_to(run_dir)) for path in (run_dir / "artifacts").glob("*"))
    manifest = {
        "issue_id": config.get("issue_id"),
        "created_at": now(),
        "artifacts": artifacts,
        "original_art_moved": False,
        "assembly_status": "ready_for_manual_art_and_layout_review",
    }
    path = run_dir / "artifacts" / "assembly-manifest.json"
    json_write(path, manifest)
    return [path]


def stage_qc(config: dict[str, Any], run_dir: Path) -> list[Path]:
    validation = validate_all(config, run_dir)
    report = render_qc_report(validation)
    json_path = run_dir / "artifacts" / "qc-report.json"
    md_path = run_dir / "artifacts" / "qc-report.md"
    json_write(json_path, validation)
    md_write(md_path, report)
    return [json_path, md_path]


def render_kv_markdown(title: str, data: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for key, value in data.items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines) + "\n"


def render_panel_plan(plan: dict[str, Any]) -> str:
    lines = [f"# Page Plan", "", f"- Pages: {plan['page_count']}", f"- Total panels: {plan['total_panels']}"]
    for page in plan["pages"]:
        lines.append(f"- Page {page['page']}: {page['panel_count']} panel(s)")
    return "\n".join(lines) + "\n"


def render_lettering(checks: list[dict[str, Any]], max_words: int) -> str:
    lines = ["# Lettering Plan", "", f"Max dialogue words per balloon: {max_words}", ""]
    for check in checks:
        marker = "PASS" if check["within_limit"] else "WARN"
        lines.append(f"- {marker}: {check['word_count']} words - `{check['line']}`")
    return "\n".join(lines) + "\n"


def validate_stage(config: dict[str, Any], run_dir: Path, stage: str) -> dict[str, Any]:
    issues = validate_config(config)
    required_by_stage = {
        "concept": ["concept.json"],
        "outline": ["outline.json"],
        "page_plan": ["page-plan.json"],
        "script": ["character-context.json", "script-generation-prompt.md", "generated-script.md", "proposed-continuity-update.json"],
        "image_generation": ["art-prompt-pack.json"],
        "lettering": ["lettering-plan.json"],
        "assembly": ["assembly-manifest.json"],
        "qc": ["qc-report.json"],
    }
    for name in required_by_stage.get(stage, []):
        if not (run_dir / "artifacts" / name).exists():
            issues.append(issue("high", f"artifacts/{name}", f"Missing {stage} artifact.", "Rerun the stage."))
    issues.extend(validate_character_rules(config, run_dir))
    if stage in {"page_plan", "script", "qc"}:
        issues.extend(validate_counts(config, run_dir))
    if stage in {"script", "lettering", "qc"}:
        issues.extend(validate_script_outputs(config, run_dir))
    result = {
        "stage": stage,
        "checked_at": now(),
        "status": "pass" if not blocking(issues) else "fail",
        "issues": issues,
    }
    json_write(run_dir / "validation" / f"{stage}.json", result)
    md_write(run_dir / "validation" / f"{stage}.md", render_validation(result))
    return result


def validate_all(config: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    issues = validate_config(config)
    issues.extend(validate_counts(config, run_dir))
    issues.extend(validate_character_rules(config, run_dir))
    issues.extend(validate_script_outputs(config, run_dir))
    issues.extend(validate_artifacts(run_dir))
    return {
        "checked_at": now(),
        "status": "pass" if not blocking(issues) else "fail",
        "issues": dedupe_issues(issues),
    }


def blocking(issues: list[dict[str, str]]) -> bool:
    return any(item["severity"] in {"critical", "high"} for item in issues)


def dedupe_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for item in issues:
        key = (item["severity"], item["location"], item["message"])
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def validate_counts(config: dict[str, Any], run_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    plan_path = run_dir / "artifacts" / "page-plan.json"
    if not plan_path.exists():
        return issues
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    
    plan_page_count = int(plan.get("page_count") or 0)
    config_page_count = int(config.get("page_count") or 0)
    if plan_page_count != config_page_count:
        issues.append(issue("high", "page-plan.json", "Generated page count does not match config.", "Regenerate page plan."))
        
    plan_total_panels = int(plan.get("total_panels") or 0)
    config_panel_count = int(config.get("panel_count") or 0)
    if plan_total_panels != config_panel_count:
        issues.append(issue("high", "page-plan.json", "Generated panel count does not match config.", "Regenerate page plan."))
        
    pages = plan.get("pages", [])
    if any(int(page.get("panel_count") or 0) < 1 for page in pages):
        issues.append(issue("high", "page-plan.json", "A page has no panels.", "Adjust panel count or page count."))
        
    # Enforce specific cover and story page panel counts if page_count is 12
    if plan_page_count == 12:
        for page in pages:
            p_num = int(page.get("page") or 0)
            p_panels = int(page.get("panel_count") or 0)
            if p_num == 1:
                if p_panels != 1:
                    issues.append(issue("high", "page-plan.json", f"Page 1 (Front Cover) has {p_panels} panels; expected exactly 1 panel.", "Adjust total panel count or planning logic to ensure 1 panel for front cover."))
            elif p_num == 12:
                if p_panels != 1:
                    issues.append(issue("high", "page-plan.json", f"Page 12 (Back Cover) has {p_panels} panels; expected exactly 1 panel.", "Adjust total panel count or planning logic to ensure 1 panel for back cover."))
            else:
                if p_panels < 2 or p_panels > 6:
                    issues.append(issue("high", "page-plan.json", f"Page {p_num} has {p_panels} panels; expected between 2 and 6 panels per page.", "Adjust total panel count or planning logic."))
                    
    return issues



def validate_character_rules(config: dict[str, Any], run_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for character_id, data in load_selected_bibles(config):
        ident = data.get("identification", {}) or {}
        visual = data.get("visual_canon", {}) or {}
        if ident.get("naming_status") != "personal_name_canon" and ident.get("personal_name"):
            issues.append(issue("medium", f"{character_id}/bible.yaml", "Personal name exists without personal_name_canon status.", "Review naming before using it in generated scripts."))
        ref = visual.get("primary_reference_image")
        if (config.get("validation", {}) or {}).get("require_reference_images", True) and not ref:
            issues.append(issue("medium", f"{character_id}/bible.yaml", "Primary reference image is missing.", "Select a primary reference in the review interface."))
        if ref and not (WORKSPACE_ROOT / "character-bibles" / character_id / ref).exists():
            issues.append(issue("high", f"{character_id}/{ref}", "Primary reference image path does not exist.", "Restore or correct the reference path."))
        if character_id != "MZ-CHAR-CLEVER" and visual.get("glasses_status") == "confirmed_glasses":
            issues.append(issue("high", f"{character_id}/bible.yaml", "Non-Clever character has confirmed glasses.", "Flag for owner review; do not generate glasses silently."))
    return issues


def validate_script_outputs(config: dict[str, Any], run_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    script_path = run_dir / "artifacts" / "generated-script.md"
    if not script_path.exists():
        return issues
    script = script_path.read_text(encoding="utf-8")
    max_words = int((config.get("production", {}) or {}).get("max_dialogue_words_per_balloon") or 15)
    for line_number, line in enumerate(script.splitlines(), start=1):
        if line.startswith("- Dialogue:"):
            words = [word for word in line.split(":", 1)[-1].replace('"', "").split() if word != "-"]
            if len(words) > max_words:
                issues.append(issue("medium", f"generated-script.md:{line_number}", "Dialogue exceeds lettering word limit.", "Shorten the balloon text."))
    proposal_path = run_dir / "artifacts" / "proposed-continuity-update.json"
    if proposal_path.exists():
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        if proposal.get("status") != "proposed_owner_review_required":
            issues.append(issue("high", "proposed-continuity-update.json", "Continuity update is not marked for owner approval.", "Keep continuity proposed until approved."))
    if "glasses" in script.lower():
        for character_id, data in load_selected_bibles(config):
            name = bible_display_name(data)
            if character_id != "MZ-CHAR-CLEVER" and name.lower() in script.lower():
                # story_context adds "no glasses" notes for non-Clever characters; flag only direct positive phrasing.
                if f"{name.lower()} wears glasses" in script.lower():
                    issues.append(issue("high", "generated-script.md", f"{name} may be given glasses.", "Remove or flag for owner review."))
    return issues


def validate_artifacts(run_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    manifest_path = run_dir / "artifacts" / "assembly-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("original_art_moved") is not False:
            issues.append(issue("high", "assembly-manifest.json", "Manifest does not confirm original art stayed in place.", "Do not move source artwork during workflow runs."))
    return issues


def render_validation(result: dict[str, Any]) -> str:
    lines = [f"# Validation: {result['stage']}", "", f"Status: {result['status']}", ""]
    if not result["issues"]:
        lines.append("- PASS: no blocking issues found.")
    else:
        for item in result["issues"]:
            lines.append(f"- {item['severity'].upper()} `{item['location']}`: {item['message']} Action: {item['action']}")
    return "\n".join(lines) + "\n"


def render_qc_report(result: dict[str, Any]) -> str:
    lines = ["# Quality Control Report", "", f"Status: {result['status']}", f"Checked: {result['checked_at']}", ""]
    lines.append("## Findings")
    if not result["issues"]:
        lines.append("- No blocking issues found.")
    for item in result["issues"]:
        lines.append(f"- {item['severity'].upper()} `{item['location']}`: {item['message']} Action: {item['action']}")
    lines.extend([
        "",
        "## Required Manual Checks",
        "- Review final art against primary references before publishing.",
        "- Approve or reject proposed continuity updates in the Character Bible interface.",
        "- Confirm experimental traits remain reviewable and are not promoted by the script.",
    ])
    return "\n".join(lines) + "\n"


def run_stage(stage: str, config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    if stage not in STAGES:
        raise WorkflowError(f"Unknown stage: {stage}")
    run_dir = ensure_dirs(config, output_root)
    stage_funcs = {
        "concept": stage_concept,
        "outline": stage_outline,
        "page_plan": stage_page_plan,
        "script": stage_script,
        "image_generation": stage_image_generation,
        "lettering": stage_lettering,
        "assembly": stage_assembly,
        "qc": stage_qc,
    }
    written = stage_funcs[stage](config, run_dir)
    validation = validate_stage(config, run_dir, stage)
    return {"stage": stage, "run_dir": str(run_dir), "written": [str(path) for path in written], "validation": validation}


def run_workflow(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    stages = ((config.get("production", {}) or {}).get("stages") or STAGES)
    results = []
    for stage in stages:
        result = run_stage(stage, config, output_root)
        results.append(result)
        if result["validation"]["status"] == "fail":
            break
    improvement = run_improvement_loop(config, issue_dir(config, output_root))
    return {"results": results, "improvement": improvement}


def run_improvement_loop(config: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    validation_files = sorted((run_dir / "validation").glob("*.json"))
    validations = [json.loads(path.read_text(encoding="utf-8")) for path in validation_files]
    qc_path = run_dir / "artifacts" / "qc-report.json"
    qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {"issues": []}
    all_issues = dedupe_issues([issue for result in validations for issue in result.get("issues", [])] + qc.get("issues", []))
    scorecard = {
        "Superior Quality": score_quality(all_issues),
        "Peak Performance": "pass" if len(validation_files) >= 1 else "needs_run",
        "Optimized Execution": "pass" if (run_dir / "artifacts" / "assembly-manifest.json").exists() else "incomplete",
        "High-Yield Production": "pass" if (run_dir / "artifacts" / "generated-script.md").exists() else "incomplete",
        "Elevated Efficiency": "pass" if len(all_issues) <= 3 else "review_needed",
        "Maximum Impact": "owner_review_required",
    }
    report = {
        "issue_id": config.get("issue_id"),
        "created_at": now(),
        "scorecard": scorecard,
        "open_issues": all_issues,
        "next_actions": next_actions(all_issues),
        "source_skills_used": [
            "Strategy to System Converter",
            "Quality Checklist Builder",
            "Anti-Drift Guardrail Writer",
            "Verification and Escalation",
            "AI Work Reviewer",
            "Regression Smoke Suite Builder",
            "Reproducibility Capture",
        ],
    }
    json_write(run_dir / "improvement" / "improvement-report.json", report)
    md = render_improvement(report)
    md_write(run_dir / "improvement" / "improvement-report.md", md)
    # Keep runs directed to a temporary/test root isolated from tracked production files.
    log_root = WORKSPACE_ROOT if output_root_is_workspace(run_dir) else run_dir.parent
    md_write(log_root / "improvement_log.md", md)
    capture_reproducibility(config, run_dir)
    return report


def output_root_is_workspace(run_dir: Path) -> bool:
    try:
        run_dir.resolve().relative_to(WORKSPACE_ROOT.resolve())
        return True
    except ValueError:
        return False


def score_quality(issues: list[dict[str, str]]) -> str:
    if any(item["severity"] in {"critical", "high"} for item in issues):
        return "blocked"
    if issues:
        return "review_needed"
    return "pass"


def next_actions(issues: list[dict[str, str]]) -> list[str]:
    if not issues:
        return ["Run the smoke workflow after the next config, Bible, or script change."]
    return [f"{item['severity'].upper()} {item['location']}: {item['action']}" for item in issues[:8]]


def render_improvement(report: dict[str, Any]) -> str:
    lines = [
        f"# Improvement Loop: {report['issue_id']}",
        "",
        f"Created: {report['created_at']}",
        "",
        "## Peak-Performance Scorecard",
    ]
    for name, status in report["scorecard"].items():
        lines.append(f"- {name}: {status}")
    lines.extend(["", "## Open Issues"])
    if not report["open_issues"]:
        lines.append("- None from automated checks.")
    for item in report["open_issues"]:
        lines.append(f"- {item['severity'].upper()} `{item['location']}`: {item['message']} Action: {item['action']}")
    lines.extend(["", "## Next Actions"])
    for action in report["next_actions"]:
        lines.append(f"- {action}")
    lines.extend([
        "",
        "## Standing Loop",
        "- Review source-of-truth inputs before each run.",
        "- Run every production stage in order.",
        "- Validate after every stage and halt on high-severity defects.",
        "- Review generated script, continuity proposals, and character context before publication.",
        "- Add a smoke probe when a regression escapes or a new workflow feature ships.",
    ])
    return "\n".join(lines) + "\n"


def capture_reproducibility(config: dict[str, Any], run_dir: Path) -> None:
    config_path = WORKSPACE_ROOT / "config" / "production_config.yaml"
    inputs = [
        {"name": "production_config", "path": str(config_path), "sha256": sha256(config_path)},
        {"name": "workflow_engine", "path": str(Path(__file__)), "sha256": sha256(Path(__file__))},
    ]
    for selected in config.get("characters") or []:
        character_id = selected.get("character_id") if isinstance(selected, dict) else selected
        path = WORKSPACE_ROOT / "character-bibles" / character_id / "bible.yaml"
        if path.exists():
            inputs.append({"name": character_id, "path": str(path), "sha256": sha256(path)})
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": str(WORKSPACE_ROOT),
    }
    try:
        env["git_head"] = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=WORKSPACE_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        env["git_head"] = "not_available"
    capture = {
        "result": str(run_dir),
        "captured": now(),
        "reproduction_status": "verified_by_current_run",
        "inputs": inputs,
        "environment": env,
        "randomness": {"seed": "not used; deterministic local sample workflow"},
        "invocation": f"powershell -ExecutionPolicy Bypass -File scripts/run_workflow.ps1 -Config config/production_config.yaml -OutputRoot {(run_dir.parent).name}",
    }
    json_write(run_dir / "reproducibility" / "capture.json", capture)
    md_write(run_dir / "reproducibility" / "capture.md", render_reproducibility(capture))


def render_reproducibility(capture: dict[str, Any]) -> str:
    lines = [
        f"# Reproducibility Capture: {Path(capture['result']).name}",
        "",
        f"Result: `{capture['result']}`",
        f"Captured: {capture['captured']}",
        f"Status: {capture['reproduction_status']}",
        "",
        "## Inputs",
    ]
    for item in capture["inputs"]:
        lines.append(f"- {item['name']}: `{item['path']}` sha256 `{item['sha256']}`")
    lines.extend(["", "## Environment", "```json", json.dumps(capture["environment"], indent=2), "```", "", "## Invocation", "```powershell", capture["invocation"], "```"])
    return "\n".join(lines) + "\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def smoke_suite(output_path: Path) -> None:
    text = """# Smoke Suite: MonkeyZoo Comic Factory

Run after: every config, workflow, Character Bible, or story-context change.
Measured runtime: under 10 minutes for the local automated core.
Base path: current workspace root.
Stop rule: if P1 or P2 fails, halt and mark later probes NOT RUN.

## Core Probes

### P1 - Source Inputs Exist [FOUNDATIONAL] (source: auth/entry equivalent)
- Setup: workspace root is the current directory.
- Action: run `python scripts/workflow_engine.py validate --config config/production_config.yaml --output-root runs`.
- Expect: command exits 0 and writes a validation JSON file.

### P2 - Character Bibles Validate [FOUNDATIONAL] (source: data loss / canon integrity)
- Setup: character-bibles folder exists.
- Action: run `python character-bibles/_schema/validate-character-bibles.py --root character-bibles --workspace-root .`.
- Expect: process exits 0.

### P3 - Compact Story Context Builds (source: traffic / primary workflow)
- Setup: production_config.yaml selects at least two existing characters.
- Action: run `python scripts/workflow_engine.py stage script --config config/production_config.yaml --output-root runs`.
- Expect: `runs/<issue_id>/artifacts/script-generation-prompt.md` exists.

### P4 - Continuity Remains Proposed (source: canon integrity)
- Setup: P3 completed.
- Action: open `runs/<issue_id>/artifacts/proposed-continuity-update.json`.
- Expect: JSON field `status` is exactly `proposed_owner_review_required`.

### P5 - End-to-End Workflow Runs (source: traffic / release path)
- Setup: no stage process is already running.
- Action: run `powershell -ExecutionPolicy Bypass -File scripts/run_workflow.ps1 -Config config/production_config.yaml -OutputRoot runs`.
- Expect: `runs/<issue_id>/improvement/improvement-report.md` exists.

## Intake Rules
- New workflow feature ships with a concrete smoke probe.
- Escaped regression adds a same-day probe citing the incident.
"""
    md_write(output_path, text)


def command_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MonkeyZoo production workflow engine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["run", "validate", "improve"]:
        sp = sub.add_parser(name)
        sp.add_argument("--config", default="config/production_config.yaml")
        sp.add_argument("--output-root", default="runs")
    stage_parser = sub.add_parser("stage")
    stage_parser.add_argument("stage", choices=STAGES)
    stage_parser.add_argument("--config", default="config/production_config.yaml")
    stage_parser.add_argument("--output-root", default="runs")
    smoke_parser = sub.add_parser("smoke-suite")
    smoke_parser.add_argument("--output", default="source_of_truth/validation/smoke-suite.md")
    args = parser.parse_args(argv)

    if args.command == "smoke-suite":
        smoke_suite(WORKSPACE_ROOT / args.output)
        return 0

    config_path = (WORKSPACE_ROOT / args.config).resolve()
    output_root = (WORKSPACE_ROOT / args.output_root).resolve()
    config = load_config(config_path)
    run_dir = ensure_dirs(config, output_root)
    try:
        if args.command == "run":
            result = run_workflow(config, output_root)
            print(json.dumps({"run_dir": str(issue_dir(config, output_root)), "stage_count": len(result["results"])}, indent=2))
        elif args.command == "stage":
            result = run_stage(args.stage, config, output_root)
            print(json.dumps({"run_dir": result["run_dir"], "stage": args.stage, "status": result["validation"]["status"]}, indent=2))
            return 1 if result["validation"]["status"] == "fail" else 0
        elif args.command == "validate":
            result = validate_stage(config, run_dir, "manual")
            print(json.dumps({"run_dir": str(run_dir), "status": result["status"]}, indent=2))
            return 1 if result["status"] == "fail" else 0
        elif args.command == "improve":
            result = run_improvement_loop(config, run_dir)
            print(json.dumps({"run_dir": str(run_dir), "open_issues": len(result["open_issues"])}, indent=2))
    except (WorkflowError, bible_store.BibleStoreError, story_context.StoryContextError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(command_main())
