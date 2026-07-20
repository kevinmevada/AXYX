"""Project-level application state for AXYX."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from motion_engine.models import MotionDatabase


@dataclass
class ProjectModel:
    """In-memory project / workspace state.

    Attributes:
        database: Loaded :class:`MotionDatabase`, if any.
        dataset_path: Source MATLAB path.
        subject_ids: Cached subject ID list.
        status_message: Last human-readable status line.
        busy: True while a long operation runs.
    """

    database: MotionDatabase | None = None
    dataset_path: Path | None = None
    subject_ids: list[str] = field(default_factory=list)
    status_message: str = "Ready"
    busy: bool = False
    error_message: str | None = None

    @property
    def is_loaded(self) -> bool:
        """Return True when a database is available."""
        return self.database is not None and bool(self.subject_ids)

    @property
    def subject_count(self) -> int:
        """Number of subjects in the project."""
        return len(self.subject_ids)

    def clear(self) -> None:
        """Reset project state."""
        self.database = None
        self.dataset_path = None
        self.subject_ids = []
        self.status_message = "Ready"
        self.busy = False
        self.error_message = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize lightweight project metadata."""
        return {
            "dataset_path": str(self.dataset_path) if self.dataset_path else None,
            "subject_count": self.subject_count,
            "status_message": self.status_message,
            "busy": self.busy,
            "error_message": self.error_message,
        }
