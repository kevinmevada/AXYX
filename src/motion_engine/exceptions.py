"""
Exception hierarchy for the Motion Engine.

This module defines the foundational error types used across the package.
Domain-specific loaders, parsers, and validators should raise subclasses of
``MotionEngineError`` rather than bare built-ins.
"""

from __future__ import annotations


class MotionEngineError(Exception):
    """Base exception for all Motion Engine errors."""


class ModelValidationError(MotionEngineError):
    """Raised when a domain model fails lightweight structural validation."""


class SubjectNotFoundError(MotionEngineError, KeyError):
    """Raised when a requested subject ID is not present in the database."""


class SessionNotFoundError(MotionEngineError, KeyError):
    """Raised when a requested session name is not present on a subject."""


class VariableNotFoundError(MotionEngineError, KeyError):
    """Raised when a requested kinematic or clinical variable is missing."""


# ---------------------------------------------------------------------------
# Placeholders for future modules
# ---------------------------------------------------------------------------

class LoaderError(MotionEngineError):
    """Raised by the MATLAB loader layer.

    TODO: Expand with path, IO, and schema-discovery subclasses when
    ``loader.py`` is implemented.
    """


class ParserError(MotionEngineError):
    """Raised by the MATLAB structure parser.

    TODO: Expand with field-mapping and layout-detection subclasses when
    ``parser.py`` is implemented.
    """


class ValidatorError(MotionEngineError):
    """Raised by dataset validation routines.

    TODO: Expand when ``validator.py`` is implemented.
    """


class StatisticsError(MotionEngineError):
    """Raised by aggregate statistics routines.

    TODO: Expand when ``statistics.py`` is implemented.
    """
