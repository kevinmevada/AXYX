"""Phase 3 orchestration. Labels join only after screening."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..features.context import LABEL_COLUMNS
from ..labels import load_female_labels
from ..paths import ml_project_root, survey_xlsx
from .anatomical_analysis import anatomical_summary, attach_anatomy
from .group_comparison import compare_groups
from .multiple_testing import benjamini_hochberg
from .phase_analysis import phase_effects
from .robustness import leave_one_subject_out, permutation_cliffs
from .screening import analysis_columns, quality_screen, redundancy_clusters

FDR_ALPHA = 0.10
FDR_ALPHA_STRICT = 0.05
DELTA_MIN = 0.33
LOSO_DIR_MIN = 0.80
CONSIST_MIN = 0.60
N_PERM = 999
SEED = 20260813
TOP_EXPLORATORY = 20


def load_subject_matrix(project_root: Path) -> pd.DataFrame:
    root = ml_project_root(project_root)
    path = root / "results" / "phase2" / "subject_features.parquet"
    df = pd.read_parquet(path)
    for col in LABEL_COLUMNS:
        if col in df.columns:
            raise RuntimeError(f"Phase 2 subject table contains label column {col}")
    if len(df) != 31:
        raise RuntimeError(f"expected 31 subjects, found {len(df)}")
    return df


def attach_labels(project_root: Path, subjects: pd.DataFrame) -> pd.DataFrame:
    labels = load_female_labels(survey_xlsx())
    lab = labels[["subject_id", "victimized"]].drop_duplicates()
    out = subjects.merge(lab, on="subject_id", how="left")
    if out["victimized"].isna().any():
        raise RuntimeError("label merge failed for some subjects")
    if (out["victimized"] == "Y").sum() != 17:
        raise RuntimeError(f"expected 17 victims, got {(out['victimized']=='Y').sum()}")
    if (out["victimized"] == "N").sum() != 14:
        raise RuntimeError(f"expected 14 controls, got {(out['victimized']=='N').sum()}")
    return out


def _rank_score(row: pd.Series) -> float:
    delta = abs(float(row["cliffs_delta"])) if np.isfinite(row["cliffs_delta"]) else 0.0
    fdr = float(row["fdr_q"]) if np.isfinite(row.get("fdr_q", np.nan)) else 1.0
    fdr_w = 1.0 if fdr <= FDR_ALPHA_STRICT else 0.7 if fdr <= FDR_ALPHA else 0.35 if fdr <= 0.25 else 0.15
    rob = float(row.get("loso_direction_agreement", 0)) if np.isfinite(row.get("loso_direction_agreement", np.nan)) else 0.0
    cons = float(row.get("victim_consistency", 0)) if np.isfinite(row.get("victim_consistency", np.nan)) else 0.0
    fam = str(row.get("family", ""))
    interp = {
        "kinematic": 1.0,
        "temporal": 1.0,
        "spatial": 0.95,
        "phase": 0.9,
        "symmetry": 0.85,
        "coordination": 0.8,
        "smoothness": 0.8,
        "variability": 0.75,
    }.get(fam, 0.7)
    cover = 1.0 if int(row.get("n_victims", 0)) == 17 and int(row.get("n_controls", 0)) == 14 else 0.5
    return float(delta * fdr_w * max(rob, 0) * max(cons, 0) * interp * cover)


def _signature_flag(row: pd.Series) -> str:
    if (
        np.isfinite(row.get("fdr_q", np.nan))
        and row["fdr_q"] <= FDR_ALPHA
        and abs(row["cliffs_delta"]) >= DELTA_MIN
        and row.get("loso_direction_agreement", 0) >= LOSO_DIR_MIN
        and row.get("victim_consistency", 0) >= CONSIST_MIN
    ):
        return "signature_candidate"
    return "exploratory"


def run_phase3(project_root: Path) -> dict:
    subjects = load_subject_matrix(project_root)
    cols = analysis_columns(subjects)
    screen_df, passed = quality_screen(subjects, cols, min_n=31)
    clusters, reps = redundancy_clusters(subjects, passed, rho=0.90)

    labeled = attach_labels(project_root, subjects)
    comparisons = compare_groups(labeled, reps)
    comparisons["fdr_q"] = benjamini_hochberg(comparisons["raw_p"].to_numpy())
    comparisons["adjusted_p"] = comparisons["fdr_q"]

    loso = leave_one_subject_out(labeled, reps)
    perm = permutation_cliffs(labeled, reps, n_perm=N_PERM, seed=SEED)
    stats = comparisons.merge(loso, on="feature", how="left").merge(perm, on="feature", how="left")
    stats = attach_anatomy(stats)
    stats["rank_score"] = stats.apply(_rank_score, axis=1)
    stats["signature_status"] = stats.apply(_signature_flag, axis=1)
    stats["is_sig"] = (stats["signature_status"] == "signature_candidate").astype(int)
    stats = stats.sort_values(["is_sig", "rank_score"], ascending=[False, False]).drop(columns=["is_sig"]).reset_index(drop=True)
    stats["rank"] = np.arange(1, len(stats) + 1)

    phase_df = phase_effects(stats)
    anatomy_df = anatomical_summary(stats, fdr_alpha=FDR_ALPHA, delta_min=DELTA_MIN)

    signature = stats.head(TOP_EXPLORATORY).copy()
    n_sig = int((stats["signature_status"] == "signature_candidate").sum())
    n_fdr = int((stats["fdr_q"] <= FDR_ALPHA).sum())
    n_fdr_strict = int((stats["fdr_q"] <= FDR_ALPHA_STRICT).sum())

    return {
        "n_subjects": len(subjects),
        "n_analysis_columns": len(cols),
        "screen": screen_df,
        "clusters": clusters,
        "representatives": reps,
        "stats": stats,
        "loso": loso,
        "perm": perm,
        "phase": phase_df,
        "anatomy": anatomy_df,
        "signature": signature,
        "n_signature": n_sig,
        "n_fdr_0_10": n_fdr,
        "n_fdr_0_05": n_fdr_strict,
        "n_victims": int((labeled["victimized"] == "Y").sum()),
        "n_controls": int((labeled["victimized"] == "N").sum()),
        "seed": SEED,
        "n_perm": N_PERM,
        "thresholds": {
            "fdr_alpha": FDR_ALPHA,
            "fdr_alpha_strict": FDR_ALPHA_STRICT,
            "cliffs_medium": DELTA_MIN,
            "loso_direction_min": LOSO_DIR_MIN,
            "victim_consistency_min": CONSIST_MIN,
        },
    }
