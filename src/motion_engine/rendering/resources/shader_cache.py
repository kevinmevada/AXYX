"""Shader / pipeline cache (backend-agnostic keys)."""

from __future__ import annotations

from typing import Any

from motion_engine.rendering.resources.mesh_cache import ResourceCache

ShaderCache = ResourceCache[str, Any]

__all__ = ["ShaderCache"]
