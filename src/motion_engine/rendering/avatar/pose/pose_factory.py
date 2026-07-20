"""Factory: AvatarSkeleton → validated BindPose (Pose API)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from motion_engine.rendering.avatar.pose.bind_matrix import (
    BindMatrixSet,
    compute_inverse_bind,
)
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.coordinate_system import PoseCoordinateSystem
from motion_engine.rendering.avatar.pose.exceptions import PoseFactoryError
from motion_engine.rendering.avatar.pose.matrix_utils import identity_matrix
from motion_engine.rendering.avatar.pose.pose import AnimationPose, BonePose, Pose
from motion_engine.rendering.avatar.pose.pose_cache import PoseCache
from motion_engine.rendering.avatar.pose.pose_statistics import compute_pose_statistics
from motion_engine.rendering.avatar.pose.pose_validation import PoseValidator
from motion_engine.rendering.avatar.pose.rest_pose import RestPoseInfo
from motion_engine.rendering.avatar.pose.transform_propagation import (
    propagate_world_transforms,
)
from motion_engine.rendering.avatar.pose.types import RestPoseKind

if TYPE_CHECKING:
    from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton


class BindPoseFactory:
    """Construct immutable :class:`BindPose` instances from runtime skeletons.

    Does **not** mutate :class:`AvatarSkeleton`. Future mocap / clip / retarget
    entry points can share this factory surface without changing architecture.
    """

    def __init__(
        self,
        *,
        validate: bool = True,
        recompute_world_from_local: bool = False,
        prefer_authored_ibm: bool = True,
        cache: PoseCache | None = None,
    ) -> None:
        self.validate = validate
        self.recompute_world_from_local = recompute_world_from_local
        self.prefer_authored_ibm = prefer_authored_ibm
        self.cache = cache

    def from_skeleton(
        self,
        skeleton: AvatarSkeleton,
        *,
        rest_kind: RestPoseKind = RestPoseKind.IMPORTED,
        name: str | None = None,
        source_asset_id: str = "",
        cache_key: str | None = None,
    ) -> BindPose:
        """Build a bind pose from an M2 :class:`AvatarSkeleton`.

        Raises:
            PoseFactoryError: If the skeleton is empty or conversion fails.
        """
        if skeleton is None:  # type: ignore[redundant-expr]
            raise PoseFactoryError("Skeleton is None", code="POSE_FACTORY_NULL")
        if skeleton.bone_count == 0:
            raise PoseFactoryError("Skeleton has no bones", code="POSE_FACTORY_EMPTY")

        key = cache_key or f"{skeleton.name}:{rest_kind.value}:{skeleton.bone_count}"
        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None and isinstance(hit, BindPose):
                return hit

        try:
            from motion_engine.rendering.avatar.pose.matrix_utils import invert_affine

            bones = list(skeleton.bones)
            parents = [b.parent_index for b in bones]
            authored_world = [
                np.asarray(b.world_matrix, dtype=np.float64).reshape(4, 4).copy()
                for b in bones
            ]
            authored_ibm = [
                None if b.inverse_bind is None else np.asarray(b.inverse_bind, dtype=np.float64)
                for b in bones
            ]

            if self.recompute_world_from_local:
                # FK from skeleton local TRS (may diverge from authored bind_world).
                locals_m = [b.local_matrix for b in bones]
                prop = propagate_world_transforms(
                    locals_m,
                    parents,
                    topo_order=list(skeleton.hierarchy.topo_order),
                )
                worlds = list(prop.world_matrices)
            else:
                # Authoritative bind worlds; derive locals so FK is consistent.
                worlds = authored_world
                locals_m = []
                for i, w in enumerate(worlds):
                    p = parents[i]
                    if p is None:
                        locals_m.append(w.copy())
                    else:
                        locals_m.append(invert_affine(worlds[p]) @ w)

            inversion_count = 0
            ibm_list: list[np.ndarray] = []
            for i, w in enumerate(worlds):
                authored = authored_ibm[i] if self.prefer_authored_ibm else None
                if authored is None:
                    inversion_count += 1
                ibm_list.append(compute_inverse_bind(w, authored))

            bind_set = BindMatrixSet(
                rest_world=tuple(worlds),
                inverse_bind=tuple(ibm_list),
            )

            bone_poses: list[BonePose] = []
            for i, b in enumerate(bones):
                bone_poses.append(
                    BonePose.from_matrices(
                        bone_id=int(b.id),
                        index=b.index,
                        name=b.name,
                        parent_index=b.parent_index,
                        children=b.children,
                        local_matrix=locals_m[i],
                        global_matrix=worlds[i],
                        rest_matrix=worlds[i],
                        inverse_bind_matrix=ibm_list[i],
                        metadata={"source": "avatar_skeleton"},
                    )
                )

            coords = PoseCoordinateSystem.from_skeleton_metadata(
                skeleton.metadata.coordinate_system,
                skeleton.metadata.units,
                extra={"skeleton_runtime": skeleton.metadata.runtime_version},
            )
            rest_info = RestPoseInfo(kind=rest_kind, label=rest_kind.value)
            stats = compute_pose_statistics(
                bone_poses,
                parents,
                matrix_inversion_count=inversion_count,
            )
            pose = BindPose.create(
                tuple(bone_poses),
                name=name or f"bind:{skeleton.name}",
                coordinate_system=coords,
                rest_info=rest_info,
                bind_matrices=bind_set,
                statistics=stats,
                skeleton_name=skeleton.name,
                source_asset_id=source_asset_id or skeleton.metadata.source_asset_id,
            )

            if self.validate:
                PoseValidator().validate(pose).raise_if_invalid()

            if self.cache is not None:
                self.cache.put(key, pose)
            return pose
        except PoseFactoryError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PoseFactoryError(
                f"Failed to build bind pose: {exc}",
                code="POSE_FACTORY_CONVERT",
                details={"error": str(exc)},
            ) from exc

    def animation_pose_from_bind(self, bind: BindPose, *, name: str | None = None) -> AnimationPose:
        """Create a mutable :class:`AnimationPose` seeded from a bind pose."""
        return AnimationPose.from_pose(bind, name=name)

    def identity_bind(self, names: list[str], *, name: str = "identity_bind") -> BindPose:
        """Testing helper: identity chain bind pose."""
        eye = identity_matrix()
        bone_poses: list[BonePose] = []
        for i, nm in enumerate(names):
            parent = None if i == 0 else i - 1
            kids = (i + 1,) if i + 1 < len(names) else ()
            bone_poses.append(
                BonePose.from_matrices(
                    bone_id=i,
                    index=i,
                    name=nm,
                    parent_index=parent,
                    children=kids,
                    local_matrix=eye.copy(),
                    global_matrix=eye.copy(),
                    inverse_bind_matrix=eye.copy(),
                )
            )
        parents = [b.parent_index for b in bone_poses]
        stats = compute_pose_statistics(bone_poses, parents, matrix_inversion_count=0)
        pose = BindPose.create(
            tuple(bone_poses),
            name=name,
            rest_info=RestPoseInfo(kind=RestPoseKind.CUSTOM, label="identity"),
            statistics=stats,
        )
        if self.validate:
            PoseValidator().validate(pose).raise_if_invalid()
        return pose


# Alias matching the specification naming.
PoseFactory = BindPoseFactory

__all__ = ["BindPoseFactory", "PoseFactory"]
