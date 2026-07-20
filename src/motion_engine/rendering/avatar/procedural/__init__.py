"""Procedural metallic skeleton avatar package."""

from __future__ import annotations

from motion_engine.rendering.avatar.procedural.bone_geometry import (
    BoneProfile,
    build_unit_bone_template,
    merge_bone_meshes,
    profile_for_bone,
    radius_at,
    transform_bone,
)
from motion_engine.rendering.avatar.procedural.procedural_avatar import (
    ProceduralAvatar,
    ProceduralPoseFrame,
)

__all__ = [
    "BoneProfile",
    "build_unit_bone_template",
    "merge_bone_meshes",
    "profile_for_bone",
    "radius_at",
    "transform_bone",
    "ProceduralAvatar",
    "ProceduralPoseFrame",
]
