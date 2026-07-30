"""Animation keyframe."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from motion_engine.rendering.avatar.animation.quaternion import quat_normalize
from motion_engine.rendering.avatar.animation.types import Quat, Vec3


@dataclass(frozen=True, slots=True)
class Keyframe:
    """Single keyframe sample.

    Channels may be sparse: omit translation / rotation / scale when unused.
    Rotation is always a unit quaternion ``(x, y, z, w)`` — never Euler.
    """

    time: float
    translation: tuple[float, float, float] | None = None
    rotation_xyzw: tuple[float, float, float, float] | None = None
    scale: tuple[float, float, float] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "time", float(self.time))
        if self.translation is not None:
            t = tuple(float(v) for v in self.translation)
            object.__setattr__(self, "translation", (t[0], t[1], t[2]))
        if self.rotation_xyzw is not None:
            q = quat_normalize(self.rotation_xyzw)
            object.__setattr__(
                self,
                "rotation_xyzw",
                (float(q[0]), float(q[1]), float(q[2]), float(q[3])),
            )
        if self.scale is not None:
            s = tuple(float(v) for v in self.scale)
            object.__setattr__(self, "scale", (s[0], s[1], s[2]))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def has_translation(self) -> bool:
        return self.translation is not None

    @property
    def has_rotation(self) -> bool:
        return self.rotation_xyzw is not None

    @property
    def has_scale(self) -> bool:
        return self.scale is not None

    def translation_vec(self) -> Vec3 | None:
        if self.translation is None:
            return None
        return np.asarray(self.translation, dtype=np.float64)

    def rotation_quat(self) -> Quat | None:
        if self.rotation_xyzw is None:
            return None
        return np.asarray(self.rotation_xyzw, dtype=np.float64)

    def scale_vec(self) -> Vec3 | None:
        if self.scale is None:
            return None
        return np.asarray(self.scale, dtype=np.float64)


__all__ = ["Keyframe"]
