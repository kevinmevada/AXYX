"""Bind / joint / bone offset solver for initial alignment."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import decompose_trs
from motion_engine.rendering.avatar.retarget._quat import q_conjugate, q_mul, q_normalize
from motion_engine.rendering.avatar.retarget.constants import QUAT_IDENTITY, VEC3_ZERO
from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.types import (
    BoneMapEntry,
    MotionPose,
    Quat,
    Vec3,
)


@dataclass(frozen=True, slots=True)
class BoneOffset:
    target: str
    rotation_xyzw: Quat = QUAT_IDENTITY
    translation: Vec3 = VEC3_ZERO


@dataclass
class OffsetTable:
    """Per-target offsets computed at session prepare."""

    by_target: dict[str, BoneOffset] = field(default_factory=dict)
    root_translation: Vec3 = VEC3_ZERO
    root_rotation_xyzw: Quat = QUAT_IDENTITY

    def rotation(self, target: str) -> Quat:
        o = self.by_target.get(target)
        return o.rotation_xyzw if o else QUAT_IDENTITY

    def translation(self, target: str) -> Vec3:
        o = self.by_target.get(target)
        return o.translation if o else VEC3_ZERO


class OffsetSolver:
    """Compute bind offsets that align source rest pose to avatar bind.

    Source rest and bind must be compared in the **same** coordinate space.
    When ``coords`` is provided, source rest rotations/translations are mapped
    into target space before the offset is computed.
    """

    def solve(
        self,
        entries: list[BoneMapEntry],
        source_rest: MotionPose,
        bind: BindPose,
        *,
        coords: CoordinateMapper | None = None,
    ) -> OffsetTable:
        table = OffsetTable()
        for entry in entries:
            src = source_rest.get(entry.source)
            if src is None:
                continue
            for target in entry.targets:
                if not bind.exists(target):
                    continue
                bone = bind.find(target)
                _, bind_q, _ = decompose_trs(bone.local_matrix)
                bind_q_t = (
                    float(bind_q[0]),
                    float(bind_q[1]),
                    float(bind_q[2]),
                    float(bind_q[3]),
                )
                # Map source rest into target bind space before differencing.
                src_q = q_normalize(src.rotation_xyzw)
                st = src.translation
                if coords is not None:
                    src_q = coords.map_quat(src_q)
                    st = coords.map_vector(st)
                # offset * mapped_source_rest ≈ bind  →  offset = bind * src^{-1}
                offset_q = q_normalize(q_mul(bind_q_t, q_conjugate(src_q)))
                bt = bone.translation
                offset_t = (bt[0] - st[0], bt[1] - st[1], bt[2] - st[2])
                table.by_target[target] = BoneOffset(
                    target=target,
                    rotation_xyzw=offset_q,
                    translation=offset_t,
                )
                if entry.copy_translation:
                    table.root_translation = offset_t
                    table.root_rotation_xyzw = offset_q
        return table

    def apply_rotation(self, source_q: Quat, offset: Quat) -> Quat:
        return q_normalize(q_mul(offset, source_q))


__all__ = ["BoneOffset", "OffsetTable", "OffsetSolver"]
