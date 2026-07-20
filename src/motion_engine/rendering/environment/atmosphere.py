"""Atmosphere / fog helpers."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def disable_fog(renderer: Any, *, ambient: tuple[float, float, float] = (0.28, 0.28, 0.29)) -> None:
    """Turn fog off and set a bright studio ambient."""
    try:
        if hasattr(renderer, "SetUseFog"):
            renderer.SetUseFog(False)
        elif hasattr(renderer, "UseFogOff"):
            renderer.UseFogOff()
        renderer.SetAmbient(*ambient)
        renderer.SetTwoSidedLighting(True)
    except Exception:
        logger.debug("Atmosphere setup skipped", exc_info=True)


__all__ = ["disable_fog"]
