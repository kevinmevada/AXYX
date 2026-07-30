"""Pose and weight blending."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.animation.exceptions import AnimationPlaybackError
from motion_engine.rendering.avatar.animation.interpolation import lerp_vec
from motion_engine.rendering.avatar.animation.pose_builder import rebuild_fk
from motion_engine.rendering.avatar.animation.quaternion import quat_slerp
from motion_engine.rendering.avatar.pose.matrix_utils import compose_trs, decompose_trs
from motion_engine.rendering.avatar.pose.pose import AnimationPose


def blend_poses(
    a: AnimationPose,
    b: AnimationPose,
    weight: float,
    *,
    name: str | None = None,
) -> AnimationPose:
    """Blend two animation poses (local TRS + FK).

    ``weight`` 0 → fully ``a``, 1 → fully ``b``. Bone sets must match by name.
    """
    w = float(np.clip(weight, 0.0, 1.0))
    if a.bone_count != b.bone_count:
        raise AnimationPlaybackError(
            "Pose bone counts differ",
            code="ANIM_BLEND_COUNT",
            details={"a": a.bone_count, "b": b.bone_count},
        )
    out = AnimationPose.from_pose(a, name=name or f"blend:{w:.3f}")
    for bone in out.bones:
        if not b.exists(bone.name):
            continue
        ba = a.find(bone.name)
        bb = b.find(bone.name)
        ta, qa, sa = decompose_trs(ba.local_matrix)
        tb, qb, sb = decompose_trs(bb.local_matrix)
        t = lerp_vec(ta, tb, w)
        q = quat_slerp(qa, qb, w)
        s = lerp_vec(sa, sb, w)
        out.set_local_matrix(bone.name, compose_trs(t, q, s))
    return rebuild_fk(out)


def crossfade_weight(elapsed: float, duration: float) -> float:
    """Smoothstep crossfade weight in ``[0, 1]``."""
    if duration <= 1e-9:
        return 1.0
    t = float(np.clip(elapsed / duration, 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


def blend_weights(weights: list[float]) -> list[float]:
    """Normalize a list of blend weights to sum to 1 (or empty → empty)."""
    arr = np.asarray(weights, dtype=np.float64)
    if arr.size == 0:
        return []
    arr = np.maximum(arr, 0.0)
    total = float(arr.sum())
    if total <= 1e-15:
        return [1.0 / len(weights)] * len(weights)
    return (arr / total).tolist()


__all__ = ["blend_poses", "crossfade_weight", "blend_weights"]
