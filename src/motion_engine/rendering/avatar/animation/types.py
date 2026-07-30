"""Animation runtime enumerations and type aliases."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]
Vec3 = NDArray[np.floating]
Quat = NDArray[np.floating]  # xyzw
Mat4 = NDArray[np.floating]
JsonDict = dict[str, Any]


class InterpolationMode(Enum):
    """Keyframe interpolation mode."""

    STEP = auto()
    LINEAR = auto()
    CUBIC = auto()


class TrackChannel(Enum):
    """What a track animates."""

    TRANSLATION = auto()
    ROTATION = auto()
    SCALE = auto()
    TRANSFORM = auto()  # combined TRS keyframes
    MORPH = auto()  # reserved for future morph targets


class PlaybackState(Enum):
    """Player / timeline playback state."""

    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


class LoopMode(Enum):
    """Clip looping behaviour."""

    ONCE = auto()
    LOOP = auto()
    PING_PONG = auto()


class ControllerState(Enum):
    """High-level locomotion / action states."""

    IDLE = auto()
    WALK = auto()
    RUN = auto()
    JUMP = auto()
    CUSTOM = auto()


__all__ = [
    "FloatArray",
    "Vec3",
    "Quat",
    "Mat4",
    "JsonDict",
    "InterpolationMode",
    "TrackChannel",
    "PlaybackState",
    "LoopMode",
    "ControllerState",
]
