"""Clinical stick-figure visualization — delegates to existing viewer flags."""

from __future__ import annotations

from typing import Any, Callable

from motion_engine.rendering.visualization.base_renderer import BaseVisualizationRenderer
from motion_engine.rendering.visualization.modes import VisualizationMode
from motion_engine.skeleton import Pose


class StickRenderer(BaseVisualizationRenderer):
    """Mode 1 — procedural shafts + joint spheres (fastest path).

    Does not draw itself; it configures the existing ``SkeletonViewer`` /
    ``PyVistaRenderer`` stick path via callbacks so playback stays untouched.
    """

    mode = VisualizationMode.STICK

    def __init__(
        self,
        *,
        on_activate: Callable[[], None] | None = None,
        on_deactivate: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate

    def activate(self) -> None:
        self._active = True
        if self._on_activate is not None:
            self._on_activate()

    def deactivate(self) -> None:
        self._active = False
        if self._on_deactivate is not None:
            self._on_deactivate()

    def render_pose(self, pose: Pose) -> None:
        # Stick path is drawn by SkeletonViewer._draw_frame when show_bones/joints.
        _ = pose
