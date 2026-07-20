"""Session browser list for AXYX."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.theme import DEFAULT_THEME
from motion_engine.studio.widgets.empty_state import EmptyStateWidget
from motion_engine.studio.widgets.search_bar import SearchBar


class SessionBrowser(QWidget):
    """Searchable session list for the active subject."""

    sessionSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sessions: list[SessionModel] = []
        self._query = ""
        self._subject_id: str | None = None
        sp = DEFAULT_THEME.spacing

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(sp.xs)

        self._header = QLabel("Sessions")
        self._header.setObjectName("SectionLabel")
        self._search = SearchBar("Search sessions...")
        self._search.queryChanged.connect(self._on_query)
        self._list = QListWidget()
        self._list.setObjectName("SessionList")
        self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._empty = EmptyStateWidget(
            "No sessions",
            "Select a subject to load capture sessions.",
        )
        self._meta = QLabel("Select a subject to load sessions.")
        self._meta.setObjectName("MutedLabel")
        self._meta.setWordWrap(True)

        layout.addWidget(self._header)
        layout.addWidget(self._search)
        layout.addWidget(self._list, stretch=1)
        layout.addWidget(self._empty, stretch=1)
        layout.addWidget(self._meta)
        self._list.hide()
        self._empty.show()

    def set_sessions(self, subject_id: str, sessions: list[SessionModel]) -> None:
        self._subject_id = subject_id
        self._sessions = list(sessions)
        self._header.setText(f"Sessions | {subject_id}")
        self.refresh()

    def clear_sessions(self) -> None:
        self._subject_id = None
        self._sessions = []
        self._header.setText("Sessions")
        self._list.clear()
        self._list.hide()
        self._empty.show()
        self._empty.set_messages(
            "No sessions",
            "Select a subject to load capture sessions.",
        )
        self._meta.setText("Select a subject to load sessions.")

    def refresh(self) -> None:
        self._list.clear()
        visible = [s for s in self._sessions if s.matches_query(self._query)]
        visible.sort(key=lambda s: s.name)
        for session in visible:
            item = QListWidgetItem(f"{session.display_name}  -  {session.classification}")
            item.setData(Qt.ItemDataRole.UserRole, session.name)
            item.setToolTip(session.subtitle)
            self._list.addItem(item)
        empty = len(visible) == 0
        self._list.setVisible(not empty)
        self._empty.setVisible(empty)
        if empty and self._subject_id:
            self._empty.set_messages(
                "No matches",
                f"No sessions for {self._subject_id} match this search.",
            )
            self._meta.setText(f"0 sessions for {self._subject_id}")
        elif self._subject_id:
            self._meta.setText(f"{len(visible)} sessions for {self._subject_id}")
        else:
            self._meta.setText("Select a subject to load sessions.")

    def _on_query(self, query: str) -> None:
        self._query = query
        self.refresh()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.sessionSelected.emit(str(name))
