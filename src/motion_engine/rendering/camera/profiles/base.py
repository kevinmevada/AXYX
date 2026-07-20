"""Camera profile descriptors — FOV, damping, framing, clipping, speed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CameraProfile:
    """Named camera behaviour profile for clinical / presentation / cinematic use."""

    name: str
    fov_deg: float = 16.1
    focal_length_mm: float = 85.0
    damping: float = 0.18
    framing_margin: float = 0.74
    near_clip: float = 1.0
    far_clip: float = 100000.0
    orbit_sensitivity: float = 0.0042
    pan_sensitivity: float = 0.00085
    zoom_sensitivity: float = 0.0014
    animation_seconds: float = 0.42
    fit_distance_factor: float = 2.65
    notes: str = ""
