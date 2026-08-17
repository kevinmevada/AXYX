"""Victim-only subgroup discovery. k is not chosen to separate victims from controls."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..phenotypes.clustering import evaluate_k_grid, relabel_by_size, select_k
from ..phenotypes.stability import stability_grid
from ..phenotypes.representation import SEED

VICTIM_K = (2, 3)


def discover_victim_subgroups(
    X_victims: np.ndarray,
    victim_ids: np.ndarray,
    *,
    seed: int = SEED,
) -> dict:
    if X_victims.shape[0] != 17:
        raise RuntimeError(f"expected 17 victims, got {X_victims.shape[0]}")
    metrics, assignments = evaluate_k_grid(X_victims, ks=VICTIM_K, seed=seed)
    stability, per_subject = stability_grid(X_victims, assignments, victim_ids, seed=seed)
    choice = select_k(metrics, stability)
    assign = pd.DataFrame({"subject_id": victim_ids})
    frozen = None
    if choice["k"] is None:
        assign["subgroup"] = "none_stable"
        assign["assignment_stability"] = np.nan
        assign["cluster_method"] = "hierarchical_ward"
        assign["cluster_solution"] = "no_stable_structure"
    else:
        raw = assignments[("hierarchical", choice["k"])]
        labs = relabel_by_size(raw)
        frozen = labs
        freq = per_subject[("hierarchical", choice["k"])][["subject_id", "assignment_frequency"]]
        assign = pd.DataFrame({"subject_id": victim_ids, "subgroup": labs}).merge(freq, on="subject_id")
        assign = assign.rename(columns={"assignment_frequency": "assignment_stability"})
        assign["cluster_method"] = "hierarchical_ward"
        assign["cluster_solution"] = f"k={choice['k']}"
    loso = float("nan")
    if choice["k"] is not None:
        row = stability[(stability["method"] == "hierarchical") & (stability["k"] == choice["k"])]
        if len(row):
            loso = float(row.iloc[0]["mean_loso_ari"])
    return {
        "metrics": metrics,
        "stability": stability,
        "choice": choice,
        "assignments": assign,
        "frozen": frozen,
        "loso_ari": loso,
    }
