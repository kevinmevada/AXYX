"""Clinical lighting preset."""

from __future__ import annotations

from motion_engine.rendering.lighting.presets.base import LightDesc, LightingPreset

PRESET = LightingPreset(
    name="clinical",
    lights=(
        LightDesc("key", (-1.0, -1.2, 2.4), (1.0, 1.0, 1.0), 0.55),
        LightDesc("fill", (1.0, 0.5, 1.8), (0.95, 0.97, 1.0), 0.35),
        LightDesc(
            "ambient", (0.0, 0.0, 1.0), (1.0, 1.0, 1.0), 0.22, light_type="headlight"
        ),
    ),
)
