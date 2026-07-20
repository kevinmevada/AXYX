"""Studio environment orchestration — floor, grid context, IBL, atmosphere."""

from __future__ import annotations

import logging
from typing import Any

from motion_engine.rendering.environment.atmosphere import disable_fog
from motion_engine.rendering.environment.hdri import (
    apply_environment_texture,
    build_studio_ibl_texture,
)

logger = logging.getLogger(__name__)


class StudioEnvironment:
    """High-level environment setup for the light photography studio."""

    def __init__(self) -> None:
        self._ibl_ready = False

    def configure_renderer(self, plotter: Any) -> None:
        """Apply atmosphere + IBL to an initialized plotter."""
        if plotter is None:
            return
        try:
            disable_fog(plotter.renderer)
        except Exception:
            logger.debug("Fog disable failed", exc_info=True)
        if self._ibl_ready:
            return
        try:
            import pyvista as pv

            tex = build_studio_ibl_texture(pv)
        except Exception:
            logger.debug("PyVista IBL build failed", exc_info=True)
            tex = None
        if apply_environment_texture(plotter, tex):
            self._ibl_ready = True
            logger.info("Studio IBL environment texture installed")


__all__ = ["StudioEnvironment"]
