"""
Coordinate-system models and loaders for Human Reconstruction.

Reads ``config/coordinate_system.yaml``. SkeletonBuilder consumes a simplified
view of this configuration; full remapping presets are future work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class CoordinateSystemConfig:
    """Laboratory / export coordinate-system policy."""

    name: str = "lab"
    units: str = "Unknown"
    internal_layout: str = "N,3"
    supported_layouts: list[str] = field(default_factory=lambda: ["N,3", "3,N"])
    axes: dict[str, str] = field(default_factory=dict)
    export_presets: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> CoordinateSystemConfig:
        """Load a coordinate-system configuration file."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return cls(
            name=str(data.get("name", "lab")),
            units=str(data.get("units", "Unknown")),
            internal_layout=str(data.get("internal_layout", "N,3")),
            supported_layouts=list(data.get("supported_layouts", ["N,3", "3,N"])),
            axes=dict(data.get("axes", {})),
            export_presets=dict(data.get("export_presets", {})),
            raw=data,
        )


# TODO: Implement LabFrame, AxisRemapper, and export-preset converters.
