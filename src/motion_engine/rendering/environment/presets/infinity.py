"""Infinity-floor environment preset."""

from __future__ import annotations

from motion_engine.rendering.environment.presets.base import EnvironmentPreset

PRESET = EnvironmentPreset(
    name="infinity",
    background=(0.94, 0.94, 0.95),
    floor_color=(0.94, 0.94, 0.95),
    edge_fade=False,
    show_grid=False,
    hdri_enabled=True,
    fog_enabled=False,
    infinity_floor=True,
    vignette=False,
    notes="Seamless infinity cyc",
)
