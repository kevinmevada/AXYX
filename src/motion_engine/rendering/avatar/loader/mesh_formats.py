"""Mesh format handlers — GLB/GLTF primary; NPZ for cached research packs."""

from __future__ import annotations

import json
import logging
import struct
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from motion_engine.rendering.avatar.loader.exceptions import MeshLoadError
from motion_engine.rendering.avatar.models.mesh import (
    MeshData,
    SubMesh,
    compute_bounds,
)

logger = logging.getLogger(__name__)


class MeshFormatHandler(ABC):
    """Extensible mesh format interface (FBX/USD can register later)."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Short format id (``gltf``, ``npz``, …)."""

    @abstractmethod
    def can_load(self, path: Path) -> bool:
        """Return True if this handler can read ``path``."""

    @abstractmethod
    def load(self, path: Path, *, name: str | None = None) -> MeshData:
        """Load mesh from ``path``."""


class NpzMeshHandler(MeshFormatHandler):
    """Load AXYX research mesh caches (``.npz``)."""

    @property
    def format_name(self) -> str:
        return "npz"

    def can_load(self, path: Path) -> bool:
        return path.suffix.lower() == ".npz"

    def load(self, path: Path, *, name: str | None = None) -> MeshData:
        logger.info("NPZ mesh load started: %s", path)
        if not path.is_file():
            raise MeshLoadError(f"Mesh file not found: {path}")
        try:
            data = np.load(path, allow_pickle=True)
        except Exception as exc:
            raise MeshLoadError(f"Corrupted NPZ mesh: {path}: {exc}") from exc
        try:
            positions = np.asarray(data["positions"], dtype=np.float32)
            faces = np.asarray(data["faces"], dtype=np.int32)
            if faces.ndim == 2:
                indices = faces.reshape(-1)
            else:
                indices = faces.astype(np.int32).reshape(-1)
            if "normals" in data.files:
                normals = np.asarray(data["normals"], dtype=np.float32)
            else:
                normals = _generate_normals(positions, indices)
                logger.warning("NPZ missing normals — generated: %s", path)
            if "uvs" in data.files:
                uvs = np.asarray(data["uvs"], dtype=np.float32)
            else:
                uvs = np.zeros((positions.shape[0], 2), dtype=np.float32)
                logger.warning("NPZ missing UVs — zeros: %s", path)
            joint_indices = (
                np.asarray(data["bone_indices"], dtype=np.int32)
                if "bone_indices" in data.files
                else None
            )
            joint_weights = (
                np.asarray(data["bone_weights"], dtype=np.float32)
                if "bone_weights" in data.files
                else None
            )
        except KeyError as exc:
            raise MeshLoadError(f"NPZ missing required array {exc}: {path}") from exc

        if positions.size == 0:
            raise MeshLoadError(f"Empty mesh: {path}")

        mesh_name = name or path.stem
        mesh = MeshData(
            name=mesh_name,
            positions=positions,
            normals=normals,
            uvs=uvs,
            indices=indices,
            submeshes=(
                SubMesh(
                    name=mesh_name,
                    index_offset=0,
                    index_count=int(indices.size),
                ),
            ),
            bounds=compute_bounds(positions),
            joint_indices=joint_indices,
            joint_weights=joint_weights,
            source_path=path.resolve(),
            format=self.format_name,
        )
        logger.info(
            "NPZ mesh loaded %s verts=%d tris=%d",
            path.name,
            mesh.vertex_count,
            mesh.triangle_count,
        )
        return mesh


class GltfMeshHandler(MeshFormatHandler):
    """Minimal glTF 2.0 / GLB mesh loader (positions, normals, uvs, indices)."""

    @property
    def format_name(self) -> str:
        return "gltf"

    def can_load(self, path: Path) -> bool:
        return path.suffix.lower() in {".gltf", ".glb"}

    def load(self, path: Path, *, name: str | None = None) -> MeshData:
        logger.info("glTF mesh load started: %s", path)
        if not path.is_file():
            raise MeshLoadError(f"Mesh file not found: {path}")
        try:
            gltf, bin_blob = _read_gltf(path)
            positions, normals, uvs, indices = _extract_first_mesh(gltf, bin_blob, path)
        except MeshLoadError:
            raise
        except Exception as exc:
            raise MeshLoadError(f"Failed to parse glTF {path}: {exc}") from exc

        if positions.shape[0] == 0:
            raise MeshLoadError(f"Empty glTF mesh: {path}")
        if normals.shape[0] != positions.shape[0]:
            normals = _generate_normals(positions, indices)
            logger.warning("glTF missing normals — generated: %s", path)
        if uvs.shape[0] != positions.shape[0]:
            uvs = np.zeros((positions.shape[0], 2), dtype=np.float32)
            logger.warning("glTF missing UVs — zeros: %s", path)

        mesh_name = name or path.stem
        mesh = MeshData(
            name=mesh_name,
            positions=positions,
            normals=normals,
            uvs=uvs,
            indices=indices,
            submeshes=(
                SubMesh(name=mesh_name, index_offset=0, index_count=int(indices.size)),
            ),
            bounds=compute_bounds(positions),
            source_path=path.resolve(),
            format=self.format_name,
        )
        logger.info(
            "glTF mesh loaded %s verts=%d tris=%d",
            path.name,
            mesh.vertex_count,
            mesh.triangle_count,
        )
        return mesh


def _generate_normals(positions: np.ndarray, indices: np.ndarray) -> np.ndarray:
    normals = np.zeros_like(positions, dtype=np.float32)
    tris = indices.reshape(-1, 3)
    for i0, i1, i2 in tris:
        p0, p1, p2 = positions[i0], positions[i1], positions[i2]
        n = np.cross(p1 - p0, p2 - p0)
        normals[i0] += n
        normals[i1] += n
        normals[i2] += n
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths = np.maximum(lengths, 1e-8)
    return (normals / lengths).astype(np.float32)


def _read_gltf(path: Path) -> tuple[dict[str, Any], bytes]:
    suffix = path.suffix.lower()
    if suffix == ".gltf":
        gltf = json.loads(path.read_text(encoding="utf-8"))
        bin_blob = b""
        for buf in gltf.get("buffers") or []:
            uri = buf.get("uri")
            if not uri:
                continue
            if uri.startswith("data:"):
                import base64

                _, b64 = uri.split(",", 1)
                bin_blob = base64.b64decode(b64)
            else:
                bin_blob = (path.parent / uri).read_bytes()
        return gltf, bin_blob

    # GLB
    data = path.read_bytes()
    if len(data) < 12 or data[0:4] != b"glTF":
        raise MeshLoadError(f"Invalid GLB header: {path}")
    _magic, version, length = struct.unpack_from("<III", data, 0)
    if version != 2:
        raise MeshLoadError(f"Unsupported GLB version {version}: {path}")
    offset = 12
    gltf: dict[str, Any] | None = None
    bin_blob = b""
    while offset + 8 <= len(data) and offset < length:
        chunk_len, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_len]
        offset += chunk_len
        if chunk_type == 0x4E4F534A:  # JSON
            gltf = json.loads(chunk.decode("utf-8"))
        elif chunk_type == 0x004E4942:  # BIN
            bin_blob = chunk
    if gltf is None:
        raise MeshLoadError(f"GLB missing JSON chunk: {path}")
    return gltf, bin_blob


_COMPONENT_BYTES = {
    5120: 1,
    5121: 1,
    5122: 2,
    5123: 2,
    5125: 4,
    5126: 4,
}
_TYPE_COUNT = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}
_DTYPE = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}


def _accessor_numpy(
    gltf: dict[str, Any], bin_blob: bytes, accessor_index: int, base: Path
) -> np.ndarray:
    accessor = gltf["accessors"][accessor_index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    buffer_index = int(view.get("buffer", 0))
    if buffer_index != 0 and (gltf.get("buffers") or [{}])[0].get("uri"):
        # External buffer already flattened into bin_blob by _read_gltf for first buffer
        pass
    byte_offset = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    comp = int(accessor["componentType"])
    count = int(accessor["count"])
    n = _TYPE_COUNT[accessor["type"]]
    dtype = _DTYPE[comp]
    total = count * n
    raw = np.frombuffer(
        bin_blob, dtype=dtype, count=total, offset=byte_offset
    )
    return np.asarray(raw).reshape(count, n) if n > 1 else np.asarray(raw)


def _extract_first_mesh(
    gltf: dict[str, Any], bin_blob: bytes, path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    meshes = gltf.get("meshes") or []
    if not meshes:
        raise MeshLoadError(f"glTF has no meshes: {path}")
    prim = (meshes[0].get("primitives") or [None])[0]
    if prim is None:
        raise MeshLoadError(f"glTF mesh has no primitives: {path}")
    attrs = prim.get("attributes") or {}
    if "POSITION" not in attrs:
        raise MeshLoadError(f"glTF primitive missing POSITION: {path}")
    positions = _accessor_numpy(gltf, bin_blob, int(attrs["POSITION"]), path).astype(
        np.float32
    )
    if "NORMAL" in attrs:
        normals = _accessor_numpy(gltf, bin_blob, int(attrs["NORMAL"]), path).astype(
            np.float32
        )
    else:
        normals = np.zeros_like(positions)
    if "TEXCOORD_0" in attrs:
        uvs = _accessor_numpy(gltf, bin_blob, int(attrs["TEXCOORD_0"]), path).astype(
            np.float32
        )
    else:
        uvs = np.zeros((positions.shape[0], 2), dtype=np.float32)
    if "indices" in prim:
        indices = _accessor_numpy(gltf, bin_blob, int(prim["indices"]), path).astype(
            np.int32
        ).reshape(-1)
    else:
        indices = np.arange(positions.shape[0], dtype=np.int32)
    return positions, normals, uvs, indices


def default_mesh_handlers() -> list[MeshFormatHandler]:
    """Built-in handlers: glTF/GLB first, then NPZ research caches."""
    return [GltfMeshHandler(), NpzMeshHandler()]


__all__ = [
    "MeshFormatHandler",
    "NpzMeshHandler",
    "GltfMeshHandler",
    "default_mesh_handlers",
]
