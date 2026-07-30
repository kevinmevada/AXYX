"""Settings dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from motion_engine.studio.settings import StudioSettings


class SettingsDialog(QDialog):
    """Edit studio preferences."""

    def __init__(self, settings: StudioSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setAccessibleName("Settings")
        self._settings = settings

        layout = QVBoxLayout(self)
        form = QFormLayout()

        path_row = QHBoxLayout()
        self._dataset = QLineEdit(settings.dataset_path or "")
        self._dataset.setPlaceholderText("MotionDatabase folder…")
        self._dataset.setAccessibleName("Dataset path")
        browse = QPushButton("Browse…")
        browse.setAccessibleName("Browse dataset path")
        browse.clicked.connect(self._browse_dataset)
        path_row.addWidget(self._dataset, stretch=1)
        path_row.addWidget(browse)

        self._speed = QDoubleSpinBox()
        self._speed.setRange(0.1, 4.0)
        self._speed.setSingleStep(0.1)
        self._speed.setValue(settings.playback_speed)
        self._speed.setAccessibleName("Default playback speed")
        self._loop = QCheckBox("Loop playback by default")
        self._loop.setChecked(settings.loop_playback)
        self._loop.setAccessibleName("Loop playback")
        self._open_viewer = QCheckBox("Open external viewer on session select")
        self._open_viewer.setChecked(settings.open_viewer_on_session_select)
        self._open_viewer.setAccessibleName("Open external viewer on session select")
        self._theme = QComboBox()
        self._theme.setAccessibleName("Theme")
        self._theme.addItem("Light", "light")
        self._theme.addItem("Dark", "dark")
        self._theme.addItem("High contrast", "high_contrast")
        theme_index = self._theme.findData(settings.theme_mode)
        if theme_index >= 0:
            self._theme.setCurrentIndex(theme_index)

        form.addRow("Dataset path", path_row)
        form.addRow("Default speed", self._speed)
        form.addRow("Theme", self._theme)
        form.addRow(self._loop)
        form.addRow(self._open_viewer)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _browse_dataset(self) -> None:
        start = self._dataset.text().strip() or str(Path.home())
        path = QFileDialog.getExistingDirectory(self, "Select dataset folder", start)
        if path:
            self._dataset.setText(path)

    def _save(self) -> None:
        text = self._dataset.text().strip()
        self._settings.dataset_path = text or None
        self._settings.playback_speed = float(self._speed.value())
        self._settings.loop_playback = self._loop.isChecked()
        self._settings.open_viewer_on_session_select = self._open_viewer.isChecked()
        theme_mode = self._theme.currentData()
        if isinstance(theme_mode, str):
            self._settings.theme_mode = theme_mode
        self._settings.validate()
        self._settings.save()
        self.accept()
