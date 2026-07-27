#!/usr/bin/env python3
"""The single canonical contract for "where does an issue's final cover live?".

Why this module exists
----------------------
Two independently written resolvers disagreed about the cover location, and
production data was genuinely split across both conventions:

* the Studio release gate looked ONLY under ``generated_art/`` --
  ``sorted((folder/"generated_art").rglob("*cover*.png"))`` -- and raised the
  blocker ``"No final cover image found"``, naming no path it had searched;
* the CLI packager (``build_release._find_cover``) looked at
  ``exports/cover.png`` FIRST, then ``generated_art/covers/main_cover.png``.

The trap was reachable straight from the designated instructions:
``.claude/skills/mz-package/SKILL.md`` -- the skill CLAUDE.md assigns to Stages
8-10 -- says to save ``exports/cover.png``, and 00_SYSTEM repeated that in
``automation_rules.md``, ``qa_checklist.md`` and ``monthly_issue_template.md``.
Only ``docs/OPERATOR_RUNBOOK.md`` named ``generated_art/covers/main_cover.png``.
So an operator following canon produced a cover the Release gate could not see.

Measured at the time of the fix: three issues (2026-07_Issue_05,
2026-08_Issue_06, 2026-07_Mango_Pier) held a real cover at ``exports/cover.png``
and were reporting "No final cover image found".

The contract
------------
``generated_art/covers/main_cover.png`` is CANONICAL. It is what the live
pipeline writes (``rc_real_issue_run.py``, ``live_app_test_issue.py``,
``prepare_issue01_release_assets.py``) and what all four issues that actually
reached release already use -- so making it canonical migrates nothing that has
shipped.

``exports/cover.png`` is a DEPRECATED compatibility fallback. It is accepted so
the issues already sitting on it are not stranded, but every surface that
accepts it says so and prints the one-line migration. It is scheduled for
removal -- see ``LEGACY_REMOVAL_CRITERION``. Two permanently-accepted locations
would just recreate the divergence later.

Cardinality matters here
------------------------
There are two genuinely different questions, and the old code conflated them:

1. *"Which single file IS the final cover deliverable?"* -> :func:`resolve_final_cover`.
   Used for the blocker, and by the CBZ/PDF builders, which embed exactly one.
2. *"Which cover-ish images belong in the release evidence hash and the
   published archive?"* -> :func:`cover_evidence_images`, which returns a LIST.

Collapsing (2) into (1) would silently drop ``COVER_FRONT.png`` /
``COVER_BACK.png`` from published archives and change every release evidence
hash, so the two are deliberately kept apart.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, Optional

# Repo-relative, POSIX-style, so every surface prints the same string.
CANONICAL_RELPATH = "generated_art/covers/main_cover.png"
LEGACY_RELPATH = "exports/cover.png"

LEGACY_REMOVAL_CRITERION = (
    "Remove the exports/cover.png fallback once no folder under 02_MONTHLY_ISSUES "
    "resolves via source='legacy' (check with: python 00_SYSTEM/scripts/issue_cover.py --audit)."
)


def migration_hint(issue_folder_name: str = "<issue-folder>") -> str:
    """The exact command that moves a legacy cover to the canonical location."""
    return (
        f"Migrate it:  mkdir -p 02_MONTHLY_ISSUES/{issue_folder_name}/generated_art/covers  "
        f"&&  git mv 02_MONTHLY_ISSUES/{issue_folder_name}/{LEGACY_RELPATH} "
        f"02_MONTHLY_ISSUES/{issue_folder_name}/{CANONICAL_RELPATH}"
    )


class CoverResolution(NamedTuple):
    """Where the final cover was found, and what to tell the operator."""

    path: Optional[Path]
    source: str                  # "canonical" | "legacy" | "missing"
    warning: Optional[str]       # set when source == "legacy"
    blocker: Optional[str]       # set when source == "missing"

    @property
    def found(self) -> bool:
        return self.path is not None


def _usable(path: Path) -> bool:
    """A zero-byte cover is not a cover; it is an interrupted write."""
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def resolve_final_cover(issue_dir: Path) -> CoverResolution:
    """Resolve THE final cover deliverable for *issue_dir*.

    Canonical first, then the deprecated fallback. Never guesses beyond those
    two: a fuzzy ``*cover*`` search is what let a preview render stand in for
    the deliverable, and it made the answer depend on filesystem case rules.
    """
    canonical = issue_dir / Path(CANONICAL_RELPATH)
    if _usable(canonical):
        return CoverResolution(canonical, "canonical", None, None)

    legacy = issue_dir / Path(LEGACY_RELPATH)
    if _usable(legacy):
        return CoverResolution(
            legacy,
            "legacy",
            (f"DEPRECATED cover location: {LEGACY_RELPATH}. "
             f"The canonical location is {CANONICAL_RELPATH}. "
             + migration_hint(issue_dir.name)),
            None,
        )

    return CoverResolution(
        None,
        "missing",
        None,
        (f"No final cover image found. Searched {CANONICAL_RELPATH} (canonical) "
         f"and {LEGACY_RELPATH} (deprecated)."),
    )


def cover_evidence_images(issue_dir: Path) -> list[Path]:
    """Every cover-ish image that belongs in the evidence hash and the archive.

    Sorted, and matched case-INSENSITIVELY on every platform.

    The case rule is not cosmetic. The previous ``rglob("*cover*.png")`` is
    case-insensitive on Windows and case-sensitive on POSIX, so
    ``2026-09_Issue_02`` contributed 4 covers on the Windows dev rig and 2 on
    Linux CI -- meaning its release evidence hash, which gates approval and is
    written into ``release_hash_manifest.json``, did not reproduce across the
    two machines that both compute it. Matching case-insensitively everywhere
    converges Linux onto the behaviour the operator has always seen on Windows,
    so no hash the operator has approved changes.

    The resolved final cover is always included, so a legacy-located cover still
    contributes evidence instead of vanishing from the record.
    """
    images: list[Path] = []
    generated = issue_dir / "generated_art"
    if generated.exists():
        images = sorted(
            p for p in generated.rglob("*.png")
            if p.is_file() and "cover" in p.name.lower()
        )

    resolved = resolve_final_cover(issue_dir)
    if resolved.path is not None and resolved.path not in images:
        images.append(resolved.path)
        images.sort()
    return images


def _audit(root: Path) -> int:
    """Report which issues still rely on the deprecated location."""
    issues_root = root / "02_MONTHLY_ISSUES"
    if not issues_root.is_dir():
        print(f"No 02_MONTHLY_ISSUES under {root}")
        return 2
    legacy, missing, canonical = [], [], []
    for folder in sorted(p for p in issues_root.iterdir() if p.is_dir()):
        bucket = {"canonical": canonical, "legacy": legacy, "missing": missing}
        bucket[resolve_final_cover(folder).source].append(folder.name)

    print(f"canonical ({len(canonical)}): {', '.join(canonical) or '-'}")
    print(f"legacy    ({len(legacy)}): {', '.join(legacy) or '-'}")
    print(f"missing   ({len(missing)}): {', '.join(missing) or '-'}")
    if legacy:
        print(f"\n{LEGACY_REMOVAL_CRITERION}")
        for name in legacy:
            print(f"  {migration_hint(name)}")
    return 1 if legacy else 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Canonical issue-cover contract.")
    parser.add_argument("--audit", action="store_true",
                        help="List which issues use the canonical vs deprecated cover location")
    parser.add_argument("--root", help="Factory root (defaults to the repo this file lives in)")
    args = parser.parse_args()
    factory = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    raise SystemExit(_audit(factory) if args.audit else _audit(factory))
