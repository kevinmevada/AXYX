"""P0.1 power / MDE runner.

Reads frozen residualized Phase 4 representation and frozen P0.1 permutation
null. Does not modify Phases 0–6 or P0.1–P0.6 result files.
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

from gait_research.similarity.deviation import (  # noqa: E402
    SEED,
    permute_mean_pairwise_cosine,
    residualize_columns,
)
from gait_research.similarity.load import load_covariates, load_phase4_compact  # noqa: E402
from gait_research.similarity.power_analysis import (  # noqa: E402
    LAMBDA_GRID_DEFAULT,
    N_PERM_POWER,
    N_SIM_DEFAULT,
    compare_null_moments,
    fit_control_noise_model,
    run_power_curve,
)


def _dirs(root: Path) -> Path:
    out = root / "results" / "similarity" / "power_analysis"
    (out / "figures").mkdir(parents=True, exist_ok=True)
    return out


def _plot_power_curve(df: pd.DataFrame, mde: float, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df["lambda"], df["power"], color="#6b4c7a", marker="o", lw=2)
    ax.axhline(0.80, color="#8aa0a8", ls="--", lw=1, label="80% power")
    ax.axhline(0.05, color="#cccccc", ls=":", lw=1, label="α = 0.05")
    if np.isfinite(mde):
        ax.axvline(mde, color="#6b4c7a", ls=":", lw=1.2, label=f"MDE λ={mde:.2f}")
    ax.set_xlabel("λ (shared-direction magnitude / typical control ||d||)")
    ax.set_ylabel("Power (P(perm p ≤ 0.05))")
    ax.set_ylim(-0.02, 1.05)
    ax.set_title("P0.1 power curve (n=17 vs 14, residualized 27-D)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _plot_null_compare(sim: np.ndarray, real: np.ndarray, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.hist(real, bins=40, density=True, color="#8aa0a8", alpha=0.7, label="residualized P0.1 perm null")
    ax.hist(sim, bins=30, density=True, color="#6b4c7a", alpha=0.55, label="simulated lambda=0 observed")
    ax.set_xlabel("Mean pairwise cosine among labeled victims")
    ax.set_ylabel("Density")
    ax.set_title("Noise-model check: simulated λ=0 vs frozen P0.1 null")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _write_report(
    out: Path,
    summary,
    noise: dict,
    cmp_: dict,
    observed_cosine: float,
) -> None:
    mde = summary.mde_lambda_80
    mde_cos = summary.mde_mean_cosine_80
    if np.isfinite(mde) and observed_cosine < mde_cos:
        vs = (
            f"The observed residualized cosine ({observed_cosine:.3f}) is "
            f"**smaller than this detection threshold** (expected cosine at "
            f"the 80% MDE ≈ {mde_cos:.3f}) and is therefore consistent with "
            f"being undetectable given n=17 vs 14."
        )
    elif np.isfinite(mde):
        vs = (
            f"The observed residualized cosine ({observed_cosine:.3f}) is "
            f"near the 80% MDE expected cosine ({mde_cos:.3f})."
        )
    else:
        vs = "Power did not reach 80% anywhere on the simulated grid."

    pw_half = next(
        (pw for lam, pw in zip(summary.lambdas, summary.power) if abs(lam - 0.5) < 1e-12),
        None,
    )
    honest = ""
    if np.isfinite(mde):
        half = (
            f" At λ=0.50, simulated power was only {pw_half:.0%}."
            if pw_half is not None
            else ""
        )
        honest = (
            f" That MDE is a *large* shared shift: victims would need a common "
            f"offset of {mde:.2f}× a typical control's entire residual deviation "
            f"(median ||d|| = {noise['typical_norm']:.2f} in 27-D) before this "
            f"n=17 vs 14 design reliably detects it.{half} This battery is "
            f"powered for a gross shared direction, not a subtle one."
        )

    rows = "\n".join(
        f"| {lam:.2f} | {pw:.3f} | {cs:.3f} | {nr}/{summary.n_sim} |"
        for lam, pw, cs, nr in zip(
            summary.lambdas, summary.power, summary.mean_observed_cosine, summary.n_reject
        )
    )
    text = f"""# P0.1 power / minimum-detectable effect

Generated: {date.today().isoformat()}

## Question

At n=17 victims vs 14 controls in residualized Phase 4 27-D space, how large
a **shared deviation direction** would P0.1 have been likely to detect?

This does not re-run or alter the frozen P0.1 test. It asks whether the
observed null (cosine 0.052, p=0.758) is unsurprising given the design's
sensitivity.

## Method

- **Noise model:** the frozen residualized 31 × 27 Phase 4 cloud itself.
  Each replicate randomly partitions those 31 points into 17/14 and, for
  λ>0, adds a shared offset of length `λ × median_control||d||` to the 17
  (same shared-direction generator as `test_deviation.test_shared_direction_detected`,
  with empirical residual noise instead of isotropic Gaussian).
  A parametric Ledoit–Wolf MVN fit to the 14 controls failed the null-shape
  check (too spherical; simulated λ=0 cosine mean 0.06 vs residualized
  permutation null 0.11) and was not used for the headline MDE.
- **Typical individual scale:** median **control** `||d_i||` = {noise['typical_norm']:.4f}.
- **Effect size λ:** shared offset Euclidean length = `λ × median ||d_control||`
  along a random unit direction (same generative pattern as
  `test_deviation.test_shared_direction_detected`, with real residual noise
  replacing isotropic N(0, 0.3²I)).
- **Test:** the actual P0.1 statistic (mean pairwise cosine among 17 labeled
  victims, one-sided subject-label permutation).
- **Simulations:** {summary.n_sim} datasets per λ; {summary.n_perm} permutations
  per dataset (reduced from P0.1's 9999 for compute; documented). α = 0.05.
- **Seed:** {summary.seed}.

## Sanity checks

| Check | Result |
|---|---|
| False-positive rate at λ=0 | {summary.fpr_at_zero:.3f} (target ~0.05) |
| Power at λ={summary.lambdas[-1]:.1f} | {summary.power_at_large:.3f} (must approach 1) |
| Simulated λ=0 cosine mean vs real P0.1 null mean | {cmp_['sim_mean']:.3f} vs {cmp_['real_mean']:.3f} (rel. diff {cmp_['rel_mean_diff']:.2f}) |
| Simulated λ=0 cosine SD vs real P0.1 null SD | {cmp_['sim_sd']:.3f} vs {cmp_['real_sd']:.3f} (rel. diff {cmp_['rel_sd_diff']:.2f}) |

## Power curve

| λ | Power | Mean observed cosine | Rejections |
|---|---|---|---|
{rows}

## Headline MDE

**80% power at λ = {mde:.2f}** (shared-direction magnitude as a fraction of
typical individual control deviation). At that λ, simulated mean pairwise
cosine is approximately **{mde_cos:.3f}**.

This design had approximately **80% power to detect a shared deviation
direction of magnitude ≥ {mde:.2f}× the typical individual control
deviation-vector norm** (equivalently: a shared offset that produces mean
pairwise cosine among victims of about {mde_cos:.3f} under this noise model).
{vs}{honest}

Observed P0.1 residualized cosine = {observed_cosine:.3f} (perm p = 0.758).

## What this does not say

- It does not turn the P0.1 null into a positive.
- It does not estimate power for P0.2–P0.6 (not run; P0.1 is the primary MDE).
- λ>0 is a shared Euclidean offset in a random direction on the empirical
  residual cloud — one alternative, not every possible shared pattern.
  If the λ=0 vs residualized-permutation-null gap is large, do not trust
  the MDE.

Phases 0–6 and P0.1–P0.6 result files were not modified.
"""
    (out / "mde_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P0.1 power / MDE analysis")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--n-sim", type=int, default=N_SIM_DEFAULT)
    parser.add_argument("--n-perm", type=int, default=N_PERM_POWER)
    args = parser.parse_args()
    root = args.root.resolve()
    out = _dirs(root)

    data = load_phase4_compact(root)
    cov, _cov_names = load_covariates(root, data["subject_id"])
    X_res = residualize_columns(data["X"], cov)
    victim = data["victim"]
    noise = fit_control_noise_model(X_res, victim)

    print("Noise model: empirical injection on residualized 31-point cloud")
    print(f"  typical control ||d||     {noise['typical_norm']:.4f}")
    print(f"  n_sim={args.n_sim}  n_perm={args.n_perm}  grid={LAMBDA_GRID_DEFAULT}")
    print("Recomputing residualized P0.1 permutation null for shape check ...")
    real_null_a = permute_mean_pairwise_cosine(X_res, victim, n_perm=9999, seed=SEED)["null"]
    pd.DataFrame({"residualized_perm_null_cosine": real_null_a}).to_csv(
        out / "residualized_p01_perm_null.csv", index=False
    )
    observed = float(
        json.loads((root / "results" / "similarity" / "p01_deviation" / "summary.json").read_text())[
            "residualized"
        ]["mean_pairwise_cosine"]
    )

    summary, details = run_power_curve(
        noise["Sigma"],
        noise["mu"],
        noise["typical_norm"],
        lambdas=LAMBDA_GRID_DEFAULT,
        n_sim=args.n_sim,
        n_perm=args.n_perm,
        seed=SEED,
        observed_p01_cosine=observed,
        progress=True,
        X_empirical=X_res,
    )
    summary.ledoit_wolf_shrinkage = float(noise["ledoit_wolf_shrinkage"])

    cmp_ = compare_null_moments(details["obs_cosine_at_lambda0"], real_null_a)
    if cmp_["rel_mean_diff"] > 0.35 or cmp_["rel_sd_diff"] > 0.50:
        print("WARNING: simulated lambda=0 null shape differs from frozen P0.1 null.")
        print(f"  {cmp_}")

    df = pd.DataFrame(
        {
            "lambda": list(summary.lambdas),
            "power": list(summary.power),
            "mean_observed_cosine": list(summary.mean_observed_cosine),
            "n_reject": list(summary.n_reject),
            "n_sim": summary.n_sim,
            "n_perm": summary.n_perm,
        }
    )
    df.to_csv(out / "summary.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(
            {
                "summary": summary.to_dict(),
                "noise": {
                    k: (float(v) if isinstance(v, (float, np.floating, int)) else v)
                    for k, v in noise.items()
                    if k not in {"Sigma", "mu", "control_norms"}
                },
                "noise_model": "empirical_injection_on_residualized_31x27_cloud",
                "null_compare": cmp_,
            },
            indent=2,
            default=float,
        ),
        encoding="utf-8",
    )
    pd.DataFrame({"sim_lambda0_observed_cosine": details["obs_cosine_at_lambda0"]}).to_csv(
        out / "sim_lambda0_observed.csv", index=False
    )

    _plot_power_curve(df, summary.mde_lambda_80, out / "figures" / "power_curve.png")
    _plot_null_compare(
        details["obs_cosine_at_lambda0"], real_null_a, out / "figures" / "null_compare.png"
    )
    _write_report(out, summary, noise, cmp_, observed)

    print("=" * 60)
    print("P0.1 POWER / MDE")
    print("=" * 60)
    print(f"FPR at lambda=0       {summary.fpr_at_zero:.3f}")
    print(f"Power at lambda={summary.lambdas[-1]:.1f}  {summary.power_at_large:.3f}")
    print(f"MDE (80% power)      lambda={summary.mde_lambda_80:.3f}")
    print(f"  -> mean cosine      {summary.mde_mean_cosine_80:.3f}")
    print(f"Observed P0.1 cos    {observed:.3f}")
    print(f"Wrote                {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
