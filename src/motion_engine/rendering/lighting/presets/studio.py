"""Studio lighting preset — soft key/fill for pale floor."""

from __future__ import annotations

from motion_engine.rendering.lighting.presets.base import LightDesc, LightingPreset

PRESET = LightingPreset(
    name="studio",
    lights=(
        LightDesc("key", (-1.5, -1.0, 2.6), (1.0, 0.99, 0.97), 0.48),
        LightDesc("fill", (1.2, -0.3, 1.5), (0.95, 0.96, 0.98), 0.22),
        LightDesc(
            "ambient", (0.0, 0.0, 1.0), (1.0, 1.0, 1.0), 0.18, light_type="headlight"
        ),
    ),
)
