"""Welcome - soft floating card on layered background."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.icons import icon_app
from motion_engine.studio.theme import DEFAULT_THEME, apply_elevation

_FEATURES = (
    ("Capture", "Frame-accurate gait sessions"),
    ("Clinical", "Live metrics & diagnosis context"),
    ("Stage", "Cinematic 3D motion viewport"),
)


class WelcomeScreen(QWidget):
    """Premium first-run surface."""

    openDatasetRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WelcomeRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sp = DEFAULT_THEME.spacing

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(sp.xxxl, sp.xxxl, sp.xxxl, sp.xxxl)

        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumWidth(520)
        card.setMaximumWidth(640)
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        apply_elevation(card, level=3)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(sp.xxxl, sp.xxxl, sp.xxxl, sp.xl)
        layout.setSpacing(sp.sm)

        icon = QLabel()
        icon.setPixmap(icon_app(72).pixmap(72, 72))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        eyebrow = QLabel("RESEARCH MOTION PLATFORM")
        eyebrow.setObjectName("EyebrowLabel")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("AXYX")
        title.setObjectName("HeroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Open a gait dataset to explore subjects, reconstruct skeletons, "
            "and review motion in the research viewport."
        )
        subtitle.setObjectName("MutedLabel")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setMaximumWidth(440)

        open_btn = QPushButton("Open Dataset")
        open_btn.setObjectName("PrimaryButton")
        open_btn.setFixedWidth(220)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self.openDatasetRequested.emit)

        divider = QFrame()
        divider.setObjectName("Divider")

        features = QWidget()
        fl = QHBoxLayout(features)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(sp.lg)
        for name, blurb in _FEATURES:
            fl.addWidget(_chip(name, blurb))

        layout.addWidget(icon)
        layout.addSpacing(sp.xs)
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addSpacing(sp.xs)
        layout.addWidget(subtitle)
        layout.addSpacing(sp.md)
        layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(sp.lg)
        layout.addWidget(divider)
        layout.addSpacing(sp.md)
        layout.addWidget(features)
        outer.addWidget(card)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(DEFAULT_THEME.colors.background))
        painter.end()
        super().paintEvent(event)


def _chip(name: str, blurb: str) -> QWidget:
    chip = QWidget()
    chip.setFixedWidth(150)
    layout = QVBoxLayout(chip)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(DEFAULT_THEME.spacing.xxs)
    heading = QLabel(name)
    heading.setObjectName("FeatureHeading")
    heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
    body = QLabel(blurb)
    body.setObjectName("FeatureBody")
    body.setWordWrap(True)
    body.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(heading)
    layout.addWidget(body)
    return chip
