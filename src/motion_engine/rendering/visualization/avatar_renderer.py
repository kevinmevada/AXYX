"""Human avatar visualization — wraps the existing digital-twin bridge."""

from __future__ import annotations

from typing import Callable

from motion_engine.rendering.visualization.base_renderer import BaseVisualizationRenderer
from motion_engine.rendering.visualization.modes import VisualizationMode
from motion_engine.skeleton import Pose


class AvatarRenderer(BaseVisualizationRenderer):
    """Mode 3 — skinned FBX avatar (Army Girl / MetaHuman).

    Activation hooks into the existing ``DigitalTwinViewportBridge`` path.
    """

    mode = VisualizationMode.AVATAR

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
        # Avatar mesh is updated via viewer body_callback / draw_avatar_body.
        _ = pose
