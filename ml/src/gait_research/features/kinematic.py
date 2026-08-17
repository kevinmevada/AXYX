"""Family 1 — kinematic summaries of joint-angle trajectories."""

from __future__ import annotations

import numpy as np

from .anatomy import ANGLE_SIGNALS, meta
from .base import AXIS_NAMES, FeatureSpec, argmin_max_pct, derivative, series_stats, smooth_series
from .context import CycleRecord, dt_seconds


def specs() -> list[FeatureSpec]:
    out: list[FeatureSpec] = []
    for signal in ANGLE_SIGNALS:
        info = meta(signal)
        for axis in AXIS_NAMES:
            for agg, desc in (
                ("min", "minimum"),
                ("max", "maximum"),
                ("mean", "mean"),
                ("median", "median"),
                ("std", "standard deviation"),
                ("rom", "range of motion (max-min)"),
                ("tmin_pct", "gait-cycle percent at minimum"),
                ("tmax_pct", "gait-cycle percent at maximum"),
            ):
                unit = info["unit"] if agg not in {"tmin_pct", "tmax_pct"} else "pct_cycle"
                out.append(
                    FeatureSpec(
                        name=f"{signal}_{axis}_{agg}",
                        family="kinematic",
                        source_signal=signal,
                        anatomical_region=info["region"],
                        side=info["side"],
                        unit=unit,
                        aggregation=agg,
                        phase="full_cycle",
                        related_anatomy=info["related"],
                        description=f"{desc} of {signal} {axis}",
                    )
                )
            for agg in ("peak_vel", "tpeak_vel_pct", "vel_rms", "peak_acc", "acc_rms"):
                unit = "deg_per_s" if "vel" in agg and "tpeak" not in agg else ("pct_cycle" if "tpeak" in agg else "deg_per_s2")
                out.append(
                    FeatureSpec(
                        name=f"{signal}_{axis}_{agg}",
                        family="kinematic",
                        source_signal=signal,
                        anatomical_region=info["region"],
                        side=info["side"],
                        unit=unit,
                        aggregation=agg,
                        phase="full_cycle",
                        related_anatomy=info["related"],
                        description=f"{agg} of smoothed {signal} {axis}",
                        uses_smoothing=True,
                    )
                )
    return out


def extract(record: CycleRecord) -> dict[str, float]:
    dt = dt_seconds(record)
    values: dict[str, float] = {}
    for signal in ANGLE_SIGNALS:
        arr = record.signals.get(signal)
        if arr is None:
            continue
        for j, axis in enumerate(AXIS_NAMES):
            col = arr[:, j]
            stats = series_stats(col)
            tmin, tmax = argmin_max_pct(col)
            prefix = f"{signal}_{axis}"
            values[f"{prefix}_min"] = stats["min"]
            values[f"{prefix}_max"] = stats["max"]
            values[f"{prefix}_mean"] = stats["mean"]
            values[f"{prefix}_median"] = stats["median"]
            values[f"{prefix}_std"] = stats["std"]
            values[f"{prefix}_rom"] = stats["rom"]
            values[f"{prefix}_tmin_pct"] = tmin
            values[f"{prefix}_tmax_pct"] = tmax

            sm = smooth_series(col)
            vel = derivative(sm, dt)
            acc = derivative(vel, dt)
            absvel = np.abs(vel)
            tpeak = argmin_max_pct(absvel)[1]
            finite_v = absvel[np.isfinite(absvel)]
            values[f"{prefix}_peak_vel"] = float(np.max(finite_v)) if finite_v.size else float("nan")
            values[f"{prefix}_tpeak_vel_pct"] = tpeak
            values[f"{prefix}_vel_rms"] = float(np.sqrt(np.nanmean(vel * vel))) if np.isfinite(vel).any() else float("nan")
            finite_a = np.abs(acc)
            finite_a = finite_a[np.isfinite(finite_a)]
            values[f"{prefix}_peak_acc"] = float(np.max(finite_a)) if finite_a.size else float("nan")
            values[f"{prefix}_acc_rms"] = float(np.sqrt(np.nanmean(acc * acc))) if np.isfinite(acc).any() else float("nan")
    return values
