"""Retarget engine exceptions."""

from __future__ import annotations


class RetargetError(Exception):
    """Base retarget failure."""

    def __init__(self, message: str, *, code: str = "RETARGET") -> None:
        super().__init__(message)
        self.code = code


class MappingError(RetargetError):
    """Invalid or incomplete skeleton / joint mapping."""

    def __init__(self, message: str, *, code: str = "MAPPING") -> None:
        super().__init__(message, code=code)


class ValidationError(RetargetError):
    """Retarget validation failed."""

    def __init__(self, message: str, *, code: str = "VALIDATION") -> None:
        super().__init__(message, code=code)


class CoordinateError(RetargetError):
    """Coordinate-system conversion failure."""

    def __init__(self, message: str, *, code: str = "COORD") -> None:
        super().__init__(message, code=code)


class ConstraintError(RetargetError):
    """Joint constraint violation (when hard mode is enabled)."""

    def __init__(self, message: str, *, code: str = "CONSTRAINT") -> None:
        super().__init__(message, code=code)


__all__ = [
    "RetargetError",
    "MappingError",
    "ValidationError",
    "CoordinateError",
    "ConstraintError",
]
