"""Avatar registry — id → lazy LoadedAvatar."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader
from motion_engine.rendering.avatar.loader.exceptions import AvatarError, ValidationError
from motion_engine.rendering.avatar.models.avatar import LoadedAvatar

logger = logging.getLogger(__name__)


class AvatarRegistry:
    """Register avatars by stable id with lazy loading and hot-reload hooks.

    The Viewer never sees filesystem paths — only registry ids.

    Example:
        >>> reg = AvatarRegistry()
        >>> reg.register_path("avatar.metahuman.default", "metahuman")
        >>> avatar = reg.get("avatar.metahuman.default")
    """

    def __init__(self, loader: AvatarLoader | None = None) -> None:
        self._loader = loader or AvatarLoader()
        self._sources: dict[str, str | Path] = {}
        self._cache: dict[str, LoadedAvatar] = {}
        self._factories: dict[str, Callable[[], LoadedAvatar]] = {}
        self._lod: dict[str, int | None] = {}

    def register_path(
        self,
        avatar_id: str,
        source: str | Path,
        *,
        lod: int | None = None,
        replace: bool = False,
    ) -> None:
        """Register an avatar id → manifest source for lazy loading."""
        if avatar_id in self._sources and not replace:
            raise ValidationError(f"Duplicate avatar id: {avatar_id}")
        self._sources[avatar_id] = source
        self._lod[avatar_id] = lod
        self._cache.pop(avatar_id, None)
        logger.info("Registered avatar id %r → %s", avatar_id, source)

    def register_factory(
        self,
        avatar_id: str,
        factory: Callable[[], LoadedAvatar],
        *,
        replace: bool = False,
    ) -> None:
        """Register a custom factory (tests / procedural builders)."""
        if avatar_id in self._factories and not replace:
            raise ValidationError(f"Duplicate avatar factory id: {avatar_id}")
        self._factories[avatar_id] = factory
        self._cache.pop(avatar_id, None)
        logger.info("Registered avatar factory %r", avatar_id)

    def register(
        self,
        avatar_id: str,
        source: str | Path,
        *,
        lod: int | None = None,
        replace: bool = False,
    ) -> None:
        """Alias for :meth:`register_path` (certification / public naming)."""
        self.register_path(avatar_id, source, lod=lod, replace=replace)

    def exists(self, avatar_id: str) -> bool:
        """Return True if ``avatar_id`` is registered."""
        return avatar_id in self._sources or avatar_id in self._factories

    def list(self) -> list[str]:
        """Alias for :meth:`ids`."""
        return self.ids()

    def reload(self, avatar_id: str) -> LoadedAvatar:
        """Invalidate cache and force a fresh load."""
        self.invalidate(avatar_id)
        return self.get(avatar_id, force_reload=True)

    def unregister(self, avatar_id: str) -> None:
        """Drop registration and cache entry."""
        self._sources.pop(avatar_id, None)
        self._factories.pop(avatar_id, None)
        self._lod.pop(avatar_id, None)
        self._cache.pop(avatar_id, None)

    def ids(self) -> list[str]:
        """Return registered avatar ids."""
        return sorted(set(self._sources) | set(self._factories))

    def get(self, avatar_id: str, *, force_reload: bool = False) -> LoadedAvatar:
        """Return cached or freshly loaded avatar.

        Raises:
            AvatarError: Unknown id or load failure.
        """
        if not force_reload and avatar_id in self._cache:
            return self._cache[avatar_id]

        if avatar_id in self._factories:
            loaded = self._factories[avatar_id]()
        elif avatar_id in self._sources:
            loaded = self._loader.load(
                self._sources[avatar_id], lod=self._lod.get(avatar_id)
            )
        else:
            raise AvatarError(f"Unknown avatar id: {avatar_id}")

        self._cache[avatar_id] = loaded
        logger.debug("Avatar %r ready (cached)", avatar_id)
        return loaded

    def invalidate(self, avatar_id: str | None = None) -> None:
        """Hot-reload support — drop one or all cached avatars."""
        if avatar_id is None:
            self._cache.clear()
            logger.info("AvatarRegistry cache cleared")
            return
        self._cache.pop(avatar_id, None)
        logger.info("AvatarRegistry invalidated %r", avatar_id)

    def put(self, avatar_id: str, loaded: LoadedAvatar) -> None:
        """Insert a pre-loaded avatar into the cache."""
        self._cache[avatar_id] = loaded

    def preload(self, avatar_id: str) -> LoadedAvatar:
        """Force load and cache."""
        return self.get(avatar_id, force_reload=True)


__all__ = ["AvatarRegistry"]
