"""Compatibility shim — prefer ``loader.AvatarLoader`` (orchestrator).

Legacy path helpers remain as :class:`AvatarPackResolver`.
"""

from __future__ import annotations

import logging
from pathlib import Path

from motion_engine.rendering.assets import (
    AVATARS_ROOT,
    METAHUMAN_ROOT,
    PROCEDURAL_ROOT,
    ensure_asset_layout,
)
from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader

logger = logging.getLogger(__name__)


class AvatarPackResolver:
    """Filesystem helper for avatar asset pack directories."""

    def __init__(self, root: Path | None = None) -> None:
        ensure_asset_layout()
        self.root = Path(root) if root is not None else AVATARS_ROOT

    def resolve(self, avatar_id: str) -> Path:
        """Return the asset directory for ``avatar_id`` (creates if needed)."""
        path = self.root / avatar_id
        path.mkdir(parents=True, exist_ok=True)
        logger.debug("Resolved avatar assets: %s", path)
        return path

    def metahuman_dir(self) -> Path:
        ensure_asset_layout()
        return METAHUMAN_ROOT

    def procedural_dir(self) -> Path:
        ensure_asset_layout()
        return PROCEDURAL_ROOT


# Historical name used for the path helper — keep attribute for rare callers.
# New code should use loader.AvatarLoader for asset orchestration.
__all__ = ["AvatarLoader", "AvatarPackResolver"]
