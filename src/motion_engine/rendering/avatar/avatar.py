"""Avatar abstract base — swappable digital human / procedural figure."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Avatar(ABC):
    """Renderable animated figure driven by mocap poses.

    Future implementations: ``ProceduralAvatar``, ``MetaHumanAvatar``,
    ``SMPLAvatar``. The viewer / AvatarManager never branch on concrete type.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._loaded = False

    @property
    def name(self) -> str:
        """Stable registry key for this avatar implementation."""
        return self._name

    @property
    def is_loaded(self) -> bool:
        """True after a successful :meth:`load`."""
        return self._loaded

    @abstractmethod
    def load(self, **kwargs: Any) -> None:
        """Load meshes / materials / bindings for this avatar."""

    @abstractmethod
    def update(self, frame: Any) -> None:
        """Apply animation / pose for the current frame."""

    @abstractmethod
    def render(self, backend: Any) -> None:
        """Submit drawables to the active render backend."""

    def dispose(self) -> None:
        """Release GPU / CPU resources (override as needed)."""
        self._loaded = False
        logger.debug("Avatar disposed: %s", self.name)


__all__ = ["Avatar"]
