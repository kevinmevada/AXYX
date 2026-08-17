"""P0.1 runner: deviation-direction alignment on Phase 4 family-PC space.

Does not modify Phases 0–6. Writes results/similarity/p01_deviation/.
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
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gait_research.similarity.deviation import (  # noqa: E402
    SEED,
    residualize_columns,
    run_deviation_alignment,
)
from gait_research.similarity.load import load_covariates, load_phase4_compact  # noqa: E402


def _dirs(root: Path) -> Path:
    out = root / "results" / "similarity" / "p01_deviation"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    return out


def _plot_heatmap(C: np.ndarray, victim: np.ndarray, subject_id: np.ndarray, path: Path) -> None:
    # order: victims first, then controls
    order = np.concatenate([np.where(victim)[0], np.where(~victim)[0]])
    Cm = C[np.ix_(order, order)]
    labels = [str(subject_id[i]) for i in order]
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(Cm, vmin=-1, vmax=1, cmap="coolwarm", aspect="equal")
    n_v = int(victim.sum())
    ax.axhline(n_v - 0.5, color="k", lw=0.8)
    ax.axvline(n_v - 0.5, color="k", lw=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=6, rotation=90)
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_title("Cosine of control-referenced deviations\n(victims top-left block)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _plot_pca(D: np.ndarray, victim: np.ndarray, path: Path) -> None:
    pca = PCA(n_components=2, svd_solver="full", random_state=SEED)
    Z = pca.fit_transform(D)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(Z[~victim, 0], Z[~victim, 1], c="#8aa0a8", s=40, label="control", zorder=2)
    ax.scatter(Z[victim, 0], Z[victim, 1], c="#6b4c7a", s=44, label="victim", zorder=3)
    ax.axhline(0, color="#cccccc", lw=0.8)
    ax.axvline(0, color="#cccccc", lw=0.8)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
    ax.set_title("PCA of deviation vectors d_i = x_i − mean(controls)\n(space frozen before coloring)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _plot_null(null: np.ndarray, obs: float, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(null, bins=40, color="#8aa0a8", edgecolor="white")
    ax.axvline(obs, color="#6b4c7a", lw=2, label=f"observed={obs:.3f}")
    ax.set_xlabel("Mean pairwise cosine among labeled 'victims'")
    ax.set_title("P0.1 permutation null (subject-label shuffle)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _write_report(out: Path, raw: dict, resid: dict) -> None:
    s = raw["summary"]
    r = resid["summary"]
    decision = (
        "NULL after residualization"
        if r["perm_p"] > 0.05 or not r["loso_pass"] or r["bootstrap_ci_low"] <= 0
        else "CANDIDATE shared-direction signal (requires independent cohort)"
    )
    text = f"""# P0.1 Deviation-direction alignment

Generated: {date.today().isoformat()}

## Question

Do the 17 victims share a common *direction* of deviation from the control
centroid in Phase 4's 27-D family-PC gait space?

Statistic: mean pairwise cosine among victim deviation vectors
`d_i = x_i − mean(controls)`.

Unit: **subject** (n=31). Labels shuffled across subjects only.

## Pre-residual (raw Phase 4 representation)

| Metric | Value |
|---|---|
| Mean pairwise cosine (victims) | {s['mean_pairwise_cosine']:.4f} |
| 95% bootstrap CI | [{s['bootstrap_ci_low']:.4f}, {s['bootstrap_ci_high']:.4f}] |
| Permutation p (greater) | {s['perm_p']:.4g} |
| Null mean / 95th pct | {s['null_mean']:.4f} / {s['null_p95']:.4f} |
| Mean cosine → victim-mean direction | {s['mean_cosine_to_victim_direction']:.4f} |
| Consistency (frac cosines > 0) | {s['consistency_frac_positive']:.3f} |
| LOSO sign agreement / pass | {s['loso_sign_agreement']:.3f} / {s['loso_pass']} |
| Frac victims above null mean | {raw['details']['frac_victims_above_null_mean']:.3f} |

## Post-residual (height, mass, mean leg length, cycle duration)

| Metric | Value |
|---|---|
| Mean pairwise cosine (victims) | {r['mean_pairwise_cosine']:.4f} |
| 95% bootstrap CI | [{r['bootstrap_ci_low']:.4f}, {r['bootstrap_ci_high']:.4f}] |
| Permutation p (greater) | {r['perm_p']:.4g} |
| Null mean / 95th pct | {r['null_mean']:.4f} / {r['null_p95']:.4f} |
| Mean cosine → victim-mean direction | {r['mean_cosine_to_victim_direction']:.4f} |
| Consistency (frac cosines > 0) | {r['consistency_frac_positive']:.3f} |
| LOSO sign agreement / pass | {r['loso_sign_agreement']:.3f} / {r['loso_pass']} |
| Covariates | {', '.join(r['residual_covariates'])} |

## Decision (P0.1 only)

**{decision}**

Gate: primary evidence is the **post-residual** result. A defensible shared-direction
signal requires perm p ≤ 0.05, LOSO pass, and bootstrap CI excluding ≤0 after residualization.

Phases 0–6 were not modified. P0.2–P0.6 not run in this script.
"""
    (out / "p01_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P0.1 deviation-direction similarity")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-perm", type=int, default=9999)
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    root = args.root.resolve()
    out = _dirs(root)

    data = load_phase4_compact(root)
    X = data["X"]
    victim = data["victim"]
    ids = data["subject_id"]
    cov, cov_names = load_covariates(root, ids)

    summary, details = run_deviation_alignment(
        X, victim, representation="phase4_family_pc_27d", n_perm=args.n_perm, n_boot=args.n_boot, seed=SEED
    )
    X_res = residualize_columns(X, cov)
    summary_r, details_r = run_deviation_alignment(
        X_res,
        victim,
        representation="phase4_family_pc_27d_residualized",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
        residualized=True,
        residual_covariates=tuple(cov_names),
    )

    # tables
    pd.DataFrame([summary.to_dict(), summary_r.to_dict()]).to_csv(out / "summary.csv", index=False)
    cos_df = pd.DataFrame(details["cosine_matrix"], index=ids, columns=ids)
    cos_df.to_csv(out / "cosine_matrix.csv")
    align = []
    v_idx = np.where(victim)[0]
    v_cos = details["victim_cosines_to_mean_direction"]
    v_map = {int(i): float(v_cos[k]) for k, i in enumerate(v_idx)}
    for i, sid in enumerate(ids):
        align.append(
            {
                "subject_id": sid,
                "victimized": "Y" if victim[i] else "N",
                "deviation_norm": float(np.linalg.norm(details["D"][i])),
                "cosine_to_victim_mean_direction": v_map.get(i, float("nan")),
            }
        )
    pd.DataFrame(align).to_csv(out / "subject_alignment.csv", index=False)
    pd.DataFrame({"null_mean_pairwise_cosine": details["perm_null"]}).to_csv(out / "permutation_null.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps({"raw": summary.to_dict(), "residualized": summary_r.to_dict()}, indent=2),
        encoding="utf-8",
    )

    _plot_heatmap(details["cosine_matrix"], victim, ids, out / "figures" / "cosine_heatmap.png")
    _plot_pca(details["D"], victim, out / "figures" / "deviation_pca.png")
    _plot_null(details["perm_null"], summary.mean_pairwise_cosine, out / "figures" / "permutation_null.png")
    _plot_heatmap(details_r["cosine_matrix"], victim, ids, out / "figures" / "cosine_heatmap_residualized.png")
    _plot_null(details_r["perm_null"], summary_r.mean_pairwise_cosine, out / "figures" / "permutation_null_residualized.png")

    _write_report(
        out,
        {"summary": summary.to_dict(), "details": details},
        {"summary": summary_r.to_dict(), "details": details_r},
    )

    print("=" * 60)
    print("P0.1 DEVIATION-DIRECTION ALIGNMENT")
    print("=" * 60)
    print(f"Representation     {data['source']}  shape={X.shape}")
    print(f"Victims / controls {int(victim.sum())} / {int((~victim).sum())}")
    print("--- pre-residual ---")
    print(f"Mean pairwise cos  {summary.mean_pairwise_cosine:.4f}")
    print(f"95% CI             [{summary.bootstrap_ci_low:.4f}, {summary.bootstrap_ci_high:.4f}]")
    print(f"Perm p             {summary.perm_p:.4g}")
    print(f"Consistency (>0)   {summary.consistency_frac_positive:.3f}")
    print(f"LOSO pass          {summary.loso_pass} (agree={summary.loso_sign_agreement:.3f})")
    print("--- post-residual ---")
    print(f"Mean pairwise cos  {summary_r.mean_pairwise_cosine:.4f}")
    print(f"95% CI             [{summary_r.bootstrap_ci_low:.4f}, {summary_r.bootstrap_ci_high:.4f}]")
    print(f"Perm p             {summary_r.perm_p:.4g}")
    print(f"Consistency (>0)   {summary_r.consistency_frac_positive:.3f}")
    print(f"LOSO pass          {summary_r.loso_pass} (agree={summary_r.loso_sign_agreement:.3f})")
    print(f"Wrote              {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
