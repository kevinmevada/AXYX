"""Rendering-specific exceptions and error codes."""

from __future__ import annotations

from enum import Enum

from motion_engine.exceptions import MotionEngineError


class RenderErrorCode(str, Enum):
    """Stable error codes for rendering failures."""

    UNKNOWN = "RENDER_UNKNOWN"
    BACKEND = "RENDER_BACKEND"
    AVATAR_LOAD = "RENDER_AVATAR_LOAD"
    MESH_LOAD = "RENDER_MESH_LOAD"
    MATERIAL_LOAD = "RENDER_MATERIAL_LOAD"
    TEXTURE_LOAD = "RENDER_TEXTURE_LOAD"
    RESOURCE_NOT_FOUND = "RENDER_RESOURCE_NOT_FOUND"
    ENVIRONMENT = "RENDER_ENVIRONMENT"
    STATE = "RENDER_STATE"
    CONFIG = "RENDER_CONFIG"


class RenderError(MotionEngineError):
    """Base class for rendering subsystem errors."""

    code: RenderErrorCode = RenderErrorCode.UNKNOWN

    def __init__(self, message: str, *, code: RenderErrorCode | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class RenderBackendError(RenderError):
    code = RenderErrorCode.BACKEND


class AvatarLoadError(RenderError):
    code = RenderErrorCode.AVATAR_LOAD


class MeshLoadError(RenderError):
    code = RenderErrorCode.MESH_LOAD


class MaterialLoadError(RenderError):
    code = RenderErrorCode.MATERIAL_LOAD


class TextureLoadError(RenderError):
    code = RenderErrorCode.TEXTURE_LOAD


class ResourceNotFoundError(RenderError, FileNotFoundError):
    code = RenderErrorCode.RESOURCE_NOT_FOUND


class EnvironmentError(RenderError):
    code = RenderErrorCode.ENVIRONMENT


class RendererStateError(RenderError):
    code = RenderErrorCode.STATE


__all__ = [
    "RenderErrorCode",
    "RenderError",
    "RenderBackendError",
    "AvatarLoadError",
    "MeshLoadError",
    "MaterialLoadError",
    "TextureLoadError",
    "ResourceNotFoundError",
    "EnvironmentError",
    "RendererStateError",
]
