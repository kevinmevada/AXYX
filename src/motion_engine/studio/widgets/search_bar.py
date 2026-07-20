"""Search input used by subject and session browsers."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QWidget


class SearchBar(QWidget):
    """Compact search field with debounce-friendly textChanged signal."""

    queryChanged = Signal(str)

    def __init__(self, placeholder: str = "Search…", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._edit = QLineEdit(self)
        self._edit.setObjectName("SearchField")
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(True)
        self._edit.setToolTip(placeholder)
        self._edit.textChanged.connect(self.queryChanged.emit)
        layout.addWidget(self._edit)

    def text(self) -> str:
        """Return the current query."""
        return self._edit.text()

    def setText(self, value: str) -> None:  # noqa: N802 - Qt API
        """Set the query text."""
        self._edit.setText(value)

    def clear(self) -> None:
        """Clear the query."""
        self._edit.clear()
