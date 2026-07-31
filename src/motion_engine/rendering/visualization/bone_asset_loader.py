"""Discover, cache, and load anatomical bone meshes (OBJ/STL/PLY/GLTF/VTK)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SUPPORTED = {".obj", ".stl", ".ply", ".gltf", ".glb", ".vtk", ".vtp"}


class BoneAssetLoader:
    """Lazy mesh loader with process-lifetime cache.

    Prefer PyVista (already required for Studio). Optionally uses trimesh
    when installed for formats PyVista struggles with.
    """

    def __init__(self, roots: list[Path] | tuple[Path, ...] | None = None) -> None:
        self._roots = [Path(p) for p in (roots or [])]
        self._cache: dict[str, Any] = {}
        self._index: dict[str, Path] = {}
        self.reindex()

    def add_root(self, root: Path) -> None:
        root = Path(root)
        if root not in self._roots:
            self._roots.append(root)
            self.reindex()

    def reindex(self) -> None:
        """Scan asset roots for supported mesh files."""
        self._index.clear()
        for root in self._roots:
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if path.suffix.lower() not in _SUPPORTED:
                    continue
                key = path.stem.lower()
                self._index[key] = path
                self._index[path.name.lower()] = path

    def discover(self) -> list[str]:
        """Return sorted unique mesh stems available on disk."""
        stems = {Path(p).stem for p in self._index.values()}
        return sorted(stems)

    def resolve(self, mesh_name: str) -> Path | None:
        name = mesh_name.strip()
        key = name.lower()
        if key in self._index:
            return self._index[key]
        stem = Path(name).stem.lower()
        return self._index.get(stem)

    def load(self, mesh_name: str) -> Any | None:
        """Return cached PyVista PolyData for ``mesh_name``, or None."""
        key = mesh_name.strip().lower()
        if key in self._cache:
            return self._cache[key]
        path = self.resolve(mesh_name)
        if path is None:
            logger.warning("Bone mesh not found: %s", mesh_name)
            return None
        mesh = self._read(path)
        if mesh is None:
            return None
        try:
            if not getattr(mesh, "n_points", 0):
                logger.warning("Empty bone mesh: %s", path)
                return None
            # Ensure normals for smooth shading.
            if hasattr(mesh, "compute_normals"):
                mesh = mesh.compute_normals(
                    cell_normals=False, point_normals=True, inplace=False
                )
        except Exception:
            logger.debug("Normal computation failed for %s", path, exc_info=True)
        self._cache[key] = mesh
        self._cache[Path(mesh_name).stem.lower()] = mesh
        return mesh

    def clear_cache(self) -> None:
        self._cache.clear()

    @staticmethod
    def _read(path: Path) -> Any | None:
        try:
            import pyvista as pv

            mesh = pv.read(str(path))
            if mesh is None:
                return None
            if hasattr(mesh, "extract_surface"):
                try:
                    return mesh.extract_surface(algorithm=None).triangulate()
                except TypeError:
                    return mesh.extract_surface().triangulate()
                except Exception:
                    return mesh
            return mesh
        except Exception:
            logger.debug("PyVista failed to read %s", path, exc_info=True)
        try:
            import trimesh

            tm = trimesh.load(str(path), force="mesh")
            if tm is None:
                return None
            import pyvista as pv

            if hasattr(tm, "vertices") and hasattr(tm, "faces"):
                faces = np_faces(tm.faces)
                return pv.PolyData(np_asarray(tm.vertices), faces)
        except Exception:
            logger.warning("Failed to load bone mesh %s", path, exc_info=True)
        return None


def np_asarray(arr: Any) -> Any:
    import numpy as np

    return np.asarray(arr, dtype=float)


def np_faces(faces: Any) -> Any:
    import numpy as np

    f = np.asarray(faces, dtype=np.int64)
    if f.ndim == 2 and f.shape[1] == 3:
        return np.hstack([np.full((f.shape[0], 1), 3, dtype=np.int64), f]).ravel()
    return f
