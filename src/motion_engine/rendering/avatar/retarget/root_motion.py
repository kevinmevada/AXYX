"""Root motion extraction, in-place playback, loop correction."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from motion_engine.rendering.avatar.retarget.types import MotionPose, RootMotionMode, Vec3
from motion_engine.rendering.avatar.retarget.constants import VEC3_ZERO


@dataclass
class RootMotionState:
    mode: RootMotionMode = RootMotionMode.WORLD
    extracted: list[Vec3] = field(default_factory=list)
    loop_delta: Vec3 = VEC3_ZERO
    inplace_origin: Vec3 = VEC3_ZERO


class RootMotionProcessor:
    """Extract / suppress / correct root translation across frames."""

    def __init__(self, mode: RootMotionMode = RootMotionMode.WORLD) -> None:
        self.mode = mode
        self.state = RootMotionState(mode=mode)

    def reset(self, origin: Vec3 = VEC3_ZERO) -> None:
        self.state = RootMotionState(mode=self.mode, inplace_origin=origin)

    def process_translation(self, t: Vec3, *, frame_index: int = 0) -> Vec3:
        if self.mode == RootMotionMode.WORLD:
            self.state.extracted.append(t)
            return t
        if self.mode == RootMotionMode.IN_PLACE:
            if frame_index == 0:
                self.state.inplace_origin = t
            self.state.extracted.append(t)
            o = self.state.inplace_origin
            # Keep vertical component (index 2 for Z-up, 1 for Y-up — keep all relative XY)
            return (o[0], o[1], t[2]) if abs(t[2]) >= abs(t[1]) else (o[0], t[1], o[2])
        # EXTRACT: zero out planar, store full
        self.state.extracted.append(t)
        return (0.0, 0.0, t[2]) if abs(t[2]) >= abs(t[1]) else (0.0, t[1], 0.0)

    def from_pose(self, pose: MotionPose, root_name: str) -> Vec3:
        if pose.root_translation is not None:
            return pose.root_translation
        j = pose.get(root_name)
        if j is None:
            return VEC3_ZERO
        return j.world_position or j.translation

    def loop_correction(self, translations: list[Vec3]) -> Vec3:
        if len(translations) < 2:
            self.state.loop_delta = VEC3_ZERO
            return VEC3_ZERO
        a = np.asarray(translations[0], dtype=np.float64)
        b = np.asarray(translations[-1], dtype=np.float64)
        delta = b - a
        self.state.loop_delta = (float(delta[0]), float(delta[1]), float(delta[2]))
        return self.state.loop_delta

    def apply_loop_blend(self, t: Vec3, alpha: float) -> Vec3:
        d = self.state.loop_delta
        a = float(np.clip(alpha, 0.0, 1.0))
        return (t[0] - d[0] * a, t[1] - d[1] * a, t[2] - d[2] * a)


__all__ = ["RootMotionState", "RootMotionProcessor"]
