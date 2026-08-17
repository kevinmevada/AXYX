"""Label-blind PCA. Components are never chosen to separate victimization."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from .representation import SEED, assert_no_labels

VAR_KEEP = 0.80


def fit_pca(X: np.ndarray, *, seed: int = SEED) -> dict:
    n, p = X.shape
    n_comp = int(min(n - 1, p))
    pca = PCA(n_components=n_comp, svd_solver="full", random_state=seed)
    scores = pca.fit_transform(X)
    evr = pca.explained_variance_ratio_
    cume = np.cumsum(evr)
    n_keep = int(np.searchsorted(cume, VAR_KEEP) + 1)
    n_keep = min(max(n_keep, 2), n_comp)
    return {
        "pca": pca,
        "scores": scores,
        "scores_kept": scores[:, :n_keep],
        "explained_variance_ratio": evr,
        "cumulative": cume,
        "n_keep": n_keep,
        "loadings": pca.components_,
    }


def pca_tables(pca_fit: dict, subject_id: np.ndarray, col_prefix: str = "PC") -> tuple[pd.DataFrame, pd.DataFrame]:
    scores = pca_fit["scores"]
    cols = [f"{col_prefix}{i + 1}" for i in range(scores.shape[1])]
    score_df = pd.DataFrame(scores, columns=cols)
    score_df.insert(0, "subject_id", subject_id)
    assert_no_labels(score_df, where="pca_scores")
    summary = pd.DataFrame(
        {
            "pc": [i + 1 for i in range(len(pca_fit["explained_variance_ratio"]))],
            "explained_variance_ratio": pca_fit["explained_variance_ratio"],
            "cumulative_variance_ratio": pca_fit["cumulative"],
            "kept_for_description": [
                i < pca_fit["n_keep"] for i in range(len(pca_fit["explained_variance_ratio"]))
            ],
        }
    )
    return score_df, summary
