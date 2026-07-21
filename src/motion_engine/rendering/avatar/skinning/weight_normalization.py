"""Weight row normalization."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.skinning.constants import UNUSED_BONE_INDEX, WEIGHT_SUM_EPS
from motion_engine.rendering.avatar.skinning.exceptions import SkinningValidationError
from motion_engine.rendering.avatar.skinning.types import NormalizationMode
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


def normalize_weights(
    table: WeightTable,
    *,
    mode: NormalizationMode = NormalizationMode.AUTOMATIC,
) -> WeightTable:
    """Return a weight table with rows normalized according to ``mode``.

    * AUTOMATIC — divide by row sum when sum > eps; zero rows stay zero.
    * STRICT — raise if any used row does not already sum to ~1.
    * PRESERVE — return a clone without changing weights.
    """
    if mode is NormalizationMode.PRESERVE:
        return table.clone()

    w = table.joint_weights.astype(np.float64, copy=True)
    idx = table.joint_indices.copy()
    used = (idx >= 0) & (w > 0.0)
    row_sum = np.where(used, w, 0.0).sum(axis=1)

    if mode is NormalizationMode.STRICT:
        active = row_sum > WEIGHT_SUM_EPS
        bad = active & (np.abs(row_sum - 1.0) > WEIGHT_SUM_EPS)
        if np.any(bad):
            raise SkinningValidationError(
                f"{int(bad.sum())} vertices have weights not summing to 1",
                code="SKIN_WEIGHT_SUM",
                details={"count": int(bad.sum())},
            )
        return table.clone()

    # AUTOMATIC
    scale = np.ones_like(row_sum)
    nonzero = row_sum > WEIGHT_SUM_EPS
    scale[nonzero] = 1.0 / row_sum[nonzero]
    w *= scale[:, None]
    # clear unused
    w[idx < 0] = 0.0
    w[idx == UNUSED_BONE_INDEX] = 0.0
    return WeightTable(
        joint_indices=idx,
        joint_weights=w.astype(np.float32),
        max_influences=table.max_influences,
    )


__all__ = ["normalize_weights"]
