"""Bilateral trajectory asymmetry at the subject level."""

from __future__ import annotations

import numpy as np

PAIRS = (
    ("LHipAngles", "RHipAngles", "HipAngles"),
    ("LKneeAngles", "RKneeAngles", "KneeAngles"),
    ("LAnkleAngles", "RAnkleAngles", "AnkleAngles"),
    ("LFootProgressAngles", "RFootProgressAngles", "FootProgressAngles"),
)


def asymmetry_channels(median: np.ndarray, signals: list[str], axis: int = 0) -> dict[str, np.ndarray]:
    """A(t)=L-R and |L-R| using subject median trajectories. Sign is not assumed equivalent across families."""
    out = {}
    for left, right, stem in PAIRS:
        if left not in signals or right not in signals:
            continue
        li, ri = signals.index(left), signals.index(right)
        a = median[:, li, :, axis] - median[:, ri, :, axis]
        out[f"{stem}_ax{axis + 1}_LminusR"] = a
        out[f"{stem}_ax{axis + 1}_absLminusR"] = np.abs(a)
    return out
