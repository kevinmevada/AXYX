"""Presentation environment preset."""

from __future__ import annotations

from motion_engine.rendering.environment.presets.base import EnvironmentPreset

PRESET = EnvironmentPreset(
    name="presentation",
    background=(0.98, 0.98, 0.99),
    floor_color=(0.97, 0.97, 0.98),
    edge_fade=True,
    show_grid=False,
    hdri_enabled=True,
    fog_enabled=False,
    infinity_floor=False,
    vignette=False,
    notes="Clean keynote / presentation stage",
)
