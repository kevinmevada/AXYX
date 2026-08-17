"""Label-blind Phase 2 feature engine."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .context import ID_COLUMNS, LABEL_COLUMNS, CycleRecord, inventory_without_labels
from .registry import CYCLE_MODULES, cycle_specs


def load_cycles(project_root: Path) -> list[CycleRecord]:
    inv_path = project_root / "results" / "phase1" / "gait_cycle_inventory.csv"
    npz_path = project_root / "results" / "phase1" / "gait_cycles" / "normalized_core.npz"
    inv = inventory_without_labels(inv_path)
    blob = np.load(npz_path, allow_pickle=True)
    data = blob["data"]
    cycle_ids = [str(x) for x in blob["cycle_id"].tolist()]
    signal_names = [str(x) for x in blob["signal_name"].tolist()]
    by_id = {cid: i for i, cid in enumerate(cycle_ids)}

    records: list[CycleRecord] = []
    for row in inv.itertuples(index=False):
        cid = str(row.cycle_id)
        idx = by_id.get(cid)
        if idx is None:
            continue
        cube = data[idx]
        signals = {name: cube[j] for j, name in enumerate(signal_names)}
        records.append(
            CycleRecord(
                cycle_id=cid,
                subject_id=str(row.subject_id),
                session_id=str(row.session_id),
                trial_id=str(row.trial_id),
                side=str(row.side),
                start_frame=float(row.start_frame),
                end_frame=float(row.end_frame),
                duration_seconds=float(row.duration_seconds),
                sampling_rate_hz=float(row.sampling_rate_hz),
                ipsilateral_foot_off_frame=row.ipsilateral_foot_off_frame,
                opposite_contact_frame=row.opposite_contact_frame,
                opposite_foot_off_frame=row.opposite_foot_off_frame,
                mid_stance_frame=row.mid_stance_frame,
                signals=signals,
            )
        )
    records.sort(key=lambda r: r.cycle_id)
    return records


def extract_cycle_features(records: list[CycleRecord]) -> pd.DataFrame:
    rows = []
    for rec in records:
        row = {
            "cycle_id": rec.cycle_id,
            "subject_id": rec.subject_id,
            "session_id": rec.session_id,
            "trial_id": rec.trial_id,
            "side": rec.side,
            "start_frame": rec.start_frame,
            "end_frame": rec.end_frame,
            "duration_seconds": rec.duration_seconds,
        }
        for mod in CYCLE_MODULES:
            row.update(mod.extract(rec))
        rows.append(row)
    df = pd.DataFrame(rows)
    for col in LABEL_COLUMNS:
        if col in df.columns:
            raise RuntimeError(f"label column leaked into cycle features: {col}")
    return df.sort_values("cycle_id").reset_index(drop=True)
