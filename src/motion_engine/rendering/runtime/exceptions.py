"""Digital Twin Runtime exceptions."""

from __future__ import annotations


class RuntimeError_(Exception):
    """Base digital-twin runtime failure."""

    def __init__(self, message: str, *, code: str = "RUNTIME") -> None:
        super().__init__(message)
        self.code = code


# Avoid shadowing builtin RuntimeError in public API name preference:
class DigitalTwinRuntimeError(RuntimeError_):
    """Public alias for runtime failures."""


class RuntimeConfigError(DigitalTwinRuntimeError):
    def __init__(self, message: str, *, code: str = "CONFIG") -> None:
        super().__init__(message, code=code)


class RuntimeStateError(DigitalTwinRuntimeError):
    def __init__(self, message: str, *, code: str = "STATE") -> None:
        super().__init__(message, code=code)


class RuntimeValidationError(DigitalTwinRuntimeError):
    def __init__(self, message: str, *, code: str = "VALIDATION") -> None:
        super().__init__(message, code=code)


class RuntimePipelineError(DigitalTwinRuntimeError):
    def __init__(self, message: str, *, code: str = "PIPELINE") -> None:
        super().__init__(message, code=code)


__all__ = [
    "DigitalTwinRuntimeError",
    "RuntimeConfigError",
    "RuntimeStateError",
    "RuntimeValidationError",
    "RuntimePipelineError",
]
