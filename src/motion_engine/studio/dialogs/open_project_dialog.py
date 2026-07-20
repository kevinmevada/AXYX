"""Open-project dialog for selecting a MATLAB dataset."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class OpenProjectDialog(QDialog):
    """Choose a dataset path or accept the engine default."""

    def __init__(self, current_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Open Dataset")
        self.setModal(True)
        self._path = current_path or ""

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("MATLAB dataset (.mat). Leave empty for the default filtered dataset."))
        row = QHBoxLayout()
        self._edit = QLineEdit(self._path)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(self._edit)
        row.addWidget(browse)
        layout.addLayout(row)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_path(self) -> Path | None:
        """Return the chosen path, or None for default."""
        text = self._edit.text().strip()
        return Path(text) if text else None

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MATLAB dataset",
            self._edit.text() or "",
            "MATLAB (*.mat);;All files (*.*)",
        )
        if path:
            self._edit.setText(path)
