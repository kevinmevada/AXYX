"""Camera profiles registry."""

from __future__ import annotations

import logging

from motion_engine.rendering.camera.profiles import analysis as _analysis
from motion_engine.rendering.camera.profiles import cinematic as _cinematic
from motion_engine.rendering.camera.profiles import clinical as _clinical
from motion_engine.rendering.camera.profiles import orbit as _orbit
from motion_engine.rendering.camera.profiles import presentation as _presentation
from motion_engine.rendering.camera.profiles.base import CameraProfile

logger = logging.getLogger(__name__)

PROFILES: dict[str, CameraProfile] = {
    p.name: p
    for p in (
        _clinical.PROFILE,
        _orbit.PROFILE,
        _presentation.PROFILE,
        _cinematic.PROFILE,
        _analysis.PROFILE,
    )
}


def get_camera_profile(name: str) -> CameraProfile:
    """Return profile by name; unknown → clinical with a warning."""
    profile = PROFILES.get(name)
    if profile is None:
        logger.warning("Unknown camera profile %r — using clinical", name)
        return PROFILES["clinical"]
    return profile


__all__ = ["CameraProfile", "PROFILES", "get_camera_profile"]
