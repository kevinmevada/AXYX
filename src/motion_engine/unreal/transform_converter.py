"""Transform conversion utilities for Unreal export.

This module owns transform math: quaternion normalization, matrix
composition/decomposition, parent-relative transforms, local/world
conversion, root-motion extraction, and per-frame conversion. It intentionally
does not know about MetaHuman names or file formats.

Example:
    >>> converter = TransformConverter()
    >>> converter.normalize_quaternion((0, 0, 0, 2))
    (0.0, 0.0, 0.0, 1.0)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from motion_engine.animation_clip import AnimationClip, AnimationFrame, JointTransform, RootMotion
from motion_engine.exceptions import MotionEngineError
from motion_engine.unreal.coordinate_converter import CoordinateConverter

FloatArray = NDArray[np.floating]
Quat = tuple[float, float, float, float]
Vec3 = tuple[float, float, float]
EulerDeg = tuple[float, float, float]


class TransformConversionError(MotionEngineError):
    """Raised when transform conversion fails validation."""


@dataclass(slots=True)
class TransformBundle:
    """World/local transform channels for one animation frame."""

    world: dict[str, JointTransform]
    local: dict[str, JointTransform]


class TransformConverter:
    """Convert and derive animation transforms.

    Args:
        coordinates: Optional coordinate converter. If supplied, translation
            and rotation conversions are applied before matrix construction.

    Example:
        >>> converter = TransformConverter()
        >>> local = converter.parent_relative_transform(child, parent)
    """

    def __init__(self, coordinates: CoordinateConverter | None = None) -> None:
        self.coordinates = coordinates

    def convert_translation(self, translation: Sequence[float]) -> Vec3:
        if self.coordinates is None:
            return (float(translation[0]), float(translation[1]), float(translation[2]))
        return self.coordinates.convert_point(translation)

    def normalize_quaternion(self, rotation: Sequence[float]) -> Quat:
        """Return a unit quaternion, falling back to identity for degenerate input."""
        q = np.asarray(rotation, dtype=float).reshape(4)
        norm = float(np.linalg.norm(q))
        if norm < 1e-12:
            return (0.0, 0.0, 0.0, 1.0)
        q /= norm
        # Canonical sign improves continuity across frame serialization.
        if q[3] < 0.0:
            q *= -1.0
        return (float(q[0]), float(q[1]), float(q[2]), float(q[3]))

    def convert_quaternion(self, rotation: Sequence[float]) -> Quat:
        """Remap a quaternion through an orthogonal axis change.

        For signed-permutation remaps (×/y/z with optional negation), we
        transform the imaginary vector basis. Identity rotation stays identity.
        """
        q = np.asarray(self.normalize_quaternion(rotation), dtype=float)
        if self.coordinates is None:
            return (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
        # Pure scale+axis flips: convert basis vectors and rebuild.
        # Simplified robust path: convert the rotated +Z and +X axes.
        x_axis = _rotate_vec(q, np.array([1.0, 0.0, 0.0]))
        z_axis = _rotate_vec(q, np.array([0.0, 0.0, 1.0]))
        x_axis = np.asarray(self.coordinates.convert_direction(x_axis), dtype=float)
        z_axis = np.asarray(self.coordinates.convert_direction(z_axis), dtype=float)
        y_axis = np.cross(z_axis, x_axis)
        y_n = float(np.linalg.norm(y_axis))
        if y_n < 1e-9:
            return (0.0, 0.0, 0.0, 1.0)
        y_axis /= y_n
        x_axis = np.cross(y_axis, z_axis)
        x_axis /= max(float(np.linalg.norm(x_axis)), 1e-12)
        z_axis /= max(float(np.linalg.norm(z_axis)), 1e-12)
        rot = np.column_stack([x_axis, y_axis, z_axis])
        return self.normalize_quaternion(matrix_to_quaternion(rot))

    def to_euler_deg(self, rotation: Sequence[float], order: str = "xyz") -> EulerDeg:
        return quaternion_to_euler_deg(rotation, order=order)

    def to_matrix(
        self,
        translation: Sequence[float],
        rotation: Sequence[float],
        scale: Sequence[float] = (1.0, 1.0, 1.0),
    ) -> FloatArray:
        t = self.convert_translation(translation)
        r = self.convert_quaternion(rotation)
        return compose_matrix(t, r, scale)

    def convert_transform(self, transform: JointTransform) -> JointTransform:
        """Convert one :class:`JointTransform` into the target frame."""
        if not transform.valid:
            return JointTransform(
                joint_name=transform.joint_name,
                translation=(0.0, 0.0, 0.0),
                valid=False,
            )
        return JointTransform(
            joint_name=transform.joint_name,
            translation=self.convert_translation(transform.translation),
            rotation=self.convert_quaternion(transform.rotation),
            scale=transform.scale,
            valid=True,
        )

    def convert_frame(self, frame: AnimationFrame) -> AnimationFrame:
        """Convert every transform in a frame."""
        return AnimationFrame(
            index=frame.index,
            time_sec=frame.time_sec,
            transforms={
                name: self.convert_transform(transform)
                for name, transform in frame.transforms.items()
            },
        )

    def convert_animation(self, clip: AnimationClip) -> AnimationClip:
        """Convert every frame of an animation clip."""
        frames = [self.convert_frame(frame) for frame in clip.frames]
        root_motion = (
            self.extract_root_motion_from_frames(frames, clip.root_joint, clip.fps)
            if clip.root_motion is not None
            else None
        )
        return AnimationClip(
            name=clip.name,
            frames=frames,
            fps=clip.fps,
            joint_order=list(clip.joint_order),
            bones=list(clip.bones),
            root_joint=clip.root_joint,
            root_motion=root_motion,
            units=clip.units if self.coordinates is None else "cm",
            coordinate_system=clip.coordinate_system
            if self.coordinates is None
            else self.coordinates.target_name,
            metadata=dict(clip.metadata),
            compression=clip.compression,
        )

    def frame_bundle(
        self,
        frame: AnimationFrame,
        parent_map: Mapping[str, str | None],
    ) -> TransformBundle:
        """Return world + parent-relative local transforms for a frame."""
        local: dict[str, JointTransform] = {}
        for joint, transform in frame.transforms.items():
            parent_name = parent_map.get(joint)
            parent = frame.transforms.get(parent_name) if parent_name else None
            local[joint] = (
                self.parent_relative_transform(transform, parent)
                if parent is not None and parent.valid and transform.valid
                else transform
            )
        return TransformBundle(world=dict(frame.transforms), local=local)

    def parent_relative_transform(
        self,
        child: JointTransform,
        parent: JointTransform,
    ) -> JointTransform:
        """Convert a world-space child transform to parent-local space."""
        if not child.valid:
            return JointTransform(joint_name=child.joint_name, translation=(0, 0, 0), valid=False)
        child_m = compose_matrix(child.translation, child.rotation, child.scale)
        parent_m = compose_matrix(parent.translation, parent.rotation, parent.scale)
        try:
            local_m = np.linalg.inv(parent_m) @ child_m
        except np.linalg.LinAlgError as exc:
            raise TransformConversionError(
                f"Parent transform for {child.joint_name!r} is singular"
            ) from exc
        translation = (
            float(local_m[0, 3]),
            float(local_m[1, 3]),
            float(local_m[2, 3]),
        )
        rotation = self.normalize_quaternion(matrix_to_quaternion(local_m[:3, :3]))
        return JointTransform(
            joint_name=child.joint_name,
            translation=translation,
            rotation=rotation,
            scale=child.scale,
            valid=True,
        )

    def extract_root_motion_from_frames(
        self,
        frames: Sequence[AnimationFrame],
        root_joint: str,
        fps: float,
    ) -> RootMotion:
        """Extract root translation, heading, and velocity channels."""
        positions = []
        for frame in frames:
            root = frame.transforms.get(root_joint)
            positions.append(root.translation if root and root.valid else (0.0, 0.0, 0.0))
        translations = np.asarray(positions, dtype=float)
        velocities = np.zeros_like(translations)
        headings = np.zeros((len(frames),), dtype=float)
        if len(frames) > 1:
            delta = np.diff(translations, axis=0)
            velocities[1:] = delta * float(fps)
            velocities[0] = velocities[1]
            planar = delta[:, :2]
            for i, (dx, dy) in enumerate(planar):
                if float(np.linalg.norm([dx, dy])) > 1e-9:
                    headings[i + 1] = math.atan2(float(dy), float(dx))
                else:
                    headings[i + 1] = headings[i]
            headings[0] = headings[1]
        return RootMotion(
            translations=translations,
            headings_rad=headings,
            velocities=velocities,
            root_joint=root_joint,
        )

    def enforce_quaternion_continuity(self, clip: AnimationClip) -> AnimationClip:
        """Flip quaternion signs so adjacent keyframes take the shortest path."""
        output = clip.copy()
        previous: dict[str, np.ndarray] = {}
        for frame in output.frames:
            for joint, transform in frame.transforms.items():
                q = np.asarray(self.normalize_quaternion(transform.rotation), dtype=float)
                prev = previous.get(joint)
                if prev is not None and float(np.dot(prev, q)) < 0.0:
                    q *= -1.0
                previous[joint] = q
                frame.transforms[joint] = JointTransform(
                    joint_name=transform.joint_name,
                    translation=transform.translation,
                    rotation=(float(q[0]), float(q[1]), float(q[2]), float(q[3])),
                    scale=transform.scale,
                    valid=transform.valid,
                )
        return output


def compose_matrix(
    translation: Sequence[float],
    rotation: Sequence[float],
    scale: Sequence[float] = (1.0, 1.0, 1.0),
) -> FloatArray:
    x, y, z, w = (float(v) for v in rotation)
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
    rot = rot @ np.diag([float(scale[0]), float(scale[1]), float(scale[2])])
    mat = np.eye(4, dtype=float)
    mat[:3, :3] = rot
    mat[:3, 3] = [float(translation[0]), float(translation[1]), float(translation[2])]
    return mat


def matrix_to_quaternion(rot: FloatArray) -> Quat:
    m = np.asarray(rot, dtype=float)[:3, :3]
    trace = float(m[0, 0] + m[1, 1] + m[2, 2])
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w], dtype=float)
    q /= max(float(np.linalg.norm(q)), 1e-12)
    return (float(q[0]), float(q[1]), float(q[2]), float(q[3]))


def quaternion_to_euler_deg(
    rotation: Sequence[float], *, order: str = "xyz"
) -> EulerDeg:
    """Convert quaternion to XYZ intrinsic Euler degrees (default)."""
    _ = order
    x, y, z, w = (float(v) for v in rotation)
    # roll (x)
    sinr = 2.0 * (w * x + y * z)
    cosr = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr, cosr)
    # pitch (y)
    sinp = 2.0 * (w * y - z * x)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.asin(sinp)
    # yaw (z)
    siny = 2.0 * (w * z + x * y)
    cosy = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny, cosy)
    rad2deg = 180.0 / math.pi
    return (roll * rad2deg, pitch * rad2deg, yaw * rad2deg)


def _rotate_vec(q: FloatArray, v: FloatArray) -> FloatArray:
    x, y, z, w = q
    qvec = np.array([x, y, z], dtype=float)
    uv = np.cross(qvec, v)
    uuv = np.cross(qvec, uv)
    return v + 2.0 * (w * uv + uuv)
