"""Environment package — floor, HDRI, atmosphere, reflections, presets."""

from __future__ import annotations

from motion_engine.rendering.environment.atmosphere import disable_fog
from motion_engine.rendering.environment.environment import StudioEnvironment
from motion_engine.rendering.environment.environment_manager import EnvironmentManager
from motion_engine.rendering.environment.floor import (
    build_flat_floor,
    build_warm_edge_rings,
    style_floor_actor,
)
from motion_engine.rendering.environment.hdri import (
    apply_environment_texture,
    build_studio_ibl_texture,
)
from motion_engine.rendering.environment.presets import (
    EnvironmentPreset,
    get_environment_preset,
)
from motion_engine.rendering.environment.reflections import FloorReflectionParams

__all__ = [
    "StudioEnvironment",
    "EnvironmentManager",
    "EnvironmentPreset",
    "get_environment_preset",
    "disable_fog",
    "build_flat_floor",
    "build_warm_edge_rings",
    "style_floor_actor",
    "apply_environment_texture",
    "build_studio_ibl_texture",
    "FloorReflectionParams",
]
