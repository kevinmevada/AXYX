"""
Generic skeleton-to-skeleton retargeting engine.

Mappings are always loaded from YAML - never hardcoded target joint names.
Supports robots / SMPL-X / OpenSim via YAML profiles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from motion_engine.animation_clip import (
    AnimationClip,
    AnimationClipError,
    AnimationFrame,
    BoneEdge,
    JointTransform,
    RootMotion,
)
from motion_engine.exceptions import MotionEngineError

logger = logging.getLogger(__name__)

class RetargetError(MotionEngineError):
    """Raised when retarget mapping or conversion fails."""


@dataclass(slots=True)
class JointMapping:
    """One source joint → target joint binding."""

    source: str
    target: str


@dataclass
class RetargetProfile:
    """YAML-backed retarget profile."""

    name: str
    source_skeleton: str
    target_skeleton: str
    joint_map: dict[str, str]
    root_source: str = "Pelvis"
    root_target: str = "pelvis"
    chains: dict[str, list[str]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> RetargetProfile:
        path = Path(path)
        if not path.is_file():
            raise RetargetError(f"Retarget mapping missing: {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        joints = dict(raw.get("joints") or {})
        root = raw.get("root_joint") or {}
        return cls(
            name=str(raw.get("name", path.stem)),
            source_skeleton=str(raw.get("source_skeleton", "unknown")),
            target_skeleton=str(raw.get("target_skeleton", "unknown")),
            joint_map={str(k): str(v) for k, v in joints.items()},
            root_source=str(root.get("source", "Pelvis")),
            root_target=str(root.get("target", "pelvis")),
            chains={str(k): list(v) for k, v in (raw.get("chains") or {}).items()},
            metadata={
                "schema_version": raw.get("schema_version"),
                "description": raw.get("description"),
                "path": str(path.resolve()),
            },
        )

    def mapped_targets(self) -> list[str]:
        return sorted(set(self.joint_map.values()))

    def invert(self) -> dict[str, str]:
        """Target → source (first wins on collisions)."""
        inv: dict[str, str] = {}
        for src, dst in self.joint_map.items():
            inv.setdefault(dst, src)
        return inv


class Retargeter:
    """Generic animation retargeter driven by a :class:`RetargetProfile`."""

    def __init__(self, profile: RetargetProfile) -> None:
        self.profile = profile

    @classmethod
    def from_yaml(cls, path: str | Path) -> Retargeter:
        return cls(RetargetProfile.from_yaml(path))

    def retarget(self, clip: AnimationClip) -> AnimationClip:
        """Retarget ``clip`` onto the profile target skeleton.

        Position/rotation curves are remapped by joint name. Missing source
        joints are skipped with a warning. Duplicate target joints (e.g.
        wrist/hand mapping to the same target bone) keep the last written
        source, preferring explicitly listed later entries.
        """
        if clip.n_frames <= 0:
            raise RetargetError("Cannot retarget an empty AnimationClip")

        missing = [
            src for src in self.profile.joint_map if src not in clip.joint_order
        ]
        if missing:
            logger.warning(
                "Retarget profile %s missing source joints: %s",
                self.profile.name,
                missing,
            )

        target_order = _stable_target_order(self.profile, clip)
        target_bones = _remap_bones(clip.bones, self.profile.joint_map)
        frames: list[AnimationFrame] = []

        for frame in clip.frames:
            transforms: dict[str, JointTransform] = {}
            for source_name, target_name in self.profile.joint_map.items():
                xf = frame.transforms.get(source_name)
                if xf is None:
                    continue
                transforms[target_name] = JointTransform(
                    joint_name=target_name,
                    translation=xf.translation,
                    rotation=xf.rotation,
                    scale=xf.scale,
                    valid=xf.valid,
                )
            frames.append(
                AnimationFrame(
                    index=frame.index,
                    time_sec=frame.time_sec,
                    transforms=transforms,
                )
            )

        root_motion = None
        if clip.root_motion is not None:
            root_motion = RootMotion(
                translations=clip.root_motion.translations.copy(),
                headings_rad=clip.root_motion.headings_rad.copy(),
                velocities=clip.root_motion.velocities.copy(),
                root_joint=self.profile.root_target,
            )

        out = AnimationClip(
            name=f"{clip.name}__{self.profile.target_skeleton}",
            frames=frames,
            fps=clip.fps,
            joint_order=target_order,
            bones=target_bones,
            root_joint=self.profile.root_target,
            root_motion=root_motion,
            units=clip.units,
            coordinate_system=clip.coordinate_system,
            metadata={
                **dict(clip.metadata),
                "retarget_profile": self.profile.name,
                "source_skeleton": self.profile.source_skeleton,
                "target_skeleton": self.profile.target_skeleton,
                "source_clip": clip.name,
            },
            compression=clip.compression,
        )
        report = out.validate()
        if report["errors"]:
            raise RetargetError(f"Retargeted clip invalid: {report['errors']}")
        logger.info(
            "Retargeted %s → %s (%d joints, %d frames)",
            clip.name,
            self.profile.target_skeleton,
            out.n_joints,
            out.n_frames,
        )
        return out


def _stable_target_order(
    profile: RetargetProfile, clip: AnimationClip
) -> list[str]:
    """Preserve source order while emitting unique target names."""
    seen: set[str] = set()
    order: list[str] = []
    for source in clip.joint_order:
        target = profile.joint_map.get(source)
        if target is None or target in seen:
            continue
        seen.add(target)
        order.append(target)
    for source, target in profile.joint_map.items():
        if target not in seen:
            seen.add(target)
            order.append(target)
    return order


def _remap_bones(
    bones: list[BoneEdge], joint_map: Mapping[str, str]
) -> list[BoneEdge]:
    remapped: list[BoneEdge] = []
    seen: set[tuple[str, str]] = set()
    for bone in bones:
        parent = joint_map.get(bone.parent_joint)
        child = joint_map.get(bone.child_joint)
        if parent is None or child is None or parent == child:
            continue
        key = (parent, child)
        if key in seen:
            continue
        seen.add(key)
        remapped.append(
            BoneEdge(
                name=f"{parent}_{child}",
                parent_joint=parent,
                child_joint=child,
            )
        )
    return remapped
