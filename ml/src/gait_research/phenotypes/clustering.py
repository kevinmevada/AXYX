"""Label-blind clustering. k is never chosen from victimization separation."""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score

from .representation import SEED, assert_no_labels

K_CANDIDATES = (2, 3, 4)
MIN_CLUSTER_SIZE = 4
MIN_SILHOUETTE = 0.20
MIN_MEAN_ARI = 0.50


def hierarchical_labels(X: np.ndarray, k: int) -> np.ndarray:
    z = linkage(X, method="ward")
    return fcluster(z, k, criterion="maxclust").astype(int)


def kmeans_labels(X: np.ndarray, k: int, *, seed: int = SEED) -> np.ndarray:
    km = KMeans(n_clusters=k, n_init=10, random_state=seed)
    return km.fit_predict(X).astype(int) + 1


def cluster_quality(X: np.ndarray, labels: np.ndarray) -> dict:
    labs = np.asarray(labels)
    k = int(np.unique(labs).size)
    sizes = [int(np.sum(labs == c)) for c in sorted(np.unique(labs))]
    sil = float("nan")
    db = float("nan")
    if k >= 2 and len(np.unique(labs)) < len(labs):
        try:
            sil = float(silhouette_score(X, labs, metric="euclidean"))
        except ValueError:
            sil = float("nan")
        try:
            db = float(davies_bouldin_score(X, labs))
        except ValueError:
            db = float("nan")
    cents = []
    within = []
    for c in sorted(np.unique(labs)):
        part = X[labs == c]
        mu = part.mean(axis=0)
        cents.append(mu)
        within.append(float(np.mean(np.sum((part - mu) ** 2, axis=1))))
    cents_a = np.vstack(cents)
    between = float(np.mean([np.linalg.norm(a - b) for i, a in enumerate(cents_a) for b in cents_a[i + 1 :]])) if k > 1 else 0.0
    return {
        "k": k,
        "sizes": sizes,
        "min_size": min(sizes) if sizes else 0,
        "max_size": max(sizes) if sizes else 0,
        "silhouette": sil,
        "davies_bouldin": db,
        "mean_within_ss": float(np.mean(within)) if within else float("nan"),
        "mean_between_centroid": between,
    }


def evaluate_k_grid(X: np.ndarray, *, ks: tuple[int, ...] = K_CANDIDATES, seed: int = SEED) -> tuple[pd.DataFrame, dict]:
    rows = []
    assignments = {}
    for k in ks:
        for method, fn in (("hierarchical", hierarchical_labels), ("kmeans", lambda x, kk: kmeans_labels(x, kk, seed=seed))):
            labels = fn(X, k)
            q = cluster_quality(X, labels)
            rows.append(
                {
                    "method": method,
                    "k": k,
                    "silhouette": q["silhouette"],
                    "davies_bouldin": q["davies_bouldin"],
                    "min_size": q["min_size"],
                    "max_size": q["max_size"],
                    "sizes": "|".join(str(s) for s in q["sizes"]),
                    "mean_within_ss": q["mean_within_ss"],
                    "mean_between_centroid": q["mean_between_centroid"],
                }
            )
            assignments[(method, k)] = labels
    metrics = pd.DataFrame(rows)
    assert_no_labels(metrics, where="cluster_metrics")
    return metrics, assignments


def select_k(metrics: pd.DataFrame, stability: pd.DataFrame) -> dict:
    """Choose k from silhouette, size, and stability only. No labels."""
    hier = metrics[metrics["method"] == "hierarchical"].copy()
    stab = stability[stability["method"] == "hierarchical"][["k", "mean_boot_ari", "mean_loso_ari"]].drop_duplicates()
    merged = hier.merge(stab, on="k", how="left")
    ok = merged[
        (merged["min_size"] >= MIN_CLUSTER_SIZE)
        & (merged["silhouette"] >= MIN_SILHOUETTE)
        & (merged["mean_boot_ari"] >= MIN_MEAN_ARI)
    ]
    if ok.empty:
        return {
            "k": None,
            "method": "hierarchical",
            "reason": "no_stable_phenotype_structure",
            "criteria": {
                "min_cluster_size": MIN_CLUSTER_SIZE,
                "min_silhouette": MIN_SILHOUETTE,
                "min_mean_boot_ari": MIN_MEAN_ARI,
            },
        }
    ok = ok.sort_values(["mean_boot_ari", "silhouette", "k"], ascending=[False, False, True])
    row = ok.iloc[0]
    return {
        "k": int(row["k"]),
        "method": "hierarchical",
        "reason": "max_bootstrap_ari_among_stable_hierarchical",
        "silhouette": float(row["silhouette"]),
        "mean_boot_ari": float(row["mean_boot_ari"]),
        "min_size": int(row["min_size"]),
        "criteria": {
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_silhouette": MIN_SILHOUETTE,
            "min_mean_boot_ari": MIN_MEAN_ARI,
        },
    }


def relabel_by_size(labels: np.ndarray) -> np.ndarray:
    """Phenotype ids 1..k by decreasing size. No labels used."""
    labs = np.asarray(labels)
    order = sorted(np.unique(labs), key=lambda c: (-int(np.sum(labs == c)), int(c)))
    mapping = {old: i + 1 for i, old in enumerate(order)}
    return np.array([mapping[v] for v in labs], dtype=int)
