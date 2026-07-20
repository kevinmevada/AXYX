"""Environment preset descriptors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EnvironmentPreset:
    """Named environment profile loaded by the renderer."""

    name: str
    background: tuple[float, float, float] = (0.96, 0.96, 0.97)
    floor_color: tuple[float, float, float] = (0.957, 0.957, 0.965)
    edge_fade: bool = True
    show_grid: bool = True
    hdri_enabled: bool = True
    fog_enabled: bool = False
    infinity_floor: bool = False
    vignette: bool = False
    notes: str = ""
