"""Embedded PyVista motion viewport for AXYX.

Hosts the existing Motion Engine :class:`PyVistaRenderer` inside the studio
center panel so walking skeletons appear in the same application window.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from motion_engine.colors import get_theme
from motion_engine.renderer import PyVistaRenderer
from motion_engine.skeleton import Skeleton
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.error_banner import ErrorBanner
from motion_engine.studio.widgets.viewport_toolbar import ViewportToolbar
from motion_engine.viewer import SkeletonViewer

logger = logging.getLogger(__name__)

# Must be set before importing pyvistaqt so Qt binding resolves to PySide6.
os.environ.setdefault("QT_API", "pyside6")


def _is_offscreen_platform() -> bool:
    platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    return platform in {"offscreen", "minimal", "null"}


class ViewerCanvas(QFrame):
    """Center-panel PyVista viewport bound to studio playback."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CenterPanel")
        self.setMinimumHeight(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._skeleton: Skeleton | None = None
        self._frame = 0
        self._plotter: Any = None
        self._renderer: PyVistaRenderer | None = None
        self._viewer: SkeletonViewer | None = None
        self._ready = False
        self._init_error: str | None = None
        self._pending_skeleton: Skeleton | None = None

        self._drag_mode: str | None = None
        self._last_mouse = (0, 0)
        self._last_click_t = 0.0
        self._camera_obs: list[tuple[Any, str, int]] = []

        self._title = QLabel("")
        self._title.setObjectName("SectionLabel")
        self._title.hide()
        self._hint = QLabel("Select a session")
        self._hint.setObjectName("MutedLabel")
        self._error = ErrorBanner()
        self.toolbar = ViewportToolbar()
        self._wire_toolbar()

        self._host = QWidget(self)
        self._host.setObjectName("ViewportStage")
        self._host.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._host_layout = QVBoxLayout(self._host)
        self._host_layout.setContentsMargins(0, 0, 0, 0)
        self._host_layout.setSpacing(0)

        chrome = QWidget()
        chrome_layout = QVBoxLayout(chrome)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        chrome_layout.setSpacing(DEFAULT_THEME.spacing.xs)

        row = QWidget()
        tr = QHBoxLayout(row)
        tr.setContentsMargins(0, 0, 0, 0)
        tr.setSpacing(DEFAULT_THEME.spacing.sm)
        tr.addWidget(self.toolbar, stretch=1)
        tr.addWidget(self._hint)
        chrome_layout.addWidget(row)
        chrome_layout.addWidget(self._error)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(DEFAULT_THEME.spacing.sm)
        layout.addWidget(chrome)
        layout.addWidget(self._host, stretch=1)

        self._camera_timer = QTimer(self)
        self._camera_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._camera_timer.setInterval(16)
        self._camera_timer.timeout.connect(self._tick_camera)

    def _wire_toolbar(self) -> None:
        self.toolbar.cameraPresetRequested.connect(self.set_camera_preset)
        self.toolbar.resetCameraRequested.connect(self.reset_camera)
        self.toolbar.gridToggled.connect(self.set_grid_visible)
        self.toolbar.axesToggled.connect(self.set_axes_visible)
        self.toolbar.groundToggled.connect(self.set_ground_visible)
        self.toolbar.lightingToggled.connect(self.set_lighting_enabled)
        self.toolbar.fullscreenRequested.connect(self._on_fullscreen)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().showEvent(event)
        if not _is_offscreen_platform():
            self._ensure_viewport()
            if self._pending_skeleton is not None:
                skeleton = self._pending_skeleton
                self._pending_skeleton = None
                self.set_skeleton(skeleton, self._frame)

    def _ensure_viewport(self) -> bool:
        """Create the embedded QtInteractor + PyVista renderer once."""
        if self._ready:
            return True
        if self._init_error is not None:
            return False
        if _is_offscreen_platform():
            self._hint.setText("3D viewport disabled on offscreen Qt platform.")
            return False
        try:
            from pyvistaqt import QtInteractor

            plotter = QtInteractor(self._host)
            self._host_layout.addWidget(plotter.interactor)
            theme = get_theme("studio")
            renderer = PyVistaRenderer(theme=theme)
            renderer.attach_plotter(plotter)
            renderer.set_background(theme.background)
            self._plotter = plotter
            self._renderer = renderer
            self._viewer = SkeletonViewer(
                renderer=renderer,
                theme=theme,
                backend="pyvista",
                block=False,
            )
            try:
                self._install_clinical_camera(plotter)
            except Exception:
                logger.exception(
                    "Clinical camera controls failed; falling back to default PyVista camera"
                )
            self._camera_timer.start()
            self._ready = True
            logger.info("Embedded PyVista viewport ready")
            return True
        except Exception as exc:  # noqa: BLE001 - surface in UI
            self._init_error = str(exc)
            logger.exception("Failed to initialize embedded viewport")
            self._error.show_error(
                "Viewport unavailable",
                f"{exc}. Install pyvista / pyvistaqt in venv311.",
            )
            self._hint.setText("3D viewport could not start.")
            return False

    def _install_clinical_camera(self, plotter: Any) -> None:
        """Replace free trackball with constrained orbit / pan / zoom."""
        iren = getattr(plotter, "iren", None)
        if iren is None:
            return

        try:
            from vtkmodules.vtkInteractionStyle import vtkInteractorStyleUser
        except Exception:
            try:
                from vtk.vtkInteractionStyle import vtkInteractorStyleUser  # type: ignore
            except Exception:
                logger.debug("Clinical camera style unavailable", exc_info=True)
                return

        # PyVista wraps VTK - set style via ``iren.style``, not SetInteractorStyle.
        try:
            iren.style = vtkInteractorStyleUser()
        except Exception:
            try:
                iren.interactor.SetInteractorStyle(vtkInteractorStyleUser())
            except Exception:
                logger.debug("Could not install clinical interactor style", exc_info=True)
                return

        def _event_pos() -> tuple[int, int]:
            try:
                return tuple(iren.get_event_position())  # type: ignore[return-value]
            except Exception:
                return tuple(iren.interactor.GetEventPosition())  # type: ignore[return-value]

        def _obs(event: str, callback) -> None:
            try:
                tag = iren.add_observer(event, callback, interactor_style_fallback=False)
            except TypeError:
                tag = iren.add_observer(event, callback)
            self._camera_obs.append((iren, event, tag))

        def on_left_press(_obj, _evt) -> None:
            now = time.perf_counter()
            if now - self._last_click_t < 0.35:
                self.reset_camera()
                self._last_click_t = 0.0
                self._drag_mode = None
                return
            self._last_click_t = now
            self._drag_mode = "orbit"
            self._last_mouse = _event_pos()

        def on_middle_press(_obj, _evt) -> None:
            self._drag_mode = "pan"
            self._last_mouse = _event_pos()

        def on_right_press(_obj, _evt) -> None:
            self._drag_mode = "pan"
            self._last_mouse = _event_pos()

        def on_release(_obj, _evt) -> None:
            self._drag_mode = None

        def on_move(_obj, _evt) -> None:
            if self._viewer is None or self._drag_mode is None:
                return
            x, y = _event_pos()
            lx, ly = self._last_mouse
            dx, dy = float(x - lx), float(y - ly)
            self._last_mouse = (x, y)
            cam = self._viewer.camera
            if self._drag_mode == "orbit":
                cam.orbit(dx, dy)
            elif self._drag_mode == "pan":
                cam.pan(dx, dy)
            elif self._drag_mode == "dolly":
                cam.zoom(dy)

        def on_wheel_forward(_obj, _evt) -> None:
            if self._viewer is not None:
                self._viewer.camera.zoom(1.0)

        def on_wheel_backward(_obj, _evt) -> None:
            if self._viewer is not None:
                self._viewer.camera.zoom(-1.0)

        _obs("LeftButtonPressEvent", on_left_press)
        _obs("MiddleButtonPressEvent", on_middle_press)
        _obs("RightButtonPressEvent", on_right_press)
        _obs("LeftButtonReleaseEvent", on_release)
        _obs("MiddleButtonReleaseEvent", on_release)
        _obs("RightButtonReleaseEvent", on_release)
        _obs("MouseMoveEvent", on_move)
        _obs("MouseWheelForwardEvent", on_wheel_forward)
        _obs("MouseWheelBackwardEvent", on_wheel_backward)

    def _tick_camera(self) -> None:
        """Advance smooth camera transitions without waiting on playback."""
        if self._viewer is None or self._viewer.skeleton is None:
            return
        cam = self._viewer.camera
        cam.update()
        if cam.is_dirty() or cam.is_animating():
            try:
                self._viewer.update_frame()
            except Exception:
                logger.debug("Camera tick failed", exc_info=True)

    def set_skeleton(self, skeleton: Skeleton | None, frame: int = 0) -> None:
        """Load a skeleton into the embedded viewport."""
        if (
            skeleton is not None
            and self._skeleton is not None
            and skeleton.subject_id == self._skeleton.subject_id
            and skeleton.session_name == self._skeleton.session_name
            and skeleton.frame_count == self._skeleton.frame_count
            and self._viewer is not None
            and self._viewer.skeleton is not None
        ):
            self.set_frame(frame)
            return

        self._skeleton = skeleton
        self._frame = frame
        if skeleton is None:
            self._hint.setText("Select a session")
            self._pending_skeleton = None
            self._error.hide()
            return

        if not self.isVisible() or not self._ensure_viewport() or self._viewer is None:
            self._pending_skeleton = skeleton
            self._hint.setText(f"{skeleton.subject_id}/{skeleton.session_name}")
            return

        self._pending_skeleton = None
        self._hint.setText(
            f"{skeleton.subject_id}/{skeleton.session_name} | {skeleton.frame_count}f"
        )
        try:
            self._viewer.show(skeleton)
            self._viewer.pause()
            self.set_frame(frame)
            self.reset_camera()
            self._error.hide()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to show skeleton in embedded viewport")
            self._error.show_error("Failed to load skeleton", str(exc))
            self._hint.setText("Skeleton could not be rendered.")

    def set_frame(self, frame: int) -> None:
        """Seek the embedded viewer to ``frame``."""
        self._frame = frame
        if self._viewer is None or self._viewer.skeleton is None:
            return
        try:
            self._viewer.seek(int(frame))
        except Exception:
            logger.debug("Embedded seek failed", exc_info=True)

    def reset_camera(self) -> None:
        """Front clinical view: center subject, fit full body, smooth transition."""
        if self._viewer is None:
            return
        try:
            self._viewer.camera.reset(animate=True)
            self._viewer.update_frame()
        except Exception:
            logger.debug("Camera reset failed", exc_info=True)

    def fit_camera(self) -> None:
        """Fit the subject in the current view direction."""
        if self._viewer is None:
            return
        try:
            self._viewer.camera.focus_subject(animate=True)
            self._viewer.update_frame()
        except Exception:
            logger.debug("Camera fit failed", exc_info=True)

    def set_camera_preset(self, preset: str) -> None:
        """Anatomical presets: Front / Back / Left / Right - one smooth framed move."""
        if self._viewer is None:
            return
        cam = self._viewer.camera
        try:
            name = preset.lower().strip()
            if name == "front":
                cam.front(animate=True)
            elif name == "back":
                cam.back(animate=True)
            elif name in {"right", "side"}:
                cam.right(animate=True)
            elif name == "left":
                cam.left(animate=True)
            else:
                cam.front(animate=True)
            self._viewer.update_frame()
        except Exception:
            logger.debug("Camera preset failed", exc_info=True)

    def set_grid_visible(self, visible: bool) -> None:
        if self._viewer is None:
            return
        if self._viewer.scene.show_grid != visible:
            self._viewer.scene.show_grid = visible
            self._viewer.update_frame()

    def set_axes_visible(self, visible: bool) -> None:
        if self._viewer is None:
            return
        if self._viewer.scene.show_axes != visible:
            self._viewer.scene.show_axes = visible
            self._viewer.update_frame()

    def set_ground_visible(self, visible: bool) -> None:
        if self._viewer is None:
            return
        if self._viewer.scene.show_ground != visible:
            self._viewer.scene.show_ground = visible
            self._viewer.update_frame()

    def set_lighting_enabled(self, enabled: bool) -> None:
        if self._viewer is None or self._renderer is None:
            return
        try:
            self._renderer.set_lighting_enabled(enabled)
            self._viewer.update_frame()
        except Exception:
            logger.debug("Lighting toggle failed", exc_info=True)

    def show_skeleton(self, skeleton: Skeleton) -> None:
        """RendererService-compatible entry point."""
        self.set_skeleton(skeleton, frame=0)

    def _on_fullscreen(self) -> None:
        window = self.window()
        if window is None:
            return
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()
