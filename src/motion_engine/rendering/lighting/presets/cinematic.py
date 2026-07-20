"""Cinematic lighting preset."""

from __future__ import annotations

from motion_engine.rendering.lighting.presets.base import LightDesc, LightingPreset

PRESET = LightingPreset(
    name="cinematic",
    lights=(
        LightDesc("key", (-1.8, -1.2, 2.5), (1.0, 0.92, 0.82), 0.70),
        LightDesc("fill", (1.5, -0.4, 1.4), (0.75, 0.82, 0.95), 0.18),
        LightDesc("rim", (0.3, 2.0, 1.3), (0.55, 0.70, 1.0), 0.35),
        LightDesc(
            "ambient", (0.0, 0.0, 1.0), (1.0, 1.0, 1.0), 0.10, light_type="headlight"
        ),
    ),
)
