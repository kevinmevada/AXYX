"""Studio environment preset — Museum White empty field."""

from __future__ import annotations

from motion_engine.rendering.environment.presets.base import EnvironmentPreset

PRESET = EnvironmentPreset(
    name="studio",
    background=(1.0, 1.0, 1.0),
    floor_color=(1.0, 1.0, 1.0),
    edge_fade=False,
    show_grid=False,
    hdri_enabled=False,
    fog_enabled=False,
    infinity_floor=False,
    vignette=False,
    notes="Museum White — empty white field",
)
