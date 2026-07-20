"""Path resolution helpers for avatar asset packs."""

from __future__ import annotations

import logging
from pathlib import Path

from motion_engine.rendering.assets import AVATARS_ROOT, ensure_asset_layout
from motion_engine.rendering.assets.asset_ids import resolve_avatar_manifest
from motion_engine.rendering.avatar.loader.exceptions import (
    AssetNotFoundError,
    ManifestError,
)

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "avatar.json"


def ensure_avatars_root() -> Path:
    """Ensure the canonical avatars directory exists and return it."""
    ensure_asset_layout()
    return AVATARS_ROOT


def avatar_pack_dir(avatar_name: str, *, root: Path | None = None) -> Path:
    """Return ``<root>/<avatar_name>/`` without creating it."""
    base = Path(root) if root is not None else ensure_avatars_root()
    return (base / avatar_name).resolve()


def resolve_manifest_path(
    source: str | Path,
    *,
    root: Path | None = None,
) -> Path:
    """Resolve an asset id, avatar name, or filesystem path to ``avatar.json``.

    Args:
        source: Stable asset id (``avatar.metahuman.default``), pack name
            (``metahuman``), directory containing ``avatar.json``, or a direct
            path to the manifest file.
        root: Optional avatars root override.

    Returns:
        Absolute path to an existing ``avatar.json``.

    Raises:
        AssetNotFoundError: If the manifest cannot be located.
        ManifestError: If ``source`` is empty.
    """
    if source is None or (isinstance(source, str) and not source.strip()):
        raise ManifestError("Empty manifest source")

    if isinstance(source, Path) or (
        isinstance(source, str)
        and (source.endswith(".json") or "/" in source or "\\" in source)
    ):
        path = Path(source)
        if path.is_dir():
            path = path / MANIFEST_FILENAME
        if path.is_file():
            resolved = path.resolve()
            logger.debug("Resolved manifest path %s", resolved)
            return resolved
        raise AssetNotFoundError(f"Manifest not found: {path}")

    text = str(source).strip()
    if text.startswith("avatar."):
        found = resolve_avatar_manifest(text)
        if found is not None and found.is_file():
            logger.debug("Resolved asset id %s → %s", text, found)
            return found.resolve()
        raise AssetNotFoundError(f"Unknown or missing asset id: {text}")

    candidate = avatar_pack_dir(text, root=root) / MANIFEST_FILENAME
    if candidate.is_file():
        logger.debug("Resolved avatar name %s → %s", text, candidate)
        return candidate.resolve()
    raise AssetNotFoundError(f"Manifest not found for avatar {text!r}: {candidate}")


def resolve_under_root(root: Path, relative: str | Path) -> Path:
    """Resolve ``relative`` against ``root``; reject path escape.

    Args:
        root: Avatar pack root directory.
        relative: Relative path from the manifest.

    Returns:
        Absolute path (may not exist yet — callers validate existence).

    Raises:
        AssetNotFoundError: If the path would escape the pack root.
    """
    root_res = root.resolve()
    rel = Path(relative)
    if rel.is_absolute():
        candidate = rel.resolve()
    else:
        candidate = (root_res / rel).resolve()
    try:
        candidate.relative_to(root_res)
    except ValueError as exc:
        raise AssetNotFoundError(
            f"Path escapes avatar root: {relative} (root={root_res})"
        ) from exc
    return candidate


__all__ = [
    "MANIFEST_FILENAME",
    "ensure_avatars_root",
    "avatar_pack_dir",
    "resolve_manifest_path",
    "resolve_under_root",
]
