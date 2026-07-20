"""Avatar subsystem — swappable figures for the AXYX viewport."""

from __future__ import annotations

from motion_engine.rendering.avatar.avatar import Avatar
from motion_engine.rendering.avatar.avatar_loader import AvatarLoader, AvatarPackResolver
from motion_engine.rendering.avatar.avatar_manager import AvatarManager
from motion_engine.rendering.avatar.avatar_manifest import AvatarManifest
from motion_engine.rendering.avatar.avatar_renderer import AvatarRenderer
from motion_engine.rendering.avatar.bind_pose import BindPose
from motion_engine.rendering.avatar.digital_avatar import DigitalAvatar
from motion_engine.rendering.avatar.models import LoadedAvatar
from motion_engine.rendering.avatar.procedural import (
    ProceduralAvatar,
    ProceduralPoseFrame,
)
from motion_engine.rendering.avatar.registry import AvatarFactory, AvatarRegistry
from motion_engine.rendering.avatar.retarget import AvatarRetarget, AvatarRetargetProfile

__all__ = [
    "Avatar",
    "AvatarLoader",
    "AvatarPackResolver",
    "AvatarManager",
    "AvatarManifest",
    "AvatarRenderer",
    "BindPose",
    "DigitalAvatar",
    "LoadedAvatar",
    "ProceduralAvatar",
    "ProceduralPoseFrame",
    "AvatarRetarget",
    "AvatarRetargetProfile",
    "AvatarRegistry",
    "AvatarFactory",
]
