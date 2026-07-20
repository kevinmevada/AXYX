"""Subject browser list for AXYX."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.empty_state import EmptyStateWidget
from motion_engine.studio.widgets.search_bar import SearchBar


class SubjectBrowser(QWidget):
    """Searchable subject list with cohort filter support."""

    subjectSelected = Signal(str)
    pinToggled = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._subjects: list[SubjectModel] = []
        self._query = ""
        self._cohort_ids: set[str] | None = None
        sp = DEFAULT_THEME.spacing

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(sp.xs)

        header = QLabel("Subjects")
        header.setObjectName("SectionLabel")
        self._search = SearchBar("Search subjects...")
        self._search.queryChanged.connect(self._on_query)
        self._list = QListWidget()
        self._list.setObjectName("StudioList")
        self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._empty = EmptyStateWidget(
            "No subjects",
            "Open a dataset or clear search / cohort filters.",
        )
        self._empty.hide()
        self._count = QLabel("0 subjects")
        self._count.setObjectName("MutedLabel")

        layout.addWidget(header)
        layout.addWidget(self._search)
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._empty, stretch=1)
        layout.addWidget(self._count)

    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        self._subjects = list(subjects)
        self.refresh()

    def set_cohort_filter(self, subject_ids: set[str] | None) -> None:
        """Restrict to ``subject_ids``, or clear when ``None``."""
        self._cohort_ids = subject_ids
        self.refresh()

    def refresh(self) -> None:
        self._list.clear()
        visible = [s for s in self._subjects if s.matches_query(self._query)]
        if self._cohort_ids is not None:
            visible = [s for s in visible if s.subject_id in self._cohort_ids]
        visible.sort(key=lambda s: (not s.pinned, s.subject_id))
        for subject in visible:
            pin = "* " if subject.pinned else ""
            item = QListWidgetItem(f"{pin}{subject.display_name}")
            item.setData(Qt.ItemDataRole.UserRole, subject.subject_id)
            item.setToolTip(subject.subtitle)
            self._list.addItem(item)
        empty = len(visible) == 0
        self._list.setVisible(not empty)
        self._empty.setVisible(empty)
        if empty and self._subjects:
            self._empty.set_messages(
                "No matches",
                "Try another search term or select Dataset in the cohort list.",
            )
        elif empty:
            self._empty.set_messages(
                "No subjects",
                "Open a dataset to browse participants.",
            )
        self._count.setText(f"{len(visible)} / {len(self._subjects)} subjects")

    def select_subject(self, subject_id: str) -> None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == subject_id:
                self._list.setCurrentItem(item)
                break

    def _on_query(self, query: str) -> None:
        self._query = query
        self.refresh()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        subject_id = item.data(Qt.ItemDataRole.UserRole)
        if subject_id:
            self.subjectSelected.emit(str(subject_id))
