"""Serialization — mapping profiles, stats, validation reports, research metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from motion_engine.rendering.avatar.retarget.constants import RUNTIME_VERSION, SCHEMA_VERSION
from motion_engine.rendering.avatar.retarget.mapping import mapping_from_dict, mapping_to_dict
from motion_engine.rendering.avatar.retarget.types import MappingProfile, RetargetStatistics
from motion_engine.rendering.avatar.retarget.validation import ValidationReport


def export_profile(profile: MappingProfile, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping_to_dict(profile), indent=2), encoding="utf-8")


def import_profile(path: str | Path) -> MappingProfile:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return mapping_from_dict(data)


def export_statistics(stats: RetargetStatistics | dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    payload = stats.as_dict() if isinstance(stats, RetargetStatistics) else dict(stats)
    payload["runtime_version"] = RUNTIME_VERSION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_validation(report: ValidationReport, path: str | Path) -> None:
    path = Path(path)
    payload = report.as_dict()
    payload["schema_version"] = SCHEMA_VERSION
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_research_metadata(meta: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "metadata": meta,
    }
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")


__all__ = [
    "export_profile",
    "import_profile",
    "export_statistics",
    "export_validation",
    "export_research_metadata",
]
