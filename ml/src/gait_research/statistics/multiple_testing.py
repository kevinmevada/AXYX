"""Benjamini-Hochberg FDR. Applied after group tests, never during screening."""

from __future__ import annotations

import numpy as np


def benjamini_hochberg(pvalues: np.ndarray) -> np.ndarray:
    p = np.asarray(pvalues, dtype=float)
    n = p.size
    adj = np.full(n, np.nan)
    finite = np.isfinite(p)
    if not finite.any():
        return adj
    idx = np.where(finite)[0]
    pv = p[idx]
    m = pv.size
    order = np.argsort(pv)
    ranked = pv[order]
    q = np.empty(m, dtype=float)
    running = 1.0
    for i in range(m - 1, -1, -1):
        running = min(running, ranked[i] * m / (i + 1))
        q[i] = min(running, 1.0)
    inv = np.empty(m, dtype=int)
    inv[order] = np.arange(m)
    adj[idx] = q[inv]
    return adj
