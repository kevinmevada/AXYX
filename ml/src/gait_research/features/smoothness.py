"""Family 8 — conservative smoothness (mean-squared jerk on smoothed series)."""

from __future__ import annotations

import numpy as np

from .base import FeatureSpec, derivative, smooth_series
from .context import CycleRecord, dt_seconds


def specs() -> list[FeatureSpec]:
    return [
        FeatureSpec(
            name="COM_msjerk",
            family="smoothness",
            source_signal="CentreOfMass",
            anatomical_region="whole_body",
            side="none",
            unit="mm_per_s3_sq",
            aggregation="mean_squared_jerk",
            phase="full_cycle",
            related_anatomy="CentreOfMass",
            description="Mean squared jerk of 3D COM speed (Savitzky-Golay then differentiate)",
            uses_smoothing=True,
        ),
        FeatureSpec(
            name="LKneeAngles_ax1_msjerk",
            family="smoothness",
            source_signal="LKneeAngles",
            anatomical_region="knee",
            side="left",
            unit="deg_per_s3_sq",
            aggregation="mean_squared_jerk",
            phase="full_cycle",
            related_anatomy="LKJC",
            description="Mean squared jerk of LKneeAngles ax1",
            uses_smoothing=True,
        ),
        FeatureSpec(
            name="RKneeAngles_ax1_msjerk",
            family="smoothness",
            source_signal="RKneeAngles",
            anatomical_region="knee",
            side="right",
            unit="deg_per_s3_sq",
            aggregation="mean_squared_jerk",
            phase="full_cycle",
            related_anatomy="RKJC",
            description="Mean squared jerk of RKneeAngles ax1",
            uses_smoothing=True,
        ),
    ]


def _msjerk(x: np.ndarray, dt: float) -> float:
    sm = smooth_series(x)
    vel = derivative(sm, dt)
    acc = derivative(vel, dt)
    jerk = derivative(acc, dt)
    finite = jerk[np.isfinite(jerk)]
    if finite.size == 0:
        return float("nan")
    return float(np.mean(finite * finite))


def extract(record: CycleRecord) -> dict[str, float]:
    dt = dt_seconds(record)
    values: dict[str, float] = {}
    com = record.signals.get("CentreOfMass")
    if com is None:
        values["COM_msjerk"] = float("nan")
    else:
        d = np.diff(com, axis=0)
        speed = np.sqrt(np.sum(d * d, axis=1))
        speed = np.concatenate([[speed[0]], speed]) if speed.size else speed
        values["COM_msjerk"] = _msjerk(speed, dt)
    for name, key in (("LKneeAngles", "LKneeAngles_ax1_msjerk"), ("RKneeAngles", "RKneeAngles_ax1_msjerk")):
        arr = record.signals.get(name)
        values[key] = float("nan") if arr is None else _msjerk(arr[:, 0], dt)
    return values
