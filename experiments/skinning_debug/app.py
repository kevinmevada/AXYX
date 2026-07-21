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

from PySide6.QtCore import Qt
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
        self.plotter.add_axes()
        self.plotter.set_background("#1a1a1e")
        self._reset()

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

    def _reset(self) -> None:
        for axis in ("X", "Y", "Z"):
            self.sliders[axis].blockSignals(True)
            self.spin[axis].blockSignals(True)
            self.sliders[axis].setValue(0)
            self.spin[axis].setValue(0)
            self.sliders[axis].blockSignals(False)
            self.spin[axis].blockSignals(False)
        self.session.reset()
        self._refresh()
        self.plotter.reset_camera()

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

        if self.chk_mesh.isChecked():
            faces = np.hstack(
                [
                    np.full((defm.triangle_count, 1), 3, dtype=np.int64),
                    defm.indices.reshape(-1, 3).astype(np.int64),
                ]
            ).ravel()
            grid = pv.PolyData(np.asarray(defm.positions, dtype=np.float64), faces)
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
                # pyvista lines
                points = segs.reshape(-1, 3)
                lines = []
                for i in range(segs.shape[0]):
                    lines.extend([2, 2 * i, 2 * i + 1])
                bone_poly = pv.PolyData(points, lines=np.asarray(lines, dtype=np.int64))
                self.plotter.add_mesh(bone_poly, color="#5b9bd5", line_width=2)

        if self.chk_joints.isChecked():
            pts = session.skeleton_joint_positions()
            if pts.size:
                cloud = pv.PolyData(pts)
                self.plotter.add_mesh(cloud, color="#ffd54f", point_size=6, render_points_as_spheres=True)

        d = session.diagnostics
        self.diag_label.setText(
            f"Vertices: {d['vertices']:,}\n"
            f"Triangles: {d['triangles']:,}\n"
            f"Bones: {d['bones']}\n"
            f"Influences: {d['influences']}\n"
            f"Skinning: {d['skinning_ms']:.2f} ms ({d['algorithm']} / {d['backend']})\n"
            f"Bone: {d['selected_bone']}"
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
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
