"""Pose sampling helpers for skinning (bind vs animation)."""

from __future__ import annotations

from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose, Pose
from motion_engine.rendering.avatar.skinning.exceptions import SkinningValidationError


def resolve_pose(*, bind: BindPose | None = None, animation: Pose | None = None) -> Pose:
    """Select the active pose for skinning (animation overrides bind)."""
    if animation is not None:
        return animation
    if bind is not None:
        return bind
    raise SkinningValidationError("No pose provided for skinning", code="SKIN_NO_POSE")


def ensure_animation_from_bind(bind: BindPose) -> AnimationPose:
    """Create an independently owned animation pose seeded from bind."""
    return AnimationPose.from_pose(bind)


__all__ = ["resolve_pose", "ensure_animation_from_bind"]
