"""
Pose primitives for Human Reconstruction.

The production :class:`~motion_engine.skeleton.Pose` implementation currently
lives in :mod:`motion_engine.skeleton`. This module re-exports it for a stable
import path and will own pose blending / retarget buffers later.
"""

from __future__ import annotations

from motion_engine.skeleton import Pose

__all__ = ["Pose"]

# TODO: PoseSequence, pose interpolation, and retarget buffers.
