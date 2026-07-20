"""Manifest loader — parse and validate ``avatar.json`` only."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Mapping

from motion_engine.rendering.avatar.loader.exceptions import ManifestError
from motion_engine.rendering.avatar.loader.path_utils import resolve_manifest_path
from motion_engine.rendering.avatar.models.avatar_manifest import (
    AvatarManifest,
    CoordinateSystem,
    LodEntry,
)
from motion_engine.rendering.avatar.validation.manifest_validator import ManifestValidator

logger = logging.getLogger(__name__)


class ManifestLoader:
    """Load and validate avatar manifests.

    Does **not** load meshes, textures, or skeletons.

    Example:
        >>> loader = ManifestLoader()
        >>> manifest = loader.load("avatar.metahuman.default")
        >>> manifest.root.is_dir()
        True
    """

    def __init__(self, validator: ManifestValidator | None = None) -> None:
        self._validator = validator or ManifestValidator()

    def load(self, source: str | Path, *, root: Path | None = None) -> AvatarManifest:
        """Load manifest from asset id, avatar name, or path.

        Args:
            source: Asset id, pack name, directory, or ``avatar.json`` path.
            root: Optional avatars root override.

        Returns:
            Immutable :class:`AvatarManifest`.

        Raises:
            ManifestError: Invalid JSON or schema.
            AssetNotFoundError: File missing.
        """
        t0 = time.perf_counter()
        path = resolve_manifest_path(source, root=root)
        logger.info("Manifest load started: %s", path)
        try:
            text = path.read_text(encoding="utf-8")
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"Invalid JSON in {path}: {exc}") from exc
        except OSError as exc:
            raise ManifestError(f"Cannot read manifest {path}: {exc}") from exc

        self._validator.validate(raw, source=str(path))
        manifest = self._build(raw, path=path)
        dt = (time.perf_counter() - t0) * 1000.0
        logger.info(
            "Manifest loaded name=%s type=%s schema=%s (%.2f ms)",
            manifest.name,
            manifest.avatar_type,
            manifest.schema_version,
            dt,
        )
        return manifest

    def _build(self, raw: Mapping[str, Any], *, path: Path) -> AvatarManifest:
        coord_raw = raw.get("coordinate_system") or {}
        if not isinstance(coord_raw, Mapping):
            raise ManifestError("coordinate_system must be an object")
        coordinate_system = CoordinateSystem(
            up=str(coord_raw.get("up", "z")),
            forward=str(coord_raw.get("forward", "x")),
            units=str(coord_raw.get("units", "cm")),
            source=str(coord_raw.get("source", "unknown")),
        )

        lod_entries: list[LodEntry] = []
        for item in raw.get("lod") or []:
            if not isinstance(item, Mapping):
                continue
            level = int(item.get("level", 0))
            rel = item.get("path") or item.get("cache") or ""
            lod_entries.append(
                LodEntry(level=level, path=str(rel), notes=str(item.get("notes", "")))
            )

        known = {
            "schema_version",
            "name",
            "display_name",
            "type",
            "asset_id",
            "coordinate_system",
            "skeleton",
            "mesh",
            "materials",
            "textures",
            "lod",
            "retarget",
            "physics",
            "notes",
        }
        extras = {k: v for k, v in raw.items() if k not in known}
        name = str(raw["name"]).strip()
        asset_id = str(raw.get("asset_id") or f"avatar.{name}.default")

        return AvatarManifest(
            schema_version=str(raw["schema_version"]),
            name=name,
            display_name=str(raw.get("display_name") or name),
            avatar_type=str(raw["type"]).strip(),
            asset_id=asset_id,
            root=path.parent.resolve(),
            path=path.resolve(),
            coordinate_system=coordinate_system,
            skeleton=dict(raw.get("skeleton") or {}),
            mesh=dict(raw.get("mesh") or {}),
            materials=dict(raw.get("materials") or {}),
            textures=dict(raw.get("textures") or {}),
            lod=tuple(lod_entries),
            retarget=dict(raw.get("retarget") or {}),
            physics=dict(raw.get("physics") or {}),
            extras=extras,
            raw=dict(raw),
        )


__all__ = ["ManifestLoader"]
