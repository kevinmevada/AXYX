"""Presentation lighting preset."""

from __future__ import annotations

from motion_engine.rendering.lighting.presets.base import LightDesc, LightingPreset

PRESET = LightingPreset(
    name="presentation",
    lights=(
        LightDesc("key", (-1.4, -1.0, 2.8), (1.0, 0.98, 0.95), 0.65),
        LightDesc("fill", (1.3, -0.2, 1.6), (0.92, 0.94, 1.0), 0.30),
        LightDesc("rim", (0.2, 1.6, 1.4), (0.80, 0.88, 1.0), 0.20),
        LightDesc(
            "ambient", (0.0, 0.0, 1.0), (1.0, 1.0, 1.0), 0.15, light_type="headlight"
        ),
    ),
)
