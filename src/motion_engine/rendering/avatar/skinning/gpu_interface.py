"""GPU skinning interface — contract only (no GPU implementation in M4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from motion_engine.rendering.avatar.skinning.exceptions import SkinningNotSupportedError
from motion_engine.rendering.avatar.skinning.matrix_palette import MatrixPalette
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin


class GpuUploadTarget(str):
    """Logical GPU backend identifiers for future upload."""


class GpuSkinningBackend(Protocol):
    """Protocol for future OpenGL / Vulkan / Metal / CUDA / DirectX backends."""

    name: str

    def upload_weights(self, skin: MeshSkin) -> None: ...

    def upload_palette(self, palette: MatrixPalette) -> None: ...

    def dispatch(self, vertex_count: int) -> None: ...


class GpuSkinningInterface(ABC):
    """Abstract GPU skinning façade (unimplemented in M4)."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when a backend is ready."""

    @abstractmethod
    def upload_and_skin(self, skin: MeshSkin, palette: MatrixPalette, vertex_count: int) -> None:
        """Upload resources and dispatch compute/draw skinning."""


class NullGpuSkinning(GpuSkinningInterface):
    """Default CPU-only stub — raises if skinning is requested on GPU."""

    def is_available(self) -> bool:
        return False

    def upload_and_skin(self, skin: MeshSkin, palette: MatrixPalette, vertex_count: int) -> None:
        raise SkinningNotSupportedError("gpu")


__all__ = [
    "GpuSkinningBackend",
    "GpuSkinningInterface",
    "NullGpuSkinning",
]
