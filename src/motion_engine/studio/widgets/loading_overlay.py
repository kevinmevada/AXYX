"""Modal loading overlay for long-running studio operations."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QProgressBar, QVBoxLayout, QWidget

from motion_engine.studio.theme import DEFAULT_THEME


class LoadingOverlay(QWidget):
    """Semi-opaque overlay with indeterminate progress and fade transition."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LoadingOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Opacity for theme scrim is controlled via QSS background; fade
        # the whole widget with a graphics effect.
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(DEFAULT_THEME.motion.base)
        self._fade.setEasingCurve(QEasingCurve.Type.InOutCubic)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label = QLabel("Loading…")
        self._label.setObjectName("HeroTitle")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setFixedWidth(240)
        layout.addWidget(self._label)
        layout.addWidget(self._bar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def show_message(self, message: str) -> None:
        """Show the overlay with ``message``."""
        self._label.setText(message)
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.82)
        self._fade.start()

    def hide_overlay(self) -> None:
        """Fade out then hide the overlay."""
        self._fade.stop()
        self._fade.setStartValue(self._opacity.opacity())
        self._fade.setEndValue(0.0)

        def _finish() -> None:
            self.hide()
            try:
                self._fade.finished.disconnect(_finish)
            except (RuntimeError, TypeError):
                pass

        self._fade.finished.connect(_finish)
        self._fade.start()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)
