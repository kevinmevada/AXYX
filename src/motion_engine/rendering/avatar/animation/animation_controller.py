"""Animation controller — state machine with crossfade transitions."""

from __future__ import annotations

from dataclasses import dataclass, field

from motion_engine.rendering.avatar.animation.animation_player import AnimationPlayer
from motion_engine.rendering.avatar.animation.animation_state import AnimationState, Transition
from motion_engine.rendering.avatar.animation.exceptions import AnimationPlaybackError
from motion_engine.rendering.avatar.animation.pose_blending import blend_poses, crossfade_weight
from motion_engine.rendering.avatar.animation.types import ControllerState
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose import AnimationPose


@dataclass
class AnimationController:
    """High-level Idle/Walk/Run/Jump/Custom state machine."""

    bind: BindPose
    states: dict[str, AnimationState] = field(default_factory=dict)
    transitions: list[Transition] = field(default_factory=list)
    current: str | None = None
    player: AnimationPlayer | None = None
    _from_pose: AnimationPose | None = None
    _fade_elapsed: float = 0.0
    _fade_duration: float = 0.0
    _fading: bool = False

    def __post_init__(self) -> None:
        if self.player is None:
            self.player = AnimationPlayer(bind=self.bind)

    def add_state(self, state: AnimationState) -> None:
        self.states[state.name] = state

    def add_transition(self, transition: Transition) -> None:
        self.transitions.append(transition)

    def set_state(self, name: str, *, fade: float | None = None) -> AnimationPose:
        if name not in self.states:
            raise AnimationPlaybackError(
                f"Unknown state {name!r}",
                code="ANIM_STATE_MISSING",
            )
        assert self.player is not None
        st = self.states[name]
        fade_dur = fade
        if fade_dur is None and self.current is not None:
            for tr in self.transitions:
                if tr.source == self.current and tr.target == name:
                    fade_dur = tr.duration
                    break
        if fade_dur and fade_dur > 0.0 and self.player.last_pose is not None:
            self._from_pose = self.player.last_pose
            self._fade_elapsed = 0.0
            self._fade_duration = float(fade_dur)
            self._fading = True
        else:
            self._fading = False
            self._from_pose = None

        self.current = name
        self.player.load(st.clip)
        self.player.set_loop(st.loop_mode)
        self.player.set_speed(st.speed)
        self.player.play()
        return self.tick(0.0)

    def play_kind(self, kind: ControllerState, *, fade: float | None = None) -> AnimationPose:
        for name, st in self.states.items():
            if st.kind is kind:
                return self.set_state(name, fade=fade)
        raise AnimationPlaybackError(
            f"No state registered for {kind.name}",
            code="ANIM_KIND_MISSING",
        )

    def tick(self, dt: float) -> AnimationPose:
        assert self.player is not None
        if self.current is None:
            raise AnimationPlaybackError("No active state", code="ANIM_NO_STATE")
        pose = self.player.tick(dt) if dt > 0.0 or self.player.last_pose is None else self.player.evaluate()
        if self._fading and self._from_pose is not None:
            self._fade_elapsed += max(0.0, float(dt))
            w = crossfade_weight(self._fade_elapsed, self._fade_duration)
            pose = blend_poses(self._from_pose, pose, w, name=f"xfade:{self.current}")
            if w >= 1.0 - 1e-6:
                self._fading = False
                self._from_pose = None
            self.player.last_pose = pose
        return pose


__all__ = ["AnimationController"]
