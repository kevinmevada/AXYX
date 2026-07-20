"""
Animation architecture for the Visualization Engine.

Defines interfaces for timelines, animators, and optional interpolation.
Concrete playback currently lives in :class:`~motion_engine.viewer.SkeletonViewer`.

Canonical companions (imported for a single animation surface):

* :class:`~motion_engine.timeline.Timeline`
* :class:`~motion_engine.playback.PlaybackController`
* :class:`Animator`
* :class:`FrameInterpolator`
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from motion_engine.playback import PlaybackController
from motion_engine.timeline import Timeline

if TYPE_CHECKING:
    from motion_engine.skeleton import Pose, Skeleton

__all__ = [
    "Animator",
    "DiscreteSkeletonAnimator",
    "FrameInterpolator",
    "PlaybackController",
    "Timeline",
]


class Animator(ABC):
    """Produces poses over time for a skeleton."""

    @abstractmethod
    def pose_at(self, frame_index: int) -> Pose:
        """Return the pose for ``frame_index``."""


class FrameInterpolator(ABC):
    """Optional continuous-time pose interpolator.

    TODO: Implement SLERP / LERP between discrete mocap frames for slow-mo.
    """

    @abstractmethod
    def interpolate(self, skeleton: Skeleton, time_seconds: float) -> Pose:
        """Return an interpolated pose at an arbitrary time."""


class DiscreteSkeletonAnimator(Animator):
    """Nearest-frame animator over an existing :class:`Skeleton` pose list."""

    def __init__(self, skeleton: Skeleton) -> None:
        self.skeleton = skeleton

    def pose_at(self, frame_index: int) -> Pose:
        return self.skeleton.get_pose(frame_index)


# TODO: BlendTreeAnimator, RetargetAnimator, RoboticsJointAnimator
