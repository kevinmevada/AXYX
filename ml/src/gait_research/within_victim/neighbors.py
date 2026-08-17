"""Nearest-neighbor composition in gait space. Subject is the unit."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

SEED = 20260813
N_PERM = 999


def nearest_neighbor_table(
    X: np.ndarray,
    subject_id: np.ndarray,
    victimized: np.ndarray,
) -> pd.DataFrame:
    d = cdist(X, X, metric="euclidean")
    np.fill_diagonal(d, np.inf)
    nn = np.argmin(d, axis=1)
    rows = []
    for i, j in enumerate(nn):
        if victimized[i] != "Y":
            continue
        rows.append(
            {
                "subject_id": subject_id[i],
                "nearest_subject": subject_id[j],
                "nearest_distance": float(d[i, j]),
                "nearest_is_victim": victimized[j] == "Y",
            }
        )
    return pd.DataFrame(rows)


def knn_victim_fraction(
    X: np.ndarray,
    victimized: np.ndarray,
    *,
    k: int = 3,
) -> float:
    d = cdist(X, X, metric="euclidean")
    np.fill_diagonal(d, np.inf)
    vmask = victimized == "Y"
    fracs = []
    for i in np.where(vmask)[0]:
        neigh = np.argsort(d[i])[:k]
        fracs.append(float(np.mean(victimized[neigh] == "Y")))
    return float(np.mean(fracs)) if fracs else float("nan")


def nn_permutation(
    X: np.ndarray,
    victimized: np.ndarray,
    *,
    n_perm: int = N_PERM,
    seed: int = SEED,
) -> dict:
    """Observed fraction of victim-to-victim 1-NN vs shuffled labels."""
    y = np.asarray(victimized)
    table = nearest_neighbor_table(X, np.arange(len(y)).astype(str), y)
    obs = float(table["nearest_is_victim"].mean()) if len(table) else float("nan")
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm, dtype=float)
    for i in range(n_perm):
        shuf = rng.permutation(y)
        t = nearest_neighbor_table(X, np.arange(len(y)).astype(str), shuf)
        null[i] = float(t["nearest_is_victim"].mean()) if len(t) else float("nan")
    p = float((1 + np.sum(null >= obs)) / (n_perm + 1))
    return {
        "obs_frac_nn_victim": obs,
        "null_mean": float(np.nanmean(null)),
        "perm_p": p,
        "n_perm": n_perm,
        "unit": "subject",
        "knn3_victim_fraction": knn_victim_fraction(X, y, k=3),
    }
