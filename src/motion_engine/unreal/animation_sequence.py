"""Post-mapping animation sequence representation for Unreal export.

``AnimationSequence`` is the canonical representation after coordinate
conversion and skeleton mapping. It is intentionally independent of Unreal
Editor Python APIs, but its fields map directly to the information needed to
construct ``UAnimSequence`` assets in UE 5.6+.

Example:
    >>> sequence = AnimationSequence.from_clip(mapped_clip)
    >>> sequence.sample(0.25)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from motion_engine.animation_clip import AnimationClip, AnimationFrame, JointTransform
from motion_engine.exceptions import MotionEngineError


class AnimationSequenceError(MotionEngineError):
    """Raised when an animation sequence fails validation."""


@dataclass
class JointCurve:
    """Translation / rotation / scale curves for one joint."""

    joint_name: str
    translations: list[tuple[float, float, float]]
    rotations: list[tuple[float, float, float, float]]
    scales: list[tuple[float, float, float]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "joint_name": self.joint_name,
            "translations": [list(v) for v in self.translations],
            "rotations": [list(v) for v in self.rotations],
            "scales": [list(v) for v in self.scales],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JointCurve:
        return cls(
            joint_name=str(data["joint_name"]),
            translations=[tuple(float(x) for x in v) for v in data["translations"]],
            rotations=[tuple(float(x) for x in v) for v in data["rotations"]],
            scales=[tuple(float(x) for x in v) for v in data["scales"]],
        )


@dataclass
class AnimationSequence:
    """Canonical post-mapping animation sequence.

    Args:
        name: Sequence asset name.
        skeleton: Target skeleton identifier.
        frames: Converted/mapped animation frames.
        fps: Sampling frequency.
        metadata: Export metadata.
        interpolation: Sampling interpolation policy.

    Example:
        >>> seq = AnimationSequence.from_clip(clip, skeleton="metahuman_ue5")
        >>> seq.validate()
        []
    """

    name: str
    skeleton: str
    frames: list[AnimationFrame]
    fps: float
    metadata: dict[str, Any] = field(default_factory=dict)
    interpolation: str = "linear"
    joint_curves: dict[str, JointCurve] = field(default_factory=dict)

    @classmethod
    def from_clip(
        cls,
        clip: AnimationClip,
        *,
        skeleton: str | None = None,
        interpolation: str = "linear",
    ) -> AnimationSequence:
        curves: dict[str, JointCurve] = {}
        for joint in clip.joint_order:
            translations = []
            rotations = []
            scales = []
            for frame in clip.frames:
                xf = frame.transforms.get(joint)
                if xf is None or not xf.valid:
                    translations.append((0.0, 0.0, 0.0))
                    rotations.append((0.0, 0.0, 0.0, 1.0))
                    scales.append((1.0, 1.0, 1.0))
                else:
                    translations.append(xf.translation)
                    rotations.append(xf.rotation)
                    scales.append(xf.scale)
            curves[joint] = JointCurve(joint, translations, rotations, scales)
        return cls(
            name=clip.name,
            skeleton=skeleton or str(clip.metadata.get("target_skeleton", "unknown")),
            frames=list(clip.frames),
            fps=float(clip.fps),
            metadata=dict(clip.metadata),
            interpolation=interpolation,
            joint_curves=curves,
        )

    @property
    def duration(self) -> float:
        if len(self.frames) <= 1:
            return 0.0
        return (len(self.frames) - 1) / self.fps

    @property
    def num_frames(self) -> int:
        return len(self.frames)

    @property
    def frame_count(self) -> int:
        """Alias for :attr:`num_frames` (certification / external API)."""
        return self.num_frames

    @property
    def joints(self) -> list[str]:
        return list(self.joint_curves)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.fps <= 0:
            errors.append("fps must be positive")
        if not self.frames:
            errors.append("sequence has no frames")
        for name, curve in self.joint_curves.items():
            if len(curve.translations) != len(self.frames):
                errors.append(f"translation curve length mismatch: {name}")
            if len(curve.rotations) != len(self.frames):
                errors.append(f"rotation curve length mismatch: {name}")
        return errors

    def sample(self, time_sec: float) -> AnimationFrame:
        """Sample the sequence at ``time_sec`` using configured interpolation."""
        if not self.frames:
            raise AnimationSequenceError("Cannot sample empty sequence")
        if self.interpolation == "nearest" or len(self.frames) == 1:
            index = int(round(time_sec * self.fps))
            index = max(0, min(index, len(self.frames) - 1))
            return self.frames[index]
        t = max(0.0, min(float(time_sec), self.duration))
        f = t * self.fps
        i0 = int(np.floor(f))
        i1 = min(i0 + 1, len(self.frames) - 1)
        alpha = float(f - i0)
        transforms: dict[str, JointTransform] = {}
        for joint, curve in self.joint_curves.items():
            p0 = np.asarray(curve.translations[i0], dtype=float)
            p1 = np.asarray(curve.translations[i1], dtype=float)
            q0 = np.asarray(curve.rotations[i0], dtype=float)
            q1 = np.asarray(curve.rotations[i1], dtype=float)
            if float(np.dot(q0, q1)) < 0.0:
                q1 *= -1.0
            q = q0 * (1.0 - alpha) + q1 * alpha
            q /= max(float(np.linalg.norm(q)), 1e-12)
            s0 = np.asarray(curve.scales[i0], dtype=float)
            s1 = np.asarray(curve.scales[i1], dtype=float)
            transforms[joint] = JointTransform(
                joint_name=joint,
                translation=tuple(float(v) for v in (p0 * (1.0 - alpha) + p1 * alpha)),
                rotation=tuple(float(v) for v in q),
                scale=tuple(float(v) for v in (s0 * (1.0 - alpha) + s1 * alpha)),
                valid=True,
            )
        return AnimationFrame(index=i0, time_sec=t, transforms=transforms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "name": self.name,
            "skeleton": self.skeleton,
            "fps": self.fps,
            "duration": self.duration,
            "interpolation": self.interpolation,
            "metadata": dict(self.metadata),
            "joint_curves": {
                name: curve.to_dict() for name, curve in self.joint_curves.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnimationSequence:
        curves = {
            name: JointCurve.from_dict(curve)
            for name, curve in data.get("joint_curves", {}).items()
        }
        frame_count = max((len(c.translations) for c in curves.values()), default=0)
        frames: list[AnimationFrame] = []
        fps = float(data["fps"])
        for index in range(frame_count):
            transforms = {
                name: JointTransform(
                    joint_name=name,
                    translation=curve.translations[index],
                    rotation=curve.rotations[index],
                    scale=curve.scales[index],
                    valid=True,
                )
                for name, curve in curves.items()
            }
            frames.append(AnimationFrame(index=index, time_sec=index / fps, transforms=transforms))
        return cls(
            name=str(data["name"]),
            skeleton=str(data["skeleton"]),
            frames=frames,
            fps=fps,
            metadata=dict(data.get("metadata", {})),
            interpolation=str(data.get("interpolation", "linear")),
            joint_curves=curves,
        )

    def save_json(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out

    @classmethod
    def load_json(cls, path: str | Path) -> AnimationSequence:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass
class AnimationSequenceDescriptor:
    """Data required to create a UAnimSequence after FBX / JSON import."""

    name: str
    skeleton_asset: str
    fps: float
    num_frames: int
    duration_sec: float
    enable_root_motion: bool = True
    interpolation: str = "linear"
    additive: bool = False
    root_joint: str = "pelvis"
    joints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_clip(
        cls,
        clip: AnimationClip,
        *,
        skeleton_asset: str,
        enable_root_motion: bool = True,
        interpolation: str = "linear",
    ) -> AnimationSequenceDescriptor:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in clip.name)
        return cls(
            name=f"{safe}_Anim",
            skeleton_asset=skeleton_asset,
            fps=float(clip.fps),
            num_frames=int(clip.n_frames),
            duration_sec=float(clip.duration_sec),
            enable_root_motion=enable_root_motion,
            interpolation=interpolation,
            root_joint=clip.root_joint,
            joints=list(clip.joint_order),
            metadata=dict(clip.metadata),
        )
