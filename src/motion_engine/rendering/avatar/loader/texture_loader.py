"""Texture loader — images only."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

from motion_engine.rendering.avatar.loader.exceptions import TextureLoadError
from motion_engine.rendering.avatar.loader.path_utils import resolve_under_root
from motion_engine.rendering.avatar.models.texture import TextureImage

logger = logging.getLogger(__name__)

_SLOT_COLORSPACE = {
    "albedo": "srgb",
    "base_color": "srgb",
    "emissive": "srgb",
    "normal": "linear",
    "metallic": "linear",
    "roughness": "linear",
    "ao": "linear",
    "orm": "linear",
    "srmf": "linear",
    "scatter": "linear",
}


class TextureLoader:
    """Load texture images into immutable :class:`TextureImage` objects.

    Missing files produce a 1×1 fallback (never crash) unless
    ``strict=True``.

    Example:
        >>> tex = TextureLoader().load_file(path, name=\"albedo\", slot=\"albedo\")
    """

    def __init__(self, *, debug_fallback: bool = False) -> None:
        self.debug_fallback = debug_fallback

    def load_file(
        self,
        path: Path,
        *,
        name: str,
        slot: str = "albedo",
        strict: bool = False,
    ) -> TextureImage:
        """Load one image from disk."""
        t0 = time.perf_counter()
        path = Path(path)
        logger.info("Texture load started: %s slot=%s", path, slot)
        color_space = _SLOT_COLORSPACE.get(slot, "srgb")
        if not path.is_file():
            msg = f"Texture not found: {path}"
            if strict:
                raise TextureLoadError(msg)
            logger.warning("%s — using fallback", msg)
            return self._fallback(name=name, color_space=color_space)

        try:
            from PIL import Image
        except ImportError as exc:
            raise TextureLoadError("Pillow is required for texture loading") from exc

        try:
            with Image.open(path) as img:
                img = img.convert("RGBA")
                arr = np.asarray(img, dtype=np.float32) / 255.0
        except Exception as exc:
            if strict:
                raise TextureLoadError(f"Corrupted texture {path}: {exc}") from exc
            logger.warning("Texture read failed %s — fallback (%s)", path, exc)
            return self._fallback(name=name, color_space=color_space)

        h, w, c = arr.shape
        tex = TextureImage(
            name=name,
            path=path.resolve(),
            width=int(w),
            height=int(h),
            channels=int(c),
            data=arr,
            color_space=color_space,
            is_fallback=False,
        )
        logger.info(
            "Texture loaded %s %dx%d (%.2f ms)",
            path.name,
            w,
            h,
            (time.perf_counter() - t0) * 1000.0,
        )
        return tex

    def load_relative(
        self,
        root: Path,
        relative: str,
        *,
        name: str,
        slot: str = "albedo",
        strict: bool = False,
    ) -> TextureImage:
        """Resolve ``relative`` under ``root`` and load."""
        path = resolve_under_root(root, relative)
        # Prefer PNG cache sibling if TGA missing conversion
        if not path.is_file() and path.suffix.lower() == ".tga":
            png_guess = root / "cache" / "textures" / (path.stem.replace("_VT", "").lower() + ".png")
            # Common Kili cache names
            alt_map = {
                "T_Body_BC_VT": "body_bc.png",
                "T_Body_N_VT": "body_n.png",
                "T_Body_SRMF_VT": "body_srmf.png",
                "T_Body_Scatter_VT": "body_scatter.png",
            }
            alt = alt_map.get(path.stem)
            if alt:
                candidate = root / "cache" / "textures" / alt
                if candidate.is_file():
                    path = candidate
            elif png_guess.is_file():
                path = png_guess
        return self.load_file(path, name=name, slot=slot, strict=strict)

    def _fallback(self, *, name: str, color_space: str) -> TextureImage:
        if self.debug_fallback:
            color = np.array([[[1.0, 0.0, 1.0, 1.0]]], dtype=np.float32)
        else:
            color = np.array([[[0.5, 0.5, 0.5, 1.0]]], dtype=np.float32)
        return TextureImage(
            name=name,
            path=None,
            width=1,
            height=1,
            channels=4,
            data=color,
            color_space=color_space,
            is_fallback=True,
        )


__all__ = ["TextureLoader"]
