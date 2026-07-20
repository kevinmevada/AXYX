from __future__ import annotations

from motion_engine.rendering.materials.presets.base import make_preset

PRESET = make_preset(
    "glass",
    (0.85, 0.90, 0.95),
    0.0,
    0.05,
    specular=0.85,
    specular_power=96.0,
)
