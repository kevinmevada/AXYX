"""Phase 6 trajectory loading from certified Phase 1 output. No relabeling of axes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..catalog import CORE_GAIT_SIGNALS
from ..features.anatomy import SIGNAL_ANATOMY
from ..features.base import AXIS_NAMES, N_PHASE
from ..features.context import inventory_without_labels
from ..phenotypes.representation import assert_no_labels

SEED = 20260813


def signal_family(name: str) -> str:
    if name.endswith("Angles") or name.endswith("Angle"):
        if "FootProgress" in name:
            return "foot_progression"
        return "joint_angle"
    if name in {"CentreOfMass", "CentreOfMassFloor"}:
        return "com"
    if name.endswith("JC"):
        return "joint_center"
    return "marker"


def load_normalized_cube(project_root: Path) -> dict:
    inv = inventory_without_labels(project_root / "results" / "phase1" / "gait_cycle_inventory.csv")
    assert_no_labels(inv, where="phase1_inventory")
    blob = np.load(project_root / "results" / "phase1" / "gait_cycles" / "normalized_core.npz", allow_pickle=True)
    data = np.asarray(blob["data"], dtype=float)
    cycle_ids = np.array([str(x) for x in blob["cycle_id"].tolist()])
    signals = [str(x) for x in blob["signal_name"].tolist()]
    if data.ndim != 4 or data.shape[1:] != (len(signals), N_PHASE, 3):
        raise RuntimeError(f"unexpected cube shape {data.shape}")
    if data.shape[0] != 880:
        raise RuntimeError(f"expected 880 cycles, got {data.shape[0]}")
    if data.shape[2] != 101:
        raise RuntimeError(f"expected 101 points, got {data.shape[2]}")
    by_id = {cid: i for i, cid in enumerate(cycle_ids)}
    idx = []
    keep_rows = []
    for row in inv.itertuples(index=False):
        i = by_id.get(str(row.cycle_id))
        if i is None:
            continue
        idx.append(i)
        keep_rows.append(row)
    inv2 = pd.DataFrame(keep_rows)
    cube = data[np.array(idx, dtype=int)]
    return {
        "cube": cube,
        "inventory": inv2,
        "signals": signals,
        "cycle_ids": np.array([str(r.cycle_id) for r in keep_rows]),
        "core_expected": list(CORE_GAIT_SIGNALS),
        "anatomy": SIGNAL_ANATOMY,
        "axes": AXIS_NAMES,
    }
