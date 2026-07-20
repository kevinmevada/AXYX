"""Environment manager — applies named environment presets."""

from __future__ import annotations

import logging
from typing import Any

from motion_engine.rendering.environment.atmosphere import disable_fog
from motion_engine.rendering.environment.environment import StudioEnvironment
from motion_engine.rendering.environment.presets import (
    EnvironmentPreset,
    get_environment_preset,
)

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Owns the active environment preset and applies it to a plotter.

    Wraps :class:`StudioEnvironment` so callers switch profiles by name
    without duplicating IBL / atmosphere setup.
    """

    def __init__(self, preset: str = "studio") -> None:
        self.preset_name = preset
        self._studio = StudioEnvironment()
        self._active: EnvironmentPreset = get_environment_preset(preset)

    @property
    def active(self) -> EnvironmentPreset:
        return self._active

    @property
    def studio(self) -> StudioEnvironment:
        """Underlying studio environment (IBL state)."""
        return self._studio

    def set_preset(self, name: str) -> EnvironmentPreset:
        self._active = get_environment_preset(name)
        self.preset_name = self._active.name
        logger.info("Environment preset → %s", self.preset_name)
        return self._active

    def configure_renderer(self, plotter: Any) -> None:
        """Apply the active preset to ``plotter`` (graceful on failure)."""
        if plotter is None:
            return
        preset = self._active
        try:
            if not preset.fog_enabled:
                disable_fog(plotter.renderer)
        except Exception:
            logger.debug("Fog configure failed", exc_info=True)

        if not preset.hdri_enabled:
            logger.debug("HDRI disabled for preset %s", preset.name)
            return

        # Reuse StudioEnvironment IBL path; missing HDRI never crashes.
        try:
            self._studio.configure_renderer(plotter)
        except Exception:
            logger.warning(
                "Environment configure failed for %s — continuing without IBL",
                preset.name,
                exc_info=True,
            )


__all__ = ["EnvironmentManager", "EnvironmentPreset"]
