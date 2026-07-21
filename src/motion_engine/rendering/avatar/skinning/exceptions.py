"""Domain exceptions for the M4 skinning runtime."""

from __future__ import annotations

from typing import Any


class SkinningError(Exception):
    def __init__(self, message: str, *, code: str = "SKIN_RUNTIME", details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class SkinningValidationError(SkinningError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "SKIN_VALIDATION",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class SkinningFactoryError(SkinningError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "SKIN_FACTORY",
        details: Any = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class SkinningNotSupportedError(SkinningError):
    """Raised when a registered algorithm is not implemented yet."""

    def __init__(
        self,
        algorithm: str,
        *,
        code: str = "SKIN_NOT_SUPPORTED",
    ) -> None:
        super().__init__(
            f"Skinning algorithm not supported: {algorithm}",
            code=code,
            details={"algorithm": algorithm},
        )
        self.algorithm = algorithm


__all__ = [
    "SkinningError",
    "SkinningValidationError",
    "SkinningFactoryError",
    "SkinningNotSupportedError",
]
