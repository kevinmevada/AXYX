from __future__ import annotations

from motion_engine.colors import STUDIO_THEME
from motion_engine.rendering.materials.presets.base import make_preset

PRESET = make_preset(
    "floor",
    STUDIO_THEME.ground,
    0.08,
    0.72,
    specular=0.08,
    specular_power=12.0,
)
