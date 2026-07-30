"""Typed application event bus."""
from __future__ import annotations
from typing import Any
from PySide6.QtCore import QObject, Signal

class ApplicationEventBus(QObject):
    """Simple signal hub for cross-module events."""
    datasetLoaded = Signal(str)
    sessionLoaded = Signal(str, str)
    frameChanged = Signal(int)
    playbackChanged = Signal(str)
    errorRaised = Signal(str, str)
    def emit_dataset_loaded(self, path: str) -> None:
        self.datasetLoaded.emit(path)
    def emit_session_loaded(self, subject_id: str, session_name: str) -> None:
        self.sessionLoaded.emit(subject_id, session_name)
    def emit_frame_changed(self, frame: int) -> None:
        self.frameChanged.emit(frame)
    def emit_playback_changed(self, state: str) -> None:
        self.playbackChanged.emit(state)
    def emit_error(self, title: str, message: str, **_extra: Any) -> None:
        self.errorRaised.emit(title, message)
