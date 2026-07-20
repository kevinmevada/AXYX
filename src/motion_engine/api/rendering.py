"""Stable rendering API.

Prefer::

    from motion_engine.api.rendering import PyVistaRenderer, RenderSettings

over importing deep ``rendering.*`` paths in application code.
"""

from __future__ import annotations

from motion_engine.renderer import (
    NullRenderer,
    PyVistaRenderer,
    Renderer,
    RendererError,
)
from motion_engine.rendering.backend import BackendCapabilities, PYVISTA_CAPABILITIES
from motion_engine.rendering.context import (
    FrameContext,
    FrameStatistics,
    PerformanceMetrics,
    RenderFlags,
    RenderSettings,
    RenderingContext,
)
from motion_engine.rendering.errors import (
    AvatarLoadError,
    MaterialLoadError,
    MeshLoadError,
    RenderBackendError,
    RenderError,
    ResourceNotFoundError,
)
from motion_engine.rendering.lifecycle import RenderLifecycle, RenderPhase
from motion_engine.rendering.plugins import PluginRegistry
from motion_engine.rendering.quality import QualityProfile, get_quality
from motion_engine.rendering.rendergraph import RenderGraph, RenderPass
from motion_engine.rendering.resources import ResourceManager
from motion_engine.rendering.scene import SceneGraph
from motion_engine.rendering.state import RendererState, RendererStateMachine

__all__ = [
    "Renderer",
    "PyVistaRenderer",
    "NullRenderer",
    "RendererError",
    "FrameContext",
    "FrameStatistics",
    "PerformanceMetrics",
    "RenderFlags",
    "RenderSettings",
    "RenderingContext",
    "RenderLifecycle",
    "RenderPhase",
    "PluginRegistry",
    "QualityProfile",
    "get_quality",
    "RenderGraph",
    "RenderPass",
    "ResourceManager",
    "SceneGraph",
    "RendererState",
    "RendererStateMachine",
    "BackendCapabilities",
    "PYVISTA_CAPABILITIES",
    "RenderError",
    "RenderBackendError",
    "AvatarLoadError",
    "MeshLoadError",
    "MaterialLoadError",
    "ResourceNotFoundError",
]
