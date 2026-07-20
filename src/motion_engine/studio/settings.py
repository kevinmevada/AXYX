"""Persistent application settings for AXYX."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings


@dataclass
class StudioSettings:
    """Typed settings facade over :class:`QSettings`.

    Example:
        >>> settings = StudioSettings.load()
        >>> settings.recent_subjects
        []
    """

    organization: str = "AXYX"
    application: str = "Studio"
    dataset_path: str | None = None
    window_width: int = 1680
    window_height: int = 1000
    playback_speed: float = 1.0
    loop_playback: bool = True
    pinned_subjects: list[str] = field(default_factory=list)
    recent_subjects: list[str] = field(default_factory=list)
    recent_sessions: list[str] = field(default_factory=list)
    open_viewer_on_session_select: bool = False

    def _qsettings(self) -> QSettings:
        return QSettings(self.organization, self.application)

    @classmethod
    def load(cls) -> StudioSettings:
        """Load settings from the platform store."""
        raw = QSettings(cls.organization, cls.application)
        settings = cls(
            dataset_path=_as_optional_str(raw.value("dataset_path")),
            window_width=int(raw.value("window_width", 1680)),
            window_height=int(raw.value("window_height", 1000)),
            playback_speed=float(raw.value("playback_speed", 1.0)),
            loop_playback=_as_bool(raw.value("loop_playback", True)),
            pinned_subjects=_as_str_list(raw.value("pinned_subjects", [])),
            recent_subjects=_as_str_list(raw.value("recent_subjects", [])),
            recent_sessions=_as_str_list(raw.value("recent_sessions", [])),
            open_viewer_on_session_select=_as_bool(
                raw.value("open_viewer_on_session_select", False)
            ),
        )
        return settings

    def save(self) -> None:
        """Persist current values."""
        raw = self._qsettings()
        raw.setValue("dataset_path", self.dataset_path or "")
        raw.setValue("window_width", self.window_width)
        raw.setValue("window_height", self.window_height)
        raw.setValue("playback_speed", self.playback_speed)
        raw.setValue("loop_playback", self.loop_playback)
        raw.setValue("pinned_subjects", self.pinned_subjects)
        raw.setValue("recent_subjects", self.recent_subjects)
        raw.setValue("recent_sessions", self.recent_sessions)
        raw.setValue(
            "open_viewer_on_session_select", self.open_viewer_on_session_select
        )
        raw.sync()

    def remember_subject(self, subject_id: str) -> None:
        """Push ``subject_id`` onto the recent list."""
        recent = [subject_id] + [s for s in self.recent_subjects if s != subject_id]
        self.recent_subjects = recent[:12]
        self.save()

    def remember_session(self, subject_id: str, session_name: str) -> None:
        """Push a ``subject/session`` key onto recent sessions."""
        key = f"{subject_id}/{session_name}"
        recent = [key] + [s for s in self.recent_sessions if s != key]
        self.recent_sessions = recent[:16]
        self.save()

    def toggle_pin(self, subject_id: str) -> bool:
        """Pin or unpin a subject. Returns True if now pinned."""
        if subject_id in self.pinned_subjects:
            self.pinned_subjects = [s for s in self.pinned_subjects if s != subject_id]
            pinned = False
        else:
            self.pinned_subjects = [subject_id, *self.pinned_subjects]
            pinned = True
        self.save()
        return pinned

    def resolved_dataset_path(self) -> Path | None:
        """Return the configured dataset path if set."""
        if not self.dataset_path:
            return None
        return Path(self.dataset_path).expanduser()


def _as_optional_str(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
