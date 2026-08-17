"""Phase 3 statistical discovery. Does not modify Phases 0–2. No ML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase3 import certify_phase3, write_phase3  # noqa: E402
from gait_research.statistics.engine import run_phase3  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 3 statistical discovery")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()

    result = run_phase3(root)
    paths = write_phase3(root, result)
    cert = certify_phase3(root, result)
    cert_path = root / "results" / "phase3" / "phase3_certification.md"
    lines = [f"# Phase 3 certification", "", f"Status: **{cert['status']}**", ""]
    for c in cert["checks"]:
        lines.append(f"- `{c['name']}`: **{c['status']}** — {c['detail']}")
    cert_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "results" / "phase3" / "phase3_certification.json").write_text(json.dumps(cert, indent=2), encoding="utf-8")

    print("=" * 60)
    print("AXYS ML - PHASE 3 STATISTICAL DISCOVERY")
    print("=" * 60)
    print(f"Subjects                 {result['n_subjects']}")
    print(f"Victims / controls       {result['n_victims']} / {result['n_controls']}")
    print(f"Analysis columns         {result['n_analysis_columns']}")
    print(f"Screen passed            {int(result['screen']['passed'].sum())}")
    print(f"Representatives          {len(result['representatives'])}")
    print(f"FDR <= 0.05              {result['n_fdr_0_05']}")
    print(f"FDR <= 0.10              {result['n_fdr_0_10']}")
    print(f"Signature-rule hits      {result['n_signature']}")
    print()
    print(f"Certification            {cert['status']}")
    print()
    if result["n_signature"] == 0:
        print("No pre-specified signature. Exploratory ranks only. Not a victim classifier.")
    print("Wrote:")
    for k, p in paths.items():
        print(f"  {k}: {p}")
    print(f"  certification: {cert_path}")
    return 0 if cert["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
