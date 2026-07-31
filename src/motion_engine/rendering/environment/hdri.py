"""Studio IBL / HDRI helpers — Flagship dark cinematic lighting."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def build_studio_ibl_texture(pv: Any) -> Any | None:
    """Build a near-black equirectangular env map with a soft warm key."""
    try:
        h, w = 96, 192
        img = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            t = y / max(h - 1, 1)
            # Dark warm void → slightly lighter floor bounce
            top = np.array([22, 18, 16], dtype=float)   # #161210
            bot = np.array([11, 9, 13], dtype=float)     # #0B090D
            row = (1.0 - t) * top + t * bot
            img[y, :] = np.clip(row, 0, 255).astype(np.uint8)
        yy, xx = np.mgrid[0:h, 0:w]
        # Soft gold key from upper-left (low intensity — no neon wash)
        key = np.exp(
            -(((xx / w - 0.30) ** 2) / 0.06 + ((yy / h - 0.22) ** 2) / 0.05)
        )
        img = np.clip(
            img.astype(float) + key[:, :, None] * np.array([42, 32, 16]),
            0,
            255,
        ).astype(np.uint8)
        # Faint fill opposite
        fill = np.exp(
            -(((xx / w - 0.72) ** 2) / 0.10 + ((yy / h - 0.55) ** 2) / 0.12)
        )
        img = np.clip(
            img.astype(float) + fill[:, :, None] * np.array([10, 12, 18]),
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
