"""Avatar loader — orchestrates all asset loaders (no parsing of its own)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from motion_engine.rendering.avatar.loader.exceptions import AvatarError
from motion_engine.rendering.avatar.loader.manifest_loader import ManifestLoader
from motion_engine.rendering.avatar.loader.material_loader import MaterialLoader
from motion_engine.rendering.avatar.loader.mesh_loader import MeshLoader
from motion_engine.rendering.avatar.loader.skeleton_loader import SkeletonLoader
from motion_engine.rendering.avatar.loader.texture_loader import TextureLoader
from motion_engine.rendering.avatar.models.avatar import LoadedAvatar
from motion_engine.rendering.avatar.validation import AssetValidator

logger = logging.getLogger(__name__)


class AvatarLoader:
    """Coordinate manifest → mesh → textures → materials → skeleton → validate.

    This class contains **no** file-format parsing. Each concern is delegated
    to a dedicated loader.

    Example:
        >>> loaded = AvatarLoader().load("avatar.metahuman.default", lod=3)
        >>> loaded.primary_mesh is not None
        True
    """

    def __init__(
        self,
        *,
        manifest_loader: ManifestLoader | None = None,
        mesh_loader: MeshLoader | None = None,
        texture_loader: TextureLoader | None = None,
        material_loader: MaterialLoader | None = None,
        skeleton_loader: SkeletonLoader | None = None,
        validator: AssetValidator | None = None,
    ) -> None:
        self.manifest_loader = manifest_loader or ManifestLoader()
        self.texture_loader = texture_loader or TextureLoader()
        self.mesh_loader = mesh_loader or MeshLoader()
        self.material_loader = material_loader or MaterialLoader(
            texture_loader=self.texture_loader
        )
        self.skeleton_loader = skeleton_loader or SkeletonLoader()
        self.validator = validator or AssetValidator()

    def load(
        self,
        source: str | Path,
        *,
        lod: int | None = None,
        root: Path | None = None,
        strict: bool = True,
    ) -> LoadedAvatar:
        """Load a complete immutable :class:`LoadedAvatar`.

        Args:
            source: Asset id, avatar name, or manifest path.
            lod: Optional LOD override.
            root: Optional avatars root.
            strict: If True, validation errors raise.

        Returns:
            Immutable loaded avatar in bind / rest pose.

        Raises:
            AvatarError: On load or validation failure (strict mode).
        """
        t0 = time.perf_counter()
        logger.info("AvatarLoader.load started source=%s lod=%s", source, lod)
        try:
            manifest = self.manifest_loader.load(source, root=root)
            meshes = self.mesh_loader.load_from_manifest(manifest, lod=lod)
            materials, textures = self.material_loader.load_from_manifest(manifest)
            skeleton = self.skeleton_loader.load_from_manifest(manifest)

            loaded = LoadedAvatar(
                id=manifest.asset_id,
                manifest=manifest,
                meshes=meshes,
                materials=materials,
                skeleton=skeleton,
                textures=textures,
                metadata={
                    "lod": lod if lod is not None else manifest.default_lod,
                    "load_ms": 0.0,
                },
            )
            report = self.validator.validate(loaded)
            if strict:
                report.raise_if_errors()

            dt = (time.perf_counter() - t0) * 1000.0
            loaded = LoadedAvatar(
                id=loaded.id,
                manifest=loaded.manifest,
                meshes=loaded.meshes,
                materials=loaded.materials,
                skeleton=loaded.skeleton,
                textures=loaded.textures,
                metadata={
                    "lod": lod if lod is not None else manifest.default_lod,
                    "load_ms": dt,
                },
            )
            logger.info(
                "AvatarLoader.load finished id=%s meshes=%d bones=%s (%.2f ms)",
                loaded.id,
                len(loaded.meshes),
                loaded.skeleton.bone_count if loaded.skeleton else 0,
                dt,
            )
            return loaded
        except AvatarError:
            logger.exception("AvatarLoader.load failed source=%s", source)
            raise
        except Exception as exc:
            logger.exception("AvatarLoader.load unexpected failure source=%s", source)
            raise AvatarError(f"Failed to load avatar from {source!r}: {exc}") from exc


__all__ = ["AvatarLoader"]
