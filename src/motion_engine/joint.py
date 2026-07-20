"""
Joint primitives for Human Reconstruction.

The production :class:`~motion_engine.skeleton.Joint` implementation currently
lives in :mod:`motion_engine.skeleton`. This module re-exports it for a stable
import path and will own joint DOF metadata / robotics joint types later.
"""

from __future__ import annotations

from motion_engine.skeleton import Joint

__all__ = ["Joint"]

# TODO: JointDOF, JointLimits, and humanoid-robot joint type adapters.
