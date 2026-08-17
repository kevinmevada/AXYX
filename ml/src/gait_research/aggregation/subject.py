"""Subject-level aggregation. Median is the default central tendency. No labels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..features.context import ID_COLUMNS, LABEL_COLUMNS
from ..features.symmetry import extract_subject as symmetry_subject
from ..features.variability import extract_subject as variability_subject

AGG_STATS = ("median", "mean", "std", "cv", "n")


def _cv(std: float, mean: float) -> float:
    if not np.isfinite(std) or not np.isfinite(mean) or mean == 0:
        return float("nan")
    return float(std / abs(mean))


def aggregate_subjects(cycle_df: pd.DataFrame) -> pd.DataFrame:
    feat_cols = [c for c in cycle_df.columns if c not in ID_COLUMNS]
    rows = []
    for subject_id, part in cycle_df.groupby("subject_id", sort=True):
        row: dict = {
            "subject_id": subject_id,
            "n_cycles": int(len(part)),
            "n_left_cycles": int((part["side"] == "L").sum()),
            "n_right_cycles": int((part["side"] == "R").sum()),
        }
        for col in feat_cols:
            x = part[col].to_numpy(dtype=float)
            finite = x[np.isfinite(x)]
            n = int(finite.size)
            if n == 0:
                med = mean = std = c = float("nan")
            else:
                med = float(np.median(finite))
                mean = float(np.mean(finite))
                std = float(np.std(finite, ddof=1)) if n > 1 else 0.0
                c = _cv(std, mean)
            row[f"{col}__median"] = med
            row[f"{col}__mean"] = mean
            row[f"{col}__std"] = std
            row[f"{col}__cv"] = c
            row[f"{col}__n"] = n
        row.update(symmetry_subject(part))
        row.update(variability_subject(part))
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("subject_id").reset_index(drop=True)
    for col in LABEL_COLUMNS:
        if col in df.columns:
            raise RuntimeError(f"label column leaked into subject features: {col}")
    return df
