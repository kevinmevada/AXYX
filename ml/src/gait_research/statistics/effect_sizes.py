"""Effect sizes. Subject is the unit. No modeling."""

from __future__ import annotations

import numpy as np


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Cliff's delta: P(x>y) - P(x<y). x=victims, y=controls. Range [-1, 1]."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x[np.isfinite(x)]
    y = y[np.isfinite(y)]
    if x.size == 0 or y.size == 0:
        return float("nan")
    # broadcasting
    gt = np.sum(x[:, None] > y[None, :])
    lt = np.sum(x[:, None] < y[None, :])
    return float((gt - lt) / (x.size * y.size))


def cliffs_delta_label(delta: float) -> str:
    if not np.isfinite(delta):
        return "undefined"
    a = abs(delta)
    if a < 0.147:
        return "negligible"
    if a < 0.33:
        return "small"
    if a < 0.474:
        return "medium"
    return "large"


def bootstrap_cliffs_ci(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_boot: int = 1000,
    seed: int = 20260813,
    alpha: float = 0.05,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x[np.isfinite(x)]
    y = y[np.isfinite(y)]
    if x.size < 2 or y.size < 2:
        return float("nan"), float("nan")
    stats = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        xs = rng.choice(x, size=x.size, replace=True)
        ys = rng.choice(y, size=y.size, replace=True)
        stats[i] = cliffs_delta(xs, ys)
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)
