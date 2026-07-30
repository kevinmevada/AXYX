"""Left/right mirroring for gait augmentation / research."""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget._quat import q_normalize
from motion_engine.rendering.avatar.retarget.types import JointSample, MotionPose, Quat, Vec3

_LR_SWAPS = (
    ("L", "R"),
    ("l", "r"),
    ("Left", "Right"),
    ("left", "right"),
    ("_l", "_r"),
    ("_L", "_R"),
)


def mirror_name(name: str) -> str:
    for a, b in _LR_SWAPS:
        if a in name:
            return name.replace(a, b, 1)
        if b in name:
            return name.replace(b, a, 1)
    return name


def mirror_translation(v: Vec3, *, axis: int = 0) -> Vec3:
    out = [float(v[0]), float(v[1]), float(v[2])]
    out[axis] = -out[axis]
    return (out[0], out[1], out[2])


def mirror_quat_x(q: Quat) -> Quat:
    """Mirror orientation across YZ plane (negate Y and Z of quat xyz)."""
    x, y, z, w = q_normalize(q)
    return q_normalize((x, -y, -z, w))


def mirror_pose(pose: MotionPose, *, axis: int = 0) -> MotionPose:
    """Swap L/R joint names and mirror translations/rotations."""
    joints: dict[str, JointSample] = {}
    for name, sample in pose.joints.items():
        mname = mirror_name(name)
        wp = sample.world_position
        joints[mname] = JointSample(
            name=mname,
            translation=mirror_translation(sample.translation, axis=axis),
            rotation_xyzw=mirror_quat_x(sample.rotation_xyzw),
            scale=sample.scale,
            world_position=mirror_translation(wp, axis=axis) if wp else None,
            valid=sample.valid,
        )
    root = pose.root_translation
    return MotionPose(
        joints=joints,
        time=pose.time,
        index=pose.index,
        root_translation=mirror_translation(root, axis=axis) if root else None,
        metadata={**dict(pose.metadata), "mirrored": True},
    )


__all__ = ["mirror_name", "mirror_translation", "mirror_quat_x", "mirror_pose"]
