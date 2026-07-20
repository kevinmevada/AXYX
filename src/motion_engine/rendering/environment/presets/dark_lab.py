"""Dark lab environment preset."""

from __future__ import annotations

from motion_engine.rendering.environment.presets.base import EnvironmentPreset

PRESET = EnvironmentPreset(
    name="dark_lab",
    background=(0.08, 0.09, 0.11),
    floor_color=(0.12, 0.13, 0.15),
    edge_fade=True,
    show_grid=True,
    hdri_enabled=False,
    fog_enabled=False,
    infinity_floor=False,
    vignette=True,
    notes="Low-key clinical lab",
)
