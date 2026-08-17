"""LOSO and subject bootstrap for frozen trajectory regions. Subject is the unit."""

from __future__ import annotations

import numpy as np

from .cluster_perm import cliffs_curve, directional_consistency, welch_t

SEED = 20260813


def region_loo(X: np.ndarray, victim: np.ndarray, start: int, end: int) -> dict:
    sl = slice(start, end + 1)
    obs_diff = np.nanmean(np.nanmedian(X[victim], 0)[sl] - np.nanmedian(X[~victim], 0)[sl])
    obs_mean = np.nanmean(np.nanmean(X[victim], 0)[sl] - np.nanmean(X[~victim], 0)[sl])
    sign0 = np.sign(obs_diff) if obs_diff != 0 else 0.0
    signm = np.sign(obs_mean) if obs_mean != 0 else 0.0
    same = 0
    same_mean = 0
    n = X.shape[0]
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        d, _, _ = directional_consistency(X[mask], victim[mask])
        md = float(np.nanmean(d[sl]))
        if sign0 == 0 or np.sign(md) == sign0:
            same += 1
        mv = float(np.nanmean(np.nanmean(X[mask][victim[mask]], 0)[sl] - np.nanmean(X[mask][~victim[mask]], 0)[sl]))
        if signm == 0 or np.sign(mv) == signm:
            same_mean += 1
    return {
        "loo_sign_agreement": float(same / n),
        "loo_mean_sign_agreement": float(same_mean / n),
        "obs_mean_difference": float(obs_diff),
    }


def bootstrap_region_ci(
    X: np.ndarray,
    victim: np.ndarray,
    start: int,
    end: int,
    *,
    n_boot: int = 1000,
    seed: int = SEED,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Percentile CI for group median difference in the region. Resamples subjects within group."""
    rng = np.random.default_rng(seed)
    sl = slice(start, end + 1)
    xv = X[victim]
    xc = X[~victim]
    nv, nc = xv.shape[0], xc.shape[0]
    diffs = np.empty(n_boot, dtype=float)
    # also CI of full difference curve
    boot_diff = np.empty((n_boot, X.shape[1]), dtype=float)
    for b in range(n_boot):
        vi = rng.integers(0, nv, size=nv)
        ci = rng.integers(0, nc, size=nc)
        dv = np.nanmedian(xv[vi], axis=0) - np.nanmedian(xc[ci], axis=0)
        boot_diff[b] = dv
        diffs[b] = float(np.nanmean(dv[sl]))
    lo, hi = np.nanpercentile(diffs, [2.5, 97.5])
    band_lo = np.nanpercentile(boot_diff, 2.5, axis=0)
    band_hi = np.nanpercentile(boot_diff, 97.5, axis=0)
    return float(lo), float(hi), band_lo, band_hi
