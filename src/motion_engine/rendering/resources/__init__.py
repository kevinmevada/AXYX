"""Resource management package."""

from __future__ import annotations

from motion_engine.rendering.resources.material_cache import MaterialCache
from motion_engine.rendering.resources.mesh_cache import ResourceCache
from motion_engine.rendering.resources.resource_manager import MeshCache, ResourceManager
from motion_engine.rendering.resources.shader_cache import ShaderCache
from motion_engine.rendering.resources.texture_cache import TextureCache

__all__ = [
    "ResourceManager",
    "ResourceCache",
    "MeshCache",
    "TextureCache",
    "ShaderCache",
    "MaterialCache",
]
