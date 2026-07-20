"""About dialog."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class AboutDialog(QDialog):
    """About AXYX."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About AXYX")
        self.setModal(True)
        layout = QVBoxLayout(self)
        title = QLabel("AXYX")
        title.setObjectName("HeroTitle")
        body = QLabel(
            "AXYX research platform for clinical gait reconstruction,\n"
            "scientific visualization, and Motion Engine analysis.\n"
            "Viewport backend: SkeletonViewer (PyVista)."
        )
        body.setObjectName("MutedLabel")
        body.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(buttons)
