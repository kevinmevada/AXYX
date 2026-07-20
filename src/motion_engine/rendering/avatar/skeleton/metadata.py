"""Skeleton metadata (coordinate system, provenance, runtime version)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from motion_engine.rendering.avatar.skeleton.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.skeleton.types import CoordinateSystem, LengthUnit


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class SkeletonMetadata:
    """Extensible provenance / convention metadata for a runtime skeleton."""

    coordinate_system: CoordinateSystem = CoordinateSystem.UNKNOWN
    units: LengthUnit = LengthUnit.UNKNOWN
    source_format: str = "unknown"
    importer_version: str = ""
    bone_count: int = 0
    creation_timestamp: str = field(default_factory=_utc_now_iso)
    runtime_version: str = RUNTIME_VERSION
    skeleton_name: str = ""
    source_asset_id: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra))

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly metadata dict."""
        d = asdict(self)
        d["coordinate_system"] = self.coordinate_system.value
        d["units"] = self.units.value
        return d

    def with_bone_count(self, n: int) -> SkeletonMetadata:
        """Return a copy with updated bone count."""
        return SkeletonMetadata(
            coordinate_system=self.coordinate_system,
            units=self.units,
            source_format=self.source_format,
            importer_version=self.importer_version,
            bone_count=n,
            creation_timestamp=self.creation_timestamp,
            runtime_version=self.runtime_version,
            skeleton_name=self.skeleton_name,
            source_asset_id=self.source_asset_id,
            extra=self.extra,
        )


__all__ = ["SkeletonMetadata"]
