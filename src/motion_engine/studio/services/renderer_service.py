"""Swappable rendering backend for AXYX.

The studio UI depends on :class:`RendererService`. The default backend drives
the embedded center-panel viewport. A future Unreal backend can replace this
without changing widgets, models, or controller call sites.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol

from motion_engine.skeleton import Skeleton

logger = logging.getLogger(__name__)


class ViewportHost(Protocol):
    """Minimal embedded viewport surface."""

    def show_skeleton(self, skeleton: Skeleton) -> None: ...

    def set_frame(self, frame: int) -> None: ...

    def reset_camera(self) -> None: ...


class RendererService(ABC):
    """Abstract rendering backend."""

    @abstractmethod
    def show_skeleton(self, skeleton: Skeleton) -> None:
        """Display a skeleton in the rendering backend."""

    @abstractmethod
    def close(self) -> None:
        """Close any open viewer resources."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the backend can run."""

    def set_frame(self, frame: int) -> None:
        """Optional frame seek for embedded backends."""

    def reset_camera(self) -> None:
        """Optional camera reset for embedded backends."""

    @property
    def backend_name(self) -> str:
        """Human-readable backend identity."""
        return type(self).__name__


class EmbeddedViewerRenderer(RendererService):
    """Render into the studio's embedded :class:`ViewerCanvas`.

    Example:
        >>> renderer = EmbeddedViewerRenderer(canvas)
        >>> renderer.show_skeleton(skeleton)
    """

    def __init__(self, viewport: ViewportHost | None = None) -> None:
        self._viewport = viewport

    def bind(self, viewport: ViewportHost) -> None:
        """Attach the live center-panel viewport."""
        self._viewport = viewport

    def is_available(self) -> bool:
        return self._viewport is not None

    def show_skeleton(self, skeleton: Skeleton) -> None:
        if self._viewport is None:
            raise RuntimeError("Embedded viewport is not bound")
        logger.info(
            "Showing skeleton in embedded viewport %s/%s",
            skeleton.subject_id,
            skeleton.session_name,
        )
        self._viewport.show_skeleton(skeleton)

    def set_frame(self, frame: int) -> None:
        if self._viewport is not None:
            self._viewport.set_frame(frame)

    def reset_camera(self) -> None:
        if self._viewport is not None:
            self._viewport.reset_camera()

    def close(self) -> None:
        return None


# Backward-compatible alias used by older imports / tests.
class MotionViewerRenderer(EmbeddedViewerRenderer):
    """Alias for :class:`EmbeddedViewerRenderer`."""


class NullRenderer(RendererService):
    """No-op renderer used in tests."""

    def __init__(self) -> None:
        self.shown: list[str] = []
        self.frames: list[int] = []

    def is_available(self) -> bool:
        return True

    def show_skeleton(self, skeleton: Skeleton) -> None:
        self.shown.append(f"{skeleton.subject_id}/{skeleton.session_name}")

    def set_frame(self, frame: int) -> None:
        self.frames.append(int(frame))

    def close(self) -> None:
        return None
