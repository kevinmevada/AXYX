"""Retarget caches — mappings, offsets, constraints, pose conversions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Hashable

from motion_engine.rendering.avatar.retarget.offset_solver import OffsetTable
from motion_engine.rendering.avatar.retarget.retarget_context import RetargetContext
from motion_engine.rendering.avatar.retarget.types import MappingProfile


@dataclass
class RetargetCache:
    """Simple in-process cache for expensive prepare() results."""

    profiles: dict[str, MappingProfile] = field(default_factory=dict)
    contexts: dict[Hashable, RetargetContext] = field(default_factory=dict)
    offsets: dict[Hashable, OffsetTable] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get_profile(self, name: str) -> MappingProfile | None:
        if name in self.profiles:
            self.hits += 1
            return self.profiles[name]
        self.misses += 1
        return None

    def put_profile(self, profile: MappingProfile) -> None:
        self.profiles[profile.name] = profile

    def invalidate_profile(self, name: str) -> None:
        self.profiles.pop(name, None)
        # Drop contexts that may have been prepared with the old profile.
        stale = [k for k in self.contexts if isinstance(k, tuple) and k and k[0] == name]
        for k in stale:
            self.contexts.pop(k, None)
            self.offsets.pop(k, None)

    def get_context(self, key: Hashable) -> RetargetContext | None:
        if key in self.contexts:
            self.hits += 1
            return self.contexts[key]
        self.misses += 1
        return None

    def put_context(self, key: Hashable, ctx: RetargetContext) -> None:
        self.contexts[key] = ctx
        self.offsets[key] = ctx.offsets

    def clear(self) -> None:
        self.profiles.clear()
        self.contexts.clear()
        self.offsets.clear()
        self.extras.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "profiles": len(self.profiles),
            "contexts": len(self.contexts),
        }


_GLOBAL = RetargetCache()


def get_global_cache() -> RetargetCache:
    return _GLOBAL


__all__ = ["RetargetCache", "get_global_cache"]
