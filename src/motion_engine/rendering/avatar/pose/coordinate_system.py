"""Coordinate-system metadata for poses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from motion_engine.rendering.avatar.pose.types import Handedness
from motion_engine.rendering.avatar.skeleton.types import CoordinateSystem, LengthUnit


@dataclass(frozen=True, slots=True)
class PoseCoordinateSystem:
    """Authoritative coordinate convention attached to a pose."""

    coordinate_system: CoordinateSystem = CoordinateSystem.UNKNOWN
    handedness: Handedness = Handedness.UNKNOWN
    units: LengthUnit = LengthUnit.UNKNOWN
    up_axis: str = ""
    forward_axis: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra", dict(self.extra))
        if self.handedness is Handedness.UNKNOWN:
            if self.coordinate_system in {
                CoordinateSystem.Y_UP_RIGHT,
                CoordinateSystem.Z_UP_RIGHT,
            }:
                object.__setattr__(self, "handedness", Handedness.RIGHT)
            elif self.coordinate_system in {
                CoordinateSystem.Y_UP_LEFT,
                CoordinateSystem.Z_UP_LEFT,
            }:
                object.__setattr__(self, "handedness", Handedness.LEFT)

    @classmethod
    def from_skeleton_metadata(
        cls,
        coordinate_system: CoordinateSystem,
        units: LengthUnit,
        *,
        extra: Mapping[str, Any] | None = None,
    ) -> PoseCoordinateSystem:
        """Build pose coords from skeleton metadata enums."""
        up = ""
        if coordinate_system in {CoordinateSystem.Y_UP_RIGHT, CoordinateSystem.Y_UP_LEFT}:
            up = "Y"
        elif coordinate_system in {CoordinateSystem.Z_UP_RIGHT, CoordinateSystem.Z_UP_LEFT}:
            up = "Z"
        return cls(
            coordinate_system=coordinate_system,
            units=units,
            up_axis=up,
            extra=extra or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly dict."""
        d = asdict(self)
        d["coordinate_system"] = self.coordinate_system.value
        d["handedness"] = self.handedness.value
        d["units"] = self.units.value
        return d


__all__ = ["PoseCoordinateSystem"]
