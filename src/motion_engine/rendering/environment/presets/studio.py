"""Studio environment preset — light photography look."""

from __future__ import annotations

from motion_engine.rendering.environment.presets.base import EnvironmentPreset

PRESET = EnvironmentPreset(
    name="studio",
    background=(0.96, 0.96, 0.97),
    floor_color=(0.957, 0.957, 0.965),
    edge_fade=True,
    show_grid=True,
    hdri_enabled=True,
    fog_enabled=False,
    infinity_floor=False,
    vignette=False,
    notes="Light photography studio",
)
