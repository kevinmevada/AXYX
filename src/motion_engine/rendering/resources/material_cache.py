"""Material instance cache."""

from __future__ import annotations

from typing import Any

from motion_engine.rendering.resources.mesh_cache import ResourceCache

MaterialCache = ResourceCache[str, Any]

__all__ = ["MaterialCache"]
