from __future__ import annotations

from motion_engine.rendering.materials.presets.base import make_preset

PRESET = make_preset(
    "skin",
    (0.86, 0.68, 0.58),
    0.02,
    0.55,
    specular=0.15,
    specular_power=18.0,
)
