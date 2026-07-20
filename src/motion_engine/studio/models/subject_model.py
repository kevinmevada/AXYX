"""Subject presentation model for the studio UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SubjectModel:
    """UI-facing subject summary.

    Attributes:
        subject_id: Stable ID such as ``S2``.
        session_count: Number of sessions.
        classifications: Session classification histogram.
        mass: Subject mass if available.
        height: Subject height if available.
        pinned: Whether the subject is pinned in the sidebar.
    """

    subject_id: str
    session_count: int = 0
    classifications: dict[str, int] = field(default_factory=dict)
    mass: float | None = None
    height: float | None = None
    pinned: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Human-readable list label."""
        return self.subject_id

    @property
    def subtitle(self) -> str:
        """Secondary list text."""
        classes = ", ".join(
            f"{name}×{count}" for name, count in sorted(self.classifications.items())
        )
        if classes:
            return f"{self.session_count} sessions · {classes}"
        return f"{self.session_count} sessions"

    def matches_query(self, query: str) -> bool:
        """Return True if this subject matches a search query."""
        q = query.strip().lower()
        if not q:
            return True
        haystack = " ".join(
            [
                self.subject_id.lower(),
                " ".join(self.classifications.keys()).lower(),
                str(self.mass or ""),
                str(self.height or ""),
            ]
        )
        return q in haystack

    def to_dict(self) -> dict[str, Any]:
        """Serialize for inspector panels."""
        return {
            "subject_id": self.subject_id,
            "session_count": self.session_count,
            "classifications": dict(self.classifications),
            "mass": self.mass,
            "height": self.height,
            "pinned": self.pinned,
            "metadata": dict(self.metadata),
        }
