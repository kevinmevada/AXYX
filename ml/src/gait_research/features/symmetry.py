"""Family 4 — symmetry from ipsilateral-aligned cycles (subject level)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .anatomy import BILATERAL_PAIRS
from .base import FeatureSpec

ANGLE_METRICS = ("ax1_rom", "ax1_max", "ax1_tmax_pct")
SPATIAL_METRICS = ("ax1_excursion", "path3d")
ANGLE_STEMS = {
    "HipAngles",
    "KneeAngles",
    "AnkleAngles",
    "AbsAnkleAngle",
    "FootProgressAngles",
}


def _stem(left: str) -> str:
    return left[1:] if left.startswith("L") else left


def _metrics_for(left: str) -> tuple[str, ...]:
    return ANGLE_METRICS if _stem(left) in ANGLE_STEMS else SPATIAL_METRICS


def specs() -> list[FeatureSpec]:
    out: list[FeatureSpec] = []
    for left, right, region in BILATERAL_PAIRS:
        stem = _stem(left)
        for metric in _metrics_for(left):
            for form in ("absdiff", "si"):
                if form == "si":
                    unit = "si_pct"
                elif metric == "ax1_tmax_pct":
                    unit = "pct_cycle"
                elif metric in {"ax1_rom", "ax1_max"}:
                    unit = "deg"
                else:
                    unit = "mm"
                out.append(
                    FeatureSpec(
                        name=f"sym_{stem}_{metric}_{form}",
                        family="symmetry",
                        source_signal=f"{left}|{right}",
                        anatomical_region=region,
                        side="bilateral",
                        unit=unit,
                        aggregation=form,
                        phase="full_cycle",
                        related_anatomy=f"{left},{right}",
                        description=f"Ipsilateral median {left} vs {right} {metric} ({form})",
                    )
                )
    return out


def _si(left: float, right: float) -> float:
    if not np.isfinite(left) or not np.isfinite(right):
        return float("nan")
    denom = 0.5 * (abs(left) + abs(right))
    if denom == 0:
        return 0.0
    return float(100.0 * (left - right) / denom)


def extract_subject(cycle_df: pd.DataFrame) -> dict[str, float]:
    values: dict[str, float] = {}
    left_rows = cycle_df[cycle_df["side"] == "L"]
    right_rows = cycle_df[cycle_df["side"] == "R"]
    for left, right, region in BILATERAL_PAIRS:
        stem = _stem(left)
        for metric in _metrics_for(left):
            lcol = f"{left}_{metric}"
            rcol = f"{right}_{metric}"
            if lcol not in cycle_df.columns or rcol not in cycle_df.columns:
                continue
            lval = float(left_rows[lcol].median()) if len(left_rows) and left_rows[lcol].notna().any() else float("nan")
            rval = float(right_rows[rcol].median()) if len(right_rows) and right_rows[rcol].notna().any() else float("nan")
            values[f"sym_{stem}_{metric}_absdiff"] = (
                abs(lval - rval) if np.isfinite(lval) and np.isfinite(rval) else float("nan")
            )
            values[f"sym_{stem}_{metric}_si"] = _si(lval, rval)
    return values
