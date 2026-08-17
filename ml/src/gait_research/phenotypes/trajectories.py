"""Phenotype-level median trajectories from Phase 1 normalized cycles. No labels."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..features.context import inventory_without_labels
from .representation import assert_no_labels

TRAJECTORY_SIGNALS = (
    "LHipAngles",
    "RHipAngles",
    "LKneeAngles",
    "RKneeAngles",
    "LAnkleAngles",
    "RAnkleAngles",
    "LFootProgressAngles",
    "RFootProgressAngles",
    "CentreOfMass",
    "LASI",
    "RASI",
)


def load_normalized(project_root: Path) -> tuple[np.ndarray, np.ndarray, list[str], pd.DataFrame]:
    inv = inventory_without_labels(project_root / "results" / "phase1" / "gait_cycle_inventory.csv")
    assert_no_labels(inv, where="phase1_inventory_for_trajectories")
    blob = np.load(project_root / "results" / "phase1" / "gait_cycles" / "normalized_core.npz", allow_pickle=True)
    data = blob["data"]
    cycle_ids = np.array([str(x) for x in blob["cycle_id"].tolist()])
    signals = [str(x) for x in blob["signal_name"].tolist()]
    return data, cycle_ids, signals, inv


def phenotype_trajectories(
    project_root: Path,
    assignments: pd.DataFrame,
) -> dict:
    """Subject-median then phenotype-median trajectories. Cycle is not the unit."""
    if assignments.empty or "phenotype" not in assignments.columns:
        return {"data": {}, "signals": [], "axis": "ax1"}
    data, cycle_ids, signals, inv = load_normalized(project_root)
    by_id = {cid: i for i, cid in enumerate(cycle_ids)}
    inv = inv.copy()
    inv["arr_idx"] = inv["cycle_id"].map(by_id)
    inv = inv[inv["arr_idx"].notna()].copy()
    inv["arr_idx"] = inv["arr_idx"].astype(int)
    assign = assignments[["subject_id", "phenotype"]].drop_duplicates()
    inv = inv.merge(assign, on="subject_id", how="inner")
    keep = [s for s in TRAJECTORY_SIGNALS if s in signals]
    sig_idx = {s: signals.index(s) for s in keep}
    out = {}
    for ph, part in inv.groupby("phenotype"):
        stacked = []
        subjects = []
        for sid, sp in part.groupby("subject_id"):
            idxs = sp["arr_idx"].to_numpy()
            # subject median over that subject's cycles, all signals x 101 x 3
            cube = np.nanmedian(data[idxs], axis=0)
            stacked.append(cube)
            subjects.append(sid)
        if not stacked:
            continue
        arr = np.stack(stacked, axis=0)
        ph_med = np.nanmedian(arr, axis=0)
        out[int(ph)] = {
            "median": ph_med,
            "n_subjects": int(arr.shape[0]),
            "subject_ids": subjects,
        }
    return {"data": out, "signals": keep, "signal_index": sig_idx, "axis_names": ("ax1", "ax2", "ax3")}
