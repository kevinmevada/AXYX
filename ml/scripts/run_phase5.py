"""Phase 5 within-victim analysis. Does not modify Phases 0–4. No predictive ML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.phase5 import certify_phase5, write_phase5  # noqa: E402
from gait_research.within_victim.engine import run_phase5  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AXYS ML Phase 5 within-victim discovery")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    result = run_phase5(root)
    write_phase5(root, result)
    cert = certify_phase5(result)
    base = root / "results" / "phase5"
    lines = ["# Phase 5 certification", "", f"Status: **{cert['status']}**", "", f"k choice: `{cert['choice']}`", ""]
    for c in cert["checks"]:
        lines.append(f"- `{c['name']}`: **{c['status']}** — {c['detail']}")
    (base / "phase5_certification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (base / "phase5_certification.json").write_text(json.dumps(cert, indent=2, default=str), encoding="utf-8")

    sim = result["similarity"]
    sub = result["subgroups"]
    k = sub["choice"]["k"]
    print("=" * 60)
    print("AXYS ML - PHASE 5 WITHIN-VICTIM DISCOVERY")
    print("=" * 60)
    print(f"Victims                   {result['n_victims']}")
    print(f"Observed mean pairwise    {sim['observed_mean_pairwise_distance']:.4f}")
    print(f"Null mean pairwise        {sim['null_mean']:.4f}")
    print(f"Similarity perm p         {sim['perm_p']:.4g}")
    print(f"Stable subgroups k        {k}")
    if k is None:
        print("Sizes                     none")
        print("LOVO ARI                  n/a")
        print("Different from controls   n/a (no stable subgroup)")
    else:
        sizes = dict(sub["assignments"]["subgroup"].value_counts().sort_index())
        print(f"Sizes                     {sizes}")
        print(f"LOVO ARI                  {sub['loso_ari']:.3f}")
        if len(result["vs_controls_compact"]):
            any_diff = bool(result["vs_controls_compact"]["different_from_controls"].any())
            print(f"Different from controls   {any_diff}")
    print(f"Certification             {cert['status']}")
    print("Phase 6 was not started.")
    return 0 if cert["status"] != "NOT CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
