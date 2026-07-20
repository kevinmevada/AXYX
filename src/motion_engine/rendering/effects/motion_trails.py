"""Motion-trail effect hooks (disabled by default — Phase-0)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MotionTrails:
    """Reserved for gait motion trails — no-op until enabled."""

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    def update(self, frame: Any) -> None:
        if not self.enabled:
            return
        _ = frame
        logger.debug("MotionTrails.update stub")

    def render(self, backend: Any) -> None:
        if not self.enabled:
            return
        _ = backend


__all__ = ["MotionTrails"]
