"""MeshSkin — first-class skinning asset (weights + palette + metadata).

Decouples deformation data from ``MeshData`` so one mesh can bind to multiple
skeletons, LODs, or experimental weight sets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.skinning.bone_palette import BonePalette
from motion_engine.rendering.avatar.skinning.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.skinning.types import SkinningAlgorithm
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


@dataclass(frozen=True, slots=True)
class SkinningMetadata:
    """Provenance / convention metadata for a MeshSkin."""

    name: str = ""
    mesh_name: str = ""
    skeleton_name: str = ""
    algorithm_hint: SkinningAlgorithm = SkinningAlgorithm.LINEAR_BLEND
    runtime_version: str = RUNTIME_VERSION
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mesh_name": self.mesh_name,
            "skeleton_name": self.skeleton_name,
            "algorithm_hint": self.algorithm_hint.value,
            "runtime_version": self.runtime_version,
            "extra": dict(self.extra),
        }


@dataclass(frozen=True, slots=True)
class MeshSkin:
    """Skinning binding for a mesh: weights, palette, metadata.

    Does **not** own mesh geometry. Bind matrices live on :class:`Pose`
    (BindPose / AnimationPose); this asset references the intended skeleton
    via metadata and palette indices.
    """

    weight_table: WeightTable
    bone_palette: BonePalette
    metadata: SkinningMetadata = field(default_factory=SkinningMetadata)

    @property
    def vertex_count(self) -> int:
        return self.weight_table.vertex_count

    @property
    def max_influences(self) -> int:
        return self.weight_table.max_influences

    def clone(self) -> MeshSkin:
        """Independently owned copy."""
        return MeshSkin(
            weight_table=self.weight_table.clone(),
            bone_palette=BonePalette(
                bone_indices=self.bone_palette.bone_indices.copy(),
                names=self.bone_palette.names,
            ),
            metadata=SkinningMetadata(
                name=self.metadata.name,
                mesh_name=self.metadata.mesh_name,
                skeleton_name=self.metadata.skeleton_name,
                algorithm_hint=self.metadata.algorithm_hint,
                runtime_version=self.metadata.runtime_version,
                extra=dict(self.metadata.extra),
            ),
        )


__all__ = ["MeshSkin", "SkinningMetadata"]
