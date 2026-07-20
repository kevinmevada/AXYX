"""Stable public API surface for Motion Engine.

Downstream code should import from ``motion_engine.api.*`` rather than
reaching into ``motion_engine.rendering.*`` internals. Internal modules may
move; these re-exports are the compatibility contract.
"""

from __future__ import annotations

API_VERSION = "1.0.0"
"""Version of the stable public API surface (architecture freeze)."""

__all__ = ["API_VERSION"]
