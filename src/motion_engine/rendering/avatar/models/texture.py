"""Texture image model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]


@dataclass(frozen=True, slots=True)
class TextureImage:
    """CPU-side texture pixels.

    ``data`` is shaped ``(H, W, C)`` with float32 values in ``[0, 1]``.
    """

    name: str
    path: Path | None
    width: int
    height: int
    channels: int
    data: FloatArray
    color_space: str = "srgb"
    is_fallback: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", np.asarray(self.data, dtype=np.float32).copy())


__all__ = ["TextureImage"]
