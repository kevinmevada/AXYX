"""Clinical camera profile — default AXYX viewport."""

from __future__ import annotations

from motion_engine.rendering.camera.profiles.base import CameraProfile

PROFILE = CameraProfile(
    name="clinical",
    fov_deg=16.1,
    focal_length_mm=85.0,
    damping=0.18,
    framing_margin=0.74,
    near_clip=1.0,
    far_clip=100000.0,
    orbit_sensitivity=0.0042,
    pan_sensitivity=0.00085,
    zoom_sensitivity=0.0014,
    animation_seconds=0.42,
    fit_distance_factor=2.65,
    notes="Tight clinical framing, 85 mm feel",
)
