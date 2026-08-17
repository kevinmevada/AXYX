"""Subject-level robustness: leave-one-subject-out and label permutation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .effect_sizes import cliffs_delta


def leave_one_subject_out(df: pd.DataFrame, features: list[str], label_col: str = "victimized") -> pd.DataFrame:
    subjects = df["subject_id"].tolist()
    rows = []
    for feat in features:
        x = pd.to_numeric(df[feat], errors="coerce")
        y = df[label_col]
        full_v = x[y == "Y"].to_numpy(dtype=float)
        full_c = x[y == "N"].to_numpy(dtype=float)
        full_d = cliffs_delta(full_v, full_c)
        full_dir = np.sign(full_d) if np.isfinite(full_d) else 0.0
        deltas = []
        same = 0
        for sid in subjects:
            mask = df["subject_id"] != sid
            xv = x[mask & (y == "Y")].to_numpy(dtype=float)
            xc = x[mask & (y == "N")].to_numpy(dtype=float)
            d = cliffs_delta(xv, xc)
            deltas.append(d)
            if np.isfinite(d) and np.isfinite(full_d) and np.sign(d) == full_dir and full_dir != 0:
                same += 1
            elif full_dir == 0 and np.isfinite(d) and d == 0:
                same += 1
        deltas_a = np.array(deltas, dtype=float)
        rows.append(
            {
                "feature": feat,
                "full_cliffs_delta": full_d,
                "loso_delta_median": float(np.nanmedian(deltas_a)),
                "loso_delta_min": float(np.nanmin(deltas_a)),
                "loso_delta_max": float(np.nanmax(deltas_a)),
                "loso_direction_agreement": float(same / len(subjects)),
                "loso_max_abs_shift": float(np.nanmax(np.abs(deltas_a - full_d))),
            }
        )
    return pd.DataFrame(rows)


def permutation_cliffs(
    df: pd.DataFrame,
    features: list[str],
    *,
    n_perm: int = 999,
    seed: int = 20260813,
    label_col: str = "victimized",
) -> pd.DataFrame:
    """Shuffle group labels across subjects. Cycles are never resampled."""
    rng = np.random.default_rng(seed)
    labels = df[label_col].to_numpy()
    shuffles = np.stack([rng.permutation(labels) for _ in range(n_perm)])
    rows = []
    for feat in features:
        x = pd.to_numeric(df[feat], errors="coerce").to_numpy(dtype=float)
        obs = cliffs_delta(x[labels == "Y"], x[labels == "N"])
        null = np.empty(n_perm, dtype=float)
        for i in range(n_perm):
            shuf = shuffles[i]
            null[i] = cliffs_delta(x[shuf == "Y"], x[shuf == "N"])
        if np.isfinite(obs):
            p = (1 + np.sum(np.abs(null) >= abs(obs))) / (n_perm + 1)
        else:
            p = float("nan")
        rows.append(
            {
                "feature": feat,
                "observed_cliffs_delta": obs,
                "perm_p": float(p),
                "n_perm": n_perm,
                "unit": "subject",
            }
        )
    return pd.DataFrame(rows)
