"""Animation evaluator — clip + time → AnimationPose."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.cache import EvaluationCache
from motion_engine.rendering.avatar.animation.looping import wrap_time
from motion_engine.rendering.avatar.animation.pose_builder import PoseBuilder
from motion_engine.rendering.avatar.animation.track_sampler import TrackSampler
from motion_engine.rendering.avatar.animation.types import LoopMode
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose


@dataclass
class EvaluationStats:
    last_sample_ns: int = 0
    last_build_ns: int = 0
    last_total_ns: int = 0


@dataclass
class AnimationEvaluator:
    """Evaluate an :class:`AnimationClip` at any floating-point time."""

    bind: BindPose
    sampler: TrackSampler = field(default_factory=TrackSampler)
    builder: PoseBuilder = field(default_factory=PoseBuilder)
    cache: EvaluationCache | None = None
    stats: EvaluationStats = field(default_factory=EvaluationStats)

    def evaluate(
        self,
        clip: AnimationClip,
        time_sec: float,
        *,
        loop_mode: LoopMode = LoopMode.LOOP,
        use_cache: bool = True,
    ) -> AnimationPose:
        t0 = time.perf_counter_ns()
        wrapped, _ = wrap_time(time_sec, clip.duration, loop_mode)
        key = None
        if use_cache and self.cache is not None:
            key = f"{clip.name}:{wrapped:.6f}:{loop_mode.name}"
            hit = self.cache.get(key)
            if hit is not None:
                self.stats.last_total_ns = time.perf_counter_ns() - t0
                return hit

        t_s = time.perf_counter_ns()
        sample = self.sampler.sample(clip, wrapped)
        self.stats.last_sample_ns = time.perf_counter_ns() - t_s

        t_b = time.perf_counter_ns()
        pose = self.builder.build(self.bind, sample)
        self.stats.last_build_ns = time.perf_counter_ns() - t_b
        self.stats.last_total_ns = time.perf_counter_ns() - t0

        if key is not None and self.cache is not None:
            self.cache.put(key, pose)
        return pose


__all__ = ["AnimationEvaluator", "EvaluationStats"]
