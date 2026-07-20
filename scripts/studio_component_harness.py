"""Storybook-style harness for AXYX themed widgets.

Run (from repo root, with PYTHONPATH=src)::

    .\\venv311\\Scripts\\python.exe scripts\\studio_component_harness.py

Optional::

    set QT_QPA_PLATFORM=offscreen
    .\\venv311\\Scripts\\python.exe scripts\\studio_component_harness.py --shot out\\studio_components.png
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("QT_API", "pyside6")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.icons import icon_play  # noqa: E402
from motion_engine.studio.theme import DEFAULT_THEME, apply_elevation, build_stylesheet  # noqa: E402
from motion_engine.studio.widgets.empty_state import EmptyStateWidget  # noqa: E402
from motion_engine.studio.widgets.error_banner import ErrorBanner  # noqa: E402
from motion_engine.studio.widgets.viewport_toolbar import ViewportToolbar  # noqa: E402


def _section(title: str, body: QWidget) -> QWidget:
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    layout.addWidget(body)
    return box


def build_grid() -> QWidget:
    sp = DEFAULT_THEME.spacing
    root = QWidget()
    root.setObjectName("Workspace")
    grid = QVBoxLayout(root)
    grid.setContentsMargins(sp.xl, sp.xl, sp.xl, sp.xl)
    grid.setSpacing(sp.lg)

    # Buttons
    buttons = QWidget()
    bl = QHBoxLayout(buttons)
    primary = QPushButton("Primary")
    primary.setObjectName("PrimaryButton")
    ghost = QPushButton("Ghost")
    ghost.setObjectName("GhostButton")
    seg = QPushButton("Segment")
    seg.setObjectName("SegmentButton")
    seg.setCheckable(True)
    seg.setChecked(True)
    tool = QToolButton()
    tool.setText("Tool")
    tool.setIcon(icon_play())
    bl.addWidget(primary)
    bl.addWidget(QPushButton("Secondary"))
    bl.addWidget(ghost)
    bl.addWidget(seg)
    bl.addWidget(tool)
    bl.addStretch(1)
    grid.addWidget(_section("Buttons", buttons))

    # Lists (selection must be opaque accent_muted - never OS green)
    lists = QWidget()
    ll = QHBoxLayout(lists)
    for name, oid in (
        ("StudioList", "StudioList"),
        ("CohortList", "CohortList"),
        ("MetricsList", "MetricsList"),
    ):
        lw = QListWidget()
        lw.setObjectName(oid)
        for label in ("Alpha", "Beta", "Gamma"):
            lw.addItem(QListWidgetItem(f"{name} | {label}"))
        lw.setCurrentRow(1)
        ll.addWidget(lw)
    grid.addWidget(_section("Lists (selection)", lists))

    # Tabs / form / empty / error
    tabs = QTabWidget()
    tabs.setObjectName("InspectorTabs")
    form_host = QWidget()
    form = QFormLayout(form_host)
    form.addRow(QLabel("Field"), QLineEdit("Sample"))
    form.addRow(QLabel("Choice"), QComboBox())
    form.addRow(QCheckBox("Option"))
    tabs.addTab(form_host, "Clinical")
    tabs.addTab(EmptyStateWidget("No metrics", "Designed empty state."), "Metrics")
    tabs.addTab(QLabel("Dataset panel"), "Dataset")
    grid.addWidget(_section("Inspector tabs", tabs))

    banner = ErrorBanner()
    banner.show_error("Inline error", "Prefer banners over modal dialogs for soft failures.")
    grid.addWidget(_section("Error banner", banner))

    toolbar = ViewportToolbar()
    card = QWidget()
    apply_elevation(card, level=1)
    cl = QVBoxLayout(card)
    cl.addWidget(toolbar)
    cl.addWidget(QLabel("Viewport chrome"))
    grid.addWidget(_section("Viewport toolbar", card))

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(42)
    grid.addWidget(_section("Timeline scrubber", slider))

    return root


def main() -> int:
    parser = argparse.ArgumentParser(description="Studio component harness")
    parser.add_argument("--shot", type=Path, help="Save a PNG screenshot and exit")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet(DEFAULT_THEME))

    win = QMainWindow()
    win.setWindowTitle("AXYX - Component Harness")
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(build_grid())
    win.setCentralWidget(scroll)
    win.resize(1280, 900)
    win.show()

    if args.shot:
        app.processEvents()
        pix = win.grab()
        args.shot.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(args.shot))
        print(f"Wrote {args.shot}")
        return 0

    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
