from __future__ import annotations

from motion_engine.colors import STUDIO_THEME
from motion_engine.rendering.materials.presets.base import make_preset

PRESET = make_preset("titanium", STUDIO_THEME.bone_highlight, 0.85, 0.28, specular=0.45, specular_power=40.0)
