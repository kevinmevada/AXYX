"""Calm primary status bar for AXYX."""

from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from motion_engine import __version__


@dataclass(slots=True)
class StatusSnapshot:
    """Values displayed in the status bar."""

    dataset: str = "-"
    subject: str = "-"
    session: str = "-"
    frames: int = 0
    current_frame: int = 0
    fps: float = 0.0
    duration_sec: float = 0.0
    playback_state: str = "stopped"
    memory_mb: float | None = None
    render_fps: float | None = None
    renderer: str = "PyVista"
    gpu: str = "-"


def _stat(label: str, value: str | None) -> str:
    """Format a status field: 'Label value' when present, 'Label —' when empty."""
    if value is None or value == "" or value == "-":
        return f"{label} —"
    return f"{label}  {value}"


class StudioStatusBar(QStatusBar):
    """Primary: version · FPS · GPU · Memory · Subject · Session.

    Technical fields (renderer / frames / state) live in a developer strip
    that stays hidden unless ``set_developer_mode(True)``.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StudioStatusBar")
        self._developer_mode = False

        self._version = QLabel(f"v{__version__}")
        self._version.setObjectName("StatusVersion")
        self.addWidget(self._version)

        self._fps = QLabel("FPS —")
        self._gpu = QLabel("GPU —")
        self._memory = QLabel("Mem —")
        self._subject = QLabel("Subject —")
        self._session = QLabel("Session —")

        self._renderer = QLabel("Renderer —")
        self._frames = QLabel("Frames —")
        self._state = QLabel("STOPPED")

        for label in (self._fps, self._gpu, self._memory, self._subject, self._session):
            label.setObjectName("StatusStat")
            self.addPermanentWidget(label)

        for label in (self._renderer, self._frames):
            label.setObjectName("StatusStatSecondary")
            label.hide()
            self.addPermanentWidget(label)

        self._state.setObjectName("StatePill")
        self._state.setProperty("state", "stopped")
        self._state.hide()
        self.addPermanentWidget(self._state)

    def set_developer_mode(self, enabled: bool) -> None:
        """Show renderer / frames / playback state when True."""
        self._developer_mode = bool(enabled)
        for w in (self._renderer, self._frames, self._state):
            w.setVisible(self._developer_mode)

    def update_snapshot(self, snap: StatusSnapshot) -> None:
        fps = snap.render_fps if snap.render_fps is not None else snap.fps
        self._fps.setText(_stat("FPS", f"{fps:g}" if fps else None))
        self._gpu.setText(
            _stat("GPU", snap.gpu if snap.gpu and snap.gpu != "-" else None)
        )
        mem = snap.memory_mb if snap.memory_mb is not None else _process_memory_mb()
        self._memory.setText(_stat("Mem", f"{mem:.0f} MB" if mem is not None else None))
        self._subject.setText(
            _stat(
                "Subject",
                snap.subject if snap.subject and snap.subject != "-" else None,
            )
        )
        self._session.setText(
            _stat(
                "Session",
                snap.session if snap.session and snap.session != "-" else None,
            )
        )
        self._renderer.setText(_stat("Renderer", snap.renderer))
        self._frames.setText(_stat("Frames", f"{snap.current_frame}/{snap.frames}"))
        self._state.setText(snap.playback_state.upper())
        self._state.setProperty("state", snap.playback_state)
        self._state.style().unpolish(self._state)
        self._state.style().polish(self._state)


def _process_memory_mb() -> float | None:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return None
