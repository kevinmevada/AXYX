"""Shared lighting preset types."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LightDesc:
    role: str
    position: tuple[float, float, float]
    color: tuple[float, float, float]
    intensity: float
    positional: bool = False
    light_type: str | None = None


@dataclass(frozen=True, slots=True)
class LightingPreset:
    name: str
    lights: tuple[LightDesc, ...]


def apply_preset(plotter: Any, preset: LightingPreset) -> dict[str, Any]:
    """Apply a lighting preset; never raises to callers."""
    handles: dict[str, Any] = {}
    if plotter is None:
        return handles
    try:
        import pyvista as pv

        plotter.remove_all_lights()
        for desc in preset.lights:
            if desc.light_type == "headlight":
                light = pv.Light(light_type="headlight", intensity=desc.intensity)
            else:
                light = pv.Light(
                    position=desc.position,
                    focal_point=(0.0, 0.0, 0.55),
                    color=desc.color,
                    intensity=desc.intensity,
                    positional=desc.positional,
                )
            plotter.add_light(light)
            handles[desc.role] = light
        try:
            plotter.disable_shadows()
        except Exception:
            pass
    except Exception:
        logger.warning("Failed applying lighting preset %s", preset.name, exc_info=True)
    return handles


__all__ = ["LightDesc", "LightingPreset", "apply_preset"]
