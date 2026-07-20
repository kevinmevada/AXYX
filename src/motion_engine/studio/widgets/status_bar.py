"""Professional status bar for AXYX."""

from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtWidgets import QLabel, QStatusBar


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


class StudioStatusBar(QStatusBar):
    """Renderer | FPS | GPU | frames | memory | subject | session | state."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._renderer = QLabel("Renderer: PyVista")
        self._fps = QLabel("FPS: -")
        self._gpu = QLabel("GPU: -")
        self._frames = QLabel("Frames: -")
        self._memory = QLabel("Memory: -")
        self._subject = QLabel("Subject: -")
        self._session = QLabel("Session: -")
        self._state = QLabel("STOPPED")
        for label in (
            self._renderer,
            self._fps,
            self._gpu,
            self._frames,
            self._memory,
            self._subject,
            self._session,
        ):
            label.setObjectName("StatusStat")
            self.addPermanentWidget(label)
        self._state.setObjectName("StatePill")
        self._state.setProperty("state", "stopped")
        self.addPermanentWidget(self._state)

    def update_snapshot(self, snap: StatusSnapshot) -> None:
        self._renderer.setText(f"Renderer: {snap.renderer}")
        fps = snap.render_fps if snap.render_fps is not None else snap.fps
        self._fps.setText(f"FPS: {fps:g}" if fps else "FPS: -")
        self._gpu.setText(f"GPU: {snap.gpu}")
        self._frames.setText(f"Frames: {snap.current_frame}/{snap.frames}")
        mem = snap.memory_mb if snap.memory_mb is not None else _process_memory_mb()
        self._memory.setText(f"Mem: {mem:.0f} MB" if mem is not None else "Mem: -")
        self._subject.setText(f"Subject: {snap.subject}")
        self._session.setText(f"Session: {snap.session}")
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
