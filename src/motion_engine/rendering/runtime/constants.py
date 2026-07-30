"""AXYX Digital Twin Runtime constants (M7)."""

from __future__ import annotations

RUNTIME_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
PHASE1_VERSION = "1.0.0"

DEFAULT_FPS = 30.0
DEFAULT_MAPPING_PROFILE = "matlab_clinical_to_army_girl"
DEFAULT_AVATAR = "fixture"

PRESET_RESEARCH = "research"
PRESET_DEBUG = "debug"
PRESET_BENCHMARK = "benchmark"
PRESET_DEFAULT = "default"

STAGE_LOAD = "load"
STAGE_MAP = "map"
STAGE_RETARGET = "retarget"
STAGE_ANIMATION = "animation"
STAGE_SKINNING = "skinning"
STAGE_RENDER = "render"
STAGE_VIEWER = "viewer"
STAGE_FRAME = "frame"

EVENT_STARTED = "runtime.started"
EVENT_STOPPED = "runtime.stopped"
EVENT_SUBJECT = "session.subject"
EVENT_TRIAL = "session.trial"
EVENT_AVATAR = "session.avatar"
EVENT_FRAME = "pipeline.frame"
EVENT_ERROR = "runtime.error"

__all__ = [
    "RUNTIME_VERSION",
    "SCHEMA_VERSION",
    "PHASE1_VERSION",
    "DEFAULT_FPS",
    "DEFAULT_MAPPING_PROFILE",
    "DEFAULT_AVATAR",
    "PRESET_RESEARCH",
    "PRESET_DEBUG",
    "PRESET_BENCHMARK",
    "PRESET_DEFAULT",
    "STAGE_LOAD",
    "STAGE_MAP",
    "STAGE_RETARGET",
    "STAGE_ANIMATION",
    "STAGE_SKINNING",
    "STAGE_RENDER",
    "STAGE_VIEWER",
    "STAGE_FRAME",
    "EVENT_STARTED",
    "EVENT_STOPPED",
    "EVENT_SUBJECT",
    "EVENT_TRIAL",
    "EVENT_AVATAR",
    "EVENT_FRAME",
    "EVENT_ERROR",
]
