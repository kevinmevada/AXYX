"""P0.1 — Shared deviation-direction alignment (control-referenced).

Question
--------
Do victims share a common *direction* of deviation from the control centroid,
even if they are not close to each other in Euclidean space (Phase 5)?

Primary statistic
-----------------
Mean pairwise cosine similarity among the 17 victim deviation vectors
    d_i = x_i - mean(x_control)

Null
----
Permute victim/control labels across subjects (≥999), recompute control mean
and the same statistic. Unit = subject.

Pre-registered as the first primary similarity test. Phases 0–6 untouched.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260813
N_PERM_DEFAULT = 9999
N_BOOT_DEFAULT = 2000


def _row_norms(X: np.ndarray) -> np.ndarray:
    return np.linalg.norm(X, axis=1)


def pairwise_cosine_matrix(D: np.ndarray) -> np.ndarray:
    """Cosine similarity between every pair of row vectors. Zero-norm → 0."""
    D = np.asarray(D, dtype=float)
    n = D.shape[0]
    norms = _row_norms(D)
    out = np.zeros((n, n), dtype=float)
    for i in range(n):
        if norms[i] <= 0:
            continue
        for j in range(i, n):
            if norms[j] <= 0:
                continue
            c = float(np.dot(D[i], D[j]) / (norms[i] * norms[j]))
            out[i, j] = c
            out[j, i] = c
    return out


def mean_pairwise_cosine(D: np.ndarray) -> float:
    """Mean upper-triangle cosine among rows of D. NaN if <2 finite pairs."""
    D = np.asarray(D, dtype=float)
    if D.shape[0] < 2:
        return float("nan")
    C = pairwise_cosine_matrix(D)
    iu = np.triu_indices(D.shape[0], k=1)
    vals = C[iu]
    # exclude pairs involving a zero vector (cosine forced to 0 with itself-logic)
    norms = _row_norms(D)
    ok = (norms[iu[0]] > 0) & (norms[iu[1]] > 0)
    vals = vals[ok]
    if vals.size == 0:
        return float("nan")
    return float(np.mean(vals))


def control_referenced_deviations(X: np.ndarray, victim: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """d_i = x_i - mean(controls). Returns (D, control_mean)."""
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    if victim.ndim != 1 or victim.size != X.shape[0]:
        raise ValueError("victim mask must be length n_subjects")
    if int((~victim).sum()) < 1:
        raise ValueError("need at least one control to form reference mean")
    mu = X[~victim].mean(axis=0)
    return X - mu, mu


def cosines_to_direction(D: np.ndarray, direction: np.ndarray) -> np.ndarray:
    direction = np.asarray(direction, dtype=float)
    dn = np.linalg.norm(direction)
    D = np.asarray(D, dtype=float)
    out = np.full(D.shape[0], np.nan)
    if dn <= 0:
        return out
    norms = _row_norms(D)
    for i in range(D.shape[0]):
        if norms[i] <= 0:
            continue
        out[i] = float(np.dot(D[i], direction) / (norms[i] * dn))
    return out


def consistency_to_mean_direction(D_victims: np.ndarray) -> dict:
    """Fraction of victims with cosine(d_i, victim-mean d) > 0."""
    mean_dir = D_victims.mean(axis=0)
    cos = cosines_to_direction(D_victims, mean_dir)
    finite = cos[np.isfinite(cos)]
    if finite.size == 0:
        return {
            "victim_mean_direction_norm": float(np.linalg.norm(mean_dir)),
            "mean_cosine_to_victim_direction": float("nan"),
            "consistency_frac_positive": float("nan"),
            "n_finite": 0,
            "cosines": cos,
        }
    return {
        "victim_mean_direction_norm": float(np.linalg.norm(mean_dir)),
        "mean_cosine_to_victim_direction": float(np.mean(finite)),
        "consistency_frac_positive": float(np.mean(finite > 0)),
        "n_finite": int(finite.size),
        "cosines": cos,
    }


def permute_mean_pairwise_cosine(
    X: np.ndarray,
    victim: np.ndarray,
    *,
    n_perm: int = N_PERM_DEFAULT,
    seed: int = SEED,
) -> dict:
    """Subject-label permutation null for mean pairwise cosine among 'victims'."""
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    n = X.shape[0]
    n_v = int(victim.sum())
    D_obs, _ = control_referenced_deviations(X, victim)
    obs = mean_pairwise_cosine(D_obs[victim])
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm, dtype=float)
    idx = np.arange(n)
    for i in range(n_perm):
        pick = rng.choice(idx, size=n_v, replace=False)
        mask = np.zeros(n, dtype=bool)
        mask[pick] = True
        D, _ = control_referenced_deviations(X, mask)
        null[i] = mean_pairwise_cosine(D[mask])
    # one-sided: greater alignment than chance
    ge = int(np.sum(null >= obs - 1e-15)) if np.isfinite(obs) else n_perm
    p = (1 + ge) / (n_perm + 1)
    return {
        "observed": obs,
        "null": null,
        "null_mean": float(np.nanmean(null)),
        "null_sd": float(np.nanstd(null, ddof=1)),
        "null_p95": float(np.nanpercentile(null, 95)),
        "perm_p": float(p),
        "n_perm": n_perm,
        "unit": "subject",
        "alternative": "greater_mean_pairwise_cosine",
    }


def bootstrap_mean_pairwise_cosine(
    D_victims: np.ndarray,
    *,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    alpha: float = 0.05,
) -> dict:
    """Bootstrap CI by resampling victims with replacement."""
    D = np.asarray(D_victims, dtype=float)
    n = D.shape[0]
    rng = np.random.default_rng(seed)
    stats = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        stats[b] = mean_pairwise_cosine(D[idx])
    lo, hi = np.nanpercentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "ci_low": float(lo),
        "ci_high": float(hi),
        "n_boot": n_boot,
        "alpha": alpha,
        "boot_mean": float(np.nanmean(stats)),
    }


def loso_mean_pairwise_cosine(X: np.ndarray, victim: np.ndarray) -> dict:
    """Leave-one-subject-out: sign of observed statistic must stay positive.

    Drops one subject at a time. When a victim is dropped, n_v decreases.
    When a control is dropped, the reference mean changes.
    Passes if every LOSO observed mean-pairwise-cosine among remaining victims
    has the same sign as the full-sample observed (or both near zero).
    """
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    D_full, _ = control_referenced_deviations(X, victim)
    obs = mean_pairwise_cosine(D_full[victim])
    sign0 = 0.0 if not np.isfinite(obs) or abs(obs) < 1e-12 else float(np.sign(obs))
    n = X.shape[0]
    vals = []
    same = 0
    for i in range(n):
        keep = np.ones(n, dtype=bool)
        keep[i] = False
        v = victim[keep]
        if int(v.sum()) < 2 or int((~v).sum()) < 1:
            vals.append(float("nan"))
            continue
        D, _ = control_referenced_deviations(X[keep], v)
        s = mean_pairwise_cosine(D[v])
        vals.append(s)
        if sign0 == 0.0:
            same += 1
        elif np.isfinite(s) and np.sign(s) == sign0:
            same += 1
    vals_a = np.asarray(vals, dtype=float)
    return {
        "full_observed": obs,
        "loso_values": vals_a,
        "loso_min": float(np.nanmin(vals_a)),
        "loso_max": float(np.nanmax(vals_a)),
        "loso_sign_agreement": float(same / n),
        "loso_pass": bool(same == n and np.isfinite(obs)),
        "sign_reference": sign0,
    }


@dataclass
class DeviationResult:
    representation: str
    n_subjects: int
    n_victims: int
    n_controls: int
    n_dims: int
    mean_pairwise_cosine: float
    bootstrap_ci_low: float
    bootstrap_ci_high: float
    perm_p: float
    null_mean: float
    null_p95: float
    n_perm: int
    mean_cosine_to_victim_direction: float
    consistency_frac_positive: float
    loso_pass: bool
    loso_sign_agreement: float
    loso_min: float
    residualized: bool
    residual_covariates: tuple[str, ...]
    seed: int

    def to_dict(self) -> dict:
        return asdict(self)


def run_deviation_alignment(
    X: np.ndarray,
    victim: np.ndarray,
    *,
    representation: str = "phase4_family_pc",
    n_perm: int = N_PERM_DEFAULT,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED,
    residualized: bool = False,
    residual_covariates: tuple[str, ...] = (),
) -> tuple[DeviationResult, dict]:
    """Full P0.1 analysis. Returns summary + detailed arrays for plotting."""
    X = np.asarray(X, dtype=float)
    victim = np.asarray(victim, dtype=bool)
    if X.shape[0] != victim.size:
        raise ValueError("X rows must match victim mask")
    if int(victim.sum()) < 2:
        raise ValueError("need ≥2 victims")
    if int((~victim).sum()) < 1:
        raise ValueError("need ≥1 control")

    D, mu_c = control_referenced_deviations(X, victim)
    D_v = D[victim]
    C_all = pairwise_cosine_matrix(D)
    cons = consistency_to_mean_direction(D_v)
    perm = permute_mean_pairwise_cosine(X, victim, n_perm=n_perm, seed=seed)
    boot = bootstrap_mean_pairwise_cosine(D_v, n_boot=n_boot, seed=seed)
    loso = loso_mean_pairwise_cosine(X, victim)

    # Per-victim consistency vs null: fraction of victims whose mean cosine
    # to other victims exceeds the null mean of the group statistic.
    per_victim = []
    for i in range(D_v.shape[0]):
        others = np.delete(D_v, i, axis=0)
        # mean cosine of this victim to each other victim
        ni = np.linalg.norm(D_v[i])
        if ni <= 0:
            per_victim.append(float("nan"))
            continue
        cs = []
        for j in range(others.shape[0]):
            nj = np.linalg.norm(others[j])
            if nj <= 0:
                continue
            cs.append(float(np.dot(D_v[i], others[j]) / (ni * nj)))
        per_victim.append(float(np.mean(cs)) if cs else float("nan"))
    per_victim = np.asarray(per_victim, dtype=float)
    frac_above_null = float(np.nanmean(per_victim > perm["null_mean"])) if per_victim.size else float("nan")

    summary = DeviationResult(
        representation=representation,
        n_subjects=int(X.shape[0]),
        n_victims=int(victim.sum()),
        n_controls=int((~victim).sum()),
        n_dims=int(X.shape[1]),
        mean_pairwise_cosine=float(perm["observed"]),
        bootstrap_ci_low=boot["ci_low"],
        bootstrap_ci_high=boot["ci_high"],
        perm_p=perm["perm_p"],
        null_mean=perm["null_mean"],
        null_p95=perm["null_p95"],
        n_perm=perm["n_perm"],
        mean_cosine_to_victim_direction=cons["mean_cosine_to_victim_direction"],
        consistency_frac_positive=cons["consistency_frac_positive"],
        loso_pass=loso["loso_pass"],
        loso_sign_agreement=loso["loso_sign_agreement"],
        loso_min=loso["loso_min"],
        residualized=residualized,
        residual_covariates=residual_covariates,
        seed=seed,
    )
    details = {
        "D": D,
        "control_mean": mu_c,
        "cosine_matrix": C_all,
        "victim_mask": victim,
        "victim_cosines_to_mean_direction": cons["cosines"],
        "per_victim_mean_pairwise_cosine": per_victim,
        "frac_victims_above_null_mean": frac_above_null,
        "perm_null": perm["null"],
        "loso": loso,
        "bootstrap": boot,
        "consistency": cons,
        "permutation": {k: v for k, v in perm.items() if k != "null"},
    }
    return summary, details


def residualize_columns(X: np.ndarray, covariates: np.ndarray) -> np.ndarray:
    """Column-wise OLS residual of X on covariates (+ intercept). Subject-level only."""
    X = np.asarray(X, dtype=float)
    Z = np.asarray(covariates, dtype=float)
    if Z.ndim == 1:
        Z = Z[:, None]
    if Z.shape[0] != X.shape[0]:
        raise ValueError("covariate rows must match X")
    # fill non-finite covariates with column median
    Z2 = Z.copy()
    for j in range(Z2.shape[1]):
        col = Z2[:, j]
        med = np.nanmedian(col)
        col[~np.isfinite(col)] = med if np.isfinite(med) else 0.0
        Z2[:, j] = col
    design = np.column_stack([np.ones(X.shape[0]), Z2])
    out = np.empty_like(X)
    # least squares: beta = (D'D)^+ D' y
    DtD = design.T @ design
    try:
        DtD_inv = np.linalg.pinv(DtD)
    except np.linalg.LinAlgError:
        return X.copy()
    for j in range(X.shape[1]):
        y = X[:, j]
        beta = DtD_inv @ (design.T @ y)
        out[:, j] = y - design @ beta
    return out
