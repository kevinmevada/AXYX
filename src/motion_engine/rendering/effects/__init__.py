"""Post / stylistic effects package."""

from __future__ import annotations

from motion_engine.rendering.effects.glow import VIGNETTE_STRENGTH, ensure_vignette
from motion_engine.rendering.effects.motion_trails import MotionTrails

__all__ = ["MotionTrails", "VIGNETTE_STRENGTH", "ensure_vignette"]
