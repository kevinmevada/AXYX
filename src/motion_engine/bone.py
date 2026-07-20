"""
Bone primitives for Human Reconstruction.

The production :class:`~motion_engine.skeleton.Bone` implementation currently
lives in :mod:`motion_engine.skeleton` (Skeleton Builder phase). This module
re-exports it for a stable import path and will host bone-specific helpers
(cross-section metadata, inertia proxies, OpenSim/URDF adapters) later.
"""

from __future__ import annotations

from motion_engine.skeleton import Bone

__all__ = ["Bone"]

# TODO: BoneInertia, BoneGeometry, and export adapters (OpenSim / URDF / glTF).
