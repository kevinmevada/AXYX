"""Helpers that submit avatar drawables to a render backend."""

from __future__ import annotations

import logging
from typing import Any

from motion_engine.rendering.avatar.avatar import Avatar

logger = logging.getLogger(__name__)


class AvatarRenderer:
    """Delegates to ``Avatar.render`` — keeps backend details out of managers."""

    def draw(self, avatar: Avatar, backend: Any) -> None:
        """Render ``avatar`` via ``backend`` with error isolation."""
        try:
            avatar.render(backend)
        except Exception:
            logger.exception("Avatar render failed for %r", avatar.name)
            raise


__all__ = ["AvatarRenderer"]
