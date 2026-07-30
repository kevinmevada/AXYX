"""M5 Animation Runtime — clips → poses → M4 skinning.

Architecture::

    AnimationClip
         │
    AnimationTrack / Keyframes
         │
    Interpolator (lerp + quaternion SLERP)
         │
    AnimationEvaluator
         │
    AnimationPose  →  SkinningRuntime (M4)  →  DeformedMesh

Does not modify M1–M4 public APIs, Viewer, Studio, or Renderer.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.animation.animation_clip import AnimationClip
from motion_engine.rendering.avatar.animation.animation_controller import AnimationController
from motion_engine.rendering.avatar.animation.animation_evaluator import (
    AnimationEvaluator,
    EvaluationStats,
)
from motion_engine.rendering.avatar.animation.animation_player import AnimationPlayer
from motion_engine.rendering.avatar.animation.animation_state import AnimationState, Transition
from motion_engine.rendering.avatar.animation.animation_track import AnimationTrack, SampledTRS
from motion_engine.rendering.avatar.animation.cache import (
    AnimationCache,
    EvaluationCache,
    PoseCache,
)
from motion_engine.rendering.avatar.animation.clip_library import ClipLibrary
from motion_engine.rendering.avatar.animation.clock import AnimationClock
from motion_engine.rendering.avatar.animation.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.animation.events import (
    AnimationEvent,
    EventDispatcher,
)
from motion_engine.rendering.avatar.animation.exceptions import (
    AnimationError,
    AnimationFactoryError,
    AnimationPlaybackError,
    AnimationValidationError,
)
from motion_engine.rendering.avatar.animation.factory import AnimationFactory
from motion_engine.rendering.avatar.animation.interpolation import (
    find_key_bracket,
    interpolate_quat,
    interpolate_vec,
    lerp_vec,
)
from motion_engine.rendering.avatar.animation.keyframe import Keyframe
from motion_engine.rendering.avatar.animation.looping import wrap_time
from motion_engine.rendering.avatar.animation.markers import AnimationMarker
from motion_engine.rendering.avatar.animation.pose_blending import (
    blend_poses,
    blend_weights,
    crossfade_weight,
)
from motion_engine.rendering.avatar.animation.pose_builder import PoseBuilder, rebuild_fk
from motion_engine.rendering.avatar.animation.quaternion import (
    axis_angle_quat,
    quat_identity,
    quat_normalize,
    quat_slerp,
)
from motion_engine.rendering.avatar.animation.sampler import Sampler
from motion_engine.rendering.avatar.animation.serialization import (
    export_clip,
    export_events,
    export_markers,
    export_statistics,
    export_track,
    import_clip,
)
from motion_engine.rendering.avatar.animation.statistics import (
    AnimationStatistics,
    compute_clip_statistics,
)
from motion_engine.rendering.avatar.animation.timeline import Timeline
from motion_engine.rendering.avatar.animation.track_sampler import ClipSample, TrackSampler
from motion_engine.rendering.avatar.animation.types import (
    ControllerState,
    InterpolationMode,
    LoopMode,
    PlaybackState,
    TrackChannel,
)

__all__ = [
    "RUNTIME_VERSION",
    "AnimationCache",
    "AnimationClip",
    "AnimationClock",
    "AnimationController",
    "AnimationError",
    "AnimationEvaluator",
    "AnimationEvent",
    "AnimationFactory",
    "AnimationFactoryError",
    "AnimationMarker",
    "AnimationPlaybackError",
    "AnimationPlayer",
    "AnimationState",
    "AnimationStatistics",
    "AnimationTrack",
    "AnimationValidationError",
    "ClipLibrary",
    "ClipSample",
    "ControllerState",
    "EvaluationCache",
    "EvaluationStats",
    "EventDispatcher",
    "InterpolationMode",
    "Keyframe",
    "LoopMode",
    "PlaybackState",
    "PoseBuilder",
    "PoseCache",
    "SampledTRS",
    "Sampler",
    "Timeline",
    "TrackChannel",
    "TrackSampler",
    "Transition",
    "axis_angle_quat",
    "blend_poses",
    "blend_weights",
    "compute_clip_statistics",
    "crossfade_weight",
    "export_clip",
    "export_events",
    "export_markers",
    "export_statistics",
    "export_track",
    "find_key_bracket",
    "import_clip",
    "interpolate_quat",
    "interpolate_vec",
    "lerp_vec",
    "quat_identity",
    "quat_normalize",
    "quat_slerp",
    "rebuild_fk",
    "wrap_time",
]
