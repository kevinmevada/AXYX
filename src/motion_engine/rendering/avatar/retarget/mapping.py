"""Mapping profile container + JSON load/save helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from motion_engine.rendering.avatar.retarget.constants import SCHEMA_VERSION
from motion_engine.rendering.avatar.retarget.exceptions import MappingError
from motion_engine.rendering.avatar.retarget.types import (
    AXYX_COORDS,
    BoneMapEntry,
    CoordinateSystem,
    ForwardAxis,
    Handedness,
    JointLimit,
    MappingKind,
    MappingProfile,
    UpAxis,
)


def _coords_from_dict(d: dict[str, Any] | None, default: CoordinateSystem) -> CoordinateSystem:
    if not d:
        return default
    return CoordinateSystem(
        up=UpAxis(str(d.get("up", default.up.value)).lower()),
        forward=ForwardAxis(str(d.get("forward", default.forward.value)).lower()),
        handedness=Handedness(str(d.get("handedness", default.handedness.value)).lower()),
        units_per_meter=float(d.get("units_per_meter", default.units_per_meter)),
        name=str(d.get("name", default.name)),
    )


def _entry_from_dict(raw: dict[str, Any]) -> BoneMapEntry:
    source = str(raw["source"])
    targets_raw = raw.get("targets", raw.get("target"))
    if targets_raw is None:
        raise MappingError(f"Bone entry missing target(s): {source}")
    if isinstance(targets_raw, str):
        targets = (targets_raw,)
    else:
        targets = tuple(str(t) for t in targets_raw)
    kind = MappingKind(str(raw.get("kind", MappingKind.ONE_TO_ONE.value)))
    pre = tuple(float(x) for x in raw.get("pre_rotation_xyzw", (0, 0, 0, 1)))  # type: ignore[assignment]
    post = tuple(float(x) for x in raw.get("post_rotation_xyzw", (0, 0, 0, 1)))  # type: ignore[assignment]
    return BoneMapEntry(
        source=source,
        targets=targets,
        kind=kind,
        weight=float(raw.get("weight", 1.0)),
        optional=bool(raw.get("optional", False)),
        pre_rotation_xyzw=pre,  # type: ignore[arg-type]
        post_rotation_xyzw=post,  # type: ignore[arg-type]
        copy_translation=bool(raw.get("copy_translation", False)),
        metadata=dict(raw.get("metadata") or {}),
    )


def mapping_from_dict(data: dict[str, Any]) -> MappingProfile:
    bones_raw = data.get("bones") or data.get("joints") or []
    if isinstance(bones_raw, dict):
        # canonical_to_avatar shorthand
        bones = [
            BoneMapEntry(source=str(k), targets=(str(v),))
            for k, v in bones_raw.items()
        ]
    else:
        bones = [_entry_from_dict(b) for b in bones_raw]

    limits = []
    for lim in data.get("joint_limits") or []:
        limits.append(
            JointLimit(
                bone=str(lim["bone"]),
                min_xyz=tuple(float(x) for x in lim.get("min_xyz", (-3.14159,) * 3)),  # type: ignore[arg-type]
                max_xyz=tuple(float(x) for x in lim.get("max_xyz", (3.14159,) * 3)),  # type: ignore[arg-type]
                locked=bool(lim.get("locked", False)),
                preferred_axis=tuple(float(x) for x in lim["preferred_axis"]) if lim.get("preferred_axis") else None,  # type: ignore[arg-type]
                hard=bool(lim.get("hard", False)),
            )
        )

    root = data.get("root") or data.get("root_joint") or {}
    return MappingProfile(
        name=str(data.get("name", "unnamed")),
        source_skeleton=str(data.get("source_skeleton", "unknown")),
        target_skeleton=str(data.get("target_skeleton", "unknown")),
        bones=tuple(bones),
        root_source=str(root.get("source", data.get("root_source", "Pelvis"))),
        root_target=str(root.get("target", data.get("root_target", "pelvis"))),
        source_coords=_coords_from_dict(data.get("source_coords"), AXYX_COORDS),
        target_coords=_coords_from_dict(data.get("target_coords"), AXYX_COORDS),
        ignore_source=tuple(str(x) for x in (data.get("ignore_source") or [])),
        ignore_target=tuple(str(x) for x in (data.get("ignore_target") or [])),
        joint_limits=tuple(limits),
        chains={str(k): list(v) for k, v in (data.get("chains") or {}).items()},
        metadata={
            "schema_version": data.get("schema_version", SCHEMA_VERSION),
            **dict(data.get("metadata") or {}),
        },
    )


def mapping_to_dict(profile: MappingProfile) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "name": profile.name,
        "source_skeleton": profile.source_skeleton,
        "target_skeleton": profile.target_skeleton,
        "root": {"source": profile.root_source, "target": profile.root_target},
        "source_coords": {
            "name": profile.source_coords.name,
            "up": profile.source_coords.up.value,
            "forward": profile.source_coords.forward.value,
            "handedness": profile.source_coords.handedness.value,
            "units_per_meter": profile.source_coords.units_per_meter,
        },
        "target_coords": {
            "name": profile.target_coords.name,
            "up": profile.target_coords.up.value,
            "forward": profile.target_coords.forward.value,
            "handedness": profile.target_coords.handedness.value,
            "units_per_meter": profile.target_coords.units_per_meter,
        },
        "bones": [
            {
                "source": e.source,
                "targets": list(e.targets),
                "kind": e.kind.value,
                "weight": e.weight,
                "optional": e.optional,
                "pre_rotation_xyzw": list(e.pre_rotation_xyzw),
                "post_rotation_xyzw": list(e.post_rotation_xyzw),
                "copy_translation": e.copy_translation,
            }
            for e in profile.bones
        ],
        "ignore_source": list(profile.ignore_source),
        "ignore_target": list(profile.ignore_target),
        "joint_limits": [
            {
                "bone": lim.bone,
                "min_xyz": list(lim.min_xyz),
                "max_xyz": list(lim.max_xyz),
                "locked": lim.locked,
                "preferred_axis": list(lim.preferred_axis) if lim.preferred_axis else None,
                "hard": lim.hard,
            }
            for lim in profile.joint_limits
        ],
        "chains": {k: list(v) for k, v in profile.chains.items()},
        "metadata": dict(profile.metadata),
    }


def load_mapping(path: str | Path) -> MappingProfile:
    path = Path(path)
    if not path.is_file():
        raise MappingError(f"Mapping file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return mapping_from_dict(data)


def save_mapping(profile: MappingProfile, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping_to_dict(profile), indent=2), encoding="utf-8")


__all__ = [
    "mapping_from_dict",
    "mapping_to_dict",
    "load_mapping",
    "save_mapping",
]
