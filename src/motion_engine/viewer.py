"""
Visualization Engine - Qt + PyVista studio viewer.

Architecture
------------
Viewer (ABC)
    â””â”€â”€ SkeletonViewer   production entry point (PyVista studio)

``viewer.py`` owns UI only: toolbar, docks, status bar, shortcuts.
Camera math lives in ``camera.py``. Rendering lives in ``renderer.py``.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from motion_engine.avatar import AvatarBackend, create_default_avatar
from motion_engine.camera import BoundingBox, CameraController, CameraPreset, CameraState
from motion_engine.colors import Theme, get_theme
from motion_engine.exceptions import MotionEngineError
from motion_engine.playback import PlaybackController, PlaybackState
from motion_engine.renderer import (
    NullRenderer,
    PyVistaRenderer,
    Renderer,
    create_default_renderer,
)
from motion_engine.scene import Scene
from motion_engine.skeleton import Pose, Skeleton
from motion_engine.timeline import Timeline

logger = logging.getLogger(__name__)

DEFAULT_JOINT_RADIUS_RATIO: float = 0.028
DEFAULT_GROUND_PADDING_RATIO: float = 1.8
DEFAULT_AXES_LENGTH_RATIO: float = 0.22
DEFAULT_GRID_DIVISIONS: int = 24
MIN_JOINT_RADIUS: float = 18.0
MAX_JOINT_RADIUS: float = 55.0
TARGET_RENDER_FPS: int = 120
RENDER_TICK_MS: int = max(1, int(1000 / TARGET_RENDER_FPS))


class ViewerError(MotionEngineError):
    """Raised for viewer lifecycle / input errors."""


class Viewer(ABC):
    """Abstract visualization viewer."""

    @abstractmethod
    def show(self, skeleton: Skeleton) -> None:
        """Display ``skeleton`` interactively."""

    @abstractmethod
    def close(self) -> None:
        """Close the viewer."""

    @abstractmethod
    def reset(self) -> None:
        """Reset playback and camera."""

    @abstractmethod
    def update_frame(self, frame_index: int | None = None) -> None:
        """Draw one frame."""

    @abstractmethod
    def next_frame(self) -> None: ...

    @abstractmethod
    def previous_frame(self) -> None: ...

    @abstractmethod
    def play(self) -> None: ...

    @abstractmethod
    def pause(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def set_speed(self, speed: float) -> None: ...

    @abstractmethod
    def seek(self, frame_index: int) -> None: ...

    @abstractmethod
    def screenshot(self, path: str | Path) -> Path: ...


class SkeletonViewer(Viewer):
    """Production PyVista / Qt studio viewer for human motion.

    Args:
        renderer: Injected renderer (Null / PyVista).
        theme: Theme name or Theme instance (default ``studio``).
        backend: ``auto`` / ``pyvista`` / ``null``.
        block: If True, run the Qt event loop.
    """

    def __init__(
        self,
        renderer: Renderer | None = None,
        *,
        theme: str | Theme = "studio",
        backend: str = "auto",
        block: bool = True,
        avatar: AvatarBackend | str | None = None,
    ) -> None:
        self.theme = theme if isinstance(theme, Theme) else get_theme(theme)
        self.renderer: Renderer = renderer or create_default_renderer(
            prefer=backend, theme=self.theme
        )
        self.block = block
        self.skeleton: Skeleton | None = None
        self.scene: Scene = self.renderer.scene
        self.camera = CameraController(CameraState())
        self.timeline = Timeline(n_frames=0)
        self.playback = PlaybackController(self.timeline)

        if isinstance(avatar, AvatarBackend):
            self.avatar = avatar
        else:
            self.avatar = create_default_avatar(
                avatar if isinstance(avatar, str) else None
            )
        try:
            self.avatar.attach(self.renderer)
        except Exception:
            logger.exception("Avatar attach failed; continuing")

        # Procedural metallic stick-figure — disabled when a mesh avatar draws.
        self.show_joints = True
        self.show_bones = True
        self.show_joint_labels = False
        self.show_bone_labels = False
        self.selected_joint: str | None = None
        self.selected_bone: str | None = None

        self._bbox_center = np.zeros(3, dtype=float)
        self._bbox_extent = 1000.0
        self._ground_span = 2000.0
        self._floor_z = 0.0
        self._ground_origin = (0.0, 0.0, 0.0)
        self._joint_radius = 25.0
        self._initialized = False
        self._fps = 0.0
        self._last_tick = time.perf_counter()
        self._accum = 0.0
        self._qt_app: Any = None
        self._main_window: Any = None
        self._status_label: Any = None
        self._frame_slider: Any = None
        self._speed_slider: Any = None
        self._loop_checkbox: Any = None
        self._recording_frames: list[Any] = []
        self._is_recording = False
        self._last_drawn_frame = -1
        self._status_refresh_accum = 0.0

    # ------------------------------------------------------------------ API

    def show(self, skeleton: Skeleton) -> None:
        if skeleton.n_frames <= 0 or not skeleton.poses:
            raise ViewerError("Skeleton has no poses to visualize")

        self.skeleton = skeleton
        self.timeline = Timeline(
            n_frames=skeleton.n_frames,
            sampling_rate_hz=float(skeleton.sampling_rate_hz or 100.0),
            current_frame=0,
        )
        self.playback = PlaybackController(self.timeline, loop=True, speed=1.0)
        self._compute_bounds()
        self.camera.reset(animate=False)

        title = f"AXYX Studio - {skeleton.subject_id}/{skeleton.session_name}"

        if isinstance(self.renderer, NullRenderer) or not self.block:
            self.renderer.initialize(title=title)
            self.renderer.set_background(self.theme.background)
            self._initialized = True

        try:
            self.avatar.load(skeleton)
        except Exception:
            logger.exception(
                "Avatar %s failed to load; falling back to metallic stick-figure",
                getattr(self.avatar, "id", "?"),
            )
            from motion_engine.avatar.metallic_backend import MetallicAvatar

            self.avatar = MetallicAvatar()
            self.avatar.attach(self.renderer)

        if isinstance(self.renderer, NullRenderer) or not self.block:
            self.playback.play()
            self.update_frame(0)
            if self.block and not isinstance(self.renderer, NullRenderer):
                self._run_headless_loop()
            return

        self._build_qt_application(title)
        self._initialized = True
        self.playback.play()
        self.update_frame(0)
        if self.block and self._qt_app is not None:
            self._qt_app.exec()

    def close(self) -> None:
        self.playback.stop()
        self._is_recording = False
        if self._main_window is not None:
            try:
                self._main_window.close()
            except Exception:
                pass
            self._main_window = None
        self.renderer.close()
        self._initialized = False

    def reset(self) -> None:
        self.playback.stop()
        self.camera.reset(animate=True)
        self.update_frame(0)
        self._refresh_status()

    def update_frame(self, frame_index: int | None = None) -> None:
        if self.skeleton is None:
            raise ViewerError("No skeleton loaded. Call show(skeleton) first.")
        if frame_index is not None:
            self.timeline.seek(frame_index)
        frame_changed = self.timeline.current_frame != self._last_drawn_frame
        camera_dirty = self.camera.is_dirty()
        if frame_changed or camera_dirty:
            pose = self.skeleton.get_pose(self.timeline.current_frame)
            self._draw_frame(pose)
            self._last_drawn_frame = self.timeline.current_frame
        self.renderer.render()
        if self._is_recording and isinstance(self.renderer, PyVistaRenderer):
            try:
                img = self.renderer.plotter.screenshot(return_img=True)
                self._recording_frames.append(img)
            except Exception:
                logger.debug("Frame capture failed", exc_info=True)
        if frame_changed:
            self._sync_playback_widgets()
        self._refresh_status()

    def next_frame(self) -> None:
        self.playback.reverse = False
        self.playback.step(1)
        self.update_frame()

    def previous_frame(self) -> None:
        was = self.playback.reverse
        self.playback.reverse = True
        self.playback.step(1)
        self.playback.reverse = was
        self.update_frame()

    def play(self) -> None:
        self.playback.play()
        self._refresh_status()

    def pause(self) -> None:
        self.playback.pause()
        self._refresh_status()

    def stop(self) -> None:
        self.playback.stop()
        self.update_frame(0)

    def set_speed(self, speed: float) -> None:
        self.playback.set_speed(speed)
        self._refresh_status()

    def seek(self, frame_index: int) -> None:
        self.update_frame(frame_index)

    def toggle_axes(self) -> None:
        self.scene.show_axes = not self.scene.show_axes
        self.update_frame()

    def toggle_grid(self) -> None:
        self.scene.show_grid = not self.scene.show_grid
        self.update_frame()

    def toggle_ground(self) -> None:
        self.scene.show_ground = not self.scene.show_ground
        self.update_frame()

    def toggle_joint_labels(self) -> None:
        self.show_joint_labels = not self.show_joint_labels
        self.update_frame()

    def toggle_bone_labels(self) -> None:
        self.show_bone_labels = not self.show_bone_labels
        self.update_frame()

    def screenshot(self, path: str | Path) -> Path:
        return self.renderer.screenshot(Path(path))

    def save_frame(self, path: str | Path) -> Path:
        return self.screenshot(path)

    def screenshot_4k(self, path: str | Path) -> Path:
        return self.renderer.screenshot(Path(path), scale=3)

    def screenshot_transparent(self, path: str | Path) -> Path:
        return self.renderer.screenshot(Path(path), transparent=True, scale=2)

    def start_recording(self) -> None:
        self._recording_frames = []
        self._is_recording = True

    def stop_recording(self, path: str | Path) -> Path:
        self._is_recording = False
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if not self._recording_frames:
            raise ViewerError("No frames recorded")
        try:
            import imageio.v2 as imageio
        except ImportError as exc:
            raise ViewerError("imageio is required for MP4 export") from exc
        fps = float(self.skeleton.sampling_rate_hz or 30.0) if self.skeleton else 30.0
        fps = min(max(fps * abs(self.playback.speed), 10.0), 60.0)
        imageio.mimsave(out, self._recording_frames, fps=fps)
        self._recording_frames = []
        return out

    # Camera UI ------------------------------------------------------------

    def camera_rotate_left(self) -> None:
        """Step to the next 90Â° orbital view (counter-clockwise)."""
        self.camera.rotate_left(animate=True)

    def camera_rotate_right(self) -> None:
        """Step to the previous 90Â° orbital view (clockwise)."""
        self.camera.rotate_right(animate=True)

    def camera_reset(self) -> None:
        self.camera.reset(animate=True)

    def set_camera_preset(self, preset: CameraPreset | str) -> None:
        if isinstance(preset, str):
            preset = CameraPreset(preset)
        self.camera.set_preset(preset, animate=True)

    # Internals ------------------------------------------------------------

    def _compute_bounds(self) -> None:
        assert self.skeleton is not None
        all_points: list[np.ndarray] = []
        for pose in self.skeleton.poses:
            for position in pose.joint_positions.values():
                if np.all(np.isfinite(position)):
                    all_points.append(np.asarray(position, dtype=float))

        if not all_points:
            self._bbox_center = np.zeros(3)
            self._bbox_extent = 1000.0
            self._ground_span = 2500.0
            self._floor_z = 0.0
            self._ground_origin = (0.0, 0.0, 0.0)
            self.camera.set_model_bounds(BoundingBox())
        else:
            arr = np.vstack(all_points)
            self._floor_z = float(arr[:, 2].min())
            horiz = arr[:, :2]
            horiz_mid = 0.5 * (horiz.min(axis=0) + horiz.max(axis=0))
            horiz_span = float(np.max(horiz.max(axis=0) - horiz.min(axis=0)))
            self._ground_span = max(horiz_span * 1.55, 2600.0)
            self._ground_origin = (
                float(horiz_mid[0]),
                float(horiz_mid[1]),
                float(self._floor_z),
            )
            pose0 = [
                np.asarray(p, dtype=float)
                for p in self.skeleton.poses[0].joint_positions.values()
                if np.all(np.isfinite(p))
            ]
            if pose0:
                p0 = np.vstack(pose0)
                self._bbox_center = 0.5 * (p0.min(axis=0) + p0.max(axis=0))
                self._bbox_extent = float(
                    np.max(p0.max(axis=0) - p0.min(axis=0)) * 0.5
                )
                body_bounds = BoundingBox.from_points(p0)
            else:
                self._bbox_center = 0.5 * (arr.min(axis=0) + arr.max(axis=0))
                self._bbox_extent = 1000.0
                body_bounds = BoundingBox.from_points(arr)
            self._bbox_extent = max(self._bbox_extent, 250.0)
            self.camera.set_model_bounds(body_bounds)

        self._joint_radius = float(
            np.clip(
                self._bbox_extent * DEFAULT_JOINT_RADIUS_RATIO,
                MIN_JOINT_RADIUS,
                MAX_JOINT_RADIUS,
            )
        )

    def _draw_frame(self, pose: Pose) -> None:
        assert self.skeleton is not None
        self.renderer.clear()

        ground_size = max(
            self._ground_span,
            self._bbox_extent * 2.0 * DEFAULT_GROUND_PADDING_RATIO,
        )
        if self.scene.show_ground:
            self.renderer.draw_ground(
                ground_size, self.theme.ground, origin=self._ground_origin
            )
        if self.scene.show_grid:
            self.renderer.draw_grid(
                ground_size,
                DEFAULT_GRID_DIVISIONS,
                self.theme.grid,
                origin=self._ground_origin,
            )

        live: list[np.ndarray] = []
        for position in pose.joint_positions.values():
            if np.all(np.isfinite(position)):
                live.append(np.asarray(position, dtype=float))
        if self.scene.show_axes:
            self.renderer.draw_axes(
                (
                    float(self._ground_origin[0]),
                    float(self._ground_origin[1]),
                    float(self._ground_origin[2]),
                ),
                self._bbox_extent * DEFAULT_AXES_LENGTH_RATIO,
            )

        draw_metallic = bool(
            getattr(self.avatar, "draws_procedural_skeleton", True)
        )
        if draw_metallic and self.show_bones:
            for bone_name, bone in self.skeleton.bones.items():
                start = pose.get_position(bone.parent_joint)
                end = pose.get_position(bone.child_joint)
                if start is None or end is None:
                    continue
                if not (np.all(np.isfinite(start)) and np.all(np.isfinite(end))):
                    continue
                color = (
                    self.theme.bone_highlight
                    if bone_name == self.selected_bone
                    else self.theme.bone
                )
                self.renderer.draw_line(
                    start, end, color, width=3.0, name=f"bone:{bone_name}"
                )
                if self.show_bone_labels:
                    mid = 0.5 * (np.asarray(start) + np.asarray(end))
                    self.renderer.draw_label_3d(
                        bone_name, mid, self.theme.label
                    )

        if draw_metallic and self.show_joints:
            for joint_name, position in pose.joint_positions.items():
                if not np.all(np.isfinite(position)):
                    continue
                color = (
                    self.theme.selected
                    if joint_name == self.selected_joint
                    else self.theme.joint
                )
                self.renderer.draw_sphere(
                    position,
                    self._joint_radius,
                    color,
                    name=f"joint:{joint_name}",
                )
                if self.show_joint_labels:
                    self.renderer.draw_label_3d(
                        joint_name, position, self.theme.label
                    )

        try:
            self.avatar.update(pose, skeleton=self.skeleton)
        except Exception:
            logger.debug("Avatar update failed", exc_info=True)

        if self.camera.is_dirty():
            self.renderer.set_camera(self.camera.get_state())
            self.camera.clear_dirty()

    def _refresh_status(self) -> None:
        if self._status_label is None or self.skeleton is None:
            return
        cam = self.camera.get_state()
        text = (
            f"  Camera: {cam.view_name}   |   "
            f"FPS: {self._fps:5.1f}   |   "
            f"Frame: {self.timeline.current_frame + 1}/{self.timeline.n_frames}   |   "
            f"Speed: {self.playback.speed:g}x   |   "
            f"Status: {self.playback.state.value.upper()}   "
        )
        self._status_label.setText(text)

    def _sync_playback_widgets(self) -> None:
        if self._frame_slider is not None:
            self._frame_slider.blockSignals(True)
            self._frame_slider.setValue(self.timeline.current_frame)
            self._frame_slider.blockSignals(False)

    def _run_headless_loop(self) -> None:
        rate = float(self.skeleton.sampling_rate_hz or 100.0) if self.skeleton else 100.0
        self._last_tick = time.perf_counter()
        while self.renderer.poll_events():
            now = time.perf_counter()
            dt = now - self._last_tick
            self._last_tick = now
            if dt > 0:
                self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt) if self._fps else 1.0 / dt
            self.camera.update(dt)
            animating = self.camera.is_animating() or self.camera.is_dirty()
            if self.playback.state is PlaybackState.PLAYING:
                self._accum += dt * abs(self.playback.speed) * rate
                steps = int(self._accum)
                if steps > 0:
                    self._accum -= steps
                    for _ in range(min(steps, 32)):
                        self.playback.step(1)
                    self.update_frame()
                elif animating:
                    self.update_frame()
            elif animating:
                self.update_frame()
        self.close()

    # ---- Qt UI -----------------------------------------------------------

    def _build_qt_application(self, title: str) -> None:
        from PyQt5 import QtCore, QtGui, QtWidgets
        from pyvistaqt import QtInteractor

        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
        self._qt_app = app

        window = QtWidgets.QMainWindow()
        window.setWindowTitle(title)
        window.resize(1680, 1000)
        window.setStyleSheet(self._qss())

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        plotter = QtInteractor(central)
        layout.addWidget(plotter.interactor, stretch=1)
        window.setCentralWidget(central)

        if not isinstance(self.renderer, PyVistaRenderer):
            self.renderer = PyVistaRenderer(theme=self.theme)
        self.renderer.attach_plotter(plotter)
        self.renderer.set_background(self.theme.background)

        self._build_toolbar(window)
        self._build_left_panel(window)
        self._build_right_panel(window)
        self._build_status_bar(window)
        self._bind_qt_keys(window)

        timer = QtCore.QTimer(window)
        timer.setTimerType(QtCore.Qt.PreciseTimer)
        timer.setInterval(RENDER_TICK_MS)
        timer.timeout.connect(self._on_qt_tick)
        timer.start()
        self._qt_timer = timer

        window.show()
        self._main_window = window

    def _qss(self) -> str:
        return """
        QMainWindow, QWidget {
            background-color: #1c1e22;
            color: #e8eaed;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            font-size: 12px;
        }
        QToolBar {
            background: #23262b;
            border: none;
            spacing: 8px;
            padding: 8px 12px;
        }
        QToolButton {
            background: #2f333a;
            border: 1px solid #3a3f47;
            border-radius: 8px;
            padding: 8px 14px;
            color: #e8eaed;
            font-weight: 600;
            letter-spacing: 0.4px;
        }
        QToolButton:hover { background: #3b424c; border-color: #5a8fd6; }
        QToolButton:pressed { background: #5a8fd6; color: #ffffff; }
        QDockWidget {
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
        }
        QDockWidget::title {
            background: #23262b;
            padding: 8px;
            font-weight: 600;
        }
        QSlider::groove:horizontal {
            height: 4px; background: #3a3f47; border-radius: 2px;
        }
        QSlider::handle:horizontal {
            width: 14px; margin: -6px 0; border-radius: 7px; background: #5a8fd6;
        }
        QCheckBox { spacing: 8px; }
        QStatusBar {
            background: #181a1e;
            border-top: 1px solid #2a2e35;
            color: #b8bdc5;
        }
        QPushButton {
            background: #2f333a;
            border: 1px solid #3a3f47;
            border-radius: 8px;
            padding: 7px 12px;
            font-weight: 600;
        }
        QPushButton:hover { background: #3b424c; }
        QPushButton:pressed { background: #5a8fd6; }
        """

    def _build_toolbar(self, window: Any) -> None:
        from PyQt5 import QtWidgets

        toolbar = window.addToolBar("Camera")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        style = window.style()

        left = toolbar.addAction("Rotate Left")
        left.setIcon(style.standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        left.setToolTip("Rotate camera left (90Â°)")
        left.triggered.connect(self.camera_rotate_left)

        right = toolbar.addAction("Rotate Right")
        right.setIcon(style.standardIcon(QtWidgets.QStyle.SP_ArrowRight))
        right.setToolTip("Rotate camera right (90Â°)")
        right.triggered.connect(self.camera_rotate_right)

        reset = toolbar.addAction("RESET")
        reset.setToolTip("Reset camera to front view")
        reset.triggered.connect(self.camera_reset)

        toolbar.addSeparator()
        shot = toolbar.addAction("SCREENSHOT")
        shot.triggered.connect(
            lambda: self.screenshot(Path("output") / "studio_shot.png")
        )
        shot4k = toolbar.addAction("4K")
        shot4k.triggered.connect(
            lambda: self.screenshot_4k(Path("output") / "studio_shot_4k.png")
        )

    def _build_left_panel(self, window: Any) -> None:
        from PyQt5 import QtWidgets

        dock = QtWidgets.QDockWidget("Scene", window)
        dock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetClosable
        )
        panel = QtWidgets.QWidget()
        form = QtWidgets.QVBoxLayout(panel)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        def add_toggle(text: str, checked: bool, slot: Any) -> None:
            box = QtWidgets.QCheckBox(text)
            box.setChecked(checked)
            box.toggled.connect(lambda _=False, s=slot: s())
            form.addWidget(box)

        add_toggle("Show Floor", self.scene.show_ground, self.toggle_ground)
        add_toggle("Show Grid", self.scene.show_grid, self.toggle_grid)
        add_toggle("Show Axes", self.scene.show_axes, self.toggle_axes)
        add_toggle("Show Joint Labels", self.show_joint_labels, self.toggle_joint_labels)
        add_toggle("Show Bone Labels", self.show_bone_labels, self.toggle_bone_labels)

        lighting = QtWidgets.QCheckBox("Studio Lighting")
        lighting.setChecked(True)

        def on_light(checked: bool) -> None:
            self.renderer.set_lighting_enabled(checked)
            self.update_frame()

        lighting.toggled.connect(on_light)
        form.addWidget(lighting)
        form.addStretch(1)
        dock.setWidget(panel)
        from PyQt5 import QtCore

        window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

    def _build_right_panel(self, window: Any) -> None:
        from PyQt5 import QtCore, QtWidgets

        dock = QtWidgets.QDockWidget("Playback", window)
        dock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetClosable
        )
        panel = QtWidgets.QWidget()
        form = QtWidgets.QVBoxLayout(panel)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        row = QtWidgets.QHBoxLayout()
        for text, slot in (
            ("Play", self.play),
            ("Pause", self.pause),
            ("Stop", self.stop),
        ):
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        form.addLayout(row)

        form.addWidget(QtWidgets.QLabel("Animation Speed"))
        speed = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        speed.setMinimum(25)
        speed.setMaximum(300)
        speed.setValue(100)
        speed.valueChanged.connect(lambda v: self.set_speed(v / 100.0))
        self._speed_slider = speed
        form.addWidget(speed)

        form.addWidget(QtWidgets.QLabel("Frame"))
        frame = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        frame.setMinimum(0)
        frame.setMaximum(max(self.timeline.n_frames - 1, 0))
        frame.valueChanged.connect(self.seek)
        self._frame_slider = frame
        form.addWidget(frame)

        loop = QtWidgets.QCheckBox("Loop")
        loop.setChecked(True)

        def on_loop(checked: bool) -> None:
            self.playback.loop = checked

        loop.toggled.connect(on_loop)
        self._loop_checkbox = loop
        form.addWidget(loop)

        rec_row = QtWidgets.QHBoxLayout()
        start_btn = QtWidgets.QPushButton("Record")
        stop_btn = QtWidgets.QPushButton("Save MP4")
        start_btn.clicked.connect(self.start_recording)
        stop_btn.clicked.connect(
            lambda: self.stop_recording(Path("output") / "motion.mp4")
        )
        rec_row.addWidget(start_btn)
        rec_row.addWidget(stop_btn)
        form.addLayout(rec_row)
        form.addStretch(1)
        dock.setWidget(panel)
        from PyQt5 import QtCore

        window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def _build_status_bar(self, window: Any) -> None:
        from PyQt5 import QtWidgets

        status = QtWidgets.QStatusBar()
        label = QtWidgets.QLabel("  Ready")
        status.addWidget(label, 1)
        window.setStatusBar(status)
        self._status_label = label

    def _bind_qt_keys(self, window: Any) -> None:
        from PyQt5 import QtCore, QtGui, QtWidgets

        def bind(seq: Any, slot: Any) -> None:
            action = QtWidgets.QAction(window)
            action.setShortcut(QtGui.QKeySequence(seq))
            action.triggered.connect(slot)
            window.addAction(action)

        bind("[", self.camera_rotate_left)
        bind("]", self.camera_rotate_right)
        bind("0", self.camera_reset)
        bind(QtCore.Qt.Key_Home, self.camera_reset)
        bind(QtCore.Qt.Key_Space, self._toggle_playback)
        bind(QtCore.Qt.Key_Right, self.next_frame)
        bind(QtCore.Qt.Key_Left, self.previous_frame)
        bind("P", self._toggle_playback)
        bind("G", self.toggle_grid)
        bind("A", self.toggle_axes)

    def _toggle_playback(self) -> None:
        if self.playback.state is PlaybackState.PLAYING:
            self.pause()
        else:
            self.play()

    def _on_qt_tick(self) -> None:
        now = time.perf_counter()
        dt = now - self._last_tick
        self._last_tick = now
        if dt > 0:
            self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt) if self._fps else 1.0 / dt

        self.camera.update(dt)
        animating = self.camera.is_animating() or self.camera.is_dirty()
        rate = (
            float(self.skeleton.sampling_rate_hz or 100.0) if self.skeleton else 100.0
        )

        if self.playback.state is PlaybackState.PLAYING:
            self._accum += dt * abs(self.playback.speed) * rate
            steps = int(self._accum)
            if steps > 0:
                self._accum -= steps
                for _ in range(min(steps, 32)):
                    self.playback.step(1)
                self.update_frame()
            elif animating:
                self.update_frame()
        elif animating:
            self.update_frame()
        else:
            self._status_refresh_accum += dt
            if self._status_refresh_accum >= 0.25:
                self._status_refresh_accum = 0.0
                self._refresh_status()


# Backward-compatible aliases
class Open3DViewer(SkeletonViewer):
    """Deprecated alias - routes to the PyVista studio viewer."""

    def __init__(self, *, theme: str | Theme = "studio", block: bool = True) -> None:
        super().__init__(theme=theme, backend="pyvista", block=block)


class MatplotlibViewer(SkeletonViewer):
    """Deprecated alias - routes to the PyVista studio viewer."""

    def __init__(self, *, theme: str | Theme = "studio", block: bool = True) -> None:
        super().__init__(theme=theme, backend="pyvista", block=block)


class PyVistaViewer(SkeletonViewer):
    """Explicit PyVista studio viewer."""

    def __init__(self, *, theme: str | Theme = "studio", block: bool = True) -> None:
        super().__init__(theme=theme, backend="pyvista", block=block)
