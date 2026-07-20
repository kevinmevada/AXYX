"""YAML-driven skeleton mapping helpers for Unreal / MetaHuman export.

``SkeletonMapper`` reads ``config/retarget_metahuman.yaml`` (or any compatible
profile) and maps Motion Engine joint names onto a target skeleton without
hardcoded names.

Example:
    >>> mapper = SkeletonMapper.load_mapping("config/retarget_metahuman.yaml")
    >>> mapper.map_joint("Pelvis")
    'pelvis'
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from motion_engine.animation_clip import AnimationClip, AnimationFrame, BoneEdge, JointTransform
from motion_engine.exceptions import MotionEngineError
from motion_engine.retarget import DEFAULT_METAHUMAN_MAPPING, RetargetProfile

logger = logging.getLogger(__name__)


class SkeletonMappingError(MotionEngineError):
    """Raised when skeleton mapping cannot be loaded or applied."""


@dataclass(slots=True)
class MappingResult:
    """Result details for a mapping operation."""

    mapped: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SkeletonMapper:
    """Map Motion Engine joints / frames / clips to a target skeleton.

    Args:
        profile: Retarget profile with ``source -> target`` joint mappings.
        aliases: Alternate source names resolved before mapping.
        ignored_joints: Source joints to omit intentionally.
        required_joints: Source joints that should warn if missing.

    Example:
        >>> mapper = SkeletonMapper.load_mapping()
        >>> mapped_frame, result = mapper.map_pose(frame)
    """

    profile: RetargetProfile | None = None
    aliases: dict[str, str] = field(default_factory=dict)
    ignored_joints: set[str] = field(default_factory=set)
    required_joints: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> SkeletonMapper:
        """Load a mapper from YAML (classmethod constructor)."""
        return cls().load_mapping(path)

    def load_mapping(self, path: str | Path | None = None) -> SkeletonMapper:
        """Load YAML mappings into this mapper instance and return ``self``."""
        mapping_path = Path(path) if path is not None else DEFAULT_METAHUMAN_MAPPING
        if not mapping_path.is_file():
            raise SkeletonMappingError(f"Mapping file not found: {mapping_path}")
        raw = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
        profile = RetargetProfile.from_yaml(mapping_path)
        self.profile = profile
        self.aliases = {str(k): str(v) for k, v in (raw.get("aliases") or {}).items()}
        self.ignored_joints = {str(v) for v in (raw.get("ignored_joints") or [])}
        self.required_joints = {str(v) for v in (raw.get("required_joints") or [])}
        return self

    @property
    def mapping_count(self) -> int:
        """Number of unique target joints currently mapped."""
        return len(set(self.joint_map.values()))

    def has_joint(self, joint_name: str) -> bool:
        """Return True if ``joint_name`` exists as a source or target joint."""
        name = joint_name.strip()
        if name in self.joint_map or name in self.joint_map.values():
            return True
        canonical = self.aliases.get(name, name)
        if canonical in self.joint_map:
            return True
        lower = name.lower()
        return any(v.lower() == lower for v in self.joint_map.values()) or any(
            k.lower() == lower for k in self.joint_map
        )

    @property
    def joint_map(self) -> dict[str, str]:
        if self.profile is None:
            return {}
        return dict(self.profile.joint_map)

    def map_joint(self, source_joint: str) -> str | None:
        """Map one source joint to a target joint, applying aliases."""
        canonical = self.aliases.get(source_joint, source_joint)
        if canonical in self.ignored_joints:
            return None
        return self.joint_map.get(canonical)

    def map_pose(
        self,
        frame: AnimationFrame,
    ) -> tuple[AnimationFrame, MappingResult]:
        """Map a single animation frame."""
        result = MappingResult()
        transforms: dict[str, JointTransform] = {}
        for source, transform in frame.transforms.items():
            canonical = self.aliases.get(source, source)
            if canonical in self.ignored_joints:
                result.ignored.append(source)
                continue
            target = self.joint_map.get(canonical)
            if target is None:
                result.missing.append(source)
                continue
            transforms[target] = JointTransform(
                joint_name=target,
                translation=transform.translation,
                rotation=transform.rotation,
                scale=transform.scale,
                valid=transform.valid,
            )
            result.mapped.append(source)
        for required in sorted(self.required_joints):
            if required not in frame.transforms:
                msg = f"Required source joint missing in frame {frame.index}: {required}"
                result.warnings.append(msg)
        self.warnings.extend(result.warnings)
        return (
            AnimationFrame(
                index=frame.index,
                time_sec=frame.time_sec,
                transforms=transforms,
            ),
            result,
        )

    def map_skeleton(self, clip: AnimationClip) -> AnimationClip:
        """Map an :class:`AnimationClip` skeleton and transforms."""
        if self.profile is None:
            raise SkeletonMappingError("No RetargetProfile loaded")
        mapped_frames: list[AnimationFrame] = []
        aggregate = MappingResult()
        for frame in clip.frames:
            mapped, result = self.map_pose(frame)
            mapped_frames.append(mapped)
            aggregate.mapped.extend(result.mapped)
            aggregate.missing.extend(result.missing)
            aggregate.ignored.extend(result.ignored)
            aggregate.warnings.extend(result.warnings)

        joint_order = _unique_preserve_order(
            target for source in clip.joint_order if (target := self.map_joint(source))
        )
        bones = self.remap_hierarchy(clip.bones, self.joint_map)
        root = self.profile.root_target
        out = AnimationClip(
            name=f"{clip.name}__{self.profile.target_skeleton}",
            frames=mapped_frames,
            fps=clip.fps,
            joint_order=joint_order,
            bones=bones,
            root_joint=root,
            root_motion=clip.root_motion,
            units=clip.units,
            coordinate_system=clip.coordinate_system,
            metadata={
                **dict(clip.metadata),
                "skeleton_mapper": self.profile.name,
                "source_skeleton": self.profile.source_skeleton,
                "target_skeleton": self.profile.target_skeleton,
                "mapping_warnings": aggregate.warnings[:32],
                "missing_unmapped_joints": sorted(set(aggregate.missing)),
            },
            compression=clip.compression,
        )
        missing_required = [
            name for name in sorted(self.required_joints) if name not in clip.joint_order
        ]
        if missing_required:
            warning = f"Required source joints missing from clip: {missing_required}"
            self.warnings.append(warning)
            logger.warning(warning)
        return out

    def bone_hierarchy(self, clip: AnimationClip) -> list[dict[str, str]]:
        """Return hierarchy as JSON-friendly Unreal import records."""
        return [
            {
                "name": bone.name,
                "parent": bone.parent_joint,
                "child": bone.child_joint,
            }
            for bone in clip.bones
        ]

    def joint_parent_map(self, clip: AnimationClip) -> dict[str, str | None]:
        """Return child -> parent mapping."""
        parents: dict[str, str | None] = {name: None for name in clip.joint_order}
        for bone in clip.bones:
            parents[bone.child_joint] = bone.parent_joint
        if clip.root_joint in parents:
            parents[clip.root_joint] = None
        return parents

    def remap_hierarchy(
        self, bones: list[BoneEdge], joint_map: dict[str, str]
    ) -> list[BoneEdge]:
        """Remap bone edges and remove duplicates / collapsed edges."""
        out: list[BoneEdge] = []
        seen: set[tuple[str, str]] = set()
        for bone in bones:
            parent = joint_map.get(bone.parent_joint)
            child = joint_map.get(bone.child_joint)
            if not parent or not child or parent == child:
                continue
            key = (parent, child)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                BoneEdge(
                    name=f"{parent}_{child}",
                    parent_joint=parent,
                    child_joint=child,
                )
            )
        return out


def _unique_preserve_order(values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
