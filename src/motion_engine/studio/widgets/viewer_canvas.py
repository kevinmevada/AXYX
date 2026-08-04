"""Embedded PyVista motion viewport for AXYX.
Hosts the existing Motion Engine :class:`PyVistaRenderer` inside the studio
center panel so walking skeletons appear in the same application window.
"""
from __future__ import annotations
import logging
import os
import time
from typing import Any

import numpy as np
from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from motion_engine.colors import get_theme
from motion_engine.rendering.runtime.studio_viewport import DigitalTwinViewportBridge
from motion_engine.rendering.visualization import (
    AvatarRenderer,
    BoneRenderer,
    StickRenderer,
    VisualizationManager,
    VisualizationMode,
)
from motion_engine.renderer import PyVistaRenderer
from motion_engine.skeleton import Pose, Skeleton
from motion_engine.studio.widgets.error_banner import ErrorBanner
from motion_engine.studio.widgets.subject_info_hud import SubjectInfoHud
from motion_engine.studio.widgets.viewport_toolbar import ViewportToolbar
from motion_engine.viewer import SkeletonViewer
logger = logging.getLogger(__name__)
os.environ.setdefault("QT_API", "pyside6")

def _is_offscreen_platform() -> bool:
    platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    return platform in {"offscreen", "minimal", "null"}

class _AvatarPrepWorker(QThread):
    """Prepare retarget pipeline off the UI thread (no overlay)."""
    finished = Signal(object, str)
    def __init__(self, skeleton: Skeleton, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._skeleton = skeleton
    def run(self) -> None:
        bridge = DigitalTwinViewportBridge()
        try:
            ok = bridge.prepare(self._skeleton)
        except Exception as exc:  # noqa: BLE001
            self.finished.emit(None, str(exc))
            return
        if ok:
            self.finished.emit(bridge, "")
        else:
            self.finished.emit(None, bridge.error or "Avatar failed to load")

class ViewerCanvas(QFrame):
    """Center-panel PyVista viewport bound to studio playback."""

    sessionReadoutChanged = Signal(str)

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
        self._digital_twin_enabled = False
        self._viz_mode = VisualizationMode.STICK
        self._dt_bridge = DigitalTwinViewportBridge()
        self._prep_worker: _AvatarPrepWorker | None = None
        self._prep_token = 0
        self._drag_mode: str | None = None
        self._last_mouse = (0, 0)
        self._last_click_t = 0.0
        self._last_camera_tick = time.perf_counter()
        self._camera_obs: list[tuple[Any, str, int]] = []
        self._error = ErrorBanner()
        self.toolbar = ViewportToolbar()
        self.subject_info = SubjectInfoHud(self)
        self._viz = VisualizationManager(
            stick=StickRenderer(
                on_activate=self._activate_stick,
                on_deactivate=None,
            ),
            bones=BoneRenderer(),
            avatar=AvatarRenderer(
                on_activate=self._activate_avatar,
                on_deactivate=self._deactivate_avatar,
            ),
        )
        self._wire_toolbar()
        self._host = QWidget(self)
        self._host.setObjectName("ViewportStage")
        self._host.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._host_layout = QVBoxLayout(self._host)
        self._host_layout.setContentsMargins(0, 0, 0, 0)
        self._host_layout.setSpacing(0)
        # Subject clinical card lives ABOVE the OpenGL surface (not over it —
        # Qt widgets over the interactor blank the canvas on Windows).
        chrome = QWidget(self)
        chrome.setObjectName("ViewportChrome")
        chrome.setFixedHeight(0)
        chrome_layout = QHBoxLayout(chrome)
        chrome_layout.setContentsMargins(0, 8, 12, 0)
        chrome_layout.setSpacing(0)
        chrome_layout.addStretch(1)
        chrome_layout.addWidget(
            self.subject_info, alignment=Qt.AlignmentFlag.AlignTop
        )
        self._viewport_chrome = chrome
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._error)
        layout.addWidget(self._viewport_chrome)
        layout.addWidget(self._host, stretch=1)
        self._camera_timer = QTimer(self)
        self._camera_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._camera_timer.setInterval(8)
        self._camera_timer.timeout.connect(self._tick_camera)
        self._publish_readout("Select a session")

    def _publish_readout(self, text: str) -> None:
        self.sessionReadoutChanged.emit(text)

    def set_subject_info(
        self,
        subject_id: str | None,
        *,
        mass: float | None = None,
        height: float | None = None,
        sex: str | None = None,
    ) -> None:
        """Show mass / height / sex for the selected subject (top-right chrome)."""
        if not subject_id:
            self.clear_subject_info()
            return
        kwargs: dict[str, object] = {"mass": mass, "height": height}
        if sex is not None:
            kwargs["sex"] = sex
        self.subject_info.set_subject(subject_id, **kwargs)  # type: ignore[arg-type]
        self._viewport_chrome.setFixedHeight(max(self.subject_info.sizeHint().height() + 12, 72))

    def clear_subject_info(self) -> None:
        """Hide the subject clinical card."""
        self.subject_info.clear()
        self._viewport_chrome.setFixedHeight(0)

    def _wire_toolbar(self) -> None:
        self.toolbar.cameraPresetRequested.connect(self.set_camera_preset)
        self.toolbar.resetCameraRequested.connect(self.reset_camera)
        self.toolbar.gridToggled.connect(self.set_grid_visible)
        self.toolbar.axesToggled.connect(self.set_axes_visible)
        self.toolbar.groundToggled.connect(self.set_ground_visible)
        self.toolbar.lightingToggled.connect(self.set_lighting_enabled)
        self.toolbar.fullscreenRequested.connect(self._on_fullscreen)
        self.toolbar.visualizationChanged.connect(self.set_visualization)
        self.toolbar.digitalTwinToggled.connect(self._on_legacy_avatar_toggle)
        self.toolbar.set_visualization(self._viz_mode.value)
    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not _is_offscreen_platform():
            self._ensure_viewport()
            if self._pending_skeleton is not None:
                skeleton = self._pending_skeleton
                self._pending_skeleton = None
                self.set_skeleton(skeleton, self._frame)

    def _ensure_viewport(self) -> bool:
        if self._ready:
            return True
        if self._init_error is not None:
            return False
        if _is_offscreen_platform():
            self._publish_readout("3D viewport disabled on offscreen Qt platform.")
            return False
        try:
            from pyvistaqt import QtInteractor
            plotter = QtInteractor(self._host)
            self._host_layout.addWidget(plotter.interactor)
            theme = get_theme("studio")
            renderer = PyVistaRenderer(theme=theme)
            renderer.attach_plotter(plotter)
            # Museum White void + soft floor plane under the walk.
            plotter.set_background("#FFFFFF", top="#FFFFFF")
            renderer.set_background(theme.background)
            if hasattr(renderer, "scene"):
                renderer.scene.show_grid = False
                renderer.scene.show_ground = True
            self._plotter = plotter
            self._renderer = renderer
            self._viewer = SkeletonViewer(
                renderer=renderer,
                theme=theme,
                backend="pyvista",
                block=False,
            )
            self._viewer.body_callback = self._draw_body
            self._viz.bind(plotter, theme=theme)
            self._viz.set_mode(VisualizationMode.STICK)
            try:
                self._install_clinical_camera(plotter)
            except Exception:
                logger.exception("Clinical camera controls failed")
            self._camera_timer.start()
            self._ready = True
            logger.info("Embedded PyVista viewport ready")
            return True
        except Exception as exc:  # noqa: BLE001
            self._init_error = str(exc)
            logger.exception("Failed to initialize embedded viewport")
            self._error.show_error(
                "Viewport unavailable",
                f"{exc}. Install pyvista / pyvistaqt in venv311.",
            )
            self._publish_readout("3D viewport could not start.")
            return False
    def _install_clinical_camera(self, plotter: Any) -> None:
        iren = getattr(plotter, "iren", None)
        if iren is None:
            return
        try:
            from vtkmodules.vtkInteractionStyle import vtkInteractorStyleUser
        except Exception:
            try:
                from vtk.vtkInteractionStyle import vtkInteractorStyleUser  # type: ignore
            except Exception:
                return
        try:
            iren.style = vtkInteractorStyleUser()
        except Exception:
            try:
                iren.interactor.SetInteractorStyle(vtkInteractorStyleUser())
            except Exception:
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
        if self._viewer is None or self._viewer.skeleton is None:
            return
        now = time.perf_counter()
        dt = now - self._last_camera_tick
        self._last_camera_tick = now
        cam = self._viewer.camera
        cam.update(dt)
        if cam.is_dirty() or cam.is_animating():
            try:
                self._viewer.update_frame()
            except Exception:
                logger.debug("Camera tick failed", exc_info=True)
    def _draw_body(self, pose: Pose) -> None:
        """Body callback — avatar mesh or anatomical bone transforms."""
        if self._viz_mode == VisualizationMode.AVATAR:
            self._draw_avatar_body(pose)
            return
        if self._viz_mode == VisualizationMode.BONES:
            self._viz.render_pose(pose)
            if self._renderer is None or not self._viz.bones._show_joints:
                return
            theme = self._viewer.theme if self._viewer is not None else None
            joint_rgb = theme.joint if theme is not None else (0.36, 0.29, 0.86)
            for joint_name, position in pose.joint_positions.items():
                if not np.all(np.isfinite(position)):
                    continue
                self._renderer.draw_sphere(
                    position,
                    10.0,
                    joint_rgb,
                    name=f"joint:{joint_name}",
                )

    def _activate_stick(self) -> None:
        self._digital_twin_enabled = False
        self._viz.bones.deactivate()
        if self._renderer is not None:
            self._renderer.clear_avatar()
        if self._viewer is not None:
            self._viewer.show_body = False
            self._viewer.show_bones = True
            self._viewer.show_joints = True
            if self._viewer.skeleton is not None:
                self._viewer.update_frame(self._frame)

    def _activate_avatar(self) -> None:
        self._digital_twin_enabled = True
        self._viz.bones.deactivate()
        if self._dt_bridge.ready:
            self._attach_avatar()
        elif self._skeleton is not None:
            self._begin_avatar_prep(self._skeleton)

    def _deactivate_avatar(self) -> None:
        self._digital_twin_enabled = False
        self._cancel_avatar_prep()
        self._detach_avatar()

    def _activate_bones(self) -> bool:
        """Enable anatomical skeleton. Returns False on asset failure."""
        self._digital_twin_enabled = False
        self._cancel_avatar_prep()
        if self._renderer is not None:
            self._renderer.clear_avatar()
        self._viz.bones.bind(self._plotter, theme=None)
        self._viz.bones.activate()
        if not self._viz.bones.ready:
            return False
        if self._viewer is not None:
            self._viewer.show_body = True
            self._viewer.show_bones = False
            self._viewer.show_joints = False
            if self._viewer.skeleton is not None:
                self._viewer.update_frame(self._frame)
        return True

    def set_visualization(self, mode: str | VisualizationMode) -> None:
        """Switch stick / bones / avatar without resetting camera or playback."""
        try:
            target = VisualizationMode.parse(mode)
        except ValueError:
            logger.warning("Unknown visualization mode: %s", mode)
            return
        if target == self._viz_mode and (
            target != VisualizationMode.BONES or self._viz.bones.active
        ):
            self.toolbar.set_visualization(target.value)
            return

        # Deactivate current mode's exclusive resources.
        if self._viz_mode == VisualizationMode.AVATAR:
            self._deactivate_avatar()
        elif self._viz_mode == VisualizationMode.BONES:
            self._viz.bones.deactivate()

        applied = target
        if target == VisualizationMode.STICK:
            self._activate_stick()
        elif target == VisualizationMode.BONES:
            if not self._activate_bones():
                self._error.show_error(
                    "Bone anatomy unavailable",
                    "Could not install anatomical meshes — using stick figure.",
                )
                self._activate_stick()
                applied = VisualizationMode.STICK
        elif target == VisualizationMode.AVATAR:
            if self._skeleton is None:
                self._error.show_error("Avatar unavailable", "Load a session first.")
                self._activate_stick()
                applied = VisualizationMode.STICK
            else:
                self._activate_avatar()

        self._viz_mode = applied
        self._viz._mode = applied  # keep manager in sync
        self.toolbar.set_visualization(applied.value)

    def _on_legacy_avatar_toggle(self, enabled: bool) -> None:
        # Ignore echoes from set_visualization → toolbar sync.
        if enabled and self._viz_mode == VisualizationMode.AVATAR:
            return
        if not enabled and self._viz_mode != VisualizationMode.AVATAR:
            return
        self.set_visualization(
            VisualizationMode.AVATAR if enabled else VisualizationMode.STICK
        )

    def _draw_avatar_body(self, pose: Pose) -> None:
        """Same frame tick as stick figure — mesh + head/toe markers."""
        if self._renderer is None or not self._dt_bridge.ready:
            return
        mesh_pts, landmarks = self._dt_bridge.frame_package(pose.frame_index)
        if mesh_pts is not None:
            self._renderer.draw_avatar_body(mesh_pts)
        head = landmarks.get("head")
        if head is not None:
            self._renderer.draw_sphere(
                head,
                22.0 * max(self._dt_bridge._stage_scale * 0.02, 1.0),
                (1.0, 0.25, 0.25),
                name="avatar:head",
            )
        for key, color in (
            ("foot_l", (0.3, 0.55, 1.0)),
            ("foot_r", (0.3, 0.55, 1.0)),
            ("ball_l", (0.15, 0.35, 0.9)),
            ("ball_r", (0.15, 0.35, 0.9)),
        ):
            pt = landmarks.get(key)
            if pt is not None:
                self._renderer.draw_sphere(
                    pt,
                    14.0 * max(self._dt_bridge._stage_scale * 0.02, 1.0),
                    color,
                    name=f"avatar:{key}",
                )
    def _attach_avatar(self) -> None:
        if self._viewer is None or self._renderer is None or not self._dt_bridge.ready:
            return
        faces = self._dt_bridge.pv_faces()
        if faces is not None:
            self._renderer.set_avatar_topology(faces, self._dt_bridge.vertex_count)
        self._viewer.show_body = True
        self._viewer.show_bones = False
        self._viewer.show_joints = False
        self._viewer.update_frame(self._frame)
    def _detach_avatar(self) -> None:
        if self._viewer is not None:
            self._viewer.show_body = False
            self._viewer.show_bones = True
            self._viewer.show_joints = True
        if self._renderer is not None:
            self._renderer.clear_avatar()
        if self._viewer is not None and self._viewer.skeleton is not None:
            self._viewer.update_frame(self._frame)
    def _cancel_avatar_prep(self) -> None:
        worker = self._prep_worker
        self._prep_worker = None
        if worker is not None and worker.isRunning():
            worker.quit()
            worker.wait(1500)
    def _begin_avatar_prep(self, skeleton: Skeleton) -> None:
        self._cancel_avatar_prep()
        self._prep_token += 1
        token = self._prep_token
        self._publish_readout(
            f"{skeleton.subject_id}/{skeleton.session_name} | "
            f"{skeleton.frame_count}f | Avatar loading…"
        )
        worker = _AvatarPrepWorker(skeleton, self)
        self._prep_worker = worker
        worker.finished.connect(
            lambda bridge, err: self._on_avatar_prep_done(token, bridge, err)
        )
        worker.start()
    def _on_avatar_prep_done(self, token: int, bridge: object, error: str) -> None:
        if token != self._prep_token:
            return
        self._prep_worker = None
        sk = self._skeleton
        if sk is not None:
            self._publish_readout(
                f"{sk.subject_id}/{sk.session_name} | {sk.frame_count}f"
            )
        if not self._digital_twin_enabled:
            return
        if bridge is None or not getattr(bridge, "ready", False):
            self._error.show_error("Avatar unavailable", error or "Load failed")
            self._digital_twin_enabled = False
            if hasattr(self.toolbar, "_avatar_btn"):
                self.toolbar._avatar_btn.blockSignals(True)
                self.toolbar._avatar_btn.setChecked(False)
                self.toolbar._avatar_btn.blockSignals(False)
            return
        self._dt_bridge = bridge  # type: ignore[assignment]
        if sk is not None:
            mode = "bind pose" if self._dt_bridge.use_bind_pose else "retarget"
            avatar_name = self._dt_bridge.avatar_label or "avatar"
            self._publish_readout(
                f"{sk.subject_id}/{sk.session_name} | {sk.frame_count}f | "
                f"{avatar_name.title()} {self._dt_bridge.vertex_count}v ({mode})"
            )
        self._error.hide()
        self._attach_avatar()
        # Do not reset camera — visualization switches must preserve framing.
    def set_skeleton(self, skeleton: Skeleton | None, frame: int = 0) -> None:
        """Load a skeleton — same playback path for stick and avatar."""
        same = (
            skeleton is not None
            and self._skeleton is not None
            and skeleton.subject_id == self._skeleton.subject_id
            and skeleton.session_name == self._skeleton.session_name
            and skeleton.frame_count == self._skeleton.frame_count
            and self._viewer is not None
            and self._viewer.skeleton is not None
        )
        if same:
            self.set_frame(frame)
            return
        self._cancel_avatar_prep()
        self._skeleton = skeleton
        self._frame = frame
        if skeleton is None:
            self._detach_avatar()
            self._dt_bridge.clear()
            self._publish_readout("Select a session")
            self._pending_skeleton = None
            self._error.hide()
            return
        if not self.isVisible() or not self._ensure_viewport() or self._viewer is None:
            self._pending_skeleton = skeleton
            self._publish_readout(f"{skeleton.subject_id}/{skeleton.session_name}")
            return
        self._pending_skeleton = None
        self._dt_bridge.clear()
        self._detach_avatar()
        self._publish_readout(
            f"{skeleton.subject_id}/{skeleton.session_name} | {skeleton.frame_count}f"
        )
        try:
            self._viewer.show(skeleton)
            self._viewer.pause()
            self.set_frame(frame)
            self.reset_camera()
            self._error.hide()
            if self._viz_mode == VisualizationMode.AVATAR:
                self._begin_avatar_prep(skeleton)
            elif self._viz_mode == VisualizationMode.BONES:
                self._activate_bones()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to show skeleton in embedded viewport")
            self._error.show_error("Failed to load skeleton", str(exc))
            self._publish_readout("Skeleton could not be rendered.")
    def set_frame(self, frame: int) -> None:
        """Seek — stick and avatar share this single code path."""
        self._frame = frame
        if self._viewer is None or self._viewer.skeleton is None:
            return
        try:
            self._viewer.seek(int(frame))
        except Exception:
            logger.debug("Embedded seek failed", exc_info=True)
    def set_digital_twin_enabled(self, enabled: bool) -> None:
        """Backward-compatible avatar toggle → visualization mode."""
        self.set_visualization(
            VisualizationMode.AVATAR if enabled else VisualizationMode.STICK
        )
    def reset_camera(self) -> None:
        if self._viewer is None:
            return
        try:
            self._viewer.camera.reset(animate=True)
            self._viewer.update_frame()
        except Exception:
            logger.debug("Camera reset failed", exc_info=True)
    def fit_camera(self) -> None:
        if self._viewer is None:
            return
        try:
            self._viewer.camera.focus_subject(animate=True)
            self._viewer.update_frame()
        except Exception:
            logger.debug("Camera fit failed", exc_info=True)
    def set_camera_preset(self, preset: str) -> None:
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
        self.set_skeleton(skeleton, frame=0)
    def _on_fullscreen(self) -> None:
        window = self.window()
        if window is None:
            return
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()
