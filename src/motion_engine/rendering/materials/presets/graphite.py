from __future__ import annotations

from motion_engine.colors import STUDIO_THEME
from motion_engine.rendering.materials.presets.base import make_preset

PRESET = make_preset(
    "graphite",
    STUDIO_THEME.bone,
    0.92,
    0.22,
    specular=0.55,
    specular_power=48.0,
)
