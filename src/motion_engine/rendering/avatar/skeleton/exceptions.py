"""Domain-specific exceptions for the M2 avatar skeleton runtime."""

from __future__ import annotations

from typing import Any


class SkeletonError(Exception):
    """Base error for skeleton runtime failures."""

    def __init__(self, message: str, *, code: str = "SKEL_RUNTIME", details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class SkeletonValidationError(SkeletonError):
    """Raised when a skeleton fails hard validation."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "SKEL_VALIDATION",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class BoneNotFoundError(SkeletonError):
    """Raised when a bone lookup fails."""

    def __init__(self, key: str | int, *, code: str = "SKEL_BONE_NOT_FOUND") -> None:
        super().__init__(f"Bone not found: {key!r}", code=code, details={"key": key})
        self.key = key


class SkeletonFactoryError(SkeletonError):
    """Raised when factory conversion from an imported skeleton fails."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "SKEL_FACTORY",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class SkeletonSerializationError(SkeletonError):
    """Raised when debug serialization fails."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "SKEL_SERIALIZE",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


__all__ = [
    "SkeletonError",
    "SkeletonValidationError",
    "BoneNotFoundError",
    "SkeletonFactoryError",
    "SkeletonSerializationError",
]
