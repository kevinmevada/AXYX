"""Pose editing helpers for skinning debug (FK after local rotate)."""

from __future__ import annotations

import numpy as np

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.matrix_utils import compose_trs, decompose_trs
from motion_engine.rendering.avatar.pose.pose import AnimationPose, BonePose
from motion_engine.rendering.avatar.pose.transform_propagation import (
    propagate_world_transforms,
)


def _axis_rotation_matrix(axis: str, angle_deg: float) -> np.ndarray:
    axis = axis.lower()
    a = np.deg2rad(float(angle_deg))
    c, s = np.cos(a), np.sin(a)
    r = np.eye(4, dtype=np.float64)
    if axis == "x":
        r[1, 1], r[1, 2] = c, -s
        r[2, 1], r[2, 2] = s, c
    elif axis == "y":
        r[0, 0], r[0, 2] = c, s
        r[2, 0], r[2, 2] = -s, c
    elif axis == "z":
        r[0, 0], r[0, 1] = c, -s
        r[1, 0], r[1, 1] = s, c
    else:
        raise ValueError(f"axis must be x|y|z, got {axis!r}")
    return r


def rebuild_animation_fk(pose: AnimationPose) -> AnimationPose:
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


def rotate_bone(
    pose: AnimationPose,
    bone: str | int,
    *,
    axis: str = "z",
    angle: float = 0.0,
    absolute: bool = False,
) -> AnimationPose:
    """Return a new AnimationPose with ``bone`` rotated, then full FK.

    Args:
        pose: Source animation pose (not mutated).
        bone: Bone name or index.
        axis: ``x`` / ``y`` / ``z``.
        angle: Degrees.
        absolute: If True, replace local rotation; if False, post-multiply.
    """
    # Clone first so we own buffers.
    anim = AnimationPose.from_pose(pose)
    b = anim.find(bone)
    rot = _axis_rotation_matrix(axis, angle)
    if absolute:
        t, _q, s = decompose_trs(b.local_matrix)
        new_local = compose_trs(t, (0, 0, 0, 1), s) @ rot
    else:
        new_local = b.local_matrix @ rot
    anim.set_local_matrix(bone, new_local)
    return rebuild_animation_fk(anim)


def reset_to_bind(bind: BindPose) -> AnimationPose:
    """Fresh independently owned animation pose seeded from bind."""
    return AnimationPose.from_pose(bind)


__all__ = ["rebuild_animation_fk", "rotate_bone", "reset_to_bind"]
