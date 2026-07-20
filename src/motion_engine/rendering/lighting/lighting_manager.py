"""Lighting manager — owns studio light rig handles + presets."""

from __future__ import annotations

import logging
from typing import Any

from motion_engine.rendering.lighting.presets import apply_preset, get_lighting_preset

logger = logging.getLogger(__name__)


class LightingManager:
    """Applies and tracks the studio light rig via named presets."""

    def __init__(self, preset: str = "studio") -> None:
        self._lights: dict[str, Any] = {}
        self.enabled = True
        self.preset_name = preset

    @property
    def lights(self) -> dict[str, Any]:
        return self._lights

    def set_preset(self, name: str) -> None:
        self.preset_name = name
        logger.info("Lighting preset → %s", name)

    def setup(self, plotter: Any, preset: str | None = None) -> None:
        """Build the light rig on ``plotter``."""
        if not self.enabled:
            try:
                plotter.remove_all_lights()
            except Exception:
                pass
            self._lights = {}
            return
        name = preset or self.preset_name
        self.preset_name = name
        self._lights = apply_preset(plotter, get_lighting_preset(name))
        logger.debug("LightingManager setup preset=%s (%d)", name, len(self._lights))


__all__ = ["LightingManager"]
