"""Build AnimationPose from bind pose + sampled clip TRS."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.animation.track_sampler import ClipSample
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import compose_trs, decompose_trs
from motion_engine.rendering.avatar.pose.pose import AnimationPose, BonePose
from motion_engine.rendering.avatar.pose.transform_propagation import (
    propagate_world_transforms,
)


def rebuild_fk(pose: AnimationPose) -> AnimationPose:
    """Recompute world matrices from locals (parent-before-child)."""
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


class PoseBuilder:
    """Apply sparse clip samples onto a bind-seeded AnimationPose + FK."""

    def build(
        self,
        bind: BindPose,
        sample: ClipSample,
        *,
        name: str | None = None,
    ) -> AnimationPose:
        anim = AnimationPose.from_pose(bind, name=name or f"anim@{sample.time:.4f}")
        for bone_name, trs in sample.bones.items():
            if not anim.exists(bone_name):
                continue
            bone = anim.find(bone_name)
            t, q, s = decompose_trs(bone.local_matrix)
            if trs.translation is not None:
                t = np.asarray(trs.translation, dtype=np.float64)
            if trs.rotation_xyzw is not None:
                q = np.asarray(trs.rotation_xyzw, dtype=np.float64)
            if trs.scale is not None:
                s = np.asarray(trs.scale, dtype=np.float64)
            anim.set_local_matrix(bone_name, compose_trs(t, q, s))
        return rebuild_fk(anim)


__all__ = ["PoseBuilder", "rebuild_fk"]
