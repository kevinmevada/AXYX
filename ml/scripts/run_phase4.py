"""Phase 4 phenotype discovery. Does not modify Phases 0–3. No predictive ML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase4 import certify_phase4, write_phase4  # noqa: E402
from gait_research.phenotypes.engine import run_phase4  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 4 phenotype discovery")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()

    result = run_phase4(root)
    write_phase4(root, result)
    cert = certify_phase4(root, result)
    base = root / "results" / "phase4"
    lines = [f"# Phase 4 certification", "", f"Status: **{cert['status']}**", "", f"k choice: `{cert['choice']}`", ""]
    for c in cert["checks"]:
        lines.append(f"- `{c['name']}`: **{c['status']}** — {c['detail']}")
    (base / "phase4_certification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (base / "phase4_certification.json").write_text(json.dumps(cert, indent=2, default=str), encoding="utf-8")

    k = result["choice"]["k"]
    print("=" * 60)
    print("AXYS ML - PHASE 4 PHENOTYPE DISCOVERY")
    print("=" * 60)
    print(f"Subjects                 {result['n_subjects']}")
    print(f"Compact dimensions       {result['rep']['compact'].shape[1]}")
    print(f"Selected k               {k}")
    print(f"Selection reason         {result['choice']['reason']}")
    print(f"Certification            {cert['status']}")
    if k is None:
        print("No stable phenotype structure. Not a victim classifier.")
    print(f"Wrote                    {base}")
    return 0 if cert["status"] != "NOT CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
