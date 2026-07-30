"""Animation player — clock + evaluate → AnimationPose for M4."""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_evaluator import AnimationEvaluator
from motion_engine.rendering.avatar.animation.cache import EvaluationCache
from motion_engine.rendering.avatar.animation.events import EventDispatcher
from motion_engine.rendering.avatar.animation.exceptions import AnimationPlaybackError
from motion_engine.rendering.avatar.animation.timeline import Timeline
from motion_engine.rendering.avatar.animation.types import LoopMode, PlaybackState
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose


@dataclass
class AnimationPlayer:
    """Load a clip, advance time, evaluate poses for skinning."""

    bind: BindPose
    clip: AnimationClip | None = None
    timeline: Timeline = field(default_factory=Timeline)
    evaluator: AnimationEvaluator | None = None
    events: EventDispatcher = field(default_factory=EventDispatcher)
    last_pose: AnimationPose | None = None
    _prev_time: float = 0.0

    def __post_init__(self) -> None:
        if self.evaluator is None:
            self.evaluator = AnimationEvaluator(
                bind=self.bind,
                cache=EvaluationCache(),
            )
        if self.clip is not None:
            self.load(self.clip)

    def load(self, clip: AnimationClip) -> None:
        clip.validate()
        self.clip = clip
        self.timeline.duration = clip.duration
        self.timeline.fps = clip.fps
        self.timeline.stop()
        self._prev_time = 0.0
        self.last_pose = None

    def play(self) -> None:
        if self.clip is None:
            raise AnimationPlaybackError("No clip loaded", code="ANIM_NO_CLIP")
        self.timeline.play()

    def pause(self) -> None:
        self.timeline.pause()

    def resume(self) -> None:
        self.timeline.resume()

    def stop(self) -> None:
        self.timeline.stop()
        self._prev_time = 0.0

    def seek(self, time: float) -> AnimationPose:
        self.timeline.seek(time)
        self._prev_time = self.timeline.sample_time()
        return self.evaluate()

    def set_loop(self, mode: LoopMode) -> None:
        self.timeline.set_loop(mode)

    def set_speed(self, speed: float) -> None:
        self.timeline.set_speed(speed)

    def reverse(self) -> None:
        self.timeline.reverse()

    def step_frames(self, frames: int = 1) -> AnimationPose:
        self.timeline.step_frames(frames)
        return self.evaluate()

    def tick(self, dt: float) -> AnimationPose:
        if self.clip is None:
            raise AnimationPlaybackError("No clip loaded", code="ANIM_NO_CLIP")
        prev = self._prev_time
        t = self.timeline.tick(dt)
        looped = self.timeline.loop_mode is not LoopMode.ONCE and t < prev and dt > 0
        self.events.dispatch_range(
            self.clip.events,
            prev,
            t,
            looped=looped,
            duration=self.clip.duration,
        )
        self._prev_time = t
        return self.evaluate()

    def evaluate(self) -> AnimationPose:
        if self.clip is None or self.evaluator is None:
            raise AnimationPlaybackError("No clip loaded", code="ANIM_NO_CLIP")
        pose = self.evaluator.evaluate(
            self.clip,
            self.timeline.sample_time(),
            loop_mode=self.timeline.loop_mode,
        )
        self.last_pose = pose
        return pose

    @property
    def state(self) -> PlaybackState:
        return self.timeline.state

    @property
    def time(self) -> float:
        return self.timeline.sample_time()

    @property
    def frame(self) -> int:
        return self.timeline.frame


__all__ = ["AnimationPlayer"]
