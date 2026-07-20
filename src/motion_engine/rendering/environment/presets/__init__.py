"""Environment presets registry."""

from __future__ import annotations

import logging

from motion_engine.rendering.environment.presets import dark_lab as _dark_lab
from motion_engine.rendering.environment.presets import infinity as _infinity
from motion_engine.rendering.environment.presets import presentation as _presentation
from motion_engine.rendering.environment.presets import studio as _studio
from motion_engine.rendering.environment.presets.base import EnvironmentPreset

logger = logging.getLogger(__name__)

PRESETS: dict[str, EnvironmentPreset] = {
    p.name: p
    for p in (
        _studio.PRESET,
        _infinity.PRESET,
        _dark_lab.PRESET,
        _presentation.PRESET,
    )
}


def get_environment_preset(name: str) -> EnvironmentPreset:
    """Return preset by name; unknown → studio with a warning."""
    preset = PRESETS.get(name)
    if preset is None:
        logger.warning("Unknown environment preset %r — using studio", name)
        return PRESETS["studio"]
    return preset


__all__ = ["EnvironmentPreset", "PRESETS", "get_environment_preset"]
