"""
Compatibility shim for procedural bone meshes.

Canonical implementation:
``motion_engine.rendering.avatar.procedural.bone_geometry``

This module preserves historical imports:
``from motion_engine.bone_geometry import transform_bone, ...``
"""

from __future__ import annotations

from motion_engine.rendering.avatar.procedural.bone_geometry import (
    BoneProfile,
    build_unit_bone_template,
    merge_bone_meshes,
    profile_for_bone,
    radius_at,
    transform_bone,
)

__all__ = [
    "BoneProfile",
    "build_unit_bone_template",
    "merge_bone_meshes",
    "profile_for_bone",
    "radius_at",
    "transform_bone",
]
