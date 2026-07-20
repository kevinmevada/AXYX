"""Core rendering interfaces (protocols / ABCs).

Every concrete backend, avatar, environment, and pass should satisfy these
contracts so OpenGL / Vulkan / Unreal / SMPL can plug in later without
rewriting Studio or the viewer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from motion_engine.rendering.avatar.avatar import Avatar
from motion_engine.rendering.backend.capabilities import BackendCapabilities
from motion_engine.rendering.backend.protocol import RenderBackend
from motion_engine.rendering.rendergraph.render_pass import RenderPass
from motion_engine.rendering.scene.scene_node import RenderNode, SceneNode, TransformNode


@runtime_checkable
class RendererBackend(Protocol):
    """Backend contract used by the render graph and avatars."""

    @property
    def capabilities(self) -> BackendCapabilities:
        """Feature flags for this backend."""

    def present(self) -> None:
        """Submit the frame to the GPU / window."""


@runtime_checkable
class Environment(Protocol):
    """Environment / IBL / atmosphere provider."""

    def configure_renderer(self, plotter: Any) -> None:
        """Apply atmosphere / IBL / background to the backend plotter."""


@runtime_checkable
class Material(Protocol):
    """Minimal material contract (name + PBR scalars)."""

    name: str
    metallic: float
    roughness: float


@runtime_checkable
class Resource(Protocol):
    """Cached resource handle — identity is a stable string key."""

    def __len__(self) -> int:  # pragma: no cover - structural
        ...


@runtime_checkable
class CameraControllerProtocol(Protocol):
    """Camera behaviour contract (orbit / framing / transitions)."""

    def update(self, dt: float) -> Any:
        """Advance camera animation; return a state snapshot."""


class RenderPassInterface(ABC):
    """ABC mirror of :class:`~motion_engine.rendering.rendergraph.RenderPass`."""

    name: str

    @abstractmethod
    def execute(self, context: Any) -> None:
        """Run this pass."""


__all__ = [
    "BackendCapabilities",
    "RendererBackend",
    "RenderBackend",
    "Environment",
    "Material",
    "Resource",
    "CameraControllerProtocol",
    "RenderPassInterface",
    "Avatar",
    "RenderPass",
    "SceneNode",
    "TransformNode",
    "RenderNode",
]
