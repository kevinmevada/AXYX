"""Session presentation model for the studio UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SessionModel:
    """UI-facing session summary.

    Attributes:
        subject_id: Owning subject.
        name: Original session name (e.g. ``WU01``).
        classification: Semantic label.
        frame_count: Frames if known.
        sampling_rate_hz: Capture rate if known.
        metric_names: Clinical metric keys.
    """

    subject_id: str
    name: str
    classification: str = "Unknown"
    frame_count: int | None = None
    sampling_rate_hz: float | None = None
    metric_names: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Primary list label."""
        return self.name

    @property
    def subtitle(self) -> str:
        """Secondary list text."""
        parts = [self.classification]
        if self.frame_count is not None:
            parts.append(f"{self.frame_count} frames")
        if self.sampling_rate_hz is not None:
            parts.append(f"{self.sampling_rate_hz:g} Hz")
        return " · ".join(parts)

    @property
    def key(self) -> str:
        """Stable ``subject/session`` key."""
        return f"{self.subject_id}/{self.name}"

    def matches_query(self, query: str) -> bool:
        """Return True if this session matches a search query."""
        q = query.strip().lower()
        if not q:
            return True
        haystack = " ".join(
            [
                self.name.lower(),
                self.classification.lower(),
                " ".join(n.lower() for n in self.metric_names),
            ]
        )
        return q in haystack

    def to_dict(self) -> dict[str, Any]:
        """Serialize for inspector panels."""
        return {
            "subject_id": self.subject_id,
            "name": self.name,
            "classification": self.classification,
            "frame_count": self.frame_count,
            "sampling_rate_hz": self.sampling_rate_hz,
            "metric_names": list(self.metric_names),
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }
