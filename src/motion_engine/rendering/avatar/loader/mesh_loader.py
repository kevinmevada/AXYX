"""Mesh loader — geometry only."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from motion_engine.rendering.avatar.loader.exceptions import MeshLoadError
from motion_engine.rendering.avatar.loader.mesh_formats import (
    MeshFormatHandler,
    default_mesh_handlers,
)
from motion_engine.rendering.avatar.loader.path_utils import resolve_under_root
from motion_engine.rendering.avatar.models.avatar_manifest import AvatarManifest
from motion_engine.rendering.avatar.models.mesh import MeshData

logger = logging.getLogger(__name__)


class MeshLoader:
    """Load triangle meshes via registered format handlers.

    Example:
        >>> meshes = MeshLoader().load_from_manifest(manifest, lod=1)
    """

    def __init__(self, handlers: list[MeshFormatHandler] | None = None) -> None:
        self._handlers = list(handlers or default_mesh_handlers())

    def register_handler(self, handler: MeshFormatHandler) -> None:
        """Register an additional format (e.g. future FBX)."""
        self._handlers.insert(0, handler)
        logger.info("Registered mesh handler %s", handler.format_name)

    def load_file(self, path: Path, *, name: str | None = None) -> MeshData:
        """Load a single mesh file."""
        path = Path(path)
        t0 = time.perf_counter()
        logger.info("Mesh load started: %s", path)
        for handler in self._handlers:
            if handler.can_load(path):
                mesh = handler.load(path, name=name)
                logger.info(
                    "Mesh load finished format=%s (%.2f ms)",
                    handler.format_name,
                    (time.perf_counter() - t0) * 1000.0,
                )
                return mesh
        raise MeshLoadError(
            f"Unsupported mesh format: {path.suffix or path} "
            f"(supported: gltf, glb, npz; FBX/USD reserved)"
        )

    def load_from_manifest(
        self,
        manifest: AvatarManifest,
        *,
        lod: int | None = None,
    ) -> tuple[MeshData, ...]:
        """Load mesh(es) declared by ``manifest``.

        Procedural avatars with a ``generator`` and no LOD path return ``()``.
        """
        mesh_block = dict(manifest.mesh)
        if mesh_block.get("generator") and not manifest.lod:
            logger.info(
                "Procedural mesh generator %r — skipping binary mesh",
                mesh_block.get("generator"),
            )
            return ()

        rel = manifest.lod_path(lod)
        if not rel:
            # Direct mesh path keys
            for key in ("path", "mesh", "glb", "gltf"):
                if key in mesh_block and mesh_block[key]:
                    rel = str(mesh_block[key])
                    break
        if not rel:
            if manifest.avatar_type == "procedural":
                return ()
            raise MeshLoadError(
                f"Manifest {manifest.name!r} does not declare a mesh/LOD path"
            )

        path = resolve_under_root(manifest.root, rel)
        if not path.is_file():
            raise MeshLoadError(f"Missing mesh asset: {path}")
        mesh = self.load_file(path, name=f"{manifest.name}_lod{lod if lod is not None else manifest.default_lod}")
        return (mesh,)


__all__ = ["MeshLoader"]
