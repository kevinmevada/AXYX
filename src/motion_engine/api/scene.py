"""Stable scene / camera / environment API."""

from __future__ import annotations

from motion_engine.camera import CameraController, CameraPreset, CameraState
from motion_engine.rendering.camera import CameraProfile, get_camera_profile
from motion_engine.rendering.environment import (
    EnvironmentManager,
    EnvironmentPreset,
    StudioEnvironment,
    get_environment_preset,
)
from motion_engine.rendering.lighting import LightingManager
from motion_engine.rendering.materials import MaterialLibrary, PBRMaterial
from motion_engine.scene import Scene

__all__ = [
    "Scene",
    "CameraController",
    "CameraPreset",
    "CameraState",
    "CameraProfile",
    "get_camera_profile",
    "EnvironmentManager",
    "EnvironmentPreset",
    "StudioEnvironment",
    "get_environment_preset",
    "LightingManager",
    "MaterialLibrary",
    "PBRMaterial",
]
