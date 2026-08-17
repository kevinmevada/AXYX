"""P0.2 runner: shared abnormality-set Jaccard on preregistered features.

Does not modify Phases 0–6. Writes results/similarity/p02_abnormality/.
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

from gait_research.similarity.abnormality import (  # noqa: E402
    SEED,
    run_abnormality_overlap,
)
from gait_research.similarity.deviation import residualize_columns  # noqa: E402
from gait_research.similarity.load import (  # noqa: E402
    load_covariates,
    load_preregistered_abnormality_features,
)


def _dirs(root: Path) -> Path:
    out = root / "results" / "similarity" / "p02_abnormality"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    return out


def _short_name(name: str) -> str:
    return name.replace("__median", "").replace("Angles_", "").replace("coord_", "c_")


def _plot_fingerprint(
    B: np.ndarray,
    victim: np.ndarray,
    subject_id: np.ndarray,
    feature_names: list[str],
    path: Path,
    title: str,
) -> None:
    """Victim × feature exceedance heatmap (the shared-set fingerprint)."""
    v_idx = np.where(victim)[0]
    # order features by victim prevalence (most shared first)
    prev = B[v_idx].mean(axis=0)
    f_order = np.argsort(-prev)
    Bm = B[np.ix_(v_idx, f_order)]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.imshow(Bm, aspect="auto", cmap="Greys", vmin=0, vmax=1, interpolation="nearest")
    ax.set_yticks(range(len(v_idx)))
    ax.set_yticklabels([str(subject_id[i]) for i in v_idx], fontsize=7)
    ax.set_xticks(range(len(feature_names)))
    ax.set_xticklabels([_short_name(feature_names[j]) for j in f_order], fontsize=6, rotation=90)
    ax.set_xlabel("Preregistered features (ordered by victim exceedance prevalence)")
    ax.set_ylabel("Victims")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _plot_null(null: np.ndarray, obs: float, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(null, bins=40, color="#8aa0a8", edgecolor="white")
    ax.axvline(obs, color="#6b4c7a", lw=2, label=f"observed={obs:.3f}")
    ax.set_xlabel("Mean pairwise Jaccard among labeled 'victims'")
    ax.set_title("P0.2 permutation null (subject-label shuffle)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _plot_coexceedance(feat_tab: pd.DataFrame, path: Path) -> None:
    tab = feat_tab.sort_values("victim_pairwise_coexceedance", ascending=True)
    fig, ax = plt.subplots(figsize=(7, 8))
    y = np.arange(len(tab))
    ax.barh(y, tab["victim_pairwise_coexceedance"], color="#6b4c7a", height=0.6, label="observed")
    ax.scatter(tab["null_mean_coexceedance"], y, color="#8aa0a8", s=28, zorder=3, label="null mean")
    ax.set_yticks(y)
    ax.set_yticklabels([_short_name(f) for f in tab["feature"]], fontsize=7)
    ax.set_xlabel("Pairwise co-exceedance rate among victims")
    ax.set_title("Per-feature co-exceedance vs permutation null")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _write_report(out: Path, raw: dict, resid: dict) -> None:
    s = raw["summary"]
    r = resid["summary"]
    decision = (
        "NULL after residualization"
        if (
            r["perm_p"] > 0.05
            or not r["loso_pass"]
            or r["mean_pairwise_jaccard"] <= r["null_mean"]
        )
        else "CANDIDATE shared-abnormality-set signal (requires independent cohort)"
    )
    text = f"""# P0.2 Shared abnormality-set overlap

Generated: {date.today().isoformat()}

## Question

Do the 17 victims share *which* preregistered features fall outside the control
10th–90th percentile band — a discrete abnormality set — even if continuous
deviation directions (P0.1) do not align?

Statistic: mean pairwise Jaccard among victim binary exceedance vectors.

Unit: **subject** (n=31). Labels shuffled across subjects only.

Feature list locked in `preregistered_features.json` **before** any real test
(n={s['n_features']}). No post-hoc search of the full Phase 2 matrix.

## Pre-residual (raw preregistered features)

| Metric | Value |
|---|---|
| Mean pairwise Jaccard (victims) | {s['mean_pairwise_jaccard']:.4f} |
| 95% bootstrap CI | [{s['bootstrap_ci_low']:.4f}, {s['bootstrap_ci_high']:.4f}] |
| Permutation p (greater) | {s['perm_p']:.4g} |
| Null mean / 95th pct | {s['null_mean']:.4f} / {s['null_p95']:.4f} |
| Mean victim exceedance prevalence | {s['mean_victim_prevalence']:.3f} |
| LOSO top-5 feature-rank agreement / pass | {s['top5_feature_rank_agreement']:.3f} / {s['loso_pass']} |
| Features with co-exceedance FDR q ≤ 0.10 | {s['n_features_fdr_le_0_10']} |

## Post-residual (height, mass, mean leg length, cycle duration)

Continuous features residualized on covariates **before** control-band
binarization.

| Metric | Value |
|---|---|
| Mean pairwise Jaccard (victims) | {r['mean_pairwise_jaccard']:.4f} |
| 95% bootstrap CI | [{r['bootstrap_ci_low']:.4f}, {r['bootstrap_ci_high']:.4f}] |
| Permutation p (greater) | {r['perm_p']:.4g} |
| Null mean / 95th pct | {r['null_mean']:.4f} / {r['null_p95']:.4f} |
| Mean victim exceedance prevalence | {r['mean_victim_prevalence']:.3f} |
| LOSO top-5 feature-rank agreement / pass | {r['top5_feature_rank_agreement']:.3f} / {r['loso_pass']} |
| Features with co-exceedance FDR q ≤ 0.10 | {r['n_features_fdr_le_0_10']} |
| Covariates | {', '.join(r['residual_covariates'])} |

## Decision (P0.2 only)

**{decision}**

Gate: primary evidence is the **post-residual** result. A defensible shared-set
signal requires perm p ≤ 0.05, LOSO feature-rank pass, and observed Jaccard
above the permutation null mean after residualization.

Per-feature co-exceedance + BH-FDR is a diagnostic (fingerprint), not a second
primary claim.

Phases 0–6 were not modified. P0.3–P0.6 not run in this script.
"""
    (out / "p02_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P0.2 abnormality-set Jaccard similarity")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-perm", type=int, default=9999)
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    root = args.root.resolve()
    out = _dirs(root)

    data = load_preregistered_abnormality_features(root)
    X = data["X"]
    victim = data["victim"]
    ids = data["subject_id"]
    names = data["feature_names"]
    cov, cov_names = load_covariates(root, ids)

    summary, details = run_abnormality_overlap(
        X,
        victim,
        names,
        representation="preregistered_30",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
    )
    X_res = residualize_columns(X, cov)
    summary_r, details_r = run_abnormality_overlap(
        X_res,
        victim,
        names,
        representation="preregistered_30_residualized",
        n_perm=args.n_perm,
        n_boot=args.n_boot,
        seed=SEED,
        residualized=True,
        residual_covariates=tuple(cov_names),
    )

    pd.DataFrame([summary.to_dict(), summary_r.to_dict()]).to_csv(out / "summary.csv", index=False)
    details["feature_table"].to_csv(out / "feature_coexceedance.csv", index=False)
    details_r["feature_table"].to_csv(out / "feature_coexceedance_residualized.csv", index=False)
    pd.DataFrame(details["jaccard_matrix"], index=ids, columns=ids).to_csv(out / "jaccard_matrix.csv")
    pd.DataFrame({"null_mean_pairwise_jaccard": details["perm_null"]}).to_csv(
        out / "permutation_null.csv", index=False
    )
    # subject exceedance rows
    exc = pd.DataFrame(details["B"], columns=names)
    exc.insert(0, "subject_id", ids)
    exc.insert(1, "victimized", np.where(victim, "Y", "N"))
    exc.to_csv(out / "exceedance_matrix.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps({"raw": summary.to_dict(), "residualized": summary_r.to_dict()}, indent=2),
        encoding="utf-8",
    )

    _plot_fingerprint(
        details["B"],
        victim,
        ids,
        names,
        out / "figures" / "fingerprint_heatmap.png",
        "P0.2 fingerprint: victim exceedance of control 10–90% band",
    )
    _plot_fingerprint(
        details_r["B"],
        victim,
        ids,
        names,
        out / "figures" / "fingerprint_heatmap_residualized.png",
        "P0.2 fingerprint (residualized): victim exceedance of control 10–90% band",
    )
    _plot_null(details["perm_null"], summary.mean_pairwise_jaccard, out / "figures" / "permutation_null.png")
    _plot_null(
        details_r["perm_null"],
        summary_r.mean_pairwise_jaccard,
        out / "figures" / "permutation_null_residualized.png",
    )
    _plot_coexceedance(details["feature_table"], out / "figures" / "coexceedance_by_feature.png")
    _plot_coexceedance(
        details_r["feature_table"], out / "figures" / "coexceedance_by_feature_residualized.png"
    )

    _write_report(
        out,
        {"summary": summary.to_dict(), "details": details},
        {"summary": summary_r.to_dict(), "details": details_r},
    )

    print("=" * 60)
    print("P0.2 ABNORMALITY-SET JACCARD OVERLAP")
    print("=" * 60)
    print(f"Representation     {data['source']}  shape={X.shape}")
    print(f"Victims / controls {int(victim.sum())} / {int((~victim).sum())}")
    print("--- pre-residual ---")
    print(f"Mean pairwise Jac  {summary.mean_pairwise_jaccard:.4f}")
    print(f"95% CI             [{summary.bootstrap_ci_low:.4f}, {summary.bootstrap_ci_high:.4f}]")
    print(f"Perm p             {summary.perm_p:.4g}")
    print(f"Null mean          {summary.null_mean:.4f}")
    print(f"LOSO pass          {summary.loso_pass} (top5 agree={summary.top5_feature_rank_agreement:.3f})")
    print(f"FDR<=0.10 features  {summary.n_features_fdr_le_0_10}")
    print("--- post-residual ---")
    print(f"Mean pairwise Jac  {summary_r.mean_pairwise_jaccard:.4f}")
    print(f"95% CI             [{summary_r.bootstrap_ci_low:.4f}, {summary_r.bootstrap_ci_high:.4f}]")
    print(f"Perm p             {summary_r.perm_p:.4g}")
    print(f"Null mean          {summary_r.null_mean:.4f}")
    print(f"LOSO pass          {summary_r.loso_pass} (top5 agree={summary_r.top5_feature_rank_agreement:.3f})")
    print(f"FDR<=0.10 features  {summary_r.n_features_fdr_le_0_10}")
    print(f"Wrote              {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
