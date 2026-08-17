"""Subject-level victim vs control comparisons. Labels enter here only."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from .effect_sizes import bootstrap_cliffs_ci, cliffs_delta, cliffs_delta_label


def _direction(delta: float, v_med: float, c_med: float) -> str:
    if np.isfinite(delta):
        if delta > 0:
            return "VICTIMS_HIGHER"
        if delta < 0:
            return "VICTIMS_LOWER"
        return "TIED"
    if np.isfinite(v_med) and np.isfinite(c_med):
        if v_med > c_med:
            return "VICTIMS_HIGHER"
        if v_med < c_med:
            return "VICTIMS_LOWER"
    return "TIED"


def directional_consistency(values: np.ndarray, other_median: float, direction: str) -> float:
    v = values[np.isfinite(values)]
    if v.size == 0 or not np.isfinite(other_median):
        return float("nan")
    if direction == "VICTIMS_HIGHER":
        return float(np.mean(v > other_median))
    if direction == "VICTIMS_LOWER":
        return float(np.mean(v < other_median))
    return float("nan")


def compare_groups(df: pd.DataFrame, features: list[str], label_col: str = "victimized") -> pd.DataFrame:
    if label_col not in df.columns:
        raise ValueError("group labels required for comparison")
    if df[label_col].nunique() != 2:
        raise ValueError("expected two groups")
    n = len(df)
    if n != 31:
        # still allow but record; tests assert 31
        pass
    rows = []
    for feat in features:
        x = pd.to_numeric(df[feat], errors="coerce")
        vict = x[df[label_col] == "Y"].to_numpy(dtype=float)
        ctrl = x[df[label_col] == "N"].to_numpy(dtype=float)
        vf, cf = vict[np.isfinite(vict)], ctrl[np.isfinite(ctrl)]
        v_med = float(np.median(vf)) if vf.size else float("nan")
        c_med = float(np.median(cf)) if cf.size else float("nan")
        v_mean = float(np.mean(vf)) if vf.size else float("nan")
        c_mean = float(np.mean(cf)) if cf.size else float("nan")
        pooled_iqr = float(
            0.5
            * (
                (np.subtract(*np.percentile(vf, [75, 25])) if vf.size else np.nan)
                + (np.subtract(*np.percentile(cf, [75, 25])) if cf.size else np.nan)
            )
        )
        std_iqr = (
            (v_med - c_med) / pooled_iqr
            if np.isfinite(pooled_iqr) and pooled_iqr != 0
            else float("nan")
        )
        delta = cliffs_delta(vf, cf)
        lo, hi = bootstrap_cliffs_ci(vf, cf)
        direction = _direction(delta, v_med, c_med)
        if vf.size >= 2 and cf.size >= 2:
            try:
                u = mannwhitneyu(vf, cf, alternative="two-sided", method="auto")
                raw_p = float(u.pvalue)
                u_stat = float(u.statistic)
            except ValueError:
                raw_p, u_stat = float("nan"), float("nan")
        else:
            raw_p, u_stat = float("nan"), float("nan")
        rows.append(
            {
                "feature": feat,
                "n_subjects": n,
                "n_victims": int(vf.size),
                "n_controls": int(cf.size),
                "victim_median": v_med,
                "control_median": c_med,
                "victim_mean": v_mean,
                "control_mean": c_mean,
                "abs_median_diff": abs(v_med - c_med) if np.isfinite(v_med) and np.isfinite(c_med) else float("nan"),
                "rel_median_diff": (v_med - c_med) / abs(c_med) if np.isfinite(c_med) and c_med != 0 else float("nan"),
                "cliffs_delta": delta,
                "standardized_median_iqr": std_iqr,
                "cliffs_delta_ci_lo": lo,
                "cliffs_delta_ci_hi": hi,
                "cliffs_magnitude": cliffs_delta_label(delta),
                "direction": direction,
                "victim_consistency": directional_consistency(vf, c_med, direction),
                "control_consistency": directional_consistency(
                    cf,
                    v_med,
                    "VICTIMS_LOWER" if direction == "VICTIMS_HIGHER" else "VICTIMS_HIGHER" if direction == "VICTIMS_LOWER" else "TIED",
                ),
                "mannwhitney_u": u_stat,
                "raw_p": raw_p,
                "test": "mannwhitneyu_two_sided",
            }
        )
    return pd.DataFrame(rows)
