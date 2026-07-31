"""Abstract visualization renderer — visualizes pose data only."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from motion_engine.rendering.visualization.modes import VisualizationMode
from motion_engine.skeleton import Pose


class BaseVisualizationRenderer(ABC):
    """One visualization backend. Never owns playback or camera."""

    mode: VisualizationMode

    def __init__(self) -> None:
        self._active = False
        self._plotter: Any = None
        self._theme: Any = None

    @property
    def active(self) -> bool:
        return self._active

    def bind(self, plotter: Any, *, theme: Any = None) -> None:
        """Attach to an existing PyVista plotter (no viewport recreation)."""
        self._plotter = plotter
        self._theme = theme

    @abstractmethod
    def activate(self) -> None:
        """Show this mode's actors; hide nothing owned by other modes."""

    @abstractmethod
    def deactivate(self) -> None:
        """Hide/remove this mode's actors without touching the plotter itself."""

    @abstractmethod
    def render_pose(self, pose: Pose) -> None:
        """Update visuals for one pose. No mesh regeneration when avoidable."""

    def clear(self) -> None:
        """Drop cached GPU resources. Safe to call when inactive."""
        self.deactivate()
