"""Subject browser list for AXYX."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.widgets.empty_state import EmptyStateWidget


class SubjectBrowser(QWidget):
    """Subject list with cohort filter — no search (small datasets)."""

    subjectSelected = Signal(str)
    pinToggled = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._subjects: list[SubjectModel] = []
        self._cohort_ids: set[str] | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._list = QListWidget()
        self._list.setObjectName("StudioList")
        self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setUniformItemSizes(True)
        self._list.setFrameShape(QListWidget.Shape.NoFrame)
        self._list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._list.currentItemChanged.connect(self._on_current)
        self._empty = EmptyStateWidget(
            "No subjects",
            "Open a dataset to browse participants.",
        )
        self._empty.hide()
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._empty, stretch=1)

    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        self._subjects = list(subjects)
        self.refresh()

    def set_cohort_filter(self, subject_ids: set[str] | None) -> None:
        """Restrict to ``subject_ids``, or clear when ``None``."""
        self._cohort_ids = subject_ids
        self.refresh()

    def refresh(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        visible = list(self._subjects)
        if self._cohort_ids is not None:
            visible = [s for s in visible if s.subject_id in self._cohort_ids]
        visible.sort(key=lambda s: (not s.pinned, s.subject_id))
        for subject in visible:
            pin = "* " if subject.pinned else ""
            item = QListWidgetItem(f"{pin}{subject.display_name}")
            item.setData(Qt.ItemDataRole.UserRole, subject.subject_id)
            item.setToolTip(subject.subtitle)
            item.setSizeHint(QSize(0, 36))
            self._list.addItem(item)
        self._list.blockSignals(False)
        empty = len(visible) == 0
        self._list.setVisible(not empty)
        self._empty.setVisible(empty)
        if empty and self._subjects:
            self._empty.set_messages(
                "No matches",
                "Select Dataset in the cohort list to show all subjects.",
            )
        elif empty:
            self._empty.set_messages(
                "No subjects",
                "Open a dataset to browse participants.",
            )

    def select_subject(self, subject_id: str) -> None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == subject_id:
                self._list.setCurrentItem(item)
                break

    def _on_current(
        self, current: QListWidgetItem | None, _prev: QListWidgetItem | None
    ) -> None:
        if current is None:
            return
        subject_id = current.data(Qt.ItemDataRole.UserRole)
        if subject_id:
            self.subjectSelected.emit(str(subject_id))
