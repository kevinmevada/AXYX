"""Material presets registry."""

from __future__ import annotations

import logging

from motion_engine.rendering.materials.presets import ceramic as _ceramic
from motion_engine.rendering.materials.presets import floor as _floor
from motion_engine.rendering.materials.presets import glass as _glass
from motion_engine.rendering.materials.presets import graphite as _graphite
from motion_engine.rendering.materials.presets import skin as _skin
from motion_engine.rendering.materials.presets import titanium as _titanium
from motion_engine.rendering.materials.presets.base import MaterialPreset, make_preset

logger = logging.getLogger(__name__)

PRESETS: dict[str, MaterialPreset] = {
    p.key: p
    for p in (
        _titanium.PRESET,
        _ceramic.PRESET,
        _graphite.PRESET,
        _skin.PRESET,
        _glass.PRESET,
        _floor.PRESET,
    )
}


def get_material_preset(name: str) -> MaterialPreset:
    preset = PRESETS.get(name)
    if preset is None:
        logger.warning("Unknown material %r — using graphite", name)
        return PRESETS["graphite"]
    return preset


__all__ = ["MaterialPreset", "make_preset", "PRESETS", "get_material_preset"]
