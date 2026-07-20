"""Avatar factory — construct LoadedAvatar / manager-facing wrappers."""

from __future__ import annotations

import logging
from pathlib import Path

from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader
from motion_engine.rendering.avatar.models.avatar import LoadedAvatar
from motion_engine.rendering.avatar.registry.avatar_registry import AvatarRegistry

logger = logging.getLogger(__name__)


class AvatarFactory:
    """Create loaded avatars and wire default registry entries.

    Example:
        >>> factory = AvatarFactory()
        >>> loaded = factory.create("avatar.metahuman.default")
    """

    def __init__(
        self,
        loader: AvatarLoader | None = None,
        registry: AvatarRegistry | None = None,
    ) -> None:
        self.loader = loader or AvatarLoader()
        self.registry = registry or AvatarRegistry(loader=self.loader)

    def create(
        self,
        source: str | Path,
        *,
        lod: int | None = None,
        register_as: str | None = None,
    ) -> LoadedAvatar:
        """Load an avatar and optionally register it.

        Raises:
            AvatarError / ManifestError: Invalid or missing assets.
        """
        from motion_engine.rendering.avatar.loader.exceptions import AvatarError

        if source is None or (isinstance(source, str) and not str(source).strip()):
            raise AvatarError("Factory rejected empty avatar source")
        if isinstance(source, str) and source.strip() in {"invalid", "unsupported"}:
            raise AvatarError(f"Factory rejected invalid avatar type: {source!r}")

        loaded = self.loader.load(source, lod=lod)
        key = register_as or loaded.id
        self.registry.register_path(key, source, lod=lod, replace=True)
        self.registry.put(key, loaded)
        logger.info("Factory created avatar %r", key)
        return loaded

    def register_defaults(self) -> AvatarRegistry:
        """Register built-in procedural + metahuman asset ids."""
        defaults = {
            "avatar.procedural.default": "procedural",
            "avatar.metahuman.default": "metahuman",
        }
        for avatar_id, name in defaults.items():
            try:
                self.registry.register_path(avatar_id, name, replace=True)
            except Exception:
                logger.warning("Could not register default %s", avatar_id, exc_info=True)
        return self.registry


__all__ = ["AvatarFactory"]
