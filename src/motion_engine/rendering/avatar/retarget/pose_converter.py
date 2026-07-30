"""Convert mapped local TRS into AnimationPose without mutating bind/skeleton."""

from __future__ import annotations

from typing import Mapping

import numpy as np

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import compose_trs, decompose_trs
from motion_engine.rendering.avatar.pose.pose import AnimationPose, BonePose
from motion_engine.rendering.avatar.pose.transform_propagation import propagate_world_transforms
from motion_engine.rendering.avatar.retarget.types import Quat, Vec3


class PoseConverter:
    """Build AnimationPose from sparse target local transforms + bind seed."""

    def convert(
        self,
        bind: BindPose,
        locals_q: Mapping[str, Quat],
        locals_t: Mapping[str, Vec3] | None = None,
        *,
        name: str = "retarget",
    ) -> AnimationPose:
        anim = AnimationPose.from_pose(bind, name=name)
        locals_t = locals_t or {}
        for bone_name, q in locals_q.items():
            if not anim.exists(bone_name):
                continue
            bone = anim.find(bone_name)
            t, _, s = decompose_trs(bone.local_matrix)
            if bone_name in locals_t:
                t = np.asarray(locals_t[bone_name], dtype=np.float64)
            q_arr = np.asarray(q, dtype=np.float64)
            anim.set_local_matrix(bone_name, compose_trs(t, q_arr, s))
        return self.rebuild_fk(anim)

    def rebuild_fk(self, pose: AnimationPose) -> AnimationPose:
        locals_m = [b.local_matrix.copy() for b in pose.bones]
        parents = [b.parent_index for b in pose.bones]
        worlds = list(propagate_world_transforms(locals_m, parents).world_matrices)
        bones: list[BonePose] = []
        for i, b in enumerate(pose.bones):
            bones.append(
                BonePose.from_matrices(
                    bone_id=b.bone_id,
                    index=b.index,
                    name=b.name,
                    parent_index=b.parent_index,
                    children=b.children,
                    local_matrix=locals_m[i],
                    global_matrix=worlds[i],
                    rest_matrix=b.rest_matrix,
                    inverse_bind_matrix=b.inverse_bind_matrix,
                    metadata=dict(b.metadata),
                )
            )
        return AnimationPose(_name=pose.name, _bones=bones)


__all__ = ["PoseConverter"]
