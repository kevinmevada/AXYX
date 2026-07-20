"""
Format-agnostic animation export interfaces.

Blender / Unity / OpenSim adapters consume :class:`~motion_engine.animation_clip.AnimationClip` only.

Do **not** import DCC runtimes from this module.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from motion_engine.animation_clip import AnimationClip, AnimationClipError
from motion_engine.exceptions import MotionEngineError

logger = logging.getLogger(__name__)


class ExporterError(MotionEngineError):
    """Raised when an animation export fails."""


class ExportFormat(str, Enum):
    """Supported logical export formats."""

    ANIMATION_JSON = "animation_json"
    FBX = "fbx"
    GLTF = "gltf"
    USD = "usd"


class AnimationExporter(ABC):
    """Abstract exporter for :class:`AnimationClip` assets."""

    format: ExportFormat

    @abstractmethod
    def export(self, clip: AnimationClip, path: str | Path) -> Path:
        """Write ``clip`` to ``path`` and return the written path."""

    def validate_clip(self, clip: AnimationClip) -> None:
        report = clip.validate()
        if report["errors"]:
            raise ExporterError(f"Clip failed validation: {report['errors']}")


class AnimationJsonExporter(AnimationExporter):
    """Canonical Motion Engine JSON animation package."""

    format = ExportFormat.ANIMATION_JSON

    def export(self, clip: AnimationClip, path: str | Path) -> Path:
        self.validate_clip(clip)
        out = Path(path)
        if out.suffix.lower() != ".json":
            out = out.with_suffix(".json")
        return clip.save_json(out)


class FbxExporter(AnimationExporter):
    """FBX binary/ASCII exporter (interface reserved)."""

    format = ExportFormat.FBX

    def export(self, clip: AnimationClip, path: str | Path) -> Path:
        self.validate_clip(clip)
        raise ExporterError(
            "FBX export requires an external encoder (Autodesk FBX SDK / "
            "Blender). Use AnimationJsonExporter for now."
        )


class GltfExporter(AnimationExporter):
    """glTF 2.0 exporter (interface reserved)."""

    format = ExportFormat.GLTF

    def export(self, clip: AnimationClip, path: str | Path) -> Path:
        self.validate_clip(clip)
        raise ExporterError(
            "glTF export is reserved for a future encoder backend."
        )


class UsdExporter(AnimationExporter):
    """USD / Omniverse exporter (interface reserved)."""

    format = ExportFormat.USD

    def export(self, clip: AnimationClip, path: str | Path) -> Path:
        self.validate_clip(clip)
        raise ExporterError(
            "USD export is reserved for a future Omniverse backend."
        )


def create_exporter(fmt: ExportFormat | str) -> AnimationExporter:
    """Factory for format exporters."""
    if isinstance(fmt, str):
        fmt = ExportFormat(fmt.lower())
    mapping: dict[ExportFormat, type[AnimationExporter]] = {
        ExportFormat.ANIMATION_JSON: AnimationJsonExporter,
        ExportFormat.FBX: FbxExporter,
        ExportFormat.GLTF: GltfExporter,
        ExportFormat.USD: UsdExporter,
    }
    try:
        return mapping[fmt]()
    except KeyError as exc:
        raise ExporterError(f"Unsupported export format: {fmt}") from exc


def write_export_sidecar(
    clip: AnimationClip,
    path: str | Path,
    *,
    format_name: str,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write a small sidecar metadata JSON next to an export."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "clip": clip.name,
        "format": format_name,
        "fps": clip.fps,
        "n_frames": clip.n_frames,
        "n_joints": clip.n_joints,
        "units": clip.units,
        "coordinate_system": clip.coordinate_system,
        "root_joint": clip.root_joint,
        "metadata": dict(clip.metadata),
    }
    if extra:
        payload["extra"] = extra
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


__all__ = [
    "ExporterError",
    "ExportFormat",
    "AnimationExporter",
    "AnimationJsonExporter",
    "FbxExporter",
    "GltfExporter",
    "UsdExporter",
    "create_exporter",
    "write_export_sidecar",
]