"""AXYX Skinning Debug Studio — PySide6 + PyVista engineering viewer.

Run::

    python -m experiments.skinning_debug.run --army-girl
    python -m experiments.skinning_debug.run --fixture
    python -m experiments.skinning_debug.run --lod 3
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Prefer PySide6 for pyvistaqt before any Qt / VTK Qt imports (PyQt5 is also present).
os.environ["QT_API"] = "pyside6"

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from motion_engine.rendering.avatar.skinning.debug.heatmap import (  # noqa: E402
    weight_heatmap_rgb,
)
from motion_engine.rendering.avatar.skinning.debug.session import (  # noqa: E402
    SkinningDebugSession,
)


class SkinningDebugWindow(QMainWindow):
    """Interactive M4 skinning validation UI."""

    def __init__(self, session: SkinningDebugSession) -> None:
        super().__init__()
        self.setWindowTitle("AXYX Skinning Debug Studio")
        self.resize(1280, 800)
        self.session = session

        splitter = QSplitter()
        self.setCentralWidget(splitter)

        # --- viewport ---
        view = QWidget()
        vlayout = QVBoxLayout(view)
        self.plotter = QtInteractor(view)
        self._install_turntable_camera()
        vlayout.addWidget(self.plotter.interactor)
        splitter.addWidget(view)

        # --- side panel ---
        panel = QWidget()
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(400)
        form = QVBoxLayout(panel)

        title = QLabel("Skinning Debug")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        form.addWidget(title)

        # Mesh toggles
        mesh_box = QGroupBox("Mesh")
        mesh_l = QVBoxLayout(mesh_box)
        self.chk_mesh = QCheckBox("Show Mesh")
        self.chk_mesh.setChecked(True)
        self.chk_wire = QCheckBox("Wireframe")
        self.chk_heatmap = QCheckBox("Weight Heatmap")
        for w in (self.chk_mesh, self.chk_wire, self.chk_heatmap):
            mesh_l.addWidget(w)
            w.toggled.connect(self._refresh)
        form.addWidget(mesh_box)

        # Skeleton
        skel_box = QGroupBox("Skeleton")
        skel_l = QVBoxLayout(skel_box)
        self.chk_bones = QCheckBox("Bones")
        self.chk_bones.setChecked(True)
        self.chk_joints = QCheckBox("Joints")
        self.chk_joints.setChecked(True)
        for w in (self.chk_bones, self.chk_joints):
            skel_l.addWidget(w)
            w.toggled.connect(self._refresh)
        form.addWidget(skel_box)

        # Bone picker + rotation
        pose_box = QGroupBox("Pose")
        pose_l = QFormLayout(pose_box)
        self.bone_combo = QComboBox()
        self.bone_combo.addItems(session.bone_names)
        if session.selected_bone:
            idx = self.bone_combo.findText(session.selected_bone)
            if idx >= 0:
                self.bone_combo.setCurrentIndex(idx)
        self.bone_combo.currentTextChanged.connect(self._on_bone_changed)
        pose_l.addRow("Bone", self.bone_combo)

        self.sliders: dict[str, QSlider] = {}
        self.spin: dict[str, QDoubleSpinBox] = {}
        for axis in ("X", "Y", "Z"):
            row = QHBoxLayout()
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(-180, 180)
            sl.setValue(0)
            sp = QDoubleSpinBox()
            sp.setRange(-180, 180)
            sp.setDecimals(1)
            sp.setSuffix("°")
            sl.valueChanged.connect(lambda v, a=axis, s=sp: (s.blockSignals(True), s.setValue(v), s.blockSignals(False), self._on_rot()))
            sp.valueChanged.connect(lambda v, a=axis, s=sl: (s.blockSignals(True), s.setValue(int(v)), s.blockSignals(False), self._on_rot()))
            self.sliders[axis] = sl
            self.spin[axis] = sp
            row.addWidget(sl)
            row.addWidget(sp)
            pose_l.addRow(axis, row)

        btn_reset = QPushButton("Reset to Bind")
        btn_reset.clicked.connect(self._reset)
        pose_l.addRow(btn_reset)
        form.addWidget(pose_box)

        # M5 Animation
        anim_box = QGroupBox("Animation")
        anim_l = QFormLayout(anim_box)
        self.clip_combo = QComboBox()
        try:
            clip_names = session.ensure_animation_library()
        except Exception as exc:  # noqa: BLE001
            print(f"Animation library unavailable: {exc}", file=sys.stderr)
            clip_names = []
        self.clip_combo.addItems(clip_names)
        self.clip_combo.currentTextChanged.connect(self._on_clip_changed)
        anim_l.addRow("Clip", self.clip_combo)

        row_btns = QHBoxLayout()
        self.btn_play = QPushButton("Play")
        self.btn_pause = QPushButton("Pause")
        self.btn_stop = QPushButton("Stop")
        self.btn_play.clicked.connect(self._anim_play)
        self.btn_pause.clicked.connect(self._anim_pause)
        self.btn_stop.clicked.connect(self._anim_stop)
        for b in (self.btn_play, self.btn_pause, self.btn_stop):
            row_btns.addWidget(b)
        anim_l.addRow(row_btns)

        self.chk_loop = QCheckBox("Loop")
        self.chk_loop.setChecked(True)
        self.chk_loop.toggled.connect(lambda v: session.anim_set_loop(v))
        anim_l.addRow(self.chk_loop)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.valueChanged.connect(self._on_time_slider)
        anim_l.addRow("Timeline", self.time_slider)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.05, 4.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)
        self.speed_spin.valueChanged.connect(lambda v: session.anim_set_speed(float(v)))
        anim_l.addRow("Speed", self.speed_spin)

        self.anim_info = QLabel("t=0.00  frame=0  fps=—")
        anim_l.addRow(self.anim_info)
        form.addWidget(anim_box)

        # M6 Retarget
        retarget_box = QGroupBox("Retarget")
        retarget_l = QFormLayout(retarget_box)
        self.retarget_profile = QComboBox()
        self.retarget_profile.addItems(
            ["matlab_clinical_to_army_girl", "test_two_bone", "matlab_clinical_to_metahuman"]
        )
        retarget_l.addRow("Mapping", self.retarget_profile)

        self.retarget_root = QComboBox()
        self.retarget_root.addItems(["world", "in_place", "extract"])
        retarget_l.addRow("Root motion", self.retarget_root)

        self.chk_retarget_overlay = QCheckBox("Source overlay")
        self.chk_retarget_overlay.setChecked(True)
        retarget_l.addRow(self.chk_retarget_overlay)

        self.chk_retarget_mirror = QCheckBox("Mirror gait")
        retarget_l.addRow(self.chk_retarget_mirror)

        row_rt = QHBoxLayout()
        self.btn_retarget_play = QPushButton("Play Gait")
        self.btn_retarget_stop = QPushButton("Stop")
        self.btn_retarget_play.clicked.connect(self._retarget_play)
        self.btn_retarget_stop.clicked.connect(self._retarget_stop)
        row_rt.addWidget(self.btn_retarget_play)
        row_rt.addWidget(self.btn_retarget_stop)
        retarget_l.addRow(row_rt)

        self.retarget_info = QLabel("Retarget idle")
        self.retarget_info.setWordWrap(True)
        retarget_l.addRow(self.retarget_info)
        form.addWidget(retarget_box)

        self._retarget_demo = None
        self._source_overlay_actor = None
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._retarget_timer = QTimer(self)
        self._retarget_timer.setInterval(33)
        self._retarget_timer.timeout.connect(self._retarget_tick)

        # Diagnostics
        diag = QGroupBox("Diagnostics")
        diag_l = QVBoxLayout(diag)
        self.diag_label = QLabel()
        self.diag_label.setWordWrap(True)
        self.status_label = QLabel("PASS ✓")
        self.status_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        diag_l.addWidget(self.status_label)
        diag_l.addWidget(self.diag_label)
        form.addWidget(diag)
        form.addStretch(1)

        splitter.addWidget(panel)
        splitter.setStretchFactor(0, 1)

        self._mesh_actor = None
        self._bone_actor = None
        self._joint_actor = None
        self._camera_framed = False
        self._orbit_center = np.array([0.0, 0.0, 80.0], dtype=np.float64)
        self._char_yaw_deg = 0.0
        self.plotter.add_axes()
        self.plotter.set_background("#1a1a1e")
        self._reset()

    def _install_turntable_camera(self) -> None:
        """Hard-lock lobby camera: drag only yaws the character."""
        try:
            from vtkmodules.vtkInteractionStyle import vtkInteractorStyleUser
        except ImportError:  # pragma: no cover
            try:
                from vtk.vtkInteractionStyle import vtkInteractorStyleUser  # type: ignore
            except ImportError:
                return

        window = self
        plotter = self.plotter
        self._drag_prev_x: int | None = None

        style = vtkInteractorStyleUser()
        iren = getattr(plotter, "iren", None)
        if iren is None:
            return

        def _on_left_press(_obj, _evt) -> None:
            inter = getattr(iren, "interactor", iren)
            try:
                x, _y = inter.GetEventPosition()
            except Exception:  # noqa: BLE001
                return
            window._drag_prev_x = int(x)

        def _on_left_release(_obj, _evt) -> None:
            window._drag_prev_x = None

        def _on_mouse_move(_obj, _evt) -> None:
            if window._drag_prev_x is None:
                return
            inter = getattr(iren, "interactor", iren)
            try:
                x, _y = inter.GetEventPosition()
            except Exception:  # noqa: BLE001
                return
            dx = float(x - window._drag_prev_x)
            window._drag_prev_x = int(x)
            if abs(dx) < 1e-6:
                return
            window._char_yaw_deg = (window._char_yaw_deg - 0.35 * dx) % 360.0
            window._refresh()

        def _dolly(factor: float) -> None:
            pose = getattr(window, "_locked_cam", None)
            if not pose:
                return
            focal = np.asarray(pose["focal"], dtype=np.float64)
            pos = np.asarray(pose["position"], dtype=np.float64)
            offset = pos - focal
            dist = float(np.linalg.norm(offset))
            if dist < 1e-6:
                return
            span = float(getattr(window, "_model_span", 200.0))
            new_dist = float(np.clip(dist * factor, span * 0.55, span * 8.0))
            direction = offset / dist
            new_pos = focal + direction * new_dist
            pose["position"] = (float(new_pos[0]), float(new_pos[1]), float(new_pos[2]))
            window._apply_locked_camera()
            try:
                window.plotter.render()
            except Exception:  # noqa: BLE001
                pass

        def _on_wheel_forward(_obj, _evt) -> None:
            _dolly(0.88)

        def _on_wheel_backward(_obj, _evt) -> None:
            _dolly(1.12)

        try:
            iren.style = style
        except Exception:  # noqa: BLE001
            try:
                inter = getattr(iren, "interactor", iren)
                inter.SetInteractorStyle(style)
            except Exception:  # noqa: BLE001
                pass

        # Observe on the real VTK interactor.
        inter = getattr(iren, "interactor", None) or getattr(plotter, "interactor", None)
        target = inter if inter is not None else iren
        for event, handler in (
            ("LeftButtonPressEvent", _on_left_press),
            ("LeftButtonReleaseEvent", _on_left_release),
            ("MouseMoveEvent", _on_mouse_move),
            ("MouseWheelForwardEvent", _on_wheel_forward),
            ("MouseWheelBackwardEvent", _on_wheel_backward),
        ):
            try:
                target.AddObserver(event, handler)
            except Exception:  # noqa: BLE001
                pass

        try:
            plotter.camera.up = (0.0, 0.0, 1.0)
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def _rotate_yaw_z(points: np.ndarray, yaw_deg: float) -> np.ndarray:
        """Rotate points around world Z through the origin (character spin)."""
        pts = np.asarray(points, dtype=np.float64)
        if abs(yaw_deg) < 1e-9:
            return pts.copy()
        rad = np.deg2rad(float(yaw_deg))
        c, s = float(np.cos(rad)), float(np.sin(rad))
        out = pts.copy()
        x = pts[..., 0]
        y = pts[..., 1]
        out[..., 0] = c * x - s * y
        out[..., 1] = s * x + c * y
        return out

    def _grounded_positions(self, positions: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        """Center XY on origin and put feet on z=0. Returns (pts, center, span)."""
        pts = np.asarray(positions, dtype=np.float64).copy()
        mn = pts.min(axis=0)
        mx = pts.max(axis=0)
        pts[:, 2] -= mn[2]
        mid_xy = 0.5 * (mn[:2] + mx[:2])
        pts[:, 0] -= mid_xy[0]
        pts[:, 1] -= mid_xy[1]
        mn2 = pts.min(axis=0)
        mx2 = pts.max(axis=0)
        center = 0.5 * (mn2 + mx2)
        center[2] = max(center[2] * 0.55, (mx2[2] - mn2[2]) * 0.35)
        span = float(np.linalg.norm(mx2 - mn2))
        return pts, center, max(span, 1.0)

    def _add_floor(self, span: float) -> None:
        """Studio floor plane at z=0 under the grounded character."""
        size = max(span * 2.8, 120.0)
        floor = pv.Plane(
            center=(0.0, 0.0, 0.0),
            direction=(0.0, 0.0, 1.0),
            i_size=size,
            j_size=size,
            i_resolution=1,
            j_resolution=1,
        )
        self.plotter.add_mesh(
            floor,
            color="#2a2a30",
            opacity=1.0,
            smooth_shading=True,
            show_edges=False,
            name="floor",
        )
        # Subtle grid ring for scale reference
        grid = pv.Plane(
            center=(0.0, 0.0, 0.02),
            direction=(0.0, 0.0, 1.0),
            i_size=size * 0.85,
            j_size=size * 0.85,
            i_resolution=12,
            j_resolution=12,
        )
        self.plotter.add_mesh(
            grid,
            color="#3a3a42",
            style="wireframe",
            opacity=0.35,
            line_width=1,
            name="floor_grid",
        )

    def _frame_camera(self) -> None:
        """Store and apply a fixed upright lobby camera pose."""
        center = np.asarray(self._orbit_center, dtype=np.float64)
        span = float(getattr(self, "_model_span", 200.0))
        dist = max(span * 1.85, 120.0)
        self._locked_cam = {
            "focal": (float(center[0]), float(center[1]), float(center[2])),
            "position": (
                float(center[0]),
                float(center[1] - dist),
                float(center[2] + span * 0.12),
            ),
            "up": (0.0, 0.0, 1.0),
        }
        self._apply_locked_camera()
        self._camera_framed = True

    def _apply_locked_camera(self) -> None:
        """Force camera back to the upright lobby pose every frame."""
        pose = getattr(self, "_locked_cam", None)
        if not pose:
            return
        try:
            cam = self.plotter.renderer.GetActiveCamera()
            cam.SetViewUp(*pose["up"])
            cam.SetFocalPoint(*pose["focal"])
            cam.SetPosition(*pose["position"])
            cam.OrthogonalizeViewUp()
            self.plotter.renderer.ResetCameraClippingRange()
            self.plotter.camera.up = pose["up"]
        except Exception:  # noqa: BLE001
            pass

    def _pin_orbit_center(self) -> None:
        self._apply_locked_camera()

    def _on_bone_changed(self, name: str) -> None:
        self.session.selected_bone = name
        # reset sliders when changing bone (bind-relative edits)
        for axis in ("X", "Y", "Z"):
            self.sliders[axis].blockSignals(True)
            self.spin[axis].blockSignals(True)
            self.sliders[axis].setValue(0)
            self.spin[axis].setValue(0)
            self.sliders[axis].blockSignals(False)
            self.spin[axis].blockSignals(False)
        self._on_rot()

    def _on_rot(self) -> None:
        bone = self.bone_combo.currentText()
        if not bone:
            return
        self.session.set_bone_euler(
            bone,
            x=float(self.spin["X"].value()),
            y=float(self.spin["Y"].value()),
            z=float(self.spin["Z"].value()),
        )
        self._refresh()

    def _retarget_play(
        self,
        *,
        subject: str | None = None,
        session: str | None = None,
        mat_path: str | None = None,
    ) -> None:
        from motion_engine.rendering.avatar.retarget import RootMotionMode
        from experiments.skinning_debug.retarget_demo import RetargetDemo, load_clinical_motions

        self._anim_timer.stop()
        self.session.anim_enabled = False
        mode = {
            "world": RootMotionMode.WORLD,
            "in_place": RootMotionMode.IN_PLACE,
            "extract": RootMotionMode.EXTRACT,
        }[self.retarget_root.currentText()]
        demo = RetargetDemo()
        demo.mirrored = self.chk_retarget_mirror.isChecked()
        demo.overlay_source = self.chk_retarget_overlay.isChecked()
        clinical = None
        if subject and session:
            clinical = load_clinical_motions(subject, session, mat_path=mat_path)
        try:
            kwargs: dict = {
                "root_mode": mode,
                "profile_name": self.retarget_profile.currentText(),
            }
            if clinical is not None:
                motions, source, fps = clinical
                kwargs["clinical_motions"] = motions
                kwargs["clinical_source"] = source
                kwargs["fps"] = fps
            demo.setup(
                self.session.skeleton,
                self.session.bind,
                **kwargs,
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Retarget", str(exc))
            return
        demo.playing = True
        demo.mirrored = self.chk_retarget_mirror.isChecked()
        self._retarget_demo = demo
        self._retarget_timer.start()
        src = demo.motion_source
        self.retarget_info.setText(f"Retarget playing ({src})")
        self._retarget_tick()

    def _retarget_stop(self) -> None:
        self._retarget_timer.stop()
        if self._retarget_demo is not None:
            self._retarget_demo.playing = False
        self._retarget_demo = None
        if self._source_overlay_actor is not None:
            try:
                self.plotter.remove_actor(self._source_overlay_actor)
            except Exception:  # noqa: BLE001
                pass
            self._source_overlay_actor = None
        self.retarget_info.setText("Retarget idle")

    def _retarget_tick(self) -> None:
        demo = self._retarget_demo
        if demo is None:
            return
        demo.mirrored = self.chk_retarget_mirror.isChecked()
        demo.overlay_source = self.chk_retarget_overlay.isChecked()
        pose = demo.tick()
        if pose is None:
            return
        self.session.pose = pose
        self.session.anim_enabled = False
        self.session.deform()
        self.retarget_info.setText(demo.info_text())
        self._refresh()

    def _reset(self) -> None:
        self._anim_timer.stop()
        self._retarget_stop()
        for axis in ("X", "Y", "Z"):
            self.sliders[axis].blockSignals(True)
            self.spin[axis].blockSignals(True)
            self.sliders[axis].setValue(0)
            self.spin[axis].setValue(0)
            self.sliders[axis].blockSignals(False)
            self.spin[axis].blockSignals(False)
        self.session.reset()
        self._camera_framed = False
        self._char_yaw_deg = 0.0
        self._refresh()
        self._frame_camera()

    def _on_clip_changed(self, name: str) -> None:
        if not name:
            return
        self._anim_timer.stop()
        try:
            self.session.load_anim_clip(name)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Clip load failed", str(exc))
            return
        self._sync_timeline_slider()
        self._refresh()

    def _anim_play(self) -> None:
        self.session.anim_play()
        self._anim_timer.start()

    def _anim_pause(self) -> None:
        self.session.anim_pause()
        self._anim_timer.stop()
        self._refresh()

    def _anim_stop(self) -> None:
        self._anim_timer.stop()
        self.session.anim_stop()
        self._sync_timeline_slider()
        self._refresh()

    def _anim_tick(self) -> None:
        self.session.anim_tick(self._anim_timer.interval() / 1000.0)
        self._sync_timeline_slider()
        self._refresh()

    def _on_time_slider(self, value: int) -> None:
        player = self.session.anim_player
        if player is None or player.clip is None:
            return
        if self._anim_timer.isActive():
            return
        t = (value / 1000.0) * max(player.clip.duration, 1e-6)
        self.session.anim_seek(t)
        self._refresh()

    def _sync_timeline_slider(self) -> None:
        player = self.session.anim_player
        if player is None or player.clip is None:
            return
        dur = max(player.clip.duration, 1e-6)
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(int(round(1000.0 * player.time / dur)))
        self.time_slider.blockSignals(False)
        fps = player.clip.fps
        self.anim_info.setText(
            f"t={player.time:.2f}s  frame={player.frame}  fps={fps:.1f}  [{player.state.name}]"
        )

    def _refresh(self) -> None:
        session = self.session
        session.show_heatmap = self.chk_heatmap.isChecked()
        if session.last_deformed is None:
            session.deform()
        defm = session.last_deformed
        assert defm is not None

        self.plotter.clear()
        self.plotter.add_axes()
        self.plotter.set_background("#1a1a1e")

        raw = np.asarray(defm.positions, dtype=np.float64)
        pts, center, span = self._grounded_positions(raw)
        # Spin character only — floor stays world-fixed.
        pts = self._rotate_yaw_z(pts, self._char_yaw_deg)
        self._orbit_center = center
        self._model_span = span
        self._add_floor(span)

        # Ground skeleton overlays with the same transform + yaw.
        raw_min = raw.min(axis=0)
        mid_xy = 0.5 * (raw.min(axis=0)[:2] + raw.max(axis=0)[:2])

        def _xf(p: np.ndarray) -> np.ndarray:
            out = np.asarray(p, dtype=np.float64).copy()
            if out.ndim == 1:
                out[2] -= raw_min[2]
                out[0] -= mid_xy[0]
                out[1] -= mid_xy[1]
                return self._rotate_yaw_z(out.reshape(1, 3), self._char_yaw_deg)[0]
            out[:, 2] -= raw_min[2]
            out[:, 0] -= mid_xy[0]
            out[:, 1] -= mid_xy[1]
            return self._rotate_yaw_z(out, self._char_yaw_deg)

        if self.chk_mesh.isChecked():
            faces = np.hstack(
                [
                    np.full((defm.triangle_count, 1), 3, dtype=np.int64),
                    defm.indices.reshape(-1, 3).astype(np.int64),
                ]
            ).ravel()
            grid = pv.PolyData(pts, faces)
            style = "wireframe" if self.chk_wire.isChecked() else "surface"
            if session.show_heatmap:
                scalars = session.heatmap_scalars()
                assert scalars is not None
                grid["weights"] = scalars
                rgb = weight_heatmap_rgb(scalars)
                grid["RGB"] = (rgb * 255).astype(np.uint8)
                self.plotter.add_mesh(
                    grid,
                    scalars="RGB",
                    rgb=True,
                    style=style,
                    show_scalar_bar=False,
                )
            else:
                self.plotter.add_mesh(
                    grid,
                    color="#c4a484",
                    style=style,
                    smooth_shading=True,
                )

        if self.chk_bones.isChecked():
            segs = session.skeleton_segments()
            if segs.size:
                segs = _xf(segs.reshape(-1, 3)).reshape(segs.shape)
                points = segs.reshape(-1, 3)
                lines = []
                for i in range(segs.shape[0]):
                    lines.extend([2, 2 * i, 2 * i + 1])
                bone_poly = pv.PolyData(points, lines=np.asarray(lines, dtype=np.int64))
                self.plotter.add_mesh(bone_poly, color="#5b9bd5", line_width=2)

        if self.chk_joints.isChecked():
            jpts = session.skeleton_joint_positions()
            if jpts.size:
                cloud = pv.PolyData(_xf(jpts))
                self.plotter.add_mesh(cloud, color="#ffd54f", point_size=6, render_points_as_spheres=True)

        # M6 source skeleton overlay (clinical gait markers)
        demo = self._retarget_demo
        if demo is not None and demo.overlay_source and demo.source_positions:
            src = np.asarray(demo.source_positions, dtype=np.float64)
            # Scale clinical meters → avatar units roughly by avatar height span
            scale = max(span * 0.55, 1.0)
            src = src * scale
            src_cloud = pv.PolyData(_xf(src))
            self.plotter.add_mesh(
                src_cloud,
                color="#ff7043",
                point_size=8,
                render_points_as_spheres=True,
            )

        if not self._camera_framed:
            self._frame_camera()
        else:
            self._apply_locked_camera()

        d = session.diagnostics
        extra = ""
        if "anim_time" in d:
            extra = (
                f"\nAnim: {d.get('anim_clip')}  t={d['anim_time']:.2f}s  "
                f"frame={d['anim_frame']}  {d.get('anim_state')}"
            )
        self.diag_label.setText(
            f"Vertices: {d['vertices']:,}\n"
            f"Triangles: {d['triangles']:,}\n"
            f"Bones: {d['bones']}\n"
            f"Influences: {d['influences']}\n"
            f"Skinning: {d['skinning_ms']:.2f} ms ({d['algorithm']} / {d['backend']})\n"
            f"Bone: {d['selected_bone']}"
            f"{extra}"
        )
        # quick NaN check
        if defm is not None and np.all(np.isfinite(defm.positions)):
            self.status_label.setText("PASS ✓")
            self.status_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_label.setText("FAIL — non-finite positions")
            self.status_label.setStyleSheet("color: #c62828; font-weight: bold;")

        self.plotter.render()


def build_session(
    *,
    fixture: bool,
    lod: int,
    fbx: str | None,
) -> SkinningDebugSession:
    if fixture:
        return SkinningDebugSession.load_segment_fixture()
    if fbx:
        return SkinningDebugSession.load_fbx(fbx)
    try:
        return SkinningDebugSession.load_metahuman(lod=lod)
    except Exception as exc:  # noqa: BLE001
        print(f"MetaHuman load failed ({exc}); falling back to fixture.")
        return SkinningDebugSession.load_segment_fixture()


def main(argv: list[str] | None = None) -> int:
    import argparse

    default_army = REPO / "KILI" / "uploads_files_5923911_army_girl.fbx"
    parser = argparse.ArgumentParser(description="AXYX Skinning Debug Studio")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic 2-bone mesh")
    parser.add_argument("--lod", type=int, default=3, help="MetaHuman LOD (default 3)")
    parser.add_argument(
        "--fbx",
        type=str,
        default=None,
        help="Load a skinned FBX path (e.g. army girl)",
    )
    parser.add_argument(
        "--army-girl",
        action="store_true",
        help=f"Load {default_army.name}",
    )
    parser.add_argument(
        "--retarget",
        action="store_true",
        help="Auto-play retarget gait on the skinned avatar (use with --army-girl)",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="S2",
        help="Clinical subject for retarget motion (same as Studio stick figure)",
    )
    parser.add_argument(
        "--session",
        type=str,
        default="WU01",
        help="Clinical trial/session name (e.g. WU01 walk)",
    )
    parser.add_argument(
        "--mat",
        type=str,
        default=None,
        help="Optional path to Data_structure_filtered.mat",
    )
    args = parser.parse_args(argv)

    fbx_path = args.fbx
    if args.army_girl:
        fbx_path = str(default_army)

    app = QApplication(sys.argv)
    try:
        session = build_session(fixture=args.fixture, lod=args.lod, fbx=fbx_path)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(None, "Load failed", str(exc))
        return 1
    win = SkinningDebugWindow(session)
    win.show()
    if args.retarget or args.army_girl:
        # Realistic avatar walk: retarget clinical (or synthetic) motion onto mesh.
        win.retarget_profile.setCurrentText("matlab_clinical_to_army_girl")
        QTimer.singleShot(
            200,
            lambda: win._retarget_play(
                subject=args.subject if args.army_girl else None,
                session=args.session if args.army_girl else None,
                mat_path=args.mat,
            ),
        )
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
