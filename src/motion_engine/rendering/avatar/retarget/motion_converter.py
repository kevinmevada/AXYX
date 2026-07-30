"""Convert motion_engine AnimationClip frames → MotionPose stream."""

from __future__ import annotations

from typing import Iterator, Sequence

from motion_engine.rendering.avatar.retarget.skeleton_adapter import SkeletonAdapter
from motion_engine.rendering.avatar.retarget.types import MotionPose, MotionSkeleton


class MotionConverter:
    """Bridge clinical AnimationClip / frame dicts into MotionPose sequences."""

    def __init__(self) -> None:
        self.adapter = SkeletonAdapter()

    def from_clip_frames(self, clip: object) -> list[MotionPose]:
        """Accept motion_engine.animation_clip.AnimationClip-like object."""
        frames = getattr(clip, "frames", None)
        if frames is None:
            raise TypeError("clip has no frames")
        root = getattr(clip, "root_joint", None)
        out: list[MotionPose] = []
        for fr in frames:
            transforms = getattr(fr, "transforms", {})
            out.append(
                self.adapter.pose_from_transforms(
                    transforms,
                    time=float(getattr(fr, "time_sec", 0.0)),
                    index=int(getattr(fr, "index", len(out))),
                    root_name=root,
                )
            )
        return out

    def from_position_sequence(
        self,
        skeleton: MotionSkeleton,
        positions_per_frame: Sequence[dict],
        *,
        fps: float = 100.0,
    ) -> list[MotionPose]:
        out: list[MotionPose] = []
        for i, pos in enumerate(positions_per_frame):
            out.append(
                self.adapter.pose_from_positions(
                    skeleton,
                    pos,
                    time=i / max(fps, 1e-6),
                    index=i,
                )
            )
        return out

    def iter_gait(
        self,
        skeleton: MotionSkeleton,
        *,
        n_frames: int = 60,
        fps: float = 30.0,
    ) -> Iterator[MotionPose]:
        for i in range(n_frames):
            phase = i / max(n_frames, 1)
            pos = self.adapter.synthetic_gait_positions(skeleton, phase=phase)
            yield self.adapter.pose_from_positions(
                skeleton, pos, time=i / max(fps, 1e-6), index=i
            )


__all__ = ["MotionConverter"]
