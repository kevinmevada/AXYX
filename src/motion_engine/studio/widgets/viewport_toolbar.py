"""Compact viewport chrome - Front · Back · Left · Right · Display · Full · Reset."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFrame, QHBoxLayout, QMenu, QPushButton, QToolButton, QWidget

from motion_engine.studio.icons import ICON_SM, icon_display
from motion_engine.studio.theme import DEFAULT_THEME


class ViewportToolbar(QWidget):
    """Minimal camera + display chrome for the stage."""

    cameraPresetRequested = Signal(str)
    resetCameraRequested = Signal()
    gridToggled = Signal(bool)
    axesToggled = Signal(bool)
    groundToggled = Signal(bool)
    lightingToggled = Signal(bool)
    fullscreenRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportToolbar")
        sp = DEFAULT_THEME.spacing
        layout = QHBoxLayout(self)
        layout.setContentsMargins(sp.sm, 0, sp.sm, 0)
        layout.setSpacing(sp.xs)

        segment = QHBoxLayout()
        segment.setSpacing(0)
        segment.setContentsMargins(0, 0, 0, 0)
        self._camera_group: list[QPushButton] = []
        presets = (
            ("Front", "front", "Front (1)"),
            ("Back", "back", "Back (2)"),
            ("Left", "left", "Left side (3)"),
            ("Right", "right", "Right side (4)"),
        )
        for index, (label, preset, tip) in enumerate(presets):
            btn = QPushButton(label)
            btn.setObjectName("SegmentButton")
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setProperty(
                "segment",
                "first" if index == 0 else ("last" if index == len(presets) - 1 else "mid"),
            )
            btn.setToolTip(tip)
            btn.setShortcut(QKeySequence(str(index + 1)))
            btn.clicked.connect(lambda _=False, p=preset, b=btn: self._on_camera(p, b))
            segment.addWidget(btn)
            self._camera_group.append(btn)
        layout.addLayout(segment)

        layout.addWidget(_divider())

        display = QToolButton()
        display.setObjectName("IconChrome")
        display.setText("Display")
        display.setIcon(icon_display(ICON_SM))
        display.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        display.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        display.setToolTip("Display options")
        display.setFixedHeight(28)
        menu = QMenu(display)
        _check(menu, "Grid", "G", True, self.gridToggled)
        _check(menu, "Ground", "", True, self.groundToggled)
        _check(menu, "Axes", "A", True, self.axesToggled)
        _check(menu, "Lighting", "", True, self.lightingToggled)
        display.setMenu(menu)
        layout.addWidget(display)

        full = QToolButton()
        full.setObjectName("IconChrome")
        full.setText("Fullscreen")
        full.setToolTip("Fullscreen (F11)")
        full.setShortcut(QKeySequence("F11"))
        full.setFixedHeight(28)
        full.clicked.connect(self.fullscreenRequested.emit)
        layout.addWidget(full)

        reset = QToolButton()
        reset.setObjectName("IconChrome")
        reset.setText("Reset Camera")
        reset.setToolTip("Reset camera (R) · Double-click viewport to focus")
        reset.setShortcut(QKeySequence("R"))
        reset.setFixedHeight(28)
        reset.clicked.connect(self.resetCameraRequested.emit)
        layout.addWidget(reset)

        layout.addStretch(1)

        if self._camera_group:
            self._camera_group[0].setChecked(True)

    def _on_camera(self, preset: str, button: QPushButton) -> None:
        for btn in self._camera_group:
            btn.setChecked(btn is button)
        self.cameraPresetRequested.emit(preset)


def _divider() -> QFrame:
    d = QFrame()
    d.setObjectName("ToolbarDivider")
    return d


def _check(menu: QMenu, label: str, shortcut: str, checked: bool, signal) -> QAction:
    act = QAction(label, menu)
    act.setCheckable(True)
    act.setChecked(checked)
    if shortcut:
        act.setShortcut(QKeySequence(shortcut))
    act.toggled.connect(signal.emit)
    menu.addAction(act)
    return act
