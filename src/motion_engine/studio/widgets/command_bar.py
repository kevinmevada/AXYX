"""Top bar — single baseline: Explorer · camera · brand · readout."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from motion_engine.studio.commands.registry import CommandRegistry
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.theme.fonts import studio_font_family
from motion_engine.studio.theme.wordmark import apply_chrome_wordmark_label
from motion_engine.studio.widgets.viewport_toolbar import _CHROME_H, _chrome_font


class CommandBar(QWidget):
    """56px top chrome — every control shares one vertical centerline."""

    explorerToggled = Signal(bool)

    def __init__(
        self,
        commands: CommandRegistry | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CommandBar")
        self.setAccessibleName("Command bar")
        self.setFixedHeight(56)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._welcome_mode = False
        self._commands = commands
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._layout = layout

        self._toggle = QToolButton()
        self._toggle.setObjectName("ExplorerSwitch")
        self._toggle.setCheckable(True)
        self._toggle.setChecked(False)
        self._toggle.setAutoRaise(True)
        self._toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._toggle.setFixedHeight(_CHROME_H)
        self._toggle.setFont(_chrome_font())
        self._toggle.setAccessibleName("Show or hide Explorer")
        self._toggle.clicked.connect(self._on_switch_clicked)
        self._refresh_switch_chrome()
        layout.addWidget(self._toggle, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._chrome_host = QWidget()
        self._chrome_host.setObjectName("ChromeHost")
        self._chrome_host.setFixedHeight(_CHROME_H)
        self._chrome_layout = QHBoxLayout(self._chrome_host)
        self._chrome_layout.setContentsMargins(0, 0, 0, 0)
        self._chrome_layout.setSpacing(0)
        self._chrome_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._chrome_host, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)

        title = QLabel()
        title.setAccessibleName("AXYX")
        title.setFixedHeight(_CHROME_H)
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        apply_chrome_wordmark_label(title, pixel_size=14, object_name="BrandTitle")
        self._brand_title = title
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._welcome_stretch = QWidget()
        self._welcome_stretch.setVisible(False)
        layout.addWidget(self._welcome_stretch, stretch=1)

        self._session_readout = QLabel("")
        self._session_readout.setObjectName("FrameLabel")
        self._session_readout.setFixedHeight(_CHROME_H)
        self._session_readout.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        readout = QFont(studio_font_family())
        readout.setPixelSize(12)
        readout.setWeight(QFont.Weight.Medium)
        readout.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        self._session_readout.setFont(readout)
        layout.addWidget(self._session_readout, alignment=Qt.AlignmentFlag.AlignVCenter)

    def attach_chrome(self, chrome: QWidget) -> None:
        """Host the viewport camera/display toolbar in this top bar."""
        while self._chrome_layout.count():
            item = self._chrome_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        chrome.setFixedHeight(_CHROME_H)
        self._chrome_layout.addWidget(chrome, alignment=Qt.AlignmentFlag.AlignVCenter)

    def set_welcome_mode(self, welcome: bool) -> None:
        """Welcome: left brand + hairline. Workspace: explorer + camera + readout."""
        welcome = bool(welcome)
        self._welcome_mode = welcome
        self._toggle.setVisible(not welcome)
        self._chrome_host.setVisible(not welcome)
        self._session_readout.setVisible(not welcome)
        self._welcome_stretch.setVisible(welcome)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        c = DEFAULT_THEME.colors
        painter.fillRect(self.rect(), QColor(c.background))
        painter.setPen(QColor(c.border if self._welcome_mode else c.border_subtle))
        y = self.height() - 1
        painter.drawLine(0, y, self.width(), y)
        painter.end()

    def set_session_readout(self, text: str) -> None:
        self._session_readout.setText(text)

    def _on_switch_clicked(self, checked: bool) -> None:
        self._refresh_switch_chrome()
        self.explorerToggled.emit(bool(checked))

    def is_explorer_on(self) -> bool:
        return self._toggle.isChecked()

    def set_explorer_visible(self, visible: bool) -> None:
        """Keep the switch in sync with the Explorer dock (no extra emit)."""
        visible = bool(visible)
        if self._toggle.isChecked() == visible:
            self._refresh_switch_chrome()
            return
        self._toggle.blockSignals(True)
        self._toggle.setChecked(visible)
        self._toggle.blockSignals(False)
        self._refresh_switch_chrome()

    def _refresh_switch_chrome(self) -> None:
        on = self._toggle.isChecked()
        self._toggle.setIcon(QIcon())
        self._toggle.setText("Explorer")
        self._toggle.setToolTip("Hide Explorer" if on else "Show Explorer")

    def bind_commands(self, registry: CommandRegistry) -> None:
        """Keep a registry reference; switch is signal-driven only."""
        self._commands = registry
