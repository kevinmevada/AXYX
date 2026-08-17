"""Within-victim gait similarity. Subject is the permutation unit."""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist, squareform

SEED = 20260813
N_PERM = 999


def mean_pairwise_distance(X: np.ndarray) -> float:
    if X.shape[0] < 2:
        return float("nan")
    return float(np.mean(pdist(X, metric="euclidean")))


def within_group_similarity(
    X: np.ndarray,
    group_mask: np.ndarray,
    *,
    n_perm: int = N_PERM,
    seed: int = SEED,
) -> dict:
    """Mean pairwise distance among a group vs random groups of the same size.

    One-sided: smaller distance = more similar. Permutes subject membership, not cycles.
    """
    mask = np.asarray(group_mask, dtype=bool)
    n_g = int(mask.sum())
    n = X.shape[0]
    if n_g < 2 or n_g > n:
        raise ValueError("invalid group size")
    obs = mean_pairwise_distance(X[mask])
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm, dtype=float)
    idx_all = np.arange(n)
    for i in range(n_perm):
        pick = rng.choice(idx_all, size=n_g, replace=False)
        null[i] = mean_pairwise_distance(X[pick])
    p = float((1 + np.sum(null <= obs)) / (n_perm + 1))
    return {
        "n_group": n_g,
        "n_pool": n,
        "observed_mean_pairwise_distance": obs,
        "null_mean": float(np.mean(null)),
        "null_sd": float(np.std(null, ddof=1)),
        "null_p05": float(np.percentile(null, 5)),
        "null_p95": float(np.percentile(null, 95)),
        "perm_p": p,
        "n_perm": n_perm,
        "unit": "subject",
        "alternative": "group_more_similar_than_random_same_size",
        "null": null,
    }


def victim_control_gap(X: np.ndarray, victim_mask: np.ndarray) -> dict:
    v = X[victim_mask]
    c = X[~victim_mask]
    vv = mean_pairwise_distance(v)
    cc = mean_pairwise_distance(c)
    if v.shape[0] and c.shape[0]:
        # mean victim-control pairwise
        d = np.sqrt(((v[:, None, :] - c[None, :, :]) ** 2).sum(axis=2))
        vc = float(np.mean(d))
    else:
        vc = float("nan")
    return {
        "mean_pairwise_victim_victim": vv,
        "mean_pairwise_control_control": cc,
        "mean_pairwise_victim_control": vc,
    }
