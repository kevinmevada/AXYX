"""Animation runtime exceptions."""

from __future__ import annotations

from typing import Any


class AnimationError(Exception):
    """Base animation runtime error."""

    def __init__(self, message: str, *, code: str = "ANIM_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


class AnimationFactoryError(AnimationError):
    """Clip / player construction failed."""

    def __init__(self, message: str, *, code: str = "ANIM_FACTORY", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code=code, details=details)


class AnimationValidationError(AnimationError):
    """Invalid clip, track, or keyframe data."""

    def __init__(self, message: str, *, code: str = "ANIM_VALIDATION", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code=code, details=details)


class AnimationPlaybackError(AnimationError):
    """Playback / seek / evaluate failure."""

    def __init__(self, message: str, *, code: str = "ANIM_PLAYBACK", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code=code, details=details)


__all__ = [
    "AnimationError",
    "AnimationFactoryError",
    "AnimationValidationError",
    "AnimationPlaybackError",
]
