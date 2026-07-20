"""Immutable BindPose — canonical undeformed reference pose."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from motion_engine.rendering.avatar.pose.bind_matrix import BindMatrixSet
from motion_engine.rendering.avatar.pose.constants import DEFAULT_POSE_NAME, RUNTIME_VERSION
from motion_engine.rendering.avatar.pose.coordinate_system import PoseCoordinateSystem
from motion_engine.rendering.avatar.pose.exceptions import PoseBoneNotFoundError
from motion_engine.rendering.avatar.pose.pose import BonePose, Pose
from motion_engine.rendering.avatar.pose.pose_statistics import PoseStatistics
from motion_engine.rendering.avatar.pose.rest_pose import RestPoseInfo
from motion_engine.rendering.avatar.pose.types import PoseKind

if TYPE_CHECKING:
    from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton


@dataclass(frozen=True, slots=True)
class BindPose(Pose):
    """Immutable bind / rest pose derived from :class:`AvatarSkeleton`.

    Owns local/global/rest transforms, inverse bind matrices, coordinate
    metadata, and statistics. Does **not** own animation, IK, retarget, or
    rendering state.

    The skeleton structure remains in :class:`AvatarSkeleton`; this object is
    pure **state** (the reference pose) and never mutates the skeleton.
    """

    _name: str
    _bones: tuple[BonePose, ...]
    _by_name: dict[str, int]
    coordinate_system: PoseCoordinateSystem
    rest_info: RestPoseInfo
    bind_matrices: BindMatrixSet
    statistics: PoseStatistics
    skeleton_name: str = ""
    runtime_version: str = RUNTIME_VERSION
    source_asset_id: str = ""

    @property
    def kind(self) -> PoseKind:
        return PoseKind.BIND

    @property
    def name(self) -> str:
        return self._name

    @property
    def bone_count(self) -> int:
        return len(self._bones)

    @property
    def bones(self) -> tuple[BonePose, ...]:
        return self._bones

    def find(self, key: str | int) -> BonePose:
        if isinstance(key, int):
            if 0 <= key < len(self._bones):
                return self._bones[key]
            raise PoseBoneNotFoundError(key)
        try:
            return self._bones[self._by_name[key]]
        except KeyError as exc:
            raise PoseBoneNotFoundError(key) from exc

    def exists(self, key: str | int) -> bool:
        if isinstance(key, int):
            return 0 <= key < len(self._bones)
        return key in self._by_name

    @classmethod
    def create(
        cls,
        bones: tuple[BonePose, ...],
        *,
        name: str = DEFAULT_POSE_NAME,
        coordinate_system: PoseCoordinateSystem | None = None,
        rest_info: RestPoseInfo | None = None,
        bind_matrices: BindMatrixSet | None = None,
        statistics: PoseStatistics | None = None,
        skeleton_name: str = "",
        source_asset_id: str = "",
    ) -> BindPose:
        """Construct an immutable bind pose from bone samples."""
        by_name = {b.name: b.index for b in bones}
        if bind_matrices is None:
            from motion_engine.rendering.avatar.pose.bind_matrix import BindMatrixSet

            bind_matrices = BindMatrixSet(
                rest_world=tuple(b.rest_matrix for b in bones),
                inverse_bind=tuple(b.inverse_bind_matrix for b in bones),
            )
        if statistics is None:
            from motion_engine.rendering.avatar.pose.pose_statistics import (
                compute_pose_statistics,
            )

            parents = [b.parent_index for b in bones]
            statistics = compute_pose_statistics(bones, parents)
        return cls(
            _name=name,
            _bones=bones,
            _by_name=by_name,
            coordinate_system=coordinate_system or PoseCoordinateSystem(),
            rest_info=rest_info or RestPoseInfo(),
            bind_matrices=bind_matrices,
            statistics=statistics,
            skeleton_name=skeleton_name,
            source_asset_id=source_asset_id,
        )


__all__ = ["BindPose"]
