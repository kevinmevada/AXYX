"""Settings dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QVBoxLayout,
)

from motion_engine.studio.settings import StudioSettings


class SettingsDialog(QDialog):
    """Edit studio preferences."""

    def __init__(self, settings: StudioSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self._settings = settings

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._speed = QDoubleSpinBox()
        self._speed.setRange(0.1, 4.0)
        self._speed.setSingleStep(0.1)
        self._speed.setValue(settings.playback_speed)
        self._loop = QCheckBox("Loop playback by default")
        self._loop.setChecked(settings.loop_playback)
        self._open_viewer = QCheckBox("Keep Motion Viewer embedded (recommended)")
        self._open_viewer.setChecked(not settings.open_viewer_on_session_select)
        form.addRow("Default speed", self._speed)
        form.addRow(self._loop)
        form.addRow(self._open_viewer)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _save(self) -> None:
        self._settings.playback_speed = float(self._speed.value())
        self._settings.loop_playback = self._loop.isChecked()
        # Checked = embedded only; unchecked retains legacy external-launch preference.
        self._settings.open_viewer_on_session_select = not self._open_viewer.isChecked()
        self._settings.save()
        self.accept()
