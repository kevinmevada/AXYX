"""Camera profiles package for the rendering subsystem.

``motion_engine.camera`` remains the public clinical camera controller.
These profiles supply named defaults (FOV, damping, framing) without
replacing the existing controller API.
"""

from __future__ import annotations

from motion_engine.rendering.camera.profiles import (
    PROFILES,
    CameraProfile,
    get_camera_profile,
)

__all__ = ["CameraProfile", "PROFILES", "get_camera_profile"]
