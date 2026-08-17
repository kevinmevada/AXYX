"""Phase 6 trajectory analysis. Does not modify Phases 0–5. No predictive ML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase6 import certify_phase6, write_phase6  # noqa: E402
from gait_research.trajectories.engine import run_phase6  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 6 trajectory analysis")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-perm-primary", type=int, default=9999)
    parser.add_argument("--n-perm-secondary", type=int, default=1999)
    args = parser.parse_args()
    root = args.root.resolve()
    result = run_phase6(root, n_perm_primary=args.n_perm_primary, n_perm_secondary=args.n_perm_secondary)
    write_phase6(root, result)
    cert = certify_phase6(result)
    base = root / "results" / "phase6"
    lines = ["# Phase 6 certification", "", f"Status: **{cert['status']}**", ""]
    for c in cert["checks"]:
        lines.append(f"- `{c['name']}`: **{c['status']}** — {c['detail']}")
    (base / "phase6_certification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (base / "phase6_certification.json").write_text(json.dumps(cert, indent=2, default=str), encoding="utf-8")
    cl = result["clusters"]
    n_rob = int((cl["classification"] == "ROBUST").sum()) if len(cl) and "classification" in cl.columns else 0
    n_exp = int((cl["classification"] == "EXPLORATORY").sum()) if len(cl) and "classification" in cl.columns else 0
    print("=" * 60)
    print("AXYS ML - PHASE 6 TRAJECTORY ANALYSIS")
    print("=" * 60)
    print(f"Subjects                 {result['n_subjects']}")
    print(f"Cycles (repeated)        {result['n_cycles']}")
    print(f"Time points              {result['n_time']}")
    print(f"Channels tested          {result['n_channels_tested']}")
    print(f"Ineligible excluded      {result['n_excluded_ineligible']}")
    print(f"Robust findings          {n_rob}")
    print(f"Exploratory findings     {n_exp}")
    print(f"Certification            {cert['status']}")
    print("Phase 7 was not started.")
    return 0 if cert["status"] != "NOT CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
