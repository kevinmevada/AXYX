"""Label-blind subject representation for phenotype discovery."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from ..features.context import LABEL_COLUMNS
from ..statistics.anatomical_analysis import attach_anatomy
from ..statistics.engine import load_subject_matrix

FORBIDDEN_NAME = re.compile(r"victim|bully|survey_subject", re.I)
ID_KEEP = {"subject_id", "n_cycles", "n_left_cycles", "n_right_cycles"}
SEED = 20260813
FAMILY_VAR_KEEP = 0.80
MAX_FAMILY_PCS = 8


def assert_no_labels(df: pd.DataFrame, *, where: str = "frame") -> None:
    bad = [c for c in df.columns if c in LABEL_COLUMNS or FORBIDDEN_NAME.search(str(c))]
    if bad:
        raise RuntimeError(f"label leakage in {where}: {bad}")


def load_phase3_representatives(project_root: Path) -> list[str]:
    path = project_root / "results" / "phase3" / "screening" / "redundancy_clusters.csv"
    clusters = pd.read_csv(path)
    reps = clusters["representative"].astype(str).tolist()
    if not reps:
        raise RuntimeError("Phase 3 redundancy representatives missing")
    return reps


def feature_families(feature_names: list[str]) -> pd.DataFrame:
    meta = attach_anatomy(pd.DataFrame({"feature": feature_names}))
    return meta[["feature", "family", "anatomical_region", "side", "source_signal"]]


def robust_scale(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Median / IQR scaling. IQR=0 columns become 0. Label-blind."""
    med = np.nanmedian(X, axis=0)
    q75 = np.nanpercentile(X, 75, axis=0)
    q25 = np.nanpercentile(X, 25, axis=0)
    iqr = q75 - q25
    scale = np.where(iqr > 1e-12, iqr, 1.0)
    Z = (X - med) / scale
    Z[:, iqr <= 1e-12] = 0.0
    Z = np.where(np.isfinite(Z), Z, 0.0)
    return Z, med, iqr


def _impute_median(X: np.ndarray) -> np.ndarray:
    out = X.copy()
    for j in range(out.shape[1]):
        col = out[:, j]
        med = np.nanmedian(col)
        if not np.isfinite(med):
            med = 0.0
        col[~np.isfinite(col)] = med
        out[:, j] = col
    return out


def family_pca_block(
    Z: np.ndarray,
    names: list[str],
    families: list[str],
    *,
    var_keep: float = FAMILY_VAR_KEEP,
    max_pcs: int = MAX_FAMILY_PCS,
    seed: int = SEED,
) -> tuple[np.ndarray, list[str], dict]:
    """Within-family PCA on robust-scaled columns. Equalizes family influence."""
    blocks = []
    out_names = []
    info = {}
    n = Z.shape[0]
    for fam in sorted(set(families)):
        idx = [i for i, f in enumerate(families) if f == fam]
        block = Z[:, idx]
        n_comp = int(min(max_pcs, block.shape[1], max(n - 1, 1)))
        n_comp = max(n_comp, 1)
        if block.shape[1] == 1:
            pcs = block
            evr = np.array([1.0])
            n_keep = 1
        else:
            pca = PCA(n_components=n_comp, svd_solver="full", random_state=seed)
            pcs_all = pca.fit_transform(block)
            cume = np.cumsum(pca.explained_variance_ratio_)
            n_keep = int(np.searchsorted(cume, var_keep) + 1)
            n_keep = min(max(n_keep, 1), n_comp)
            pcs = pcs_all[:, :n_keep]
            evr = pca.explained_variance_ratio_[:n_keep]
        # unit-family influence: divide by sqrt(n_keep) so families with more PCs
        # do not dominate Euclidean distance.
        pcs = pcs / np.sqrt(n_keep)
        blocks.append(pcs)
        for j in range(n_keep):
            out_names.append(f"famPC_{fam}_{j + 1}")
        info[fam] = {
            "n_source_features": len(idx),
            "n_pcs": n_keep,
            "explained_variance_ratio": [float(x) for x in evr],
            "source_features": [names[i] for i in idx],
        }
    X = np.hstack(blocks) if blocks else Z
    return X, out_names, info


def build_representation(project_root: Path) -> dict:
    subjects = load_subject_matrix(project_root)
    assert_no_labels(subjects, where="phase2_subject_features")
    if len(subjects) != 31:
        raise RuntimeError(f"expected 31 subjects, got {len(subjects)}")
    reps = load_phase3_representatives(project_root)
    missing = [c for c in reps if c not in subjects.columns]
    if missing:
        raise RuntimeError(f"representative features missing from Phase 2 table: {missing[:5]}")
    assert_no_labels(pd.DataFrame(columns=reps), where="phase3_representatives")
    meta = feature_families(reps)
    families = meta["family"].tolist()
    raw = subjects[reps].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    raw = _impute_median(raw)
    Z, med, iqr = robust_scale(raw)
    X_compact, compact_names, family_info = family_pca_block(Z, reps, families)
    # Unbalanced sensitivity representation: robust-scaled columns, no family PCA.
    return {
        "subject_id": subjects["subject_id"].astype(str).to_numpy(),
        "n_cycles": subjects["n_cycles"].to_numpy() if "n_cycles" in subjects.columns else None,
        "raw": raw,
        "raw_names": reps,
        "scaled": Z,
        "scale_median": med,
        "scale_iqr": iqr,
        "compact": X_compact,
        "compact_names": compact_names,
        "family_info": family_info,
        "feature_meta": meta,
        "n_subjects": len(subjects),
        "method": {
            "source": "phase3_redundancy_representatives",
            "n_representatives": len(reps),
            "scaling": "median_iqr",
            "family_balance": "within_family_pca_then_1_over_sqrt_n_pcs",
            "family_variance_keep": FAMILY_VAR_KEEP,
            "max_family_pcs": MAX_FAMILY_PCS,
            "seed": SEED,
            "invalid_values": "column_median_impute_then_robust_scale",
        },
    }


def representation_frame(rep: dict) -> pd.DataFrame:
    df = pd.DataFrame(rep["compact"], columns=rep["compact_names"])
    df.insert(0, "subject_id", rep["subject_id"])
    assert_no_labels(df, where="compact_representation")
    return df
