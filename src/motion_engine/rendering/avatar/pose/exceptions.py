"""Domain exceptions for the M3 bind-pose runtime."""

from __future__ import annotations

from typing import Any


class PoseError(Exception):
    """Base error for pose runtime failures."""

    def __init__(self, message: str, *, code: str = "POSE_RUNTIME", details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class PoseValidationError(PoseError):
    """Raised when pose validation fails hard."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "POSE_VALIDATION",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class PoseBoneNotFoundError(PoseError):
    """Raised when a bone pose lookup fails."""

    def __init__(self, key: str | int, *, code: str = "POSE_BONE_NOT_FOUND") -> None:
        super().__init__(f"Bone pose not found: {key!r}", code=code, details={"key": key})
        self.key = key


class PoseFactoryError(PoseError):
    """Raised when bind-pose construction fails."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "POSE_FACTORY",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class PoseSerializationError(PoseError):
    """Raised when debug serialization fails."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "POSE_SERIALIZE",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


__all__ = [
    "PoseError",
    "PoseValidationError",
    "PoseBoneNotFoundError",
    "PoseFactoryError",
    "PoseSerializationError",
]
