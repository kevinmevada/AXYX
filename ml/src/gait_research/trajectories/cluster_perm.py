"""Subject-level cluster permutation over the gait cycle. Never permutes cycles or time."""

from __future__ import annotations

import numpy as np

from ..statistics.effect_sizes import cliffs_delta

SEED = 20260813
T_THRESH = 2.045  # |t| cluster-forming threshold, df≈29 two-sided 0.05
N_PERM = 9999


def welch_t(X: np.ndarray, victim: np.ndarray) -> np.ndarray:
    xv = X[victim]
    xc = X[~victim]
    mv = np.nanmean(xv, axis=0)
    mc = np.nanmean(xc, axis=0)
    nv = np.sum(np.isfinite(xv), axis=0).astype(float)
    nc = np.sum(np.isfinite(xc), axis=0).astype(float)
    vv = np.nanvar(xv, axis=0, ddof=1)
    vc = np.nanvar(xc, axis=0, ddof=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        se = np.sqrt(vv / np.maximum(nv, 1.0) + vc / np.maximum(nc, 1.0))
        t = (mv - mc) / se
    return np.where(np.isfinite(t), t, 0.0)


def cliffs_curve(X: np.ndarray, victim: np.ndarray) -> np.ndarray:
    xv = X[victim]
    xc = X[~victim]
    out = np.empty(X.shape[1], dtype=float)
    for t in range(X.shape[1]):
        out[t] = cliffs_delta(xv[:, t], xc[:, t])
    return out


def directional_consistency(X: np.ndarray, victim: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Predefined: share of victims on the group-difference side of the control median."""
    xv = X[victim]
    xc = X[~victim]
    cmed = np.nanmedian(xc, axis=0)
    vmed = np.nanmedian(xv, axis=0)
    diff = vmed - cmed
    v_cons = np.full(X.shape[1], np.nan)
    c_cons = np.full(X.shape[1], np.nan)
    for t in range(X.shape[1]):
        if not np.isfinite(diff[t]):
            continue
        if diff[t] > 0:
            v_cons[t] = np.nanmean(xv[:, t] > cmed[t])
            c_cons[t] = np.nanmean(xc[:, t] < vmed[t])
        elif diff[t] < 0:
            v_cons[t] = np.nanmean(xv[:, t] < cmed[t])
            c_cons[t] = np.nanmean(xc[:, t] > vmed[t])
        else:
            v_cons[t] = np.nan
    return diff, v_cons, c_cons


def clusters_from_stat(stat: np.ndarray, thresh: float = T_THRESH) -> list[tuple[int, int, float]]:
    """Contiguous |stat|>thresh clusters. Returns (start, end_inclusive, mass)."""
    out = []
    i = 0
    n = stat.size
    while i < n:
        if abs(stat[i]) > thresh:
            j = i
            mass = 0.0
            while j < n and abs(stat[j]) > thresh:
                mass += abs(stat[j])
                j += 1
            out.append((i, j - 1, float(mass)))
            i = j
        else:
            i += 1
    return out


def max_cluster_mass(stat: np.ndarray, thresh: float = T_THRESH) -> float:
    cl = clusters_from_stat(stat, thresh)
    return max((c[2] for c in cl), default=0.0)


def permute_labels(victim: np.ndarray, n_perm: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = victim.size
    n_v = int(victim.sum())
    mats = np.empty((n_perm, n), dtype=bool)
    idx = np.arange(n)
    for i in range(n_perm):
        pick = rng.choice(idx, size=n_v, replace=False)
        row = np.zeros(n, dtype=bool)
        row[pick] = True
        mats[i] = row
    return mats


def cluster_permutation(
    X: np.ndarray,
    victim: np.ndarray,
    *,
    n_perm: int = N_PERM,
    seed: int = SEED,
    thresh: float = T_THRESH,
    perm_labels: np.ndarray | None = None,
) -> dict:
    """H0: no systematic victim/control trajectory difference.

    Permutes whole subject trajectories (label shuffle). Time points stay together.
    """
    victim = np.asarray(victim, dtype=bool)
    t_obs = welch_t(X, victim)
    delta = cliffs_curve(X, victim)
    diff, v_cons, c_cons = directional_consistency(X, victim)
    obs_cl = clusters_from_stat(t_obs, thresh)
    obs_max = max((c[2] for c in obs_cl), default=0.0)
    if perm_labels is None:
        perm_labels = permute_labels(victim, n_perm, seed)
    else:
        n_perm = perm_labels.shape[0]
    null_max = np.empty(n_perm, dtype=float)
    for i in range(n_perm):
        null_max[i] = max_cluster_mass(welch_t(X, perm_labels[i]), thresh)
    rows = []
    for start, end, mass in obs_cl:
        p = float((1 + np.sum(null_max >= mass)) / (n_perm + 1))
        sl = slice(start, end + 1)
        rows.append(
            {
                "start_idx": start,
                "end_idx": end,
                "start_percent": float(start),
                "end_percent": float(end),
                "cluster_mass": mass,
                "permutation_p": p,
                "mean_t": float(np.mean(t_obs[sl])),
                "mean_abs_t": float(np.mean(np.abs(t_obs[sl]))),
                "mean_cliffs_delta": float(np.nanmean(delta[sl])),
                "mean_difference": float(np.nanmean(diff[sl])),
                "mean_victim_consistency": float(np.nanmean(v_cons[sl])),
                "mean_control_consistency": float(np.nanmean(c_cons[sl])),
                "direction": "VICTIMS_HIGHER" if np.nanmean(diff[sl]) > 0 else "VICTIMS_LOWER",
            }
        )
    return {
        "t_obs": t_obs,
        "delta": delta,
        "difference": diff,
        "victim_consistency": v_cons,
        "control_consistency": c_cons,
        "victim_median": np.nanmedian(X[victim], axis=0),
        "control_median": np.nanmedian(X[~victim], axis=0),
        "clusters": rows,
        "obs_max_mass": obs_max,
        "null_max": null_max,
        "n_perm": n_perm,
        "unit": "subject",
        "threshold": thresh,
    }
