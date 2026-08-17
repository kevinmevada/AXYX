"""Family 6 — conservative coordination (correlation and lag on ax1)."""

from __future__ import annotations

import numpy as np

from .anatomy import COORD_PAIRS, meta
from .base import FeatureSpec
from .context import CycleRecord


def specs() -> list[FeatureSpec]:
    out: list[FeatureSpec] = []
    for a, b, tag in COORD_PAIRS:
        info = meta(a)
        out.append(
            FeatureSpec(
                name=f"coord_{tag}_ax1_corr",
                family="coordination",
                source_signal=f"{a}|{b}",
                anatomical_region=info["region"],
                side=info["side"],
                unit="corr",
                aggregation="pearson",
                phase="full_cycle",
                related_anatomy=f"{a},{b}",
                description=f"Pearson correlation of {a} ax1 vs {b} ax1",
            )
        )
        out.append(
            FeatureSpec(
                name=f"coord_{tag}_ax1_lag_pct",
                family="coordination",
                source_signal=f"{a}|{b}",
                anatomical_region=info["region"],
                side=info["side"],
                unit="pct_cycle",
                aggregation="xcorr_lag",
                phase="full_cycle",
                related_anatomy=f"{a},{b}",
                description=f"Lag of max abs cross-correlation ({b} relative to {a}), clipped to ±10%",
            )
        )
    return out


def _corr_lag(a: np.ndarray, b: np.ndarray, max_lag: int = 10) -> tuple[float, float]:
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 10:
        return float("nan"), float("nan")
    a = a[mask]
    b = b[mask]
    a = a - np.mean(a)
    b = b - np.mean(b)
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    corr = float(np.sum(a * b) / denom) if denom > 0 else float("nan")
    n = a.size
    max_lag = min(max_lag, n - 2)
    best_lag = 0
    best_val = -1.0
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            aa, bb = a[-lag:], b[: n + lag]
        elif lag > 0:
            aa, bb = a[: n - lag], b[lag:]
        else:
            aa, bb = a, b
        if aa.size < 8:
            continue
        aa = aa - np.mean(aa)
        bb = bb - np.mean(bb)
        d = np.sqrt(np.sum(aa * aa) * np.sum(bb * bb))
        if d <= 0:
            continue
        val = abs(float(np.sum(aa * bb) / d))
        if val > best_val:
            best_val = val
            best_lag = lag
    # lag in percent-cycle samples (1 sample = 1%)
    return corr, float(best_lag)


def extract(record: CycleRecord) -> dict[str, float]:
    values: dict[str, float] = {}
    for a, b, tag in COORD_PAIRS:
        sa = record.signals.get(a)
        sb = record.signals.get(b)
        if sa is None or sb is None:
            values[f"coord_{tag}_ax1_corr"] = float("nan")
            values[f"coord_{tag}_ax1_lag_pct"] = float("nan")
            continue
        corr, lag = _corr_lag(sa[:, 0], sb[:, 0])
        values[f"coord_{tag}_ax1_corr"] = corr
        values[f"coord_{tag}_ax1_lag_pct"] = lag
    return values
