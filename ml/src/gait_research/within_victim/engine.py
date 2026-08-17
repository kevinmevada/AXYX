"""Phase 5: within-victim similarity and subgroup discovery. No predictive ML."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..labels import load_female_labels
from ..paths import survey_xlsx
from ..phenotypes.characterization import phenotype_feature_effects, phenotype_profiles
from ..phenotypes.confounding import load_covariates, phenotype_covariates
from ..phenotypes.representation import assert_no_labels, build_representation
from ..statistics.phase_analysis import phase_effects
from .neighbors import nearest_neighbor_table, nn_permutation
from .similarity import victim_control_gap, within_group_similarity
from .subgroups import discover_victim_subgroups
from .vs_controls import subgroup_vs_control_compact, subgroup_vs_control_features, centroid_perm_p

SEED = 20260813


def _labels(project_root: Path) -> pd.DataFrame:
    lab = load_female_labels(survey_xlsx())
    out = lab[["subject_id", "victimized"]].drop_duplicates()
    if (out["victimized"] == "Y").sum() != 17 or (out["victimized"] == "N").sum() != 14:
        raise RuntimeError("expected 17 Y / 14 N")
    return out


def run_phase5(project_root: Path) -> dict:
    rep = build_representation(project_root)
    assert_no_labels(pd.DataFrame(rep["compact"], columns=rep["compact_names"]))
    lab = _labels(project_root)
    order = pd.DataFrame({"subject_id": rep["subject_id"]}).merge(lab, on="subject_id", how="left")
    if order["victimized"].isna().any() or len(order) != 31:
        raise RuntimeError("label alignment failed")
    y = order["victimized"].to_numpy()
    ids = order["subject_id"].to_numpy()
    X = rep["compact"]
    vmask = y == "Y"
    if int(vmask.sum()) != 17:
        raise RuntimeError(f"expected 17 victims in representation, got {vmask.sum()}")

    sim = within_group_similarity(X, vmask, seed=SEED)
    gap = victim_control_gap(X, vmask)
    nn_table = nearest_neighbor_table(X, ids, y)
    nn_perm = nn_permutation(X, y, seed=SEED)

    all_vs_ctrl_dist, all_vs_ctrl_p = centroid_perm_p(X[vmask], X[~vmask], seed=SEED)

    sub = discover_victim_subgroups(X[vmask], ids[vmask], seed=SEED)
    assign = sub["assignments"]
    assert "victimized" not in assign.columns

    vs_ctrl = pd.DataFrame()
    vs_feat = pd.DataFrame()
    vs_other = pd.DataFrame()
    profiles = pd.DataFrame()
    cov = pd.DataFrame()
    phases = pd.DataFrame()
    anatomy = pd.DataFrame()

    if sub["choice"]["k"] is not None:
        vs_ctrl = subgroup_vs_control_compact(X, ids, y, assign, seed=SEED)
        vs_feat = subgroup_vs_control_features(
            rep["raw"], rep["raw_names"], rep["feature_meta"], ids, y, assign
        )
        vs_other = phenotype_feature_effects(
            rep["raw"][vmask],
            rep["raw_names"],
            assign.set_index("subject_id").loc[list(ids[vmask]), "subgroup"].to_numpy(),
            rep["feature_meta"],
        )
        vs_other = vs_other.rename(columns={"phenotype": "subgroup"})
        profiles = phenotype_profiles(vs_other.rename(columns={"subgroup": "phenotype"}))
        if len(profiles):
            profiles = profiles.rename(columns={"phenotype": "subgroup"})
        cov = phenotype_covariates(assign.rename(columns={"subgroup": "phenotype"}), load_covariates(project_root))
        if len(cov):
            cov = cov.rename(columns={"phenotype": "subgroup"})
        if len(vs_feat):
            phases = phase_effects(vs_feat)
            anatomy = (
                vs_feat.groupby(["subgroup", "anatomical_region"], as_index=False)
                .agg(n=("feature", "size"), max_abs_delta=("abs_delta", "max"), median_abs_delta=("abs_delta", "median"))
                .sort_values(["subgroup", "max_abs_delta"], ascending=[True, False])
            )

    null = sim.pop("null")
    return {
        "n_subjects": 31,
        "n_victims": 17,
        "n_controls": 14,
        "rep": rep,
        "similarity": sim,
        "similarity_null": null,
        "gap": gap,
        "nn_table": nn_table,
        "nn_perm": nn_perm,
        "all_victims_vs_controls": {
            "centroid_distance": all_vs_ctrl_dist,
            "perm_p": all_vs_ctrl_p,
            "unit": "subject",
        },
        "subgroups": sub,
        "vs_controls_compact": vs_ctrl,
        "vs_controls_features": vs_feat,
        "vs_other_victims": vs_other,
        "profiles": profiles,
        "covariates": cov,
        "phase_effects": phases,
        "anatomy": anatomy,
        "ids": ids,
        "y": y,
        "X": X,
    }
