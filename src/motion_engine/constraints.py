"""
Bone and joint constraints for skeleton validation.

Loads ``config/bone_constraints.yaml``. Soft violations are reported as
warnings by :class:`~motion_engine.skeleton.SkeletonValidator`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class BoneLengthConstraint:
    """Absolute length bounds for one bone."""

    name: str
    min_length: float = 0.0
    max_length: float = float("inf")


@dataclass(slots=True)
class ConstraintConfig:
    """Parsed bone-constraint configuration."""

    units: str = "Unknown"
    enforce_hard_limits: bool = False
    relative_min_ratio: float = 0.25
    relative_max_ratio: float = 4.0
    bones: dict[str, BoneLengthConstraint] = field(default_factory=dict)
    required_bones: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> ConstraintConfig:
        """Load bone constraints from YAML."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        relative = data.get("relative", {}) or {}
        bones: dict[str, BoneLengthConstraint] = {}
        for name, spec in (data.get("bones") or {}).items():
            bones[name] = BoneLengthConstraint(
                name=name,
                min_length=float(spec.get("min_length", 0.0)),
                max_length=float(spec.get("max_length", float("inf"))),
            )
        return cls(
            units=str(data.get("units", "Unknown")),
            enforce_hard_limits=bool(data.get("enforce_hard_limits", False)),
            relative_min_ratio=float(relative.get("min_ratio", 0.25)),
            relative_max_ratio=float(relative.get("max_ratio", 4.0)),
            bones=bones,
            required_bones=list(data.get("required_bones") or []),
            raw=data,
        )


# TODO: Joint angle limits, collision volumes, and DOF masks for humanoid robotics.
