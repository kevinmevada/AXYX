"""Load frozen Phase 2–4 inputs for similarity analyses. Does not modify them."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..labels import load_female_labels
from ..paths import survey_xlsx
from ..phenotypes.representation import build_representation


def load_labels_aligned(project_root: Path, subject_id: np.ndarray) -> np.ndarray:
    lab = load_female_labels(survey_xlsx())
    m = dict(zip(lab["subject_id"].astype(str), lab["victimized"].astype(str)))
    y = np.array([m.get(str(s), "") for s in subject_id])
    if (y == "Y").sum() != 17 or (y == "N").sum() != 14:
        raise RuntimeError(f"expected 17/14 labels, got {(y=='Y').sum()}/{(y=='N').sum()}")
    return y == "Y"


def load_phase4_compact(project_root: Path) -> dict:
    """Rebuild Phase 4 family-PC matrix from frozen Phase 2/3 (deterministic)."""
    rep = build_representation(project_root)
    victim = load_labels_aligned(project_root, rep["subject_id"])
    if rep["compact"].shape != (31, 27) and rep["compact"].shape[0] != 31:
        raise RuntimeError(f"unexpected compact shape {rep['compact'].shape}")
    return {
        "subject_id": rep["subject_id"],
        "X": rep["compact"],
        "feature_names": list(rep["compact_names"]),
        "victim": victim,
        "raw_representatives": rep["raw"],
        "raw_names": list(rep["raw_names"]),
        "n_dims": int(rep["compact"].shape[1]),
        "source": "phase4_family_pc_rebuilt_from_phase2_phase3",
    }


def load_coordination_crp_profiles(project_root: Path) -> dict:
    """Subject CRP similarity profiles from Phase 1 + locked P0.6 pairs."""
    from ..trajectories.load import load_normalized_cube
    from .coordination_crp import build_subject_crp_profiles, load_preregistered_pairs

    lock = project_root / "results" / "similarity" / "p06_coordination" / "preregistered_pairs.json"
    payload = load_preregistered_pairs(lock)
    loaded = load_normalized_cube(project_root)
    built = build_subject_crp_profiles(
        loaded["cube"], loaded["inventory"], loaded["signals"], payload["pairs"]
    )
    victim = load_labels_aligned(project_root, built["subject_id"])
    return {
        **built,
        "victim": victim,
        "pairs": payload["pairs"],
        "payload": payload,
        "source": "phase1_hilbert_crp_subject_circular_mean",
        "lock_path": str(lock),
        "n_fdr_family": int(payload["n_fdr_family"]),
    }


def load_event_phase_features(project_root: Path) -> dict:
    """Build P0.4 subject-level window features from Phase 1 events + curves."""
    from ..trajectories.load import load_normalized_cube
    from .event_phases import build_subject_phase_feature_matrix, load_preregistered_phases
    from .shape_space import load_preregistered_curves

    phase_lock = project_root / "results" / "similarity" / "p04_event_phases" / "preregistered_phases.json"
    curve_lock = project_root / "results" / "similarity" / "p03_shape" / "preregistered_curves.json"
    phase_payload = load_preregistered_phases(phase_lock)
    curves_meta = load_preregistered_curves(curve_lock)
    if len(curves_meta) != int(phase_payload["n_curves"]):
        raise RuntimeError("P0.4 n_curves does not match P0.3 locked curve count")
    loaded = load_normalized_cube(project_root)
    phase_ids = [p["id"] for p in phase_payload["phases"]]
    aggregations = list(phase_payload["aggregations"])
    built = build_subject_phase_feature_matrix(
        loaded["cube"],
        loaded["inventory"],
        loaded["signals"],
        curves_meta,
        phase_ids,
        aggregations,
    )
    victim = load_labels_aligned(project_root, built["subject_id"])
    n_feat_expected = (
        int(phase_payload["n_phases"])
        * int(phase_payload["n_curves"])
        * int(phase_payload["n_aggregations"])
    )
    if built["X"].shape != (31, n_feat_expected):
        raise RuntimeError(f"unexpected feature width {built['X'].shape}, expected (31, {n_feat_expected})")
    return {
        **built,
        "victim": victim,
        "phase_payload": phase_payload,
        "curves_meta": curves_meta,
        "source": "phase1_events_x_normalized_core_window_features",
        "lock_path": str(phase_lock),
        "n_fdr_family": int(phase_payload["n_fdr_family"]),
    }


def load_phase1_subject_median_curves(project_root: Path) -> dict:
    """Subject-median 101-pt curves for P0.3 preregistered list, from Phase 1 only."""
    from ..features.base import AXIS_NAMES
    from ..trajectories.aggregate import subject_median_trajectories
    from ..trajectories.load import load_normalized_cube
    from .shape_space import AXIS_TO_IDX, load_preregistered_curves

    lock = project_root / "results" / "similarity" / "p03_shape" / "preregistered_curves.json"
    curves_meta = load_preregistered_curves(lock)
    loaded = load_normalized_cube(project_root)
    agg = subject_median_trajectories(loaded["cube"], loaded["inventory"], loaded["signals"])
    sig_to_i = {s: i for i, s in enumerate(agg["signals"])}
    ids = agg["subject_id"]
    n = len(ids)
    X = np.full((n, len(curves_meta), 101), np.nan, dtype=float)
    curve_ids = []
    for c_i, meta in enumerate(curves_meta):
        sig = meta["signal"]
        ax = meta["axis"]
        if sig not in sig_to_i:
            raise RuntimeError(f"preregistered signal missing from Phase 1 core: {sig}")
        if ax not in AXIS_TO_IDX:
            raise RuntimeError(f"bad axis {ax}")
        X[:, c_i, :] = agg["median"][:, sig_to_i[sig], :, AXIS_TO_IDX[ax]]
        curve_ids.append(meta["id"])
    if not np.isfinite(X).all():
        raise RuntimeError("non-finite values in preregistered subject-median curves")
    victim = load_labels_aligned(project_root, ids)
    return {
        "subject_id": ids,
        "X": X,
        "curve_ids": curve_ids,
        "curves_meta": curves_meta,
        "victim": victim,
        "source": "phase1_normalized_core_subject_nanmedian",
        "lock_path": str(lock),
        "axis_names": AXIS_NAMES,
    }


def load_preregistered_abnormality_features(project_root: Path) -> dict:
    """Load the locked P0.2 feature matrix from Phase 2 subject table."""
    from .abnormality import load_preregistered_features

    lock = project_root / "results" / "similarity" / "p02_abnormality" / "preregistered_features.json"
    features = load_preregistered_features(lock)
    sub = pd.read_parquet(project_root / "results" / "phase2" / "subject_features.parquet")
    sub["subject_id"] = sub["subject_id"].astype(str)
    missing = [c for c in features if c not in sub.columns]
    if missing:
        raise RuntimeError(f"preregistered features missing from Phase 2 table: {missing[:8]}")
    # align to inventory order used elsewhere (female cohort)
    inv = pd.read_csv(project_root / "results" / "phase0" / "subject_inventory.csv")
    ids = inv["subject_id"].astype(str).to_numpy()
    sub = sub.set_index("subject_id").reindex(ids)
    if sub.isna().all(axis=1).any():
        bad = sub.index[sub.isna().all(axis=1)].tolist()
        raise RuntimeError(f"subjects missing from Phase 2 features: {bad}")
    X = sub[features].to_numpy(dtype=float)
    victim = load_labels_aligned(project_root, ids)
    return {
        "subject_id": ids,
        "X": X,
        "feature_names": features,
        "victim": victim,
        "source": "phase2_subject_features_preregistered_p02",
        "lock_path": str(lock),
    }


def load_covariates(project_root: Path, subject_id: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """height, mass, mean leg length, subject median cycle duration."""
    inv = pd.read_csv(project_root / "results" / "phase0" / "subject_inventory.csv")
    inv["subject_id"] = inv["subject_id"].astype(str)
    inv = inv.set_index("subject_id")
    # cycle duration from Phase 2 subject table if present
    sub = pd.read_parquet(project_root / "results" / "phase2" / "subject_features.parquet")
    sub["subject_id"] = sub["subject_id"].astype(str)
    sub = sub.set_index("subject_id")
    rows = []
    names = ["height_cm", "mass_kg", "mean_leg_cm", "cycle_duration_s_median"]
    for sid in subject_id:
        sid = str(sid)
        h = float(inv.loc[sid, "height_cm"]) if sid in inv.index else float("nan")
        m = float(inv.loc[sid, "mass_kg"]) if sid in inv.index else float("nan")
        if sid in inv.index:
            ll = float(inv.loc[sid, "lleg_cm"])
            rl = float(inv.loc[sid, "rleg_cm"])
            leg = 0.5 * (ll + rl)
        else:
            leg = float("nan")
        dur_col = "cycle_duration_s__median"
        dur = float(sub.loc[sid, dur_col]) if sid in sub.index and dur_col in sub.columns else float("nan")
        rows.append([h, m, leg, dur])
    return np.asarray(rows, dtype=float), names
