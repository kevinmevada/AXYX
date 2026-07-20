"""Lighting presets registry."""

from __future__ import annotations

import logging

from motion_engine.rendering.lighting.presets.base import (
    LightDesc,
    LightingPreset,
    apply_preset,
)
from motion_engine.rendering.lighting.presets import cinematic as _cinematic
from motion_engine.rendering.lighting.presets import clinical as _clinical
from motion_engine.rendering.lighting.presets import presentation as _presentation
from motion_engine.rendering.lighting.presets import studio as _studio

logger = logging.getLogger(__name__)

PRESETS: dict[str, LightingPreset] = {
    _studio.PRESET.name: _studio.PRESET,
    _clinical.PRESET.name: _clinical.PRESET,
    _presentation.PRESET.name: _presentation.PRESET,
    _cinematic.PRESET.name: _cinematic.PRESET,
}


def get_lighting_preset(name: str) -> LightingPreset:
    """Return preset by name; unknown → studio with a warning."""
    preset = PRESETS.get(name)
    if preset is None:
        logger.warning("Unknown lighting preset %r — using studio", name)
        return PRESETS["studio"]
    return preset


__all__ = [
    "LightDesc",
    "LightingPreset",
    "apply_preset",
    "PRESETS",
    "get_lighting_preset",
]
