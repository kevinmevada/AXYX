"""
Canonical animation representation for the AXYX Motion Engine.


``AnimationClip`` is the central animation asset consumed by retargeting,
exporters, Unreal/Unity/Blender adapters, and future GPU upload paths.

Coordinate / unit policy
------------------------
- Positions inherit the source :class:`~motion_engine.skeleton.Skeleton`.
- Units remain ``Unknown`` unless the producer explicitly sets them.
- Rotations are derived from bone directions when only positions exist.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator, Sequence

import numpy as np
from numpy.typing import NDArray

from motion_engine.exceptions import MotionEngineError
from motion_engine.skeleton import Skeleton

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating[Any]]
Quat = tuple[float, float, float, float]  # x, y, z, w
Vec3 = tuple[float, float, float]


class AnimationClipError(MotionEngineError):
    """Raised when an animation clip fails validation or I/O."""


@dataclass(slots=True)
class JointTransform:
    """Per-joint rigid transform at a single frame."""

    joint_name: str
    translation: Vec3
    rotation: Quat = (0.0, 0.0, 0.0, 1.0)
    scale: Vec3 = (1.0, 1.0, 1.0)
    valid: bool = True

    def as_matrix(self) -> FloatArray:
        """Return a 4×4 homogeneous transform matrix."""
        x, y, z, w = self.rotation
        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z
        rot = np.array(
            [
                [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
                [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
                [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
            ],
            dtype=float,
        )
        sx, sy, sz = self.scale
        rot = rot @ np.diag([sx, sy, sz])
        mat = np.eye(4, dtype=float)
        mat[:3, :3] = rot
        mat[:3, 3] = self.translation
        return mat


@dataclass(slots=True)
class AnimationFrame:
    """One discrete animation sample."""

    index: int
    time_sec: float
    transforms: dict[str, JointTransform] = field(default_factory=dict)

    def joint_names(self) -> list[str]:
        return sorted(self.transforms)


@dataclass(slots=True)
class BoneEdge:
    """Directed parent → child bone edge in the clip hierarchy."""

    name: str
    parent_joint: str
    child_joint: str


@dataclass(slots=True)
class RootMotion:
    """Pelvis / root trajectory used for locomotion and robot drive."""

    translations: FloatArray
    headings_rad: FloatArray
    velocities: FloatArray
    root_joint: str = "Pelvis"

    def __post_init__(self) -> None:
        self.translations = np.asarray(self.translations, dtype=float)
        self.headings_rad = np.asarray(self.headings_rad, dtype=float)
        self.velocities = np.asarray(self.velocities, dtype=float)

    @property
    def n_frames(self) -> int:
        return int(self.translations.shape[0])


@dataclass(slots=True)
class CompressionHooks:
    """Optional hooks for future curve compression / streaming / GPU upload."""

    keyframe_reduction: bool = False
    bitrate_hint: int | None = None
    streamable: bool = False
    gpu_upload_ready: bool = False
    codec: str | None = None


@dataclass
class AnimationClip:
    """Renderer-neutral animation asset.

    Attributes:
        name: Asset name.
        frames: Ordered discrete samples.
        fps: Frames per second.
        joint_order: Stable joint traversal order (root-first when possible).
        bones: Hierarchy edges.
        root_joint: Root joint name.
        root_motion: Optional locomotion channels.
        units: Physical units string (may be ``Unknown``).
        coordinate_system: Named frame (e.g. ``lab``, ``unreal``).
        metadata: Free-form producer metadata.
        compression: Future compression / streaming hooks.
    """

    name: str
    frames: list[AnimationFrame]
    fps: float
    joint_order: list[str] = field(default_factory=list)
    bones: list[BoneEdge] = field(default_factory=list)
    root_joint: str = "Pelvis"
    root_motion: RootMotion | None = None
    units: str = "Unknown"
    coordinate_system: str = "lab"
    metadata: dict[str, Any] = field(default_factory=dict)
    compression: CompressionHooks = field(default_factory=CompressionHooks)
    _lazy_path: Path | None = field(default=None, repr=False)

    # ------------------------------------------------------------------ API

    @classmethod
    def from_skeleton(
        cls,
        skeleton: Skeleton,
        *,
        name: str | None = None,
        fps: float | None = None,
        estimate_rotations: bool = True,
    ) -> AnimationClip:
        """Build an :class:`AnimationClip` from a reconstructed :class:`Skeleton`.

        Args:
            skeleton: Source skeleton (positions required).
            name: Optional override name.
            fps: Override sampling rate; defaults to ``skeleton.sampling_rate_hz``.
            estimate_rotations: Derive bone-aim quaternions from positions.
        """
        if skeleton.n_frames <= 0 or not skeleton.poses:
            raise AnimationClipError("Skeleton has no poses to convert")

        rate = float(fps if fps is not None else (skeleton.sampling_rate_hz or 100.0))
        if rate <= 0.0:
            raise AnimationClipError(f"Invalid fps/sampling rate: {rate}")

        joint_order = _topo_joint_order(skeleton)
        bones = [
            BoneEdge(
                name=bone.name,
                parent_joint=bone.parent_joint,
                child_joint=bone.child_joint,
            )
            for bone in skeleton.bones.values()
        ]
        parent_of = {
            joint.name: joint.parent for joint in skeleton.joints.values()
        }
        children_of: dict[str, list[str]] = {name: [] for name in joint_order}
        for joint in skeleton.joints.values():
            if joint.parent is not None and joint.parent in children_of:
                children_of[joint.parent].append(joint.name)

        frames: list[AnimationFrame] = []
        root_translations: list[Vec3] = []
        for pose in skeleton.poses:
            t = float(pose.frame_index) / rate
            transforms: dict[str, JointTransform] = {}
            positions: dict[str, np.ndarray] = {}
            for joint_name in joint_order:
                pos = pose.get_position(joint_name)
                if pos is None or not np.all(np.isfinite(pos)):
                    transforms[joint_name] = JointTransform(
                        joint_name=joint_name,
                        translation=(0.0, 0.0, 0.0),
                        valid=False,
                    )
                    continue
                positions[joint_name] = np.asarray(pos, dtype=float)
                xyz = (float(pos[0]), float(pos[1]), float(pos[2]))
                transforms[joint_name] = JointTransform(
                    joint_name=joint_name,
                    translation=xyz,
                    valid=True,
                )

            if estimate_rotations:
                _assign_aim_rotations(transforms, positions, children_of, parent_of)

            frames.append(
                AnimationFrame(index=pose.frame_index, time_sec=t, transforms=transforms)
            )
            root = transforms.get(skeleton.root_joint)
            if root is not None and root.valid:
                root_translations.append(root.translation)
            else:
                root_translations.append((0.0, 0.0, 0.0))

        root_motion = _build_root_motion(
            root_translations, rate, root_joint=skeleton.root_joint
        )
        clip = cls(
            name=name or skeleton.name,
            frames=frames,
            fps=rate,
            joint_order=joint_order,
            bones=bones,
            root_joint=skeleton.root_joint,
            root_motion=root_motion,
            units=skeleton.units,
            coordinate_system=skeleton.coordinate_system,
            metadata={
                "subject_id": skeleton.subject_id,
                "session_name": skeleton.session_name,
                "definition_name": skeleton.definition_name,
                "source": "Skeleton",
                **dict(skeleton.metadata or {}),
            },
        )
        report = clip.validate()
        if report["errors"]:
            raise AnimationClipError(
                f"AnimationClip validation failed: {report['errors']}"
            )
        logger.info(
            "AnimationClip built: name=%s frames=%d joints=%d fps=%.3f",
            clip.name,
            clip.n_frames,
            clip.n_joints,
            clip.fps,
        )
        return clip

    # ------------------------------------------------------------ properties

    @property
    def n_frames(self) -> int:
        return len(self.frames)

    @property
    def frame_count(self) -> int:
        """Alias for :attr:`n_frames` (certification / external API)."""
        return self.n_frames

    @property
    def n_joints(self) -> int:
        return len(self.joint_order)

    @property
    def duration_sec(self) -> float:
        if self.n_frames <= 1:
            return 0.0
        return (self.n_frames - 1) / float(self.fps)

    @property
    def duration(self) -> float:
        """Alias for :attr:`duration_sec` (certification / external API)."""
        return self.duration_sec

    @property
    def joints(self) -> list[str]:
        """Alias for :attr:`joint_order` (certification / external API)."""
        return list(self.joint_order)

    @property
    def skeleton(self) -> str:
        """Skeleton identity string used by converters / certification."""
        return str(
            self.metadata.get("target_skeleton")
            or self.metadata.get("definition_name")
            or self.root_joint
        )

    @property
    def timestamps(self) -> FloatArray:
        return np.asarray([frame.time_sec for frame in self.frames], dtype=float)

    def get_frame(self, index: int) -> AnimationFrame:
        if index < 0 or index >= self.n_frames:
            raise AnimationClipError(f"Frame index out of range: {index}")
        return self.frames[index]

    def iter_frames(self) -> Iterator[AnimationFrame]:
        return iter(self.frames)

    def joint_positions(self, frame_index: int) -> dict[str, Vec3]:
        frame = self.get_frame(frame_index)
        return {
            name: xf.translation
            for name, xf in frame.transforms.items()
            if xf.valid
        }

    # ----------------------------------------------------------- validation

    def validate(self) -> dict[str, list[str]]:
        """Lightweight structural validation."""
        errors: list[str] = []
        warnings: list[str] = []
        if self.n_frames <= 0:
            errors.append("Clip has no frames")
        if self.fps <= 0.0:
            errors.append(f"Invalid fps: {self.fps}")
        if not self.joint_order:
            warnings.append("joint_order is empty")
        if self.root_joint and self.root_joint not in self.joint_order:
            warnings.append(f"root_joint {self.root_joint!r} missing from joint_order")
        for i, frame in enumerate(self.frames):
            if frame.index != i and abs(frame.index - i) > 0:
                # Allow non-dense indices but warn on gaps.
                if i > 0 and frame.index <= self.frames[i - 1].index:
                    errors.append(f"Non-increasing frame index at {i}")
            if abs(frame.time_sec - (frame.index / self.fps)) > 1e-3:
                warnings.append(f"Timestamp mismatch at frame {i}")
        if self.root_motion is not None and self.root_motion.n_frames != self.n_frames:
            errors.append("Root motion length != frame count")
        return {"errors": errors, "warnings": warnings}

    # -------------------------------------------------------- serialization

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        payload: dict[str, Any] = {
            "schema_version": "1.0.0",
            "name": self.name,
            "fps": self.fps,
            "duration_sec": self.duration_sec,
            "n_frames": self.n_frames,
            "joint_order": list(self.joint_order),
            "root_joint": self.root_joint,
            "units": self.units,
            "coordinate_system": self.coordinate_system,
            "bones": [asdict(bone) for bone in self.bones],
            "metadata": dict(self.metadata),
            "compression": asdict(self.compression),
            "frames": [
                {
                    "index": frame.index,
                    "time_sec": frame.time_sec,
                    "transforms": {
                        name: {
                            "translation": list(xf.translation),
                            "rotation": list(xf.rotation),
                            "scale": list(xf.scale),
                            "valid": xf.valid,
                        }
                        for name, xf in frame.transforms.items()
                    },
                }
                for frame in self.frames
            ],
        }
        if self.root_motion is not None:
            payload["root_motion"] = {
                "root_joint": self.root_motion.root_joint,
                "translations": self.root_motion.translations.tolist(),
                "headings_rad": self.root_motion.headings_rad.tolist(),
                "velocities": self.root_motion.velocities.tolist(),
            }
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnimationClip:
        """Deserialize from :meth:`to_dict` output."""
        frames = [
            AnimationFrame(
                index=int(item["index"]),
                time_sec=float(item["time_sec"]),
                transforms={
                    name: JointTransform(
                        joint_name=name,
                        translation=_as_vec3(xf["translation"]),
                        rotation=_as_quat(xf.get("rotation", (0, 0, 0, 1))),
                        scale=_as_vec3(xf.get("scale", (1, 1, 1))),
                        valid=bool(xf.get("valid", True)),
                    )
                    for name, xf in item.get("transforms", {}).items()
                },
            )
            for item in data.get("frames", [])
        ]
        bones = [
            BoneEdge(**bone) for bone in data.get("bones", [])
        ]
        root_motion = None
        if "root_motion" in data and data["root_motion"] is not None:
            rm = data["root_motion"]
            root_motion = RootMotion(
                translations=np.asarray(rm["translations"], dtype=float),
                headings_rad=np.asarray(rm["headings_rad"], dtype=float),
                velocities=np.asarray(rm["velocities"], dtype=float),
                root_joint=str(rm.get("root_joint", data.get("root_joint", "Pelvis"))),
            )
        compression = CompressionHooks(**data.get("compression", {}))
        return cls(
            name=str(data["name"]),
            frames=frames,
            fps=float(data["fps"]),
            joint_order=list(data.get("joint_order", [])),
            bones=bones,
            root_joint=str(data.get("root_joint", "Pelvis")),
            root_motion=root_motion,
            units=str(data.get("units", "Unknown")),
            coordinate_system=str(data.get("coordinate_system", "lab")),
            metadata=dict(data.get("metadata", {})),
            compression=compression,
        )

    def save_json(self, path: str | Path) -> Path:
        """Write clip JSON to disk."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        logger.info("Wrote AnimationClip JSON → %s", out)
        return out

    @classmethod
    def load_json(cls, path: str | Path, *, lazy: bool = False) -> AnimationClip:
        """Load clip JSON from disk.

        Args:
            path: JSON file.
            lazy: If True, defer frame decode until first frame access
                (metadata-only shell; currently loads eagerly but marks
                ``_lazy_path`` for future streaming backends).
        """
        path = Path(path)
        if lazy:
            # Streaming / mmap backend reserved - still parse for correctness.
            logger.debug("Lazy load requested for %s (eager fallback)", path)
        data = json.loads(path.read_text(encoding="utf-8"))
        clip = cls.from_dict(data)
        clip._lazy_path = path if lazy else None
        return clip

    def copy(self) -> AnimationClip:
        """Deep-ish copy via serialize round-trip."""
        return AnimationClip.from_dict(self.to_dict())


# ------------------------------------------------------------------ helpers


def _as_vec3(value: Sequence[float]) -> Vec3:
    return (float(value[0]), float(value[1]), float(value[2]))


def _as_quat(value: Sequence[float]) -> Quat:
    return (float(value[0]), float(value[1]), float(value[2]), float(value[3]))


def _topo_joint_order(skeleton: Skeleton) -> list[str]:
    """Root-first topological joint order."""
    remaining = set(skeleton.joints)
    order: list[str] = []
    if skeleton.root_joint in remaining:
        queue = [skeleton.root_joint]
    else:
        queue = sorted(remaining)

    while queue:
        name = queue.pop(0)
        if name not in remaining:
            continue
        remaining.remove(name)
        order.append(name)
        children = sorted(skeleton.children_of(name))
        queue.extend(children)

    # Orphans / cycles: append remaining alphabetically.
    order.extend(sorted(remaining))
    return order


def _quat_from_to(from_dir: np.ndarray, to_dir: np.ndarray) -> Quat:
    """Shortest-arc quaternion rotating ``from_dir`` onto ``to_dir``."""
    a = from_dir / max(float(np.linalg.norm(from_dir)), 1e-12)
    b = to_dir / max(float(np.linalg.norm(to_dir)), 1e-12)
    dot = float(np.clip(np.dot(a, b), -1.0, 1.0))
    if dot > 0.999999:
        return (0.0, 0.0, 0.0, 1.0)
    if dot < -0.999999:
        axis = np.cross(a, np.array([1.0, 0.0, 0.0]))
        if float(np.linalg.norm(axis)) < 1e-6:
            axis = np.cross(a, np.array([0.0, 1.0, 0.0]))
        axis = axis / max(float(np.linalg.norm(axis)), 1e-12)
        return (float(axis[0]), float(axis[1]), float(axis[2]), 0.0)
    axis = np.cross(a, b)
    w = 1.0 + dot
    q = np.array([axis[0], axis[1], axis[2], w], dtype=float)
    q = q / max(float(np.linalg.norm(q)), 1e-12)
    return (float(q[0]), float(q[1]), float(q[2]), float(q[3]))


def _assign_aim_rotations(
    transforms: dict[str, JointTransform],
    positions: dict[str, np.ndarray],
    children_of: dict[str, list[str]],
    parent_of: dict[str, str | None],
) -> None:
    """Estimate joint orientations by aiming toward a primary child."""
    world_up = np.array([0.0, 0.0, 1.0], dtype=float)
    for name, xf in transforms.items():
        if not xf.valid or name not in positions:
            continue
        child_candidates = [
            child for child in children_of.get(name, []) if child in positions
        ]
        if not child_candidates:
            continue
        child = sorted(child_candidates)[0]
        direction = positions[child] - positions[name]
        if float(np.linalg.norm(direction)) < 1e-9:
            continue
        # Prefer aiming local +Z (Unreal bone forward often +X; we keep +Z
        # as bone axis for lab Z-up mocap until the Unreal converter remaps).
        rot = _quat_from_to(world_up, direction)
        transforms[name] = JointTransform(
            joint_name=name,
            translation=xf.translation,
            rotation=rot,
            scale=xf.scale,
            valid=True,
        )
    _ = parent_of  # reserved for local-space conversion


def _build_root_motion(
    translations: Sequence[Vec3],
    fps: float,
    *,
    root_joint: str,
) -> RootMotion:
    arr = np.asarray(translations, dtype=float)
    n = arr.shape[0]
    headings = np.zeros(n, dtype=float)
    velocities = np.zeros((n, 3), dtype=float)
    if n >= 2:
        delta = np.diff(arr, axis=0)
        velocities[1:] = delta * float(fps)
        velocities[0] = velocities[1]
        planar = delta[:, :2]
        norms = np.linalg.norm(planar, axis=1)
        for i, (dx, dy) in enumerate(planar):
            if norms[i] > 1e-9:
                headings[i + 1] = math.atan2(float(dy), float(dx))
            else:
                headings[i + 1] = headings[i]
        headings[0] = headings[1] if n > 1 else 0.0
    return RootMotion(
        translations=arr,
        headings_rad=headings,
        velocities=velocities,
        root_joint=root_joint,
    )
