"""Session browser list for AXYX."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.widgets.empty_state import EmptyStateWidget


class SessionBrowser(QWidget):
    """Session list for the active subject — no search (small datasets)."""

    sessionSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sessions: list[SessionModel] = []
        self._subject_id: str | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._list = QListWidget()
        self._list.setObjectName("SessionList")
        self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setUniformItemSizes(True)
        self._list.setFrameShape(QListWidget.Shape.NoFrame)
        self._list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._list.currentItemChanged.connect(self._on_current)
        self._empty = EmptyStateWidget(
            "No sessions",
            "Select a subject to load capture sessions.",
        )
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._empty, stretch=1)
        self._list.hide()
        self._empty.show()

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None:
        self._subject_id = subject_id
        self._sessions = list(sessions)
        self.refresh()

    def clear_sessions(self) -> None:
        self._subject_id = None
        self._sessions = []
        self._list.clear()
        self._list.hide()
        self._empty.show()
        self._empty.set_messages(
            "No sessions",
            "Select a subject to load capture sessions.",
        )

    def refresh(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        visible = sorted(self._sessions, key=lambda s: s.name)
        for session in visible:
            item = QListWidgetItem(f"{session.display_name}  —  {session.classification}")
            item.setData(Qt.ItemDataRole.UserRole, session.name)
            item.setToolTip(session.subtitle)
            item.setSizeHint(QSize(0, 36))
            self._list.addItem(item)
        self._list.blockSignals(False)
        empty = len(visible) == 0
        self._list.setVisible(not empty)
        self._empty.setVisible(empty)
        if empty and self._subject_id:
            self._empty.set_messages(
                "No sessions",
                f"No capture sessions for {self._subject_id}.",
            )
        elif empty:
            self._empty.set_messages(
                "No sessions",
                "Select a subject to load capture sessions.",
            )

    def _on_current(
        self, current: QListWidgetItem | None, _prev: QListWidgetItem | None
    ) -> None:
        if current is None:
            return
        name = current.data(Qt.ItemDataRole.UserRole)
        if name:
            self.sessionSelected.emit(str(name))
