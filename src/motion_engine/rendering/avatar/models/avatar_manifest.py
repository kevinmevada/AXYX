"""Coordinate system and manifest models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class CoordinateSystem:
    """Authoring coordinate metadata from the manifest."""

    up: str = "z"
    forward: str = "x"
    units: str = "cm"
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class LodEntry:
    """One LOD level descriptor."""

    level: int
    path: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class AvatarManifest:
    """Validated, immutable ``avatar.json`` description.

    Paths are relative to :attr:`root` unless absolute.

    Example:
        >>> from motion_engine.rendering.avatar.loader import ManifestLoader
        >>> m = ManifestLoader().load("procedural")
        >>> isinstance(m.name, str)
        True
    """

    schema_version: str
    name: str
    display_name: str
    avatar_type: str
    asset_id: str
    root: Path
    path: Path
    coordinate_system: CoordinateSystem
    skeleton: Mapping[str, Any]
    mesh: Mapping[str, Any]
    materials: Mapping[str, Any]
    textures: Mapping[str, Any]
    lod: tuple[LodEntry, ...]
    retarget: Mapping[str, Any] = field(default_factory=dict)
    physics: Mapping[str, Any] = field(default_factory=dict)
    extras: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def default_lod(self) -> int:
        """Preferred LOD index from mesh block or first lod entry."""
        mesh = dict(self.mesh)
        if "default_lod" in mesh:
            return int(mesh["default_lod"])
        if self.lod:
            return int(self.lod[0].level)
        return 0

    def lod_path(self, level: int | None = None) -> str | None:
        """Return relative mesh path for ``level``, if declared."""
        target = self.default_lod if level is None else int(level)
        for entry in self.lod:
            if entry.level == target:
                return entry.path
        pattern = dict(self.mesh).get("lod_cache_pattern")
        if isinstance(pattern, str) and "{n}" in pattern:
            return pattern.replace("{n}", str(target))
        return None


__all__ = ["CoordinateSystem", "LodEntry", "AvatarManifest"]
