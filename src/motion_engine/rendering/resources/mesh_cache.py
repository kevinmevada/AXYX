"""Generic typed cache with graceful miss handling."""

from __future__ import annotations

import logging
from typing import Callable, Generic, Hashable, TypeVar

logger = logging.getLogger(__name__)

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class ResourceCache(Generic[K, V]):
    """Simple key → value cache with optional factory on miss."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._items: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        return self._items.get(key)

    def put(self, key: K, value: V) -> V:
        self._items[key] = value
        return value

    def get_or_create(self, key: K, factory: Callable[[], V]) -> V:
        existing = self._items.get(key)
        if existing is not None:
            return existing
        try:
            value = factory()
        except Exception:
            logger.warning("%s: factory failed for %r", self.name, key, exc_info=True)
            raise
        self._items[key] = value
        logger.debug("%s: cached %r", self.name, key)
        return value

    def invalidate(self, key: K | None = None) -> None:
        if key is None:
            self._items.clear()
            return
        self._items.pop(key, None)

    def __len__(self) -> int:
        return len(self._items)

    def keys(self) -> list[K]:
        return list(self._items.keys())


__all__ = ["ResourceCache"]
