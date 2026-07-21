"""Factories for MeshSkin and SkinningRuntime wiring."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.skinning.bone_palette import BonePalette
from motion_engine.rendering.avatar.skinning.exceptions import SkinningFactoryError
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin, SkinningMetadata
from motion_engine.rendering.avatar.skinning.types import NormalizationMode, SkinningAlgorithm
from motion_engine.rendering.avatar.skinning.weight_normalization import normalize_weights
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable
from motion_engine.rendering.avatar.skinning.weight_validation import validate_weight_table


class MeshSkinFactory:
    """Build :class:`MeshSkin` from mesh attributes or explicit tables."""

    def __init__(
        self,
        *,
        normalize: NormalizationMode = NormalizationMode.AUTOMATIC,
        validate: bool = True,
        bone_count: int | None = None,
    ) -> None:
        self.normalize = normalize
        self.validate = validate
        self.bone_count = bone_count

    def from_mesh(
        self,
        mesh: MeshData,
        *,
        bone_count: int,
        bone_names: Sequence[str] | None = None,
        name: str = "",
        skeleton_name: str = "",
        max_influences: int | None = None,
    ) -> MeshSkin:
        """Extract weights from ``MeshData.joint_*`` attributes."""
        if mesh.joint_indices is None or mesh.joint_weights is None:
            raise SkinningFactoryError(
                f"Mesh {mesh.name!r} has no joint_indices/joint_weights",
                code="SKIN_FACTORY_NO_WEIGHTS",
            )
        table = WeightTable.from_arrays(
            mesh.joint_indices,
            mesh.joint_weights,
            max_influences=max_influences,
        )
        return self.from_weight_table(
            table,
            bone_count=bone_count,
            bone_names=bone_names,
            mesh_name=mesh.name,
            name=name or f"skin:{mesh.name}",
            skeleton_name=skeleton_name,
        )

    def from_weight_table(
        self,
        table: WeightTable,
        *,
        bone_count: int,
        bone_names: Sequence[str] | None = None,
        mesh_name: str = "",
        name: str = "",
        skeleton_name: str = "",
    ) -> MeshSkin:
        """Build MeshSkin from an explicit weight table."""
        bc = self.bone_count if self.bone_count is not None else bone_count
        table = normalize_weights(table, mode=self.normalize)
        if self.validate:
            validate_weight_table(
                table, bone_count=bc, require_unit_sum=False
            ).raise_if_invalid()
        palette = BonePalette.identity(bc, names=bone_names)
        meta = SkinningMetadata(
            name=name or "mesh_skin",
            mesh_name=mesh_name,
            skeleton_name=skeleton_name,
            algorithm_hint=SkinningAlgorithm.LINEAR_BLEND,
        )
        return MeshSkin(weight_table=table, bone_palette=palette, metadata=meta)

    def rigid_bind(
        self,
        vertex_count: int,
        bone_index: int,
        *,
        bone_count: int,
        bone_names: Sequence[str] | None = None,
        name: str = "rigid",
    ) -> MeshSkin:
        """All vertices fully weighted to a single bone (testing / props)."""
        k = 4
        idx = np.full((vertex_count, k), -1, dtype=np.int32)
        w = np.zeros((vertex_count, k), dtype=np.float32)
        idx[:, 0] = bone_index
        w[:, 0] = 1.0
        return self.from_weight_table(
            WeightTable.from_arrays(idx, w),
            bone_count=bone_count,
            bone_names=bone_names,
            name=name,
        )


__all__ = ["MeshSkinFactory"]
