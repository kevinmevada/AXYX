"""Glow / vignette effect hooks."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

VIGNETTE_STRENGTH: float = 0.10


def ensure_vignette(plotter: Any, *, strength: float = VIGNETTE_STRENGTH) -> bool:
    """Optional screen-space vignette — returns True if installed.

    Implementation stays in the PyVista renderer for Phase-0; this module
    documents the extension point for future bloom / glow passes.
    """
    _ = plotter, strength
    logger.debug("ensure_vignette extension point (handled by backend)")
    return False


__all__ = ["VIGNETTE_STRENGTH", "ensure_vignette"]
