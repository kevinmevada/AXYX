"""Family 7 — 10% gait-phase bins for primary angle axis (ax1) only."""

from __future__ import annotations

from .anatomy import PHASE_ANGLE_SIGNALS, meta
from .base import PHASE_BINS, FeatureSpec, series_stats
from .context import CycleRecord


def specs() -> list[FeatureSpec]:
    out: list[FeatureSpec] = []
    for signal in PHASE_ANGLE_SIGNALS:
        info = meta(signal)
        for lo, hi in PHASE_BINS:
            phase = f"{lo}_{hi}"
            for agg in ("mean", "min", "max", "rom"):
                out.append(
                    FeatureSpec(
                        name=f"{signal}_ax1_phase_{lo}_{hi}_{agg}",
                        family="phase",
                        source_signal=signal,
                        anatomical_region=info["region"],
                        side=info["side"],
                        unit=info["unit"],
                        aggregation=agg,
                        phase=phase,
                        related_anatomy=info["related"],
                        description=f"{signal} ax1 {agg} during {lo}-{hi}% gait cycle",
                    )
                )
    return out


def extract(record: CycleRecord) -> dict[str, float]:
    values: dict[str, float] = {}
    n = 101
    for signal in PHASE_ANGLE_SIGNALS:
        arr = record.signals.get(signal)
        if arr is None:
            continue
        col = arr[:, 0]
        for lo, hi in PHASE_BINS:
            i0 = int(round(lo * (n - 1) / 100.0))
            i1 = int(round(hi * (n - 1) / 100.0))
            if hi == 100:
                sl = col[i0 : i1 + 1]
            else:
                sl = col[i0:i1]
            stats = series_stats(sl)
            prefix = f"{signal}_ax1_phase_{lo}_{hi}"
            values[f"{prefix}_mean"] = stats["mean"]
            values[f"{prefix}_min"] = stats["min"]
            values[f"{prefix}_max"] = stats["max"]
            values[f"{prefix}_rom"] = stats["rom"]
    return values
