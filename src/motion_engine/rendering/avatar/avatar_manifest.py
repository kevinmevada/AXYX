"""Backward-compatible AvatarManifest facade.

Prefer :class:`motion_engine.rendering.avatar.loader.ManifestLoader` for
strict Milestone 1 loads. Soft helpers remain for Phase-0.5 callers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from motion_engine.rendering.assets import AVATARS_ROOT, PROCEDURAL_ROOT
from motion_engine.rendering.assets.asset_ids import resolve_avatar_manifest
from motion_engine.rendering.avatar.loader.manifest_loader import ManifestLoader
from motion_engine.rendering.avatar.models.avatar_manifest import (
    AvatarManifest as StrictAvatarManifest,
)

logger = logging.getLogger(__name__)

# Public alias — strict immutable model
AvatarManifest = StrictAvatarManifest


def load_manifest_soft(path: Path) -> AvatarManifest | None:
    """Load manifest without raising (legacy soft API)."""
    try:
        return ManifestLoader().load(path)
    except Exception:
        logger.warning("Soft manifest load failed: %s", path, exc_info=True)
        return None


def for_avatar(name: str) -> AvatarManifest | None:
    """Resolve by name or asset id (soft)."""
    try:
        if name.startswith("avatar."):
            path = resolve_avatar_manifest(name)
            return ManifestLoader().load(path) if path else None
        return ManifestLoader().load(name)
    except Exception:
        logger.warning("for_avatar failed: %s", name, exc_info=True)
        return None


def procedural_default() -> AvatarManifest | None:
    """Load procedural default manifest (soft)."""
    return for_avatar("avatar.procedural.default")


# Attach classmethods for older call sites: AvatarManifest.procedural_default()
def _procedural_default(cls: type) -> AvatarManifest | None:
    return procedural_default()


def _for_avatar(cls: type, name: str) -> AvatarManifest | None:
    return for_avatar(name)


def _load(cls: type, path: Path) -> AvatarManifest | None:
    return load_manifest_soft(path)


AvatarManifest.procedural_default = classmethod(_procedural_default)  # type: ignore[attr-defined]
AvatarManifest.for_avatar = classmethod(_for_avatar)  # type: ignore[attr-defined]
AvatarManifest.load = classmethod(_load)  # type: ignore[attr-defined]


__all__ = ["AvatarManifest", "load_manifest_soft", "for_avatar", "procedural_default"]
