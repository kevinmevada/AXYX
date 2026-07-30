"""Evaluation / pose caches."""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, Hashable, TypeVar

from motion_engine.rendering.avatar.animation.constants import CACHE_DEFAULT_CAPACITY
from motion_engine.rendering.avatar.pose.pose import AnimationPose

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """Simple LRU cache."""

    def __init__(self, capacity: int = CACHE_DEFAULT_CAPACITY) -> None:
        self.capacity = max(1, int(capacity))
        self._data: OrderedDict[K, V] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: K) -> V | None:
        if key not in self._data:
            self.misses += 1
            return None
        self.hits += 1
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: K, value: V) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        while len(self._data) > self.capacity:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()
        self.hits = 0
        self.misses = 0

    def __len__(self) -> int:
        return len(self._data)


class EvaluationCache(LRUCache[str, AnimationPose]):
    """Cache evaluated animation poses by string key."""


class PoseCache(LRUCache[str, AnimationPose]):
    """General pose cache."""


class AnimationCache(LRUCache[str, object]):
    """Generic animation asset cache (clips, baked samples, …)."""


__all__ = ["LRUCache", "EvaluationCache", "PoseCache", "AnimationCache"]
