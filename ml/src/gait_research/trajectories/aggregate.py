"""Subject-level trajectory summaries. Cycles are repeated measures, not n."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..features.base import AXIS_NAMES, N_PHASE
from .load import signal_family

MIN_SUBJECTS = 31
MIN_FINITE_FRAC = 0.90


def subject_median_trajectories(cube: np.ndarray, inventory: pd.DataFrame, signals: list[str]) -> dict:
    """cube: (n_cycles, n_signals, 101, 3). Returns median/mean (n_subjects, n_signals, 101, 3)."""
    if cube.shape[2] != N_PHASE:
        raise RuntimeError("trajectories are not 101-point normalized")
    subjects = np.array(sorted(inventory["subject_id"].astype(str).unique()))
    n_s, n_sig = subjects.size, len(signals)
    med = np.full((n_s, n_sig, N_PHASE, 3), np.nan)
    mean = np.full_like(med, np.nan)
    n_cyc = np.zeros(n_s, dtype=int)
    sid_to_i = {s: i for i, s in enumerate(subjects)}
    for sid, part in inventory.groupby(inventory["subject_id"].astype(str)):
        i = sid_to_i[str(sid)]
        rows = part.index.to_numpy()
        n_cyc[i] = int(len(rows))
        block = cube[rows]
        with np.errstate(all="ignore"):
            med[i] = np.nanmedian(block, axis=0)
            mean[i] = np.nanmean(block, axis=0)
    quality = []
    for j, sig in enumerate(signals):
        for ax in range(3):
            sl = med[:, j, :, ax]
            finite_frac = np.mean(np.isfinite(sl), axis=1)
            n_ok = int(np.sum(finite_frac >= MIN_FINITE_FRAC))
            quality.append(
                {
                    "signal": sig,
                    "axis": AXIS_NAMES[ax],
                    "family": signal_family(sig),
                    "n_subjects_ok": n_ok,
                    "n_subjects": int(n_s),
                    "median_subject_finite_frac": float(np.median(finite_frac)),
                    "min_subject_finite_frac": float(np.min(finite_frac)),
                    "eligible": n_ok == int(n_s) and n_s >= 3,
                    "zero_filled": False,
                    "interpolated": False,
                }
            )
    qdf = pd.DataFrame(quality)
    return {
        "subject_id": subjects,
        "signals": signals,
        "median": med,
        "mean": mean,
        "n_cycles": n_cyc,
        "quality": qdf,
        "n_subjects": int(n_s),
        "n_time": N_PHASE,
        "aggregation": "nanmedian_over_cycles_within_subject",
    }
