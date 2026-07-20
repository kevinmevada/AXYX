"""Pose cache — future-ready memoization without rendering dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Hashable

from motion_engine.rendering.avatar.pose.pose import Pose


@dataclass
class PoseCache:
    """Simple key → Pose cache for bind / future animation poses.

    Keys are caller-defined (e.g. asset id + rest kind). No eviction policy
    beyond explicit ``clear`` / ``invalidate`` — sufficient for M3 and ready
    for M4+ skinning reuse.
    """

    _store: dict[Hashable, Pose] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get(self, key: Hashable) -> Pose | None:
        """Return cached pose or ``None``."""
        pose = self._store.get(key)
        if pose is None:
            self.misses += 1
            return None
        self.hits += 1
        return pose

    def put(self, key: Hashable, pose: Pose) -> None:
        """Store a pose under ``key``."""
        self._store[key] = pose

    def invalidate(self, key: Hashable) -> None:
        """Remove one entry if present."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Drop all entries and reset counters."""
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    @property
    def size(self) -> int:
        return len(self._store)


__all__ = ["PoseCache"]
