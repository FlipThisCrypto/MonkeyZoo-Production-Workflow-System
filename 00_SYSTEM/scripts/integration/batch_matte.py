"""Batch-run alpha_matte.py across the approved character refs and report
pass/fail per character so failures are caught before the compositor
depends on this tool. A ref "passes" only if all four corners end up fully
transparent AND the opaque fraction falls in a plausible single-character
silhouette range (reject near-0 = keyed everything out, reject near-1 =
keyed nothing out)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from alpha_matte import extract  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT / "03_APPROVED_CANON" / "approved_characters"
OUT_DIR = ROOT / "00_SYSTEM" / "integration_upgrade" / "character_layers"

MIN_OPAQUE, MAX_OPAQUE = 0.15, 0.60


def main(sample_names: dict[str, str]):
    results = []
    for char, filename in sample_names.items():
        src = SRC_DIR / char / filename
        dst = OUT_DIR / char / filename
        if not src.exists():
            results.append({"character": char, "verdict": "MISSING_SRC", "src": str(src)})
            continue
        report = extract(src, dst)
        ok_corners = report["corners_fully_transparent"]
        ok_range = MIN_OPAQUE <= report["opaque_frac"] <= MAX_OPAQUE
        report["character"] = char
        report["verdict"] = "PASS" if (ok_corners and ok_range) else "FAIL"
        results.append(report)

    print(json.dumps(results, indent=2))
    n_pass = sum(1 for r in results if r.get("verdict") == "PASS")
    print(f"\n{n_pass}/{len(results)} PASS", file=sys.stderr)
    return results


if __name__ == "__main__":
    SAMPLES = {
        "moodz": "moodz_00_clean_base.png",
        "twotone": "twotone_00_clean_base.png",
        "static": "static_00_clean_base.png",
        "ash": "ash_00_clean_base.png",
        "neonblue": "neonblue_00_clean_base.png",
        "scarline": "scarline_00_clean_base.png",
    }
    main(SAMPLES)
