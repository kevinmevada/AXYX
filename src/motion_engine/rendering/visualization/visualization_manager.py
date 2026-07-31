"""Orchestrates interchangeable visualization backends without touching playback."""

from __future__ import annotations

import logging
from typing import Any, Callable

from motion_engine.rendering.visualization.avatar_renderer import AvatarRenderer
from motion_engine.rendering.visualization.base_renderer import BaseVisualizationRenderer
from motion_engine.rendering.visualization.bone_renderer import BoneRenderer
from motion_engine.rendering.visualization.modes import VisualizationMode
from motion_engine.rendering.visualization.stick_renderer import StickRenderer
from motion_engine.skeleton import Pose

logger = logging.getLogger(__name__)


class VisualizationManager:
    """Lifecycle + mode switching for stick / bones / avatar renderers.

    Playback, camera, timeline, and overlays stay owned by the host viewer.
    Switching modes never recreates the viewport.
    """

    def __init__(
        self,
        *,
        stick: StickRenderer | None = None,
        bones: BoneRenderer | None = None,
        avatar: AvatarRenderer | None = None,
        on_mode_changed: Callable[[VisualizationMode], None] | None = None,
    ) -> None:
        self._stick = stick or StickRenderer()
        self._bones = bones or BoneRenderer()
        self._avatar = avatar or AvatarRenderer()
        self._renderers: dict[VisualizationMode, BaseVisualizationRenderer] = {
            VisualizationMode.STICK: self._stick,
            VisualizationMode.BONES: self._bones,
            VisualizationMode.AVATAR: self._avatar,
        }
        self._mode = VisualizationMode.STICK
        self._plotter: Any = None
        self._theme: Any = None
        self._on_mode_changed = on_mode_changed
        self._bound = False

    @property
    def mode(self) -> VisualizationMode:
        return self._mode

    @property
    def stick(self) -> StickRenderer:
        return self._stick

    @property
    def bones(self) -> BoneRenderer:
        return self._bones

    @property
    def avatar(self) -> AvatarRenderer:
        return self._avatar

    def bind(self, plotter: Any, *, theme: Any = None) -> None:
        self._plotter = plotter
        self._theme = theme
        for renderer in self._renderers.values():
            renderer.bind(plotter, theme=theme)
        self._bound = True

    def set_mode(self, mode: str | VisualizationMode) -> VisualizationMode:
        """Switch visualization backend. Preserves playback/camera externally."""
        target = VisualizationMode.parse(mode)
        if target == self._mode and self._renderers[target].active:
            return self._mode

        previous = self._renderers[self._mode]
        previous.deactivate()

        nxt = self._renderers[target]
        try:
            nxt.activate()
        except Exception:
            logger.exception("Failed to activate %s — falling back to stick", target)
            target = VisualizationMode.STICK
            self._stick.activate()

        # Bone mode may fail asset install — fall back.
        if target == VisualizationMode.BONES and not self._bones.ready:
            logger.warning("Anatomical bones unavailable — using stick figure")
            self._bones.deactivate()
            target = VisualizationMode.STICK
            self._stick.activate()

        self._mode = target
        if self._on_mode_changed is not None:
            self._on_mode_changed(target)
        return self._mode

    def render_pose(self, pose: Pose) -> None:
        """Forward pose to the active renderer (no-op for stick/avatar hosts)."""
        renderer = self._renderers.get(self._mode)
        if renderer is not None and renderer.active:
            renderer.render_pose(pose)

    def clear(self) -> None:
        for renderer in self._renderers.values():
            renderer.clear()
