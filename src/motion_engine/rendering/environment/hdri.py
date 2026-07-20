"""Studio IBL / HDRI helpers."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def build_studio_ibl_texture(pv: Any) -> Any | None:
    """Build a bright equirectangular env map for PBR metallics."""
    try:
        h, w = 96, 192
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            t = y / max(h - 1, 1)
            top = np.array([247, 247, 248], dtype=float)
            bot = np.array([230, 231, 234], dtype=float)
            row = (1.0 - t) * top + t * bot
            img[y, :] = np.clip(row, 0, 255).astype(np.uint8)
        yy, xx = np.mgrid[0:h, 0:w]
        key = np.exp(
            -(((xx / w - 0.28) ** 2) / 0.05 + ((yy / h - 0.20) ** 2) / 0.04)
        )
        img = np.clip(
            img.astype(float) + key[:, :, None] * np.array([18, 16, 12]),
            0,
            255,
        ).astype(np.uint8)
        return pv.numpy_to_texture(img)
    except Exception:
        logger.debug("IBL texture build failed", exc_info=True)
        return None


def apply_environment_texture(plotter: Any, texture: Any) -> bool:
    """Install ``texture`` as the plotter environment map."""
    if texture is None or plotter is None:
        return False
    try:
        plotter.set_environment_texture(texture, is_srgb=True)
        return True
    except Exception:
        logger.debug("set_environment_texture failed", exc_info=True)
        return False


__all__ = ["build_studio_ibl_texture", "apply_environment_texture"]
