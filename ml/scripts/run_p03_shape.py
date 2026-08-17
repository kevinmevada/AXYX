"""P0.3 runner: amplitude-normalized waveform shape similarity.

Does not modify Phases 0–6. Writes results/similarity/p03_shape/.
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

from gait_research.similarity.load import (  # noqa: E402
    load_covariates,
    load_phase1_subject_median_curves,
)
from gait_research.similarity.shape_space import (  # noqa: E402
    SEED,
    residualize_curves,
    run_shape_space,
)


def _dirs(root: Path) -> Path:
    out = root / "results" / "similarity" / "p03_shape"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    return out


def _plot_overlays(
    Z: np.ndarray,
    victim: np.ndarray,
    curve_ids: list[str],
    out_dir: Path,
    *,
    tag: str,
) -> None:
    t = np.linspace(0, 100, Z.shape[2])
    n_c = len(curve_ids)
    ncols = 4
    nrows = int(np.ceil(n_c / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 2.6 * nrows), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for j, cid in enumerate(curve_ids):
        ax = axes[j]
        for i in range(Z.shape[0]):
            color = "#6b4c7a" if victim[i] else "#8aa0a8"
            lw = 1.1 if victim[i] else 0.7
            alpha = 0.55 if victim[i] else 0.35
            ax.plot(t, Z[i, j], color=color, lw=lw, alpha=alpha)
        ax.set_title(cid, fontsize=9)
        ax.set_xlim(0, 100)
        if j % ncols == 0:
            ax.set_ylabel("z-scored")
        if j >= n_c - ncols:
            ax.set_xlabel("Gait cycle %")
    for k in range(n_c, len(axes)):
        axes[k].axis("off")
    # legend proxies
    from matplotlib.lines import Line2D

    handles = [
        Line2D([0], [0], color="#6b4c7a", lw=1.5, label="victim"),
        Line2D([0], [0], color="#8aa0a8", lw=1.2, label="control"),
    ]
    fig.legend(handles=handles, loc="upper right")
    fig.suptitle(f"P0.3 z-scored subject-median curves ({tag})", y=1.01)
    fig.tight_layout()
    fig.savefig(out_dir / f"overlay_zscored_{tag}.png", dpi=140, bbox_inches="tight")
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
    pearson_survives = (
        r["perm_p_pearson"] <= 0.05
        and r["loso_pass"]
        and r["mean_pairwise_pearson"] > r["null_mean_pearson"]
    )
    dtw_survives = (
        r["perm_p_dtw"] <= 0.05
        and r["mean_pairwise_dtw"] < r["null_mean_dtw"]
    )
    if pearson_survives or dtw_survives:
        decision = "CANDIDATE shared-shape signal (requires independent cohort)"
        detail = []
        if pearson_survives:
            detail.append("Pearson")
        if dtw_survives:
            detail.append("DTW")
        decision += f" — surviving measure(s): {', '.join(detail)}"
    else:
        decision = "NULL after residualization"

    text = f"""# P0.3 Shared waveform shape (amplitude-normalized)

Generated: {date.today().isoformat()}

## Question

Do the 17 victims share *waveform shape / timing* on core gait curves after
discarding ROM/amplitude — a question neither P0.1 (PC-space direction) nor
P0.2 (binary exceedance) tested?

Unit: **subject** (n=31). Labels shuffled across subjects only.

## Amplitude normalization (preregistered)

**Z-score each subject-median curve across the 101 phase points** (zero mean,
unit variance), independently per curve. This explicitly discards amplitude/ROM
and DC offset; only shape/timing remains. The same z-scored curves enter both
Pearson and DTW so DTW cannot re-introduce magnitude.

Curve list locked in `preregistered_curves.json` **before** any real test
(n={s['n_curves']}). Phase 1 core has pelvis *markers* (LASI/RASI), not
PelvisAngles — documented in the lock file.

## Pre-residual

| Metric | Pearson (↑ similar) | DTW distance (↓ similar) |
|---|---|---|
| Mean pairwise (victims, avg over curves) | {s['mean_pairwise_pearson']:.4f} | {s['mean_pairwise_dtw']:.4f} |
| 95% bootstrap CI | [{s['pearson_ci_low']:.4f}, {s['pearson_ci_high']:.4f}] | [{s['dtw_ci_low']:.4f}, {s['dtw_ci_high']:.4f}] |
| Permutation p | {s['perm_p_pearson']:.4g} (greater) | {s['perm_p_dtw']:.4g} (less) |
| Null mean / tail | {s['null_mean_pearson']:.4f} / p95={s['null_p95_pearson']:.4f} | {s['null_mean_dtw']:.4f} / p05={s['null_p05_dtw']:.4f} |
| LOSO sign agreement / pass | {s['loso_sign_agreement']:.3f} / {s['loso_pass']} | (distance; see LOSO range in tables) |
| Curves with FDR q ≤ 0.10 | {s['n_curves_pearson_fdr_le_0_10']} | {s['n_curves_dtw_fdr_le_0_10']} |

## Post-residual (height, mass, mean leg length, cycle duration)

Each (curve × phase %) column residualized across subjects **before** z-scoring
and similarity. Covariates: {', '.join(r['residual_covariates'])}.

### Cycle duration × DTW (explicit flag)

Residualizing cycle duration removes linear associations between absolute gait
speed and the *value* of each phase-% sample. DTW on 0–100% normalized curves
already allows **nonlinear phase warping** of shape. These are different timing
constructs; neither replaces the other. Both Pearson and DTW are reported after
the same residualization — we do not silently drop duration for the DTW path.

| Metric | Pearson (↑ similar) | DTW distance (↓ similar) |
|---|---|---|
| Mean pairwise (victims, avg over curves) | {r['mean_pairwise_pearson']:.4f} | {r['mean_pairwise_dtw']:.4f} |
| 95% bootstrap CI | [{r['pearson_ci_low']:.4f}, {r['pearson_ci_high']:.4f}] | [{r['dtw_ci_low']:.4f}, {r['dtw_ci_high']:.4f}] |
| Permutation p | {r['perm_p_pearson']:.4g} (greater) | {r['perm_p_dtw']:.4g} (less) |
| Null mean / tail | {r['null_mean_pearson']:.4f} / p95={r['null_p95_pearson']:.4f} | {r['null_mean_dtw']:.4f} / p05={r['null_p05_dtw']:.4f} |
| LOSO sign agreement / pass | {r['loso_sign_agreement']:.3f} / {r['loso_pass']} | — |
| Curves with FDR q ≤ 0.10 | {r['n_curves_pearson_fdr_le_0_10']} | {r['n_curves_dtw_fdr_le_0_10']} |

## Decision (P0.3 only)

**{decision}**

Gate: primary evidence is **post-residual**. A defensible shared-shape claim
requires at least one of Pearson or DTW with perm p ≤ 0.05 and observed on the
similarity side of the null mean (Pearson above; DTW below), with Pearson also
requiring LOSO pass. The two measures are never averaged into one number.

Phases 0–6 were not modified. P0.4–P0.6 not run in this script.
"""
    (out / "p03_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P0.3 shape-space waveform similarity")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-perm", type=int, default=9999)
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    root = args.root.resolve()
    out = _dirs(root)

    data = load_phase1_subject_median_curves(root)
    X = data["X"]
    victim = data["victim"]
    ids = data["subject_id"]
    curve_ids = data["curve_ids"]
    cov, cov_names = load_covariates(root, ids)

    summary, details = run_shape_space(
        X,
        victim,
        curve_ids,
        representation="phase1_zscored_core_curves",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
    )
    X_res = residualize_curves(X, cov)
    summary_r, details_r = run_shape_space(
        X_res,
        victim,
        curve_ids,
        representation="phase1_zscored_core_curves_residualized",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
        residualized=True,
        residual_covariates=tuple(cov_names),
    )

    pd.DataFrame([summary.to_dict(), summary_r.to_dict()]).to_csv(out / "summary.csv", index=False)
    details["curve_table"].to_csv(out / "per_curve_similarity.csv", index=False)
    details_r["curve_table"].to_csv(out / "per_curve_similarity_residualized.csv", index=False)
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

    _plot_overlays(details["Z"], victim, curve_ids, out / "figures", tag="raw")
    _plot_overlays(details_r["Z"], victim, curve_ids, out / "figures", tag="residualized")
    _plot_null(
        details["perm"]["null_pearson"],
        summary.mean_pairwise_pearson,
        out / "figures" / "permutation_null_pearson.png",
        "Mean pairwise Pearson among labeled victims",
        "P0.3 Pearson permutation null",
    )
    _plot_null(
        details["perm"]["null_dtw"],
        summary.mean_pairwise_dtw,
        out / "figures" / "permutation_null_dtw.png",
        "Mean pairwise DTW distance among labeled victims",
        "P0.3 DTW permutation null",
    )
    _plot_null(
        details_r["perm"]["null_pearson"],
        summary_r.mean_pairwise_pearson,
        out / "figures" / "permutation_null_pearson_residualized.png",
        "Mean pairwise Pearson among labeled victims",
        "P0.3 Pearson permutation null (residualized)",
    )
    _plot_null(
        details_r["perm"]["null_dtw"],
        summary_r.mean_pairwise_dtw,
        out / "figures" / "permutation_null_dtw_residualized.png",
        "Mean pairwise DTW distance among labeled victims",
        "P0.3 DTW permutation null (residualized)",
    )

    _write_report(
        out,
        {"summary": summary.to_dict()},
        {"summary": summary_r.to_dict()},
    )

    print("=" * 60)
    print("P0.3 SHAPE-SPACE WAVEFORM SIMILARITY")
    print("=" * 60)
    print(f"Representation     {data['source']}  shape={X.shape}")
    print(f"Victims / controls {int(victim.sum())} / {int((~victim).sum())}")
    print(f"Curves             {len(curve_ids)} (z-scored per curve)")
    print("--- pre-residual ---")
    print(f"Pearson mean       {summary.mean_pairwise_pearson:.4f}  p={summary.perm_p_pearson:.4g}")
    print(f"DTW mean dist      {summary.mean_pairwise_dtw:.4f}  p={summary.perm_p_dtw:.4g}")
    print(f"LOSO pass          {summary.loso_pass}")
    print("--- post-residual ---")
    print(f"Pearson mean       {summary_r.mean_pairwise_pearson:.4f}  p={summary_r.perm_p_pearson:.4g}")
    print(f"DTW mean dist      {summary_r.mean_pairwise_dtw:.4f}  p={summary_r.perm_p_dtw:.4g}")
    print(f"LOSO pass          {summary_r.loso_pass}")
    print(f"FDR<=0.10 pearson  {summary_r.n_curves_pearson_fdr_le_0_10}")
    print(f"FDR<=0.10 dtw      {summary_r.n_curves_dtw_fdr_le_0_10}")
    print(f"Wrote              {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
