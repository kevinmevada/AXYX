"""Presentation camera profile."""

from __future__ import annotations

from motion_engine.rendering.camera.profiles.base import CameraProfile

PROFILE = CameraProfile(
    name="presentation",
    fov_deg=18.0,
    focal_length_mm=75.0,
    damping=0.22,
    framing_margin=0.70,
    near_clip=1.0,
    far_clip=100000.0,
    orbit_sensitivity=0.0035,
    pan_sensitivity=0.0007,
    zoom_sensitivity=0.0012,
    animation_seconds=0.50,
    fit_distance_factor=2.55,
    notes="Smooth transitions for demos / keynotes",
)
