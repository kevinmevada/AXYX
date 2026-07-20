"""Unified left navigation - VS Code Explorer style."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.dataset_explorer import DatasetExplorer
from motion_engine.studio.widgets.session_browser import SessionBrowser
from motion_engine.studio.widgets.subject_browser import SubjectBrowser


class _NavSection(QWidget):
    """Collapsible flex section that releases all space when closed."""

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
        # Non-flex sections (e.g. Recent) keep their natural height when open.
        self._flex = flex
        sp = DEFAULT_THEME.spacing
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._header = QWidget()
        self._header.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )
        row = QHBoxLayout(self._header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(sp.xs)
        self._btn = QToolButton()
        self._btn.setObjectName("IconChrome")
        self._btn.setCheckable(True)
        self._btn.setChecked(expanded)
        self._btn.setText("▾" if expanded else "▸")
        self._btn.toggled.connect(self._toggle)
        label = QLabel(title)
        label.setObjectName("SectionLabel")
        row.addWidget(self._btn)
        row.addWidget(label, stretch=1)

        self._body = body
        self._body.setVisible(expanded)
        self._layout.addWidget(self._header)
        self._layout.addWidget(self._body, stretch=1 if expanded else 0)
        self._apply_size_policy(expanded)

    def _toggle(self, on: bool) -> None:
        self._body.setVisible(on)
        self._btn.setText("▾" if on else "▸")
        self._layout.setStretch(1, 1 if on else 0)
        self._apply_size_policy(on)
        self.expandedChanged.emit()

    def is_expanded(self) -> bool:
        return self._btn.isChecked()

    @property
    def is_flex(self) -> bool:
        return self._flex

    def _header_height(self) -> int:
        return max(self._header.sizeHint().height(), self._header.minimumSizeHint().height(), 28)

    def _apply_size_policy(self, expanded: bool) -> None:
        if expanded:
            self._body.setMaximumHeight(16_777_215)
            self.setMinimumHeight(0)
            if self._flex:
                self.setMaximumHeight(16_777_215)
                self.setSizePolicy(
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Expanding,
                )
            else:
                # Natural height only - never stretch a bounded body.
                h = self._header_height() + self._body.sizeHint().height()
                self.setSizePolicy(
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Fixed,
                )
                self.setMaximumHeight(h)
        else:
            # Collapse hard to header-only - no leftover gap.
            h = self._header_height()
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed,
            )
            self.setMinimumHeight(h)
            self.setMaximumHeight(h)
            self._body.setMaximumHeight(0)
        self.updateGeometry()


class Sidebar(QFrame):
    """Single unified nav: Dataset · Subjects · Sessions · Recent."""

    subjectSelected = Signal(str)
    sessionSelected = Signal(str)
    recentSessionSelected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(240)
        self.setMaximumWidth(340)
        sp = DEFAULT_THEME.spacing

        layout = QVBoxLayout(self)
        layout.setContentsMargins(sp.md, sp.md, sp.md, sp.md)
        layout.setSpacing(sp.xs)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout = layout
        self._sections: list[tuple[_NavSection, int]] = []

        nav_title = QLabel("Explorer")
        nav_title.setObjectName("BrandTitle")
        nav_title.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )
        layout.addWidget(nav_title)

        self.dataset_explorer = DatasetExplorer()
        self.dataset_explorer.cohortSelected.connect(self._on_cohort)
        self._add_section("Dataset", self.dataset_explorer, weight=1)

        self.subject_browser = SubjectBrowser()
        self.subject_browser.subjectSelected.connect(self.subjectSelected.emit)
        self._add_section("Subjects", self.subject_browser, weight=3)

        self.session_browser = SessionBrowser()
        self.session_browser.sessionSelected.connect(self.sessionSelected.emit)
        self._add_section("Sessions", self.session_browser, weight=3)

        recent_wrap = QWidget()
        recent_layout = QVBoxLayout(recent_wrap)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(0)
        self._recent = QListWidget()
        self._recent.setObjectName("RecentList")
        self._recent.setMaximumHeight(100)
        self._recent.itemClicked.connect(self._on_recent)
        recent_layout.addWidget(self._recent)
        self._add_section("Recent", recent_wrap, weight=0, flex=False)

        # Absorbs leftover height so collapsed headers stay pinned to the top.
        layout.addItem(
            QSpacerItem(
                0,
                0,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )
        self._spacer_index = layout.count() - 1
        self._rebalance_sections()

    def _add_section(
        self, title: str, body: QWidget, *, weight: int, flex: bool = True
    ) -> None:
        section = _NavSection(title, body, flex=flex)
        section.expandedChanged.connect(self._rebalance_sections)
        self._sections.append((section, weight))
        self._layout.addWidget(section)

    def _rebalance_sections(self) -> None:
        """Open flex sections grow; fixed/closed headers stay packed at the top."""
        any_flex_open = False
        for index, (section, weight) in enumerate(self._sections, start=1):
            expanded = section.is_expanded()
            grows = expanded and section.is_flex
            any_flex_open |= grows
            self._layout.setStretch(index, weight if grows else 0)
            section._apply_size_policy(expanded)
        # Spacer soaks up free space whenever no growing section can take it
        # (all closed, or only fixed-height sections like Recent are open).
        self._layout.setStretch(self._spacer_index, 0 if any_flex_open else 1)
        self.updateGeometry()

    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        self.dataset_explorer.set_subjects(subjects)
        self.subject_browser.set_subjects(subjects)

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None:
        self.session_browser.set_sessions(subject_id, sessions)

    def clear_sessions(self) -> None:
        self.session_browser.clear_sessions()

    def set_recent_sessions(self, keys: list[str]) -> None:
        self._recent.clear()
        for key in keys:
            self._recent.addItem(QListWidgetItem(key))

    def _on_cohort(self, cohort: object) -> None:
        ids = self.dataset_explorer.subject_ids_for_cohort(
            cohort if isinstance(cohort, str) else None
        )
        self.subject_browser.set_cohort_filter(ids)

    def _on_recent(self, item: QListWidgetItem) -> None:
        if item.text():
            self.recentSessionSelected.emit(item.text())
