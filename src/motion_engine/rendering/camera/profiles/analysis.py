"""Analysis camera profile — wider, faster for measurement work."""

from __future__ import annotations

from motion_engine.rendering.camera.profiles.base import CameraProfile

PROFILE = CameraProfile(
    name="analysis",
    fov_deg=28.0,
    focal_length_mm=45.0,
    damping=0.10,
    framing_margin=0.90,
    near_clip=0.5,
    far_clip=100000.0,
    orbit_sensitivity=0.0070,
    pan_sensitivity=0.0015,
    zoom_sensitivity=0.0022,
    animation_seconds=0.28,
    fit_distance_factor=3.1,
    notes="Wider FOV for measurement / overlays",
)
