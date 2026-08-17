"""P0.6 runner: Hilbert CRP coordination similarity.

Does not modify Phases 0–6. Writes results/similarity/p06_coordination/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.similarity.coordination_crp import (  # noqa: E402
    SEED,
    residualize_curves,
    run_coordination_crp,
)
from gait_research.similarity.load import load_coordination_crp_profiles, load_covariates  # noqa: E402


def _dirs(root: Path) -> Path:
    out = root / "results" / "similarity" / "p06_coordination"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    return out


def _plot_overlays(wrapped: np.ndarray, victim: np.ndarray, pair_ids: list[str], path: Path, tag: str) -> None:
    t = np.linspace(0, 100, wrapped.shape[2])
    n_p = len(pair_ids)
    fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharex=True)
    axes = axes.ravel()
    for j, pid in enumerate(pair_ids):
        ax = axes[j]
        for i in range(wrapped.shape[0]):
            color = "#6b4c7a" if victim[i] else "#8aa0a8"
            ax.plot(t, wrapped[i, j], color=color, lw=1.0 if victim[i] else 0.7, alpha=0.5)
        ax.set_title(pid, fontsize=9)
        ax.set_ylabel("CRP (rad)" if j % 3 == 0 else "")
        ax.set_xlim(0, 100)
        if j >= 3:
            ax.set_xlabel("Gait cycle %")
    from matplotlib.lines import Line2D

    fig.legend(
        handles=[
            Line2D([0], [0], color="#6b4c7a", lw=1.5, label="victim"),
            Line2D([0], [0], color="#8aa0a8", lw=1.2, label="control"),
        ],
        loc="upper right",
    )
    fig.suptitle(f"P0.6 Hilbert CRP (circular mean; {tag})", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def _plot_null(null: np.ndarray, obs: float, path: Path, xlabel: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(null, bins=40, color="#8aa0a8", edgecolor="white")
    ax.axvline(obs, color="#6b4c7a", lw=2, label=f"observed={obs:.3f}")
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _write_report(out: Path, raw: dict, resid: dict) -> None:
    s = raw["summary"]
    r = resid["summary"]
    pearson_ok = (
        r["perm_p_pearson"] <= 0.05
        and r["loso_pass"]
        and r["mean_pairwise_pearson"] > r["null_mean_pearson"]
    )
    dtw_ok = r["perm_p_dtw"] <= 0.05 and r["mean_pairwise_dtw"] < r["null_mean_dtw"]
    fdr_ok = r["n_pairs_pearson_fdr_le_0_10"] + r["n_pairs_dtw_fdr_le_0_10"] > 0
    if (pearson_ok or dtw_ok) and fdr_ok:
        decision = "CANDIDATE shared-coupling signal (requires independent cohort)"
    else:
        decision = "NULL after residualization"

    text = f"""# P0.6 Continuous relative phase (CRP) coordination

Generated: {date.today().isoformat()}

## Question

Do the 17 victims share *inter-joint coupling* (CRP profiles) that is invisible
to single-curve / single-feature tests (P0.1–P0.4)?

Unit: **subject** (n=31). Labels shuffled across subjects only.

## CRP method (audited)

- **Input:** Phase 1 `normalized_core.npz` ax1 angle curves (101 points).
- **Velocity:** not stored in Phase 1; not required for Hilbert phase.
- **Phase:** Hilbert analytic signal of the **demeaned** angle
  (`scipy.signal.hilbert` → `np.angle`).
- **Why Hilbert (not atan2(ω, θ)):** phase-plane methods need separate
  position/velocity normalization and are sensitive to those choices; Hilbert
  phase is unique for a demeaned real signal without an extra velocity scale
  (standard CRP practice in motor coordination).
- **CRP:** `wrap(φ_proximal − φ_distal)` to (−π, π].
- **Subject profile:** circular mean CRP across cycles.
- **Similarity:** (1) circular `mean_t cos(CRP_i−CRP_j)` — preserves constant
  phase offsets that z-scored Pearson would destroy; (2) DTW on
  `unwrap(CRP−CRP[0])` for time-varying coupling shape (P0.3-style).

Pairs locked in `preregistered_pairs.json` (n={s['n_pairs']}) before any real test.
FDR family = {r['n_fdr_family']} (6 pairs × 2 measures).

## Pre-residual

| Metric | Circular mean cos(ΔCRP) (↑) | DTW on unwrap (↓) |
|---|---|---|
| Mean pairwise (avg over pairs) | {s['mean_pairwise_pearson']:.4f} | {s['mean_pairwise_dtw']:.4f} |
| 95% bootstrap CI | [{s['pearson_ci_low']:.4f}, {s['pearson_ci_high']:.4f}] | [{s['dtw_ci_low']:.4f}, {s['dtw_ci_high']:.4f}] |
| Permutation p | {s['perm_p_pearson']:.4g} | {s['perm_p_dtw']:.4g} |
| Null mean | {s['null_mean_pearson']:.4f} | {s['null_mean_dtw']:.4f} |
| LOSO pass / sign agree | {s['loso_pass']} / {s['loso_sign_agreement']:.3f} | — |
| Pairs with FDR q ≤ 0.10 | {s['n_pairs_pearson_fdr_le_0_10']} | {s['n_pairs_dtw_fdr_le_0_10']} |

## Post-residual (height, mass, mean leg length, cycle duration)

Linear residualization of wrapped CRP radians (pragmatic confound control).

| Metric | Circular mean cos(ΔCRP) (↑) | DTW on unwrap (↓) |
|---|---|---|
| Mean pairwise (avg over pairs) | {r['mean_pairwise_pearson']:.4f} | {r['mean_pairwise_dtw']:.4f} |
| 95% bootstrap CI | [{r['pearson_ci_low']:.4f}, {r['pearson_ci_high']:.4f}] | [{r['dtw_ci_low']:.4f}, {r['dtw_ci_high']:.4f}] |
| Permutation p | {r['perm_p_pearson']:.4g} | {r['perm_p_dtw']:.4g} |
| Null mean | {r['null_mean_pearson']:.4f} | {r['null_mean_dtw']:.4f} |
| LOSO pass / sign agree | {r['loso_pass']} / {r['loso_sign_agreement']:.3f} | — |
| Pairs with FDR q ≤ 0.10 | {r['n_pairs_pearson_fdr_le_0_10']} | {r['n_pairs_dtw_fdr_le_0_10']} |
| Covariates | {', '.join(r['residual_covariates'])} |

## Decision (P0.6 only)

**{decision}**

Gate: post-residual primary. Needs perm p ≤ 0.05 on Pearson or DTW (with
Pearson LOSO pass), observed on the similarity side of the null, and ≥1
pair×measure FDR q ≤ 0.10.

Phases 0–6 were not modified. P1 not started in this script.
"""
    (out / "p06_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P0.6 CRP coordination similarity")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-perm", type=int, default=9999)
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    root = args.root.resolve()
    out = _dirs(root)

    data = load_coordination_crp_profiles(root)
    X = data["X"]
    wrapped = data["wrapped_crp"]
    victim = data["victim"]
    pair_ids = data["pair_ids"]
    cov, cov_names = load_covariates(root, data["subject_id"])

    print(f"FDR family size (pre-registered): {data['n_fdr_family']}")
    print(f"CRP profiles: {X.shape}")
    print("Stage 1/2: pre-residual …")
    summary, details = run_coordination_crp(
        X,
        victim,
        pair_ids,
        representation="hilbert_crp_unwrapped",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
        show_progress=True,
    )
    X_res = residualize_curves(X, cov)
    print("Stage 2/2: post-residual …")
    summary_r, details_r = run_coordination_crp(
        X_res,
        victim,
        pair_ids,
        representation="hilbert_crp_unwrapped_residualized",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
        residualized=True,
        residual_covariates=tuple(cov_names),
        show_progress=True,
    )

    pd.DataFrame([summary.to_dict(), summary_r.to_dict()]).to_csv(out / "summary.csv", index=False)
    details["pair_table"].to_csv(out / "per_pair_similarity.csv", index=False)
    details_r["pair_table"].to_csv(out / "per_pair_similarity_residualized.csv", index=False)
    pd.DataFrame(
        {
            "null_mean_pairwise_pearson": details["perm"]["null_pearson"],
            "null_mean_pairwise_dtw": details["perm"]["null_dtw"],
        }
    ).to_csv(out / "permutation_null.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps({"raw": summary.to_dict(), "residualized": summary_r.to_dict()}, indent=2),
        encoding="utf-8",
    )

    _plot_overlays(wrapped, victim, pair_ids, out / "figures" / "crp_overlays.png", "raw circular mean")
    # residualized wrapped CRP for overlay of residualized coupling
    X_res_plot = residualize_curves(wrapped, cov)
    _plot_overlays(
        X_res_plot,
        victim,
        pair_ids,
        out / "figures" / "crp_overlays_residualized.png",
        "residualized circular mean",
    )
    _plot_null(
        details["perm"]["null_pearson"],
        summary.mean_pairwise_pearson,
        out / "figures" / "permutation_null_pearson.png",
        "Mean pairwise Pearson (CRP profiles)",
        "P0.6 Pearson null",
    )
    _plot_null(
        details_r["perm"]["null_pearson"],
        summary_r.mean_pairwise_pearson,
        out / "figures" / "permutation_null_pearson_residualized.png",
        "Mean pairwise Pearson (CRP profiles)",
        "P0.6 Pearson null (residualized)",
    )
    _plot_null(
        details_r["perm"]["null_dtw"],
        summary_r.mean_pairwise_dtw,
        out / "figures" / "permutation_null_dtw_residualized.png",
        "Mean pairwise DTW (CRP profiles)",
        "P0.6 DTW null (residualized)",
    )

    _write_report(out, {"summary": summary.to_dict()}, {"summary": summary_r.to_dict()})

    print("=" * 60)
    print("P0.6 CRP COORDINATION SIMILARITY")
    print("=" * 60)
    print(f"Source             {data['source']}")
    print(f"Pairs              {len(pair_ids)}")
    print("--- pre-residual ---")
    print(f"Circular           {summary.mean_pairwise_pearson:.4f}  p={summary.perm_p_pearson:.4g}")
    print(f"DTW                {summary.mean_pairwise_dtw:.4f}  p={summary.perm_p_dtw:.4g}")
    print("--- post-residual ---")
    print(f"Circular           {summary_r.mean_pairwise_pearson:.4f}  p={summary_r.perm_p_pearson:.4g}")
    print(f"DTW                {summary_r.mean_pairwise_dtw:.4f}  p={summary_r.perm_p_dtw:.4g}")
    print(f"FDR<=0.10 circular {summary_r.n_pairs_pearson_fdr_le_0_10}")
    print(f"FDR<=0.10 dtw      {summary_r.n_pairs_dtw_fdr_le_0_10}")
    print(f"Wrote              {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
