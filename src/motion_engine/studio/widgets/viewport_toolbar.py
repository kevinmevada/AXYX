"""Viewport chrome — camera presets + visualization mode menu."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QFont, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QMenu, QPushButton, QToolButton, QWidget

from motion_engine.studio.icons import icon_chevron_down
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.theme.fonts import studio_font_family

_CHROME_H = 32
_CHIP_MIN_W = 56
_GROUP_GAP = 16
_ITEM_GAP = 4
_FONT_PX = 12


def _chrome_font(*, bold: bool = False) -> QFont:
    """Single pixel font for every top-bar control (avoids QSS size drift)."""
    font = QFont(studio_font_family())
    font.setPixelSize(_FONT_PX)
    font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Medium)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return font


class ViewportToolbar(QWidget):
    """Camera + display chrome — fixed 32px row for top-bar alignment."""

    cameraPresetRequested = Signal(str)
    resetCameraRequested = Signal()
    gridToggled = Signal(bool)
    axesToggled = Signal(bool)
    groundToggled = Signal(bool)
    lightingToggled = Signal(bool)
    fullscreenRequested = Signal()
    digitalTwinToggled = Signal(bool)  # backward compat → avatar on/off
    visualizationChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportToolbar")
        self.setFixedHeight(_CHROME_H)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(_ITEM_GAP)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        chip_font = _chrome_font(bold=True)
        self._camera_group: list[QPushButton] = []
        presets = (
            ("Front", "front", "Front (1)"),
            ("Back", "back", "Back (2) · Default"),
            ("Left", "left", "Left side (3)"),
            ("Right", "right", "Right side (4)"),
        )
        for index, (label, preset, tip) in enumerate(presets):
            btn = QPushButton(label)
            btn.setObjectName("SegmentButton")
            btn.setCheckable(True)
            btn.setFixedHeight(_CHROME_H)
            btn.setMinimumWidth(_CHIP_MIN_W)
            btn.setFont(chip_font)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty(
                "segment",
                "first" if index == 0 else ("last" if index == len(presets) - 1 else "mid"),
            )
            btn.setToolTip(tip)
            btn.setShortcut(QKeySequence(str(index + 1)))
            btn.clicked.connect(lambda _=False, p=preset, b=btn: self._on_camera(p, b))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)
            self._camera_group.append(btn)

        layout.addSpacing(_GROUP_GAP)

        self._viz_btn = self._chrome_button(
            "Visualization",
            tip="Switch visualization mode",
            popup=True,
        )
        viz_menu = QMenu(self._viz_btn)
        self._viz_group = QActionGroup(self)
        self._viz_group.setExclusive(True)
        self._viz_actions: dict[str, QAction] = {}
        for mode, label in (
            ("stick", "Stick Figure"),
            ("bones", "Bone Anatomy"),
            ("avatar", "Human Avatar"),
        ):
            act = QAction(label, viz_menu)
            act.setCheckable(True)
            act.setData(mode)
            self._viz_group.addAction(act)
            viz_menu.addAction(act)
            self._viz_actions[mode] = act
            act.triggered.connect(lambda checked=False, m=mode: self._on_viz(m))
        self._viz_actions["stick"].setChecked(True)
        self._viz_btn.setMenu(viz_menu)
        layout.addWidget(self._viz_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Legacy handle kept for older call sites / tests.
        self._avatar_btn = QPushButton("Avatar")
        self._avatar_btn.setObjectName("GhostButton")
        self._avatar_btn.setCheckable(True)
        self._avatar_btn.setFixedHeight(_CHROME_H)
        self._avatar_btn.hide()
        self._avatar_btn.toggled.connect(self.digitalTwinToggled.emit)

        display = self._chrome_button("Display", tip="Display options", popup=True)
        menu = QMenu(display)
        _check(menu, "Alignment", "G", False, self.gridToggled)
        _check(menu, "Ground", "", True, self.groundToggled)
        _check(menu, "Axes", "A", False, self.axesToggled)
        _check(menu, "Lighting", "", True, self.lightingToggled)
        display.setMenu(menu)
        layout.addWidget(display, alignment=Qt.AlignmentFlag.AlignVCenter)

        full = self._chrome_button("Fullscreen", tip="Fullscreen (F11)")
        full.setShortcut(QKeySequence("F11"))
        full.clicked.connect(self.fullscreenRequested.emit)
        layout.addWidget(full, alignment=Qt.AlignmentFlag.AlignVCenter)

        reset = self._chrome_button(
            "Reset",
            tip="Reset camera (R) · Double-click viewport to focus",
        )
        reset.setShortcut(QKeySequence("R"))
        reset.clicked.connect(self.resetCameraRequested.emit)
        layout.addWidget(reset, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addStretch(1)

        if self._camera_group:
            # Default clinical view is Back (DC) — index 1 in the chip row.
            self._camera_group[1].setChecked(True)

        _ = DEFAULT_THEME

    @staticmethod
    def _chrome_button(
        label: str,
        *,
        tip: str,
        popup: bool = False,
    ) -> QToolButton:
        """One shared chrome control — same height, type, and padding."""
        btn = QToolButton()
        btn.setObjectName("TopChrome")
        btn.setText(label)
        btn.setFont(_chrome_font())
        btn.setFixedHeight(_CHROME_H)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        btn.setAutoRaise(True)
        if popup:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            btn.setIcon(icon_chevron_down(12))
            btn.setIconSize(QSize(12, 12))
            btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        else:
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        return btn

    def set_visualization(self, mode: str) -> None:
        """Sync menu check state without emitting (host already applied mode)."""
        act = self._viz_actions.get(mode)
        if act is None:
            return
        for a in self._viz_actions.values():
            a.blockSignals(True)
            a.setChecked(a is act)
            a.blockSignals(False)
        self._avatar_btn.blockSignals(True)
        self._avatar_btn.setChecked(mode == "avatar")
        self._avatar_btn.blockSignals(False)

    def _on_viz(self, mode: str) -> None:
        self.set_visualization(mode)
        self.visualizationChanged.emit(mode)
        self.digitalTwinToggled.emit(mode == "avatar")

    def _on_camera(self, preset: str, button: QPushButton) -> None:
        for btn in self._camera_group:
            btn.setChecked(btn is button)
        self.cameraPresetRequested.emit(preset)


def _check(menu: QMenu, label: str, shortcut: str, checked: bool, signal) -> QAction:
    act = QAction(label, menu)
    act.setCheckable(True)
    act.setChecked(checked)
    if shortcut:
        act.setShortcut(QKeySequence(shortcut))
    act.toggled.connect(signal.emit)
    menu.addAction(act)
    return act
