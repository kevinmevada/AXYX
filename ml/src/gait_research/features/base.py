"""Feature specification and label-blind calculation helpers.

Victimization labels must never enter this package.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
from scipy.signal import savgol_filter

AXIS_NAMES = ("ax1", "ax2", "ax3")
N_PHASE = 101
SGOLAY_WINDOW = 11
SGOLAY_POLY = 3
PHASE_BINS = tuple((i, i + 10) for i in range(0, 100, 10))


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    family: str
    source_signal: str
    anatomical_region: str
    side: str
    unit: str
    aggregation: str
    phase: str
    related_anatomy: str
    description: str
    uses_smoothing: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def finite_series(x: np.ndarray) -> np.ndarray | None:
    x = np.asarray(x, dtype=float).ravel()
    if x.size == 0 or not np.isfinite(x).any():
        return None
    return x


def series_stats(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=float).ravel()
    finite = x[np.isfinite(x)]
    if finite.size == 0:
        return {k: float("nan") for k in ("min", "max", "mean", "median", "std", "rom")}
    return {
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "std": float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0,
        "rom": float(np.max(finite) - np.min(finite)),
    }


def argmin_max_pct(x: np.ndarray) -> tuple[float, float]:
    """Return (tmin_pct, tmax_pct) on a 0-100% grid of length 101."""
    x = np.asarray(x, dtype=float).ravel()
    n = x.size
    if n == 0 or not np.isfinite(x).any():
        return float("nan"), float("nan")
    work = x.copy()
    work[~np.isfinite(work)] = np.nan
    tmin = float(np.nanargmin(work) * 100.0 / (n - 1)) if n > 1 else 0.0
    tmax = float(np.nanargmax(work) * 100.0 / (n - 1)) if n > 1 else 0.0
    return tmin, tmax


def path_length_3d(xyz: np.ndarray) -> float:
    xyz = np.asarray(xyz, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3:
        return float("nan")
    d = np.diff(xyz, axis=0)
    step = np.sqrt(np.sum(d * d, axis=1))
    step = step[np.isfinite(step)]
    if step.size == 0:
        return float("nan")
    return float(np.sum(step))


def excursion(xyz: np.ndarray, axis: int) -> float:
    col = np.asarray(xyz, dtype=float)[:, axis]
    finite = col[np.isfinite(col)]
    if finite.size == 0:
        return float("nan")
    return float(np.max(finite) - np.min(finite))


def smooth_series(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float).ravel()
    if x.size < SGOLAY_WINDOW:
        return x.copy()
    y = x.copy()
    mask = np.isfinite(y)
    if mask.sum() < SGOLAY_WINDOW:
        return y
    filled = y.copy()
    idx = np.arange(y.size)
    filled[~mask] = np.interp(idx[~mask], idx[mask], y[mask])
    return savgol_filter(filled, SGOLAY_WINDOW, SGOLAY_POLY, mode="interp")


def derivative(x: np.ndarray, dt: float) -> np.ndarray:
    """First derivative. dt is seconds per sample (duration/100 for 101-pt cycles)."""
    x = np.asarray(x, dtype=float).ravel()
    if x.size < 2 or not np.isfinite(dt) or dt <= 0:
        return np.full_like(x, np.nan, dtype=float)
    return np.gradient(x, dt)


def event_pct(event_frame, start_frame, end_frame) -> float:
    try:
        if event_frame == "" or event_frame is None or (isinstance(event_frame, float) and np.isnan(event_frame)):
            return float("nan")
        start = float(start_frame)
        end = float(end_frame)
        ev = float(event_frame)
        span = end - start
        if span <= 0:
            return float("nan")
        return float((ev - start) / span * 100.0)
    except (TypeError, ValueError):
        return float("nan")


def cv(std: float, mean: float) -> float:
    if not np.isfinite(std) or not np.isfinite(mean) or mean == 0:
        return float("nan")
    return float(std / abs(mean))


def mad(x: np.ndarray) -> float:
    finite = np.asarray(x, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return float("nan")
    return float(np.median(np.abs(finite - np.median(finite))))
