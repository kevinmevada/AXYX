"""AXYX rendering subsystem — environments, lighting, avatars, materials, effects.

This package is the long-term home for visualization before Digital Twin
integration. Public engine APIs in ``motion_engine.renderer``,
``motion_engine.viewer``, and ``motion_engine.bone_geometry`` remain stable
compatibility entry points.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.avatar import Avatar
from motion_engine.rendering.avatar.avatar_manager import AvatarManager
from motion_engine.rendering.avatar.procedural.procedural_avatar import (
    ProceduralAvatar,
)
from motion_engine.rendering.camera import CameraProfile, get_camera_profile
from motion_engine.rendering.context import FrameContext, RenderSettings, RenderingContext
from motion_engine.rendering.environment import (
    EnvironmentManager,
    StudioEnvironment,
)
from motion_engine.rendering.lifecycle import RenderLifecycle, RenderPhase
from motion_engine.rendering.lighting.lighting_manager import LightingManager
from motion_engine.rendering.materials.material_library import MaterialLibrary
from motion_engine.rendering.plugins import PluginRegistry
from motion_engine.rendering.quality import QualityProfile, get_quality
from motion_engine.rendering.rendergraph.render_graph import RenderGraph
from motion_engine.rendering.resources import ResourceManager
from motion_engine.rendering.scene import SceneGraph

__all__ = [
    "Avatar",
    "AvatarManager",
    "ProceduralAvatar",
    "StudioEnvironment",
    "EnvironmentManager",
    "LightingManager",
    "MaterialLibrary",
    "RenderGraph",
    "FrameContext",
    "RenderingContext",
    "RenderSettings",
    "ResourceManager",
    "SceneGraph",
    "RenderLifecycle",
    "RenderPhase",
    "PluginRegistry",
    "QualityProfile",
    "get_quality",
    "CameraProfile",
    "get_camera_profile",
]
