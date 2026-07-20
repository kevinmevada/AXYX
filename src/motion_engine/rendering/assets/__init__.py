"""Asset path resolution for the rendering subsystem."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# rendering/assets/__init__.py → parents[4] = repository root
# (assets → rendering → motion_engine → src → repo)
_REPO_ROOT: Path = Path(__file__).resolve().parents[4]
ASSETS_ROOT: Path = _REPO_ROOT / "assets"
AVATARS_ROOT: Path = ASSETS_ROOT / "avatars"
METAHUMAN_ROOT: Path = AVATARS_ROOT / "metahuman"
PROCEDURAL_ROOT: Path = AVATARS_ROOT / "procedural"
HDRI_ROOT: Path = ASSETS_ROOT / "hdri"
ENVIRONMENTS_ROOT: Path = ASSETS_ROOT / "environments"
MATERIALS_ROOT: Path = ASSETS_ROOT / "materials"


def ensure_asset_layout() -> Path:
    """Create the canonical assets tree if missing; return ``ASSETS_ROOT``."""
    for path in (
        METAHUMAN_ROOT,
        PROCEDURAL_ROOT,
        AVATARS_ROOT / "future",
        HDRI_ROOT,
        ENVIRONMENTS_ROOT,
        MATERIALS_ROOT,
    ):
        path.mkdir(parents=True, exist_ok=True)
    logger.debug("Assets layout ready at %s", ASSETS_ROOT)
    return ASSETS_ROOT


__all__ = [
    "ASSETS_ROOT",
    "AVATARS_ROOT",
    "METAHUMAN_ROOT",
    "PROCEDURAL_ROOT",
    "HDRI_ROOT",
    "ENVIRONMENTS_ROOT",
    "MATERIALS_ROOT",
    "ensure_asset_layout",
]

# Asset ID catalog (stable IDs → paths)
from motion_engine.rendering.assets.asset_ids import (  # noqa: E402
    ASSET_CATALOG,
    list_asset_ids,
    register_asset_id,
    resolve_asset_id,
    resolve_avatar_manifest,
)

__all__ += [
    "ASSET_CATALOG",
    "register_asset_id",
    "resolve_asset_id",
    "resolve_avatar_manifest",
    "list_asset_ids",
]
