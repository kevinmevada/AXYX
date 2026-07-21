"""SkinningRuntime — orchestrates MeshSkin + Pose → DeformedMesh."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import Pose
from motion_engine.rendering.avatar.skinning.dual_quaternion_placeholder import (
    CenterOfRotationSkinning,
    DualQuaternionSkinning,
)
from motion_engine.rendering.avatar.skinning.exceptions import (
    SkinningNotSupportedError,
    SkinningValidationError,
)
from motion_engine.rendering.avatar.skinning.linear_blend_skinning import LinearBlendSkinning
from motion_engine.rendering.avatar.skinning.matrix_palette import (
    MatrixPalette,
    build_matrix_palette,
)
from motion_engine.rendering.avatar.skinning.mesh_cache import SkinningCache
from motion_engine.rendering.avatar.skinning.mesh_deformer import DeformedMesh, MeshDeformer
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.avatar.skinning.pose_sampler import resolve_pose
from motion_engine.rendering.avatar.skinning.statistics import (
    SkinningStatistics,
    compute_skinning_statistics,
)
from motion_engine.rendering.avatar.skinning.types import SkinningAlgorithm
from motion_engine.rendering.avatar.skinning.weight_validation import (
    validate_pose_bone_count,
    validate_weight_table,
)


@dataclass
class SkinningRuntime:
    """Deform a mesh using MeshSkin + BindPose/AnimationPose.

    Never modifies the source mesh. Algorithm is pluggable (LBS production;
    DQS / CoR registered but raise until implemented).
    """

    algorithm: SkinningAlgorithm = SkinningAlgorithm.LINEAR_BLEND
    validate: bool = True
    deform_normals: bool = True
    cache: SkinningCache | None = None
    _lbs: LinearBlendSkinning = field(default_factory=LinearBlendSkinning)
    _deformer: MeshDeformer = field(default_factory=MeshDeformer)
    last_statistics: SkinningStatistics | None = None
    last_palette: MatrixPalette | None = None

    def deform(
        self,
        mesh: MeshData,
        skin: MeshSkin,
        *,
        bind_pose: BindPose | None = None,
        pose: Pose | None = None,
        cache_key: str | None = None,
    ) -> DeformedMesh:
        """Produce a :class:`DeformedMesh` from rest mesh + skin + pose.

        ``pose`` (animation) overrides ``bind_pose`` when both are provided.
        """
        if self.cache is not None and cache_key is not None:
            hit = self.cache.get_deformed(cache_key)
            if hit is not None:
                return hit

        active = resolve_pose(bind=bind_pose, animation=pose)
        t_val0 = time.perf_counter_ns()
        if self.validate:
            if mesh.vertex_count != skin.vertex_count:
                raise SkinningValidationError(
                    "Mesh / MeshSkin vertex count mismatch",
                    code="SKIN_VERT_MISMATCH",
                )
            # Identity palettes match pose bone count; compact palettes must
            # reference valid skeleton indices only.
            max_bone = int(skin.bone_palette.bone_indices.max()) if skin.bone_palette.size else -1
            if max_bone >= active.bone_count:
                raise SkinningValidationError(
                    "Bone palette references missing pose bones",
                    code="SKIN_PALETTE_MISMATCH",
                )
            if skin.bone_palette.size == active.bone_count:
                validate_pose_bone_count(active.bone_count, skin.bone_palette.size)
            validate_weight_table(
                skin.weight_table,
                bone_count=active.bone_count,
                vertex_count=mesh.vertex_count,
            ).raise_if_invalid()
        validation_ms = (time.perf_counter_ns() - t_val0) / 1e6

        t_pal0 = time.perf_counter_ns()
        palette = build_matrix_palette(active, bone_palette=skin.bone_palette)
        self.last_palette = palette
        palette_ms = (time.perf_counter_ns() - t_pal0) / 1e6

        t_skin0 = time.perf_counter_ns()
        result = self._dispatch(mesh, skin, palette)
        skin_ms = (time.perf_counter_ns() - t_skin0) / 1e6

        deformed = self._deformer.deform(mesh, result)
        self.last_statistics = compute_skinning_statistics(
            vertex_count=mesh.vertex_count,
            triangle_count=mesh.triangle_count,
            bone_count=active.bone_count,
            weights=skin.weight_table,
            matrix_generation_ms=palette_ms,
            skinning_ms=skin_ms,
            validation_ms=validation_ms,
        )
        if self.cache is not None and cache_key is not None:
            self.cache.put_deformed(cache_key, deformed)
        return deformed

    def _dispatch(self, mesh: MeshData, skin: MeshSkin, palette: MatrixPalette) -> Any:
        if self.algorithm is SkinningAlgorithm.LINEAR_BLEND:
            return self._lbs.deform(
                mesh,
                skin.weight_table,
                palette,
                deform_normals=self.deform_normals,
            )
        if self.algorithm is SkinningAlgorithm.DUAL_QUATERNION:
            DualQuaternionSkinning().deform(mesh, skin.weight_table, palette)
        if self.algorithm is SkinningAlgorithm.CENTER_OF_ROTATION:
            CenterOfRotationSkinning().deform(mesh, skin.weight_table, palette)
        raise SkinningNotSupportedError(self.algorithm.value)


__all__ = ["SkinningRuntime"]
