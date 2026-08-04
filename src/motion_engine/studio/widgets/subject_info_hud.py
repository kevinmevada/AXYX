"""Viewport subject readout — sex / mass / height for the selected subject.

Sits in the top-right chrome of the center panel (above the OpenGL surface so
Windows does not blank the viewport). This clinical dataset is an all-female
cohort; sex is a cohort constant, not a MATLAB field.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.theme.fonts import studio_font_family

# Fact for this filtered clinical gait cohort (not in subject.Info).
COHORT_SEX = "Female"


def _fmt_mass(mass: float | None) -> str:
    if mass is None:
        return "—"
    return f"{mass:.1f} kg"


def _fmt_height(height: float | None) -> str:
    if height is None:
        return "—"
    return f"{height:.1f} cm"


class SubjectInfoHud(QFrame):
    """Compact clinical card: subject id, sex, mass, height."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SubjectInfoHud")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        c = DEFAULT_THEME.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        self._id = QLabel("—")
        self._id.setObjectName("SubjectInfoId")
        self._sex = QLabel(COHORT_SEX)
        self._sex.setObjectName("SubjectInfoMeta")
        self._mass = QLabel("Mass  —")
        self._mass.setObjectName("SubjectInfoMeta")
        self._height = QLabel("Height  —")
        self._height.setObjectName("SubjectInfoMeta")

        for label in (self._id, self._sex, self._mass, self._height):
            label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        fam = studio_font_family().replace("'", "\\'")
        self.setStyleSheet(
            f"""
            QFrame#SubjectInfoHud {{
                background-color: {c.surface};
                border: 1px solid {c.border};
                border-radius: 8px;
            }}
            QLabel#SubjectInfoId {{
                font-family: '{fam}';
                font-size: 13px;
                font-weight: 600;
                color: {c.text_primary};
                background: transparent;
            }}
            QLabel#SubjectInfoMeta {{
                font-family: '{fam}';
                font-size: 11px;
                font-weight: 400;
                color: {c.text_secondary};
                background: transparent;
            }}
            """
        )
        layout.addWidget(self._id)
        layout.addWidget(self._sex)
        layout.addWidget(self._mass)
        layout.addWidget(self._height)
        self.hide()

    def set_subject(
        self,
        subject_id: str | None,
        *,
        mass: float | None = None,
        height: float | None = None,
        sex: str = COHORT_SEX,
    ) -> None:
        """Show the card for ``subject_id``, or hide when ``None``."""
        if not subject_id:
            self.clear()
            return
        self._id.setText(str(subject_id))
        self._sex.setText(sex or COHORT_SEX)
        self._mass.setText(f"Mass  {_fmt_mass(mass)}")
        self._height.setText(f"Height  {_fmt_height(height)}")
        self.adjustSize()
        self.show()

    def clear(self) -> None:
        """Hide and reset."""
        self._id.setText("—")
        self._sex.setText(COHORT_SEX)
        self._mass.setText("Mass  —")
        self._height.setText("Height  —")
        self.hide()
