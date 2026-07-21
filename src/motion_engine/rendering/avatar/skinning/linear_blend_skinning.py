"""Fix import order in linear_blend_skinning."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.skinning.cpu_skinner import CpuSkinner, SkinningResult
from motion_engine.rendering.avatar.skinning.matrix_palette import MatrixPalette
from motion_engine.rendering.avatar.skinning.types import SkinningAlgorithm
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


class LinearBlendSkinning:
    """Production LBS algorithm (pluggable via SkinningRuntime)."""

    algorithm = SkinningAlgorithm.LINEAR_BLEND

    def __init__(self, skinner: CpuSkinner | None = None) -> None:
        self._skinner = skinner or CpuSkinner()

    def deform(
        self,
        mesh: MeshData,
        weights: WeightTable,
        palette: MatrixPalette,
        *,
        deform_normals: bool = True,
        tangents: np.ndarray | None = None,
    ) -> SkinningResult:
        return self._skinner.skin(
            mesh,
            weights,
            palette,
            deform_normals=deform_normals,
            tangents=tangents,
        )


__all__ = ["LinearBlendSkinning"]
