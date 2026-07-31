"""Left rail — compact explorer with reliable list selection."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.icons import icon_chevron_down, icon_chevron_right
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.dataset_explorer import DatasetExplorer
from motion_engine.studio.widgets.session_browser import SessionBrowser
from motion_engine.studio.widgets.subject_browser import SubjectBrowser


class _NavSection(QWidget):
    """Collapsible section — closed = header only, no ghost gap."""

    expandedChanged = Signal()

    def __init__(
        self,
        title: str,
        body: QWidget,
        *,
        expanded: bool = True,
        flex: bool = True,
    ) -> None:
        super().__init__()
        self._flex = flex
        self._title = title
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

        self._header = QWidget()
        self._header.setFixedHeight(28)
        row = QHBoxLayout(self._header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self._btn = QToolButton()
        self._btn.setObjectName("SectionChevron")
        self._btn.setCheckable(True)
        self._btn.setChecked(expanded)
        self._btn.setFixedSize(20, 20)
        self._btn.setIconSize(QSize(16, 16))
        self._btn.setAutoRaise(True)
        self._btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setAccessibleName(f"Toggle {title} section")
        self._btn.toggled.connect(self._toggle)
        self._set_chevron(expanded)
        row.addWidget(self._btn)

        label = QLabel(title.upper())
        label.setObjectName("SectionLabel")
        label.setToolTip(title)
        font = label.font()
        font.setPointSize(DEFAULT_THEME.typography.size_xs)
        font.setWeight(QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        label.setFont(font)
        label.setStyleSheet(f"color: {DEFAULT_THEME.colors.text_disabled};")
        # Clicking the label also toggles — larger hit target.
        label.mousePressEvent = lambda _e: self._btn.toggle()  # type: ignore[method-assign]
        row.addWidget(label, stretch=1)

        self._body = body
        self._body.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding if flex else QSizePolicy.Policy.Preferred,
        )
        self._layout.addWidget(self._header)
        self._layout.addWidget(self._body, stretch=1)
        self._apply_size_policy(expanded)

    def _set_chevron(self, expanded: bool) -> None:
        self._btn.setText("")
        self._btn.setIcon(
            icon_chevron_down(16, active=expanded)
            if expanded
            else icon_chevron_right(16, active=False)
        )
        self._btn.setToolTip(f"{'Collapse' if expanded else 'Expand'} {self._title}")

    def _toggle(self, on: bool) -> None:
        self._set_chevron(on)
        self._apply_size_policy(on)
        self.expandedChanged.emit()

    def is_expanded(self) -> bool:
        return self._btn.isChecked()

    @property
    def is_flex(self) -> bool:
        return self._flex

    def _apply_size_policy(self, expanded: bool) -> None:
        if expanded:
            self._body.show()
            self._body.setMinimumHeight(0)
            self._body.setMaximumHeight(16_777_215)
            self._layout.setStretch(1, 1)
            # Clear any prior setFixedHeight from the collapsed state.
            self.setMinimumHeight(0)
            self.setMaximumHeight(16_777_215)
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Expanding if self._flex else QSizePolicy.Policy.Maximum,
            )
        else:
            self._body.hide()
            self._body.setMinimumHeight(0)
            self._body.setMaximumHeight(0)
            self._layout.setStretch(1, 0)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.setFixedHeight(self._header.height())
        self.updateGeometry()


class Sidebar(QFrame):
    """Explorer rail: Dataset · Subjects · Sessions."""

    subjectSelected = Signal(str)
    sessionSelected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        pal = self.palette()
        bg = QColor(DEFAULT_THEME.colors.background)
        pal.setColor(QPalette.ColorRole.Window, bg)
        pal.setColor(QPalette.ColorRole.Base, QColor(DEFAULT_THEME.colors.surface))
        pal.setColor(QPalette.ColorRole.Text, QColor(DEFAULT_THEME.colors.text_primary))
        self.setPalette(pal)
        self.setMinimumWidth(280)
        self.setMaximumWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)
        self._layout = layout
        self._sections: list[tuple[_NavSection, int]] = []
        self._dividers: list[QWidget] = []

        self.dataset_explorer = DatasetExplorer()
        self.dataset_explorer.cohortSelected.connect(self._on_cohort)
        self._add_section("Dataset", self.dataset_explorer, weight=2)

        self._add_divider()

        self.subject_browser = SubjectBrowser()
        self.subject_browser.subjectSelected.connect(self.subjectSelected.emit)
        self._add_section("Subjects", self.subject_browser, weight=3)

        self._add_divider()

        self.session_browser = SessionBrowser()
        self.session_browser.sessionSelected.connect(self.sessionSelected.emit)
        self._add_section("Sessions", self.session_browser, weight=3)

        # Absorbs leftover height when every section is collapsed so headers
        # pack tightly at the top instead of spreading across the rail.
        layout.addStretch(1)
        self._tail_stretch_index = layout.count() - 1

        self._rebalance_sections()

    def _add_divider(self) -> None:
        line = QFrame()
        line.setObjectName("Divider")
        line.setFixedHeight(1)
        wrap = QWidget()
        wrap.setFixedHeight(17)
        wrap_layout = QVBoxLayout(wrap)
        wrap_layout.setContentsMargins(0, 8, 0, 8)
        wrap_layout.setSpacing(0)
        wrap_layout.addWidget(line)
        self._dividers.append(wrap)
        self._layout.addWidget(wrap)

    def _add_section(
        self,
        title: str,
        body: QWidget,
        *,
        weight: int,
        flex: bool = True,
    ) -> None:
        section = _NavSection(title, body, flex=flex)
        section.expandedChanged.connect(self._rebalance_sections)
        self._sections.append((section, weight))
        self._layout.addWidget(section, stretch=weight)

    def _rebalance_sections(self) -> None:
        any_expanded = False
        for section, weight in self._sections:
            expanded = section.is_expanded()
            any_expanded = any_expanded or expanded
            section._apply_size_policy(expanded)
            idx = self._layout.indexOf(section)
            if idx >= 0:
                self._layout.setStretch(idx, weight if expanded else 0)
        # Only fight for space when a section is open; otherwise the tail
        # stretch claims everything so collapsed headers stay stacked.
        self._layout.setStretch(self._tail_stretch_index, 0 if any_expanded else 1)
        for i, divider in enumerate(self._dividers):
            above = self._sections[i][0]
            below = self._sections[i + 1][0]
            # Keep a hairline between open neighbors; hide when either side
            # is collapsed so closed headers sit flush.
            divider.setVisible(above.is_expanded() and below.is_expanded())
        self.updateGeometry()
    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        self.dataset_explorer.set_subjects(subjects)
        self.subject_browser.set_subjects(subjects)

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None:
        self.session_browser.set_sessions(subject_id, sessions)

    def clear_sessions(self) -> None:
        self.session_browser.clear_sessions()

    def _on_cohort(self, cohort: object) -> None:
        ids = self.dataset_explorer.subject_ids_for_cohort(
            cohort if isinstance(cohort, str) else None
        )
        self.subject_browser.set_cohort_filter(ids)
