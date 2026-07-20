"""Cinematic camera profile."""

from __future__ import annotations

from motion_engine.rendering.camera.profiles.base import CameraProfile

PROFILE = CameraProfile(
    name="cinematic",
    fov_deg=14.0,
    focal_length_mm=100.0,
    damping=0.28,
    framing_margin=0.68,
    near_clip=1.0,
    far_clip=120000.0,
    orbit_sensitivity=0.0028,
    pan_sensitivity=0.0005,
    zoom_sensitivity=0.0010,
    animation_seconds=0.65,
    fit_distance_factor=2.40,
    notes="Long-lens cinematic feel",
)
