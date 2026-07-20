"""Coordinate-frame conversion for Motion Engine ↔ Unreal.

The converter is a pure-Python, Unreal-independent component. It applies
the signed axis permutation and unit scale described by
``config/unreal_config.yaml`` and can convert individual points, rotations,
transforms, frames, and entire animation clips.

Example:
    >>> from motion_engine.unreal.unreal_config import UnrealConfig
    >>> converter = CoordinateConverter.from_config(UnrealConfig.load())
    >>> converter.convert_point((1000.0, 50.0, 900.0))
    (100.0, -5.0, 90.0)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from motion_engine.animation_clip import AnimationClip, AnimationFrame, JointTransform, RootMotion
from motion_engine.exceptions import MotionEngineError
from motion_engine.unreal.unreal_config import AxisRemap, UnrealConfig

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating]
Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]


class CoordinateConversionError(MotionEngineError):
    """Raised when a coordinate conversion cannot be performed."""


@dataclass(slots=True)
class CoordinateConverter:
    """Convert positions, rotations, transforms, poses, and animations.

    Args:
        axes: Signed axis remap, for example ``x:+x, y:-y, z:+z``.
        scale: Unit conversion scale applied to positions/translations.
        source_name: Source coordinate-system label.
        target_name: Target coordinate-system label.

    Example:
        >>> converter = CoordinateConverter()
        >>> converter.convert_point((10.0, 20.0, 30.0))
        (1.0, -2.0, 3.0)
    """

    axes: AxisRemap = None  # type: ignore[assignment]
    scale: float = 0.1
    source_name: str = "lab"
    target_name: str = "unreal"

    def __post_init__(self) -> None:
        if self.axes is None:
            try:
                cfg = UnrealConfig.load()
                object.__setattr__(self, "axes", cfg.axes)
                object.__setattr__(self, "scale", float(cfg.unit_scale.factor))
                object.__setattr__(self, "source_name", cfg.source_coordinate_system)
                object.__setattr__(self, "target_name", cfg.target_coordinate_system)
            except Exception:  # noqa: BLE001 - fall back to defaults
                object.__setattr__(self, "axes", AxisRemap())

    @classmethod
    def from_config(cls, config: UnrealConfig) -> CoordinateConverter:
        return cls(
            axes=config.axes,
            scale=float(config.unit_scale.factor),
            source_name=config.source_coordinate_system,
            target_name=config.target_coordinate_system,
        )

    def convert_point(self, point: Sequence[float]) -> Vec3:
        """Scale and remap a single XYZ point into the target frame."""
        arr = np.asarray(point, dtype=float).reshape(3)
        arr = arr * self.scale
        mapped = self._remap_vector(arr)
        return (float(mapped[0]), float(mapped[1]), float(mapped[2]))

    def convert_points(self, points: FloatArray) -> FloatArray:
        """Vectorized point conversion for ``(..., 3)`` arrays."""
        pts = np.asarray(points, dtype=float)
        if pts.ndim == 1:
            return np.asarray(self.convert_point(pts), dtype=float)
        if pts.shape[-1] != 3:
            raise CoordinateConversionError(
                f"Expected last dimension 3, got {pts.shape}"
            )
        matrix = self.remap_matrix() * float(self.scale)
        return pts @ matrix.T

    def convert_direction(self, direction: Sequence[float]) -> Vec3:
        """Remap a direction (no scale)."""
        arr = np.asarray(direction, dtype=float).reshape(3)
        mapped = self._remap_vector(arr)
        return (float(mapped[0]), float(mapped[1]), float(mapped[2]))

    def convert_rotation(self, rotation: Sequence[float]) -> Quat:
        """Convert a quaternion through the configured axis transform.

        Quaternions are represented as ``(x, y, z, w)``. The implementation
        converts the rotation matrix with ``M R M^-1`` and normalizes the
        result, preserving quaternion continuity for signed permutation
        coordinate changes.
        """
        q = _normalize_quaternion(rotation)
        rot = _quaternion_to_matrix(q)
        m = self.remap_matrix()
        converted = m @ rot @ np.linalg.inv(m)
        return _matrix_to_quaternion(converted)

    def convert_euler(
        self,
        euler_degrees: Sequence[float],
        *,
        order: str = "xyz",
    ) -> Vec3:
        """Convert Euler degrees by routing through quaternions."""
        quat = _euler_to_quaternion(euler_degrees, order=order)
        return _quaternion_to_euler(self.convert_rotation(quat), order=order)

    def convert_transform(
        self,
        translation: Sequence[float],
        rotation: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
        scale: Sequence[float] = (1.0, 1.0, 1.0),
    ) -> JointTransform:
        """Convert one transform into target coordinates."""
        return JointTransform(
            joint_name="",
            translation=self.convert_point(translation),
            rotation=self.convert_rotation(rotation),
            scale=(float(scale[0]), float(scale[1]), float(scale[2])),
            valid=True,
        )

    def convert_pose(self, frame: AnimationFrame) -> AnimationFrame:
        """Convert all valid transforms in a frame/pose."""
        converted: dict[str, JointTransform] = {}
        for name, transform in frame.transforms.items():
            if not transform.valid:
                converted[name] = JointTransform(
                    joint_name=name,
                    translation=(0.0, 0.0, 0.0),
                    rotation=(0.0, 0.0, 0.0, 1.0),
                    scale=transform.scale,
                    valid=False,
                )
                continue
            converted[name] = JointTransform(
                joint_name=name,
                translation=self.convert_point(transform.translation),
                rotation=self.convert_rotation(transform.rotation),
                scale=transform.scale,
                valid=True,
            )
        return AnimationFrame(
            index=frame.index,
            time_sec=frame.time_sec,
            transforms=converted,
        )

    def convert_animation(self, clip: AnimationClip) -> AnimationClip:
        """Convert an entire :class:`AnimationClip` into target coordinates."""
        frames = [self.convert_pose(frame) for frame in clip.frames]
        root_motion = None
        if clip.root_motion is not None:
            root_motion = RootMotion(
                translations=self.convert_points(clip.root_motion.translations),
                headings_rad=clip.root_motion.headings_rad.copy(),
                velocities=self.convert_points(clip.root_motion.velocities),
                root_joint=clip.root_motion.root_joint,
            )
        return AnimationClip(
            name=clip.name,
            frames=frames,
            fps=clip.fps,
            joint_order=list(clip.joint_order),
            bones=list(clip.bones),
            root_joint=clip.root_joint,
            root_motion=root_motion,
            units="cm",
            coordinate_system=self.target_name,
            metadata={
                **dict(clip.metadata),
                "definition_name": clip.metadata.get("definition_name", clip.skeleton),
                "coordinate_conversion": {
                    "source": self.source_name,
                    "target": self.target_name,
                    "scale": self.scale,
                    "axes": {
                        "x": self.axes.x,
                        "y": self.axes.y,
                        "z": self.axes.z,
                    },
                },
            },
            compression=clip.compression,
        )

    def remap_matrix(self) -> FloatArray:
        """Return the 3×3 signed-permutation remap matrix."""
        basis = {
            "x": np.array([1.0, 0.0, 0.0]),
            "y": np.array([0.0, 1.0, 0.0]),
            "z": np.array([0.0, 0.0, 1.0]),
        }
        rows: list[FloatArray] = []
        for token in (self.axes.x, self.axes.y, self.axes.z):
            token = token.strip().lower()
            if len(token) < 2 or token[-1] not in basis:
                raise CoordinateConversionError(f"Invalid axis token: {token!r}")
            sign = -1.0 if token.startswith("-") else 1.0
            rows.append(sign * basis[token[-1]])
        return np.vstack(rows)

    def _remap_vector(self, v: FloatArray) -> FloatArray:
        return self.remap_matrix() @ v


def _normalize_quaternion(rotation: Sequence[float]) -> Quat:
    q = np.asarray(rotation, dtype=float).reshape(4)
    norm = float(np.linalg.norm(q))
    if norm < 1e-12:
        return (0.0, 0.0, 0.0, 1.0)
    q /= norm
    return (float(q[0]), float(q[1]), float(q[2]), float(q[3]))


def _quaternion_to_matrix(rotation: Sequence[float]) -> FloatArray:
    x, y, z, w = _normalize_quaternion(rotation)
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=float,
    )


def _matrix_to_quaternion(rot: FloatArray) -> Quat:
    m = np.asarray(rot, dtype=float)[:3, :3]
    trace = float(np.trace(m))
    if trace > 0.0:
        s = np.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    else:
        idx = int(np.argmax(np.diag(m)))
        if idx == 0:
            s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
            x = 0.25 * s
            y = (m[0, 1] + m[1, 0]) / s
            z = (m[0, 2] + m[2, 0]) / s
            w = (m[2, 1] - m[1, 2]) / s
        elif idx == 1:
            s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
            x = (m[0, 1] + m[1, 0]) / s
            y = 0.25 * s
            z = (m[1, 2] + m[2, 1]) / s
            w = (m[0, 2] - m[2, 0]) / s
        else:
            s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
            x = (m[0, 2] + m[2, 0]) / s
            y = (m[1, 2] + m[2, 1]) / s
            z = 0.25 * s
            w = (m[1, 0] - m[0, 1]) / s
    return _normalize_quaternion((x, y, z, w))


def _euler_to_quaternion(euler_degrees: Sequence[float], *, order: str = "xyz") -> Quat:
    if order.lower() != "xyz":
        raise CoordinateConversionError("Only XYZ Euler order is currently supported")
    roll, pitch, yaw = np.radians(np.asarray(euler_degrees, dtype=float).reshape(3))
    cr, sr = np.cos(roll / 2.0), np.sin(roll / 2.0)
    cp, sp = np.cos(pitch / 2.0), np.sin(pitch / 2.0)
    cy, sy = np.cos(yaw / 2.0), np.sin(yaw / 2.0)
    return _normalize_quaternion(
        (
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy,
        )
    )


def _quaternion_to_euler(rotation: Sequence[float], *, order: str = "xyz") -> Vec3:
    if order.lower() != "xyz":
        raise CoordinateConversionError("Only XYZ Euler order is currently supported")
    x, y, z, w = _normalize_quaternion(rotation)
    roll = np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    out = np.degrees([roll, pitch, yaw])
    return (float(out[0]), float(out[1]), float(out[2]))
