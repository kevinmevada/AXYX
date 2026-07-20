"""Render backend protocol — thin contract used by render passes."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from motion_engine.rendering.backend.capabilities import (
    NULL_CAPABILITIES,
    PYVISTA_CAPABILITIES,
    BackendCapabilities,
)


@runtime_checkable
class RenderBackend(Protocol):
    """Minimal backend surface consumed by the render graph."""

    @property
    def plotter(self) -> Any:
        """Underlying plotter / device context (backend-specific)."""

    @property
    def capabilities(self) -> BackendCapabilities:
        """Feature flags for this backend."""

    def present(self) -> None:
        """Submit the frame to the GPU / window."""


__all__ = [
    "RenderBackend",
    "BackendCapabilities",
    "PYVISTA_CAPABILITIES",
    "NULL_CAPABILITIES",
]
