"""Phase 4 orchestration. Labels join only after phenotypes are frozen."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from ..features.context import LABEL_COLUMNS
from ..labels import load_female_labels
from ..paths import survey_xlsx
from .characterization import phenotype_feature_effects, phenotype_profiles
from .clustering import evaluate_k_grid, hierarchical_labels, relabel_by_size, select_k
from .confounding import load_covariates, phenotype_covariates
from .dimensionality import fit_pca, pca_tables
from .enrichment import composition_table, permutation_enrichment
from .representation import assert_no_labels, build_representation, representation_frame
from .stability import stability_grid
from .trajectories import phenotype_trajectories

SEED = 20260813


def _load_labels(project_root: Path) -> pd.DataFrame:
    lab = load_female_labels(survey_xlsx())
    out = lab[["subject_id", "victimized"]].drop_duplicates()
    if (out["victimized"] == "Y").sum() != 17 or (out["victimized"] == "N").sum() != 14:
        raise RuntimeError("expected 17 Y / 14 N labels")
    return out


def run_discovery(project_root: Path) -> dict:
    """Construct representation, PCA, clusters, stability, profiles. No labels."""
    rep = build_representation(project_root)
    X = rep["compact"]
    ids = rep["subject_id"]
    pca_fit = fit_pca(X, seed=SEED)
    scores_df, pca_summary = pca_tables(pca_fit, ids)
    metrics, assignments = evaluate_k_grid(X, seed=SEED)
    stability, per_subject = stability_grid(X, assignments, ids, seed=SEED)
    choice = select_k(metrics, stability)

    # Sensitivity: unbalanced global PCA of robust-scaled representatives (still no labels)
    pca_unbal = fit_pca(rep["scaled"], seed=SEED)
    X_unbal = pca_unbal["scores_kept"]
    sens_rows = []
    for k in sorted({kk for _, kk in assignments}):
        h = assignments[("hierarchical", k)]
        km = assignments[("kmeans", k)]
        hunbal = hierarchical_labels(X_unbal, k)
        sens_rows.append(
            {
                "k": k,
                "ari_hierarchical_vs_kmeans": float(adjusted_rand_score(h, km)),
                "ari_family_vs_unbalanced_pca": float(adjusted_rand_score(h, hunbal)),
                "unit": "subject",
            }
        )
    sensitivity = pd.DataFrame(sens_rows)

    frozen = None
    profiles = pd.DataFrame()
    effects = pd.DataFrame()
    assign_df = pd.DataFrame({"subject_id": ids})
    if choice["k"] is not None:
        raw_labels = assignments[("hierarchical", choice["k"])]
        labels = relabel_by_size(raw_labels)
        frozen = labels
        stab_subj = per_subject[("hierarchical", choice["k"])][["subject_id", "assignment_frequency"]]
        assign_df = pd.DataFrame({"subject_id": ids, "phenotype": labels}).merge(stab_subj, on="subject_id", how="left")
        assign_df = assign_df.rename(columns={"assignment_frequency": "assignment_stability"})
        assign_df["representation_method"] = "family_pca_median_iqr"
        assign_df["cluster_method"] = "hierarchical_ward"
        assign_df["cluster_solution"] = f"k={choice['k']}"
        assert_no_labels(assign_df, where="phenotype_assignments")
        effects = phenotype_feature_effects(rep["raw"], rep["raw_names"], labels, rep["feature_meta"])
        profiles = phenotype_profiles(effects)
    else:
        assign_df["phenotype"] = "none_stable"
        assign_df["assignment_stability"] = np.nan
        assign_df["representation_method"] = "family_pca_median_iqr"
        assign_df["cluster_method"] = "hierarchical_ward"
        assign_df["cluster_solution"] = "no_stable_structure"

    return {
        "rep": rep,
        "compact_frame": representation_frame(rep),
        "pca_scores": scores_df,
        "pca_summary": pca_summary,
        "pca_n_keep": pca_fit["n_keep"],
        "metrics": metrics,
        "stability": stability,
        "sensitivity": sensitivity,
        "choice": choice,
        "assignments": assign_df,
        "effects": effects,
        "profiles": profiles,
        "frozen_labels": frozen,
        "X": X,
        "n_subjects": 31,
    }


def run_phase4(project_root: Path) -> dict:
    discovery = run_discovery(project_root)
    # Labels revealed only after freeze.
    labels = _load_labels(project_root)
    assign = discovery["assignments"]
    has_structure = discovery["choice"]["k"] is not None
    composition = pd.DataFrame()
    enrich_stats = pd.DataFrame()
    covariates = pd.DataFrame()
    traj = {"data": {}, "signals": []}
    if has_structure:
        composition = composition_table(assign, labels)
        enrich_stats = permutation_enrichment(assign, labels)
        enrich_stats = composition.merge(enrich_stats, on="phenotype", how="left")
        cov = load_covariates(project_root)
        covariates = phenotype_covariates(assign, cov)
        traj = phenotype_trajectories(project_root, assign)
    discovery["labels_revealed"] = True
    discovery["composition"] = composition
    discovery["enrichment"] = enrich_stats
    discovery["covariates"] = covariates
    discovery["trajectories"] = traj
    discovery["group_labels"] = labels
    for col in LABEL_COLUMNS:
        if col in discovery["assignments"].columns:
            raise RuntimeError("victimization leaked into phenotype assignment table")
    return discovery
