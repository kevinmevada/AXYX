"""Family 5 — within-subject cycle-to-cycle variability (subject level)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import FeatureSpec, cv, mad

VARIABILITY_SOURCES = (
    "cycle_duration_s",
    "stance_pct",
    "LKneeAngles_ax1_rom",
    "RKneeAngles_ax1_rom",
    "LHipAngles_ax1_rom",
    "RHipAngles_ax1_rom",
    "LAnkleAngles_ax1_rom",
    "RAnkleAngles_ax1_rom",
    "LKneeAngles_ax1_tmax_pct",
    "RKneeAngles_ax1_tmax_pct",
    "CentreOfMass_path3d",
)


def _unit_for(src: str, agg: str) -> str:
    if agg == "cv":
        return "ratio"
    if src.endswith("_s") or src == "cycle_duration_s":
        return "s"
    if src.endswith("_pct") or "tmax_pct" in src or src == "stance_pct":
        return "pct_cycle"
    if src.endswith("path3d"):
        return "mm"
    if src.endswith("_rom"):
        return "deg"
    return "deg"


def specs() -> list[FeatureSpec]:
    out: list[FeatureSpec] = []
    for src in VARIABILITY_SOURCES:
        for agg in ("sd", "cv", "mad"):
            out.append(
                FeatureSpec(
                    name=f"var_{src}_{agg}",
                    family="variability",
                    source_signal=src,
                    anatomical_region="gait_cycle" if src.startswith("cycle") or src.startswith("stance") else "mixed",
                    side="none",
                    unit=_unit_for(src, agg),
                    aggregation=agg,
                    phase="full_cycle",
                    related_anatomy=src,
                    description=f"Within-subject {agg} of {src} across cycles",
                )
            )
    return out


def extract_subject(cycle_df: pd.DataFrame) -> dict[str, float]:
    values: dict[str, float] = {}
    for src in VARIABILITY_SOURCES:
        if src not in cycle_df.columns:
            continue
        x = cycle_df[src].to_numpy(dtype=float)
        finite = x[np.isfinite(x)]
        if finite.size == 0:
            sd = mean = m = float("nan")
        else:
            mean = float(np.mean(finite))
            sd = float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0
            m = mad(finite)
        values[f"var_{src}_sd"] = sd
        values[f"var_{src}_cv"] = cv(sd, mean)
        values[f"var_{src}_mad"] = m
    return values
