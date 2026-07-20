"""Central resource lifetime manager — meshes, textures, shaders, materials."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from motion_engine.rendering.resources.material_cache import MaterialCache
from motion_engine.rendering.resources.mesh_cache import ResourceCache
from motion_engine.rendering.resources.shader_cache import ShaderCache
from motion_engine.rendering.resources.texture_cache import TextureCache

logger = logging.getLogger(__name__)

MeshCache = ResourceCache[str, Any]


class ResourceManager:
    """Owns GPU/CPU asset caches and supports future hot-reload.

    Missing assets never raise to callers of :meth:`safe_get` — they return
    ``None`` and log a warning so the frame can continue with fallbacks.
    """

    def __init__(self) -> None:
        self.meshes: MeshCache = MeshCache("meshes")
        self.textures: TextureCache = TextureCache("textures")
        self.shaders: ShaderCache = ShaderCache("shaders")
        self.materials: MaterialCache = MaterialCache("materials")
        self._loaders: dict[str, Callable[[Path], Any]] = {}

    def register_loader(self, kind: str, loader: Callable[[Path], Any]) -> None:
        """Register a file loader for ``kind`` (``mesh``, ``texture``, …)."""
        self._loaders[kind] = loader
        logger.debug("Registered resource loader %r", kind)

    def load(
        self,
        kind: str,
        key: str,
        path: Path | None = None,
        *,
        factory: Callable[[], Any] | None = None,
    ) -> Any | None:
        """Load or return a cached resource; ``None`` on failure."""
        cache = self._cache_for(kind)
        if cache is None:
            logger.warning("Unknown resource kind %r", kind)
            return None
        existing = cache.get(key)
        if existing is not None:
            return existing
        try:
            if factory is not None:
                return cache.put(key, factory())
            if path is None:
                logger.warning("No path/factory for %s:%s", kind, key)
                return None
            if not path.is_file():
                logger.warning("Missing %s asset: %s", kind, path)
                return None
            loader = self._loaders.get(kind)
            if loader is None:
                logger.warning("No loader registered for kind %r", kind)
                return None
            return cache.put(key, loader(path))
        except Exception:
            logger.warning("Failed loading %s:%s", kind, key, exc_info=True)
            return None

    def safe_get(self, kind: str, key: str) -> Any | None:
        """Return cached value or ``None`` (never raises)."""
        cache = self._cache_for(kind)
        if cache is None:
            return None
        return cache.get(key)

    def invalidate(self, kind: str | None = None, key: str | None = None) -> None:
        """Hot-reload support — drop one or all caches."""
        if kind is None:
            for cache in (self.meshes, self.textures, self.shaders, self.materials):
                cache.invalidate()
            logger.info("ResourceManager: all caches invalidated")
            return
        cache = self._cache_for(kind)
        if cache is not None:
            cache.invalidate(key)

    def stats(self) -> dict[str, int]:
        """Cache occupancy for diagnostics."""
        return {
            "meshes": len(self.meshes),
            "textures": len(self.textures),
            "shaders": len(self.shaders),
            "materials": len(self.materials),
        }

    def _cache_for(self, kind: str) -> ResourceCache[str, Any] | None:
        return {
            "mesh": self.meshes,
            "meshes": self.meshes,
            "texture": self.textures,
            "textures": self.textures,
            "shader": self.shaders,
            "shaders": self.shaders,
            "material": self.materials,
            "materials": self.materials,
        }.get(kind)


__all__ = ["ResourceManager", "MeshCache"]
