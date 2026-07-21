"""Dual Quaternion Skinning — architecture placeholder (interface only).

DQS is registered for future research / production work without redesigning
SkinningRuntime. Calling deform raises :class:`SkinningNotSupportedError`.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.skinning.exceptions import SkinningNotSupportedError
from motion_engine.rendering.avatar.skinning.matrix_palette import MatrixPalette
from motion_engine.rendering.avatar.skinning.types import SkinningAlgorithm
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


class DualQuaternionSkinning:
    """Interface stub for Dual Quaternion Skinning (not implemented in M4)."""

    algorithm = SkinningAlgorithm.DUAL_QUATERNION

    def deform(
        self,
        mesh: MeshData,
        weights: WeightTable,
        palette: MatrixPalette,
        **kwargs: object,
    ) -> None:
        raise SkinningNotSupportedError(self.algorithm.value)


class CenterOfRotationSkinning:
    """Interface stub for Center of Rotation Skinning (not implemented in M4)."""

    algorithm = SkinningAlgorithm.CENTER_OF_ROTATION

    def deform(
        self,
        mesh: MeshData,
        weights: WeightTable,
        palette: MatrixPalette,
        **kwargs: object,
    ) -> None:
        raise SkinningNotSupportedError(self.algorithm.value)


__all__ = ["DualQuaternionSkinning", "CenterOfRotationSkinning"]
