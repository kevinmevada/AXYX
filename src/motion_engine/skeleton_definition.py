"""
Skeleton definition schema and YAML loader.

Canonical marker → joint / bone mappings are loaded from
``config/skeleton_definition.yaml`` - never hardcoded in Python builders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class JointSourceSpec:
    """One prioritized source for resolving a joint position."""

    type: str
    priority: int = 100
    name: str | None = None
    names: list[str] = field(default_factory=list)
    method: str = "centroid"


@dataclass(slots=True)
class JointDefinition:
    """Declarative joint node in the skeleton definition."""

    name: str
    parent: str | None
    sources: list[JointSourceSpec] = field(default_factory=list)


@dataclass(slots=True)
class BoneDefinition:
    """Declarative bone edge between two joints."""

    name: str
    parent_joint: str
    child_joint: str


@dataclass(slots=True)
class SkeletonDefinition:
    """Full skeleton recipe loaded from YAML."""

    name: str
    root_joint: str
    units: str = "Unknown"
    coordinate_system: str = "lab"
    description: str = ""
    joints: dict[str, JointDefinition] = field(default_factory=dict)
    bones: dict[str, BoneDefinition] = field(default_factory=dict)
    required_markers: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def required_source_markers(self) -> set[str]:
        """Return every marker name referenced by joint sources."""
        names: set[str] = set(self.required_markers)
        for joint in self.joints.values():
            for source in joint.sources:
                if source.type in {"marker", "markers"}:
                    names.update(source.names)
                    if source.name:
                        names.add(source.name)
        return names

    @classmethod
    def from_yaml(cls, path: str | Path) -> SkeletonDefinition:
        """Load a skeleton definition from YAML."""
        path = Path(path)
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        joints: dict[str, JointDefinition] = {}
        for joint_name, spec in (data.get("joints") or {}).items():
            sources: list[JointSourceSpec] = []
            for raw_source in spec.get("sources") or []:
                names = list(raw_source.get("names") or [])
                single = raw_source.get("name")
                if single and single not in names and raw_source.get("type") in {
                    "marker",
                    "markers",
                }:
                    names.append(str(single))
                sources.append(
                    JointSourceSpec(
                        type=str(raw_source.get("type", "markers")),
                        priority=int(raw_source.get("priority", 100)),
                        name=str(single) if single is not None else None,
                        names=names,
                        method=str(raw_source.get("method", "centroid")),
                    )
                )
            sources.sort(key=lambda item: item.priority)
            joints[joint_name] = JointDefinition(
                name=joint_name,
                parent=spec.get("parent"),
                sources=sources,
            )

        bones: dict[str, BoneDefinition] = {}
        for bone_name, spec in (data.get("bones") or {}).items():
            bones[bone_name] = BoneDefinition(
                name=bone_name,
                parent_joint=str(spec["parent_joint"]),
                child_joint=str(spec["child_joint"]),
            )

        return cls(
            name=str(data.get("name", "unnamed_skeleton")),
            root_joint=str(data.get("root_joint", "Pelvis")),
            units=str(data.get("units", "Unknown")),
            coordinate_system=str(data.get("coordinate_system", "lab")),
            description=str(data.get("description", "")).strip(),
            joints=joints,
            bones=bones,
            required_markers=list(data.get("required_markers") or []),
            raw=data,
        )


DEFAULT_SKELETON_DEFINITION_PATH = Path("config/skeleton_definition.yaml")
"""Default relative path to the production skeleton definition."""
