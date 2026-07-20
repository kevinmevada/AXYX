from __future__ import annotations

from motion_engine.colors import STUDIO_THEME
from motion_engine.rendering.materials.presets.base import make_preset

PRESET = make_preset(
    "ceramic",
    STUDIO_THEME.joint,
    0.08,
    0.28,
    specular=0.55,
    specular_power=64.0,
)
