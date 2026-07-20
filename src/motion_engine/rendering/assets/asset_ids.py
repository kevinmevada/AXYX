"""Stable asset IDs — manifests resolve IDs to paths.

Never hardcode filesystem paths in application code. Use IDs like::

    avatar.procedural.default
    material.graphite
    lighting.clinical
    environment.studio.default
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

# Keep path roots local to avoid circular import with assets/__init__.py
_REPO_ROOT = Path(__file__).resolve().parents[4]
ASSETS_ROOT: Path = _REPO_ROOT / "assets"
AVATARS_ROOT: Path = ASSETS_ROOT / "avatars"

logger = logging.getLogger(__name__)

# Canonical catalog — ID → relative path under assets/ (or absolute logical key).
ASSET_CATALOG: dict[str, str] = {
    # Avatars
    "avatar.procedural.default": "avatars/procedural/avatar.json",
    "avatar.metahuman.default": "avatars/metahuman/avatar.json",
    # Environments
    "environment.studio.default": "environments/studio",
    "environment.infinity.default": "environments/infinity",
    "environment.dark_lab.default": "environments/dark_lab",
    "environment.presentation.default": "environments/presentation",
    # Materials (logical — resolved via MaterialLibrary presets)
    "material.titanium": "materials/titanium",
    "material.ceramic": "materials/ceramic",
    "material.graphite": "materials/graphite",
    "material.skin": "materials/skin",
    "material.glass": "materials/glass",
    "material.floor": "materials/floor",
    # Lighting (logical — resolved via lighting presets)
    "lighting.studio": "lighting/studio",
    "lighting.clinical": "lighting/clinical",
    "lighting.presentation": "lighting/presentation",
    "lighting.cinematic": "lighting/cinematic",
    # Camera profiles
    "camera.clinical": "camera/clinical",
    "camera.orbit": "camera/orbit",
    "camera.presentation": "camera/presentation",
    "camera.cinematic": "camera/cinematic",
    "camera.analysis": "camera/analysis",
}


def register_asset_id(asset_id: str, relative_path: str) -> None:
    """Register or override an asset ID mapping."""
    ASSET_CATALOG[asset_id] = relative_path
    logger.info("Registered asset id %r → %s", asset_id, relative_path)


def resolve_asset_id(asset_id: str) -> Path | None:
    """Resolve a stable asset ID to an absolute path under ``assets/``.

    Returns ``None`` (never raises) if the ID is unknown or the file is missing.
    Logical-only IDs (materials/lighting/camera) resolve to a directory path
    that may not exist on disk — callers should treat those as catalog keys.
    """
    rel = ASSET_CATALOG.get(asset_id)
    if rel is None:
        logger.warning("Unknown asset id %r", asset_id)
        return None
    path = ASSETS_ROOT / rel
    return path


def resolve_avatar_manifest(asset_id: str = "avatar.procedural.default") -> Path | None:
    """Resolve an avatar asset ID to its ``avatar.json`` path if present."""
    path = resolve_asset_id(asset_id)
    if path is None:
        return None
    if path.is_file():
        return path
    # Allow folder → avatar.json
    candidate = path / "avatar.json" if path.suffix != ".json" else path
    if candidate.is_file():
        return candidate
    logger.warning("Avatar manifest missing for %r (%s)", asset_id, path)
    return None


def preset_key_from_id(asset_id: str) -> str | None:
    """Extract the trailing preset key from an ID (``material.graphite`` → ``graphite``)."""
    if asset_id not in ASSET_CATALOG and "." not in asset_id:
        return None
    return asset_id.rsplit(".", 1)[-1]


def list_asset_ids(*, prefix: str | None = None) -> list[str]:
    """List registered asset IDs, optionally filtered by prefix."""
    ids = sorted(ASSET_CATALOG)
    if prefix:
        return [i for i in ids if i.startswith(prefix)]
    return ids


def catalog_snapshot() -> dict[str, Any]:
    """Return a copy of the catalog for diagnostics / serialization."""
    return dict(ASSET_CATALOG)


__all__ = [
    "ASSET_CATALOG",
    "register_asset_id",
    "resolve_asset_id",
    "resolve_avatar_manifest",
    "preset_key_from_id",
    "list_asset_ids",
    "catalog_snapshot",
    "ASSETS_ROOT",
    "AVATARS_ROOT",
]
