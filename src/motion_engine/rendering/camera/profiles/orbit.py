"""Free orbit camera profile."""

from __future__ import annotations

from motion_engine.rendering.camera.profiles.base import CameraProfile

PROFILE = CameraProfile(
    name="orbit",
    fov_deg=22.0,
    focal_length_mm=60.0,
    damping=0.12,
    framing_margin=0.82,
    near_clip=1.0,
    far_clip=100000.0,
    orbit_sensitivity=0.0060,
    pan_sensitivity=0.0012,
    zoom_sensitivity=0.0018,
    animation_seconds=0.35,
    fit_distance_factor=2.9,
    notes="Faster orbit / wider FOV for exploration",
)
