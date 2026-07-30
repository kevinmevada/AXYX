"""Central runtime cache for avatars, clips, poses, mappings, meshes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Hashable


@dataclass
class RuntimeCache:
    """Process-local resource cache (does not own GPU resources)."""

    avatars: dict[str, Any] = field(default_factory=dict)
    clips: dict[str, Any] = field(default_factory=dict)
    poses: dict[Hashable, Any] = field(default_factory=dict)
    mappings: dict[str, Any] = field(default_factory=dict)
    meshes: dict[str, Any] = field(default_factory=dict)
    textures: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get(self, store: str, key: Hashable) -> Any | None:
        bucket = getattr(self, store, None)
        if not isinstance(bucket, dict):
            self.misses += 1
            return None
        if key in bucket:
            self.hits += 1
            return bucket[key]
        self.misses += 1
        return None

    def put(self, store: str, key: Hashable, value: Any) -> None:
        bucket = getattr(self, store, None)
        if isinstance(bucket, dict):
            bucket[key] = value

    def clear(self) -> None:
        for name in ("avatars", "clips", "poses", "mappings", "meshes", "textures", "extras"):
            getattr(self, name).clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "avatars": len(self.avatars),
            "clips": len(self.clips),
            "poses": len(self.poses),
            "mappings": len(self.mappings),
            "meshes": len(self.meshes),
            "textures": len(self.textures),
        }


__all__ = ["RuntimeCache"]
