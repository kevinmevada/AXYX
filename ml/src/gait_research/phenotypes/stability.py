"""Subject-level cluster stability. Never resamples gait cycles."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

from .clustering import hierarchical_labels, kmeans_labels
from .representation import SEED

N_BOOT = 150
SUBSAMPLE = 0.80


def align_labels(reference: np.ndarray, other: np.ndarray) -> np.ndarray:
    ref = np.asarray(reference)
    oth = np.asarray(other)
    u_ref = np.unique(ref)
    u_oth = np.unique(oth)
    conf = np.zeros((len(u_ref), len(u_oth)), dtype=int)
    for i, a in enumerate(u_ref):
        for j, b in enumerate(u_oth):
            conf[i, j] = int(np.sum((ref == a) & (oth == b)))
    ri, ci = linear_sum_assignment(-conf)
    mapping = {u_oth[c]: u_ref[r] for r, c in zip(ri, ci)}
    return np.array([mapping.get(v, v) for v in oth], dtype=int)


def _cluster(X: np.ndarray, k: int, method: str, seed: int) -> np.ndarray:
    if method == "hierarchical":
        return hierarchical_labels(X, k)
    return kmeans_labels(X, k, seed=seed)


def bootstrap_ari(
    X: np.ndarray,
    labels: np.ndarray,
    k: int,
    *,
    method: str = "hierarchical",
    n_boot: int = N_BOOT,
    frac: float = SUBSAMPLE,
    seed: int = SEED,
) -> tuple[float, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    m = max(int(round(frac * n)), k + 1)
    aris = []
    for b in range(n_boot):
        idx = np.sort(rng.choice(n, size=m, replace=False))
        pred = _cluster(X[idx], k, method, seed + b)
        aris.append(adjusted_rand_score(labels[idx], pred))
    return float(np.mean(aris)), np.asarray(aris, dtype=float)


def loso_ari(
    X: np.ndarray,
    labels: np.ndarray,
    k: int,
    *,
    method: str = "hierarchical",
    seed: int = SEED,
) -> float:
    n = X.shape[0]
    aris = []
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        pred = _cluster(X[mask], k, method, seed)
        aris.append(adjusted_rand_score(labels[mask], pred))
    return float(np.mean(aris))


def subject_assignment_stability(
    X: np.ndarray,
    labels: np.ndarray,
    k: int,
    subject_id: np.ndarray,
    *,
    method: str = "hierarchical",
    n_boot: int = N_BOOT,
    frac: float = SUBSAMPLE,
    seed: int = SEED,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    m = max(int(round(frac * n)), k + 1)
    agree = np.zeros(n, dtype=int)
    seen = np.zeros(n, dtype=int)
    for b in range(n_boot):
        idx = np.sort(rng.choice(n, size=m, replace=False))
        pred = _cluster(X[idx], k, method, seed + b)
        aligned = align_labels(labels[idx], pred)
        for j, i in enumerate(idx):
            seen[i] += 1
            if aligned[j] == labels[i]:
                agree[i] += 1
    freq = np.divide(agree, np.maximum(seen, 1), dtype=float)
    return pd.DataFrame(
        {
            "subject_id": subject_id,
            "phenotype": labels,
            "assignment_frequency": freq,
            "n_resamples_included": seen,
        }
    )


def stability_grid(
    X: np.ndarray,
    assignments: dict,
    subject_id: np.ndarray,
    *,
    seed: int = SEED,
) -> tuple[pd.DataFrame, dict[tuple, pd.DataFrame]]:
    rows = []
    per_subject = {}
    for (method, k), labels in assignments.items():
        mean_ari, dist = bootstrap_ari(X, labels, k, method=method, seed=seed)
        loso = loso_ari(X, labels, k, method=method, seed=seed)
        rows.append(
            {
                "method": method,
                "k": k,
                "mean_boot_ari": mean_ari,
                "boot_ari_p10": float(np.percentile(dist, 10)),
                "boot_ari_p90": float(np.percentile(dist, 90)),
                "mean_loso_ari": loso,
                "n_boot": N_BOOT,
                "subsample_fraction": SUBSAMPLE,
                "unit": "subject",
            }
        )
        per_subject[(method, k)] = subject_assignment_stability(
            X, labels, k, subject_id, method=method, seed=seed
        )
    return pd.DataFrame(rows), per_subject
