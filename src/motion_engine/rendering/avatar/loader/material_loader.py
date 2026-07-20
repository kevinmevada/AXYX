"""Material loader — immutable MaterialData only."""

from __future__ import annotations

import logging
import time
from typing import Any, Mapping

from motion_engine.rendering.avatar.loader.texture_loader import TextureLoader
from motion_engine.rendering.avatar.models.avatar_manifest import AvatarManifest
from motion_engine.rendering.avatar.models.material import MaterialData
from motion_engine.rendering.avatar.models.texture import TextureImage
from motion_engine.rendering.avatar.models.texture_set import TextureSet
from motion_engine.rendering.materials.material_library import MaterialLibrary

logger = logging.getLogger(__name__)


class MaterialLoader:
    """Build immutable materials from manifest sections + textures.

    Example:
        >>> mats, texs = MaterialLoader().load_from_manifest(manifest)
    """

    def __init__(
        self,
        texture_loader: TextureLoader | None = None,
        library: MaterialLibrary | None = None,
    ) -> None:
        self._textures = texture_loader or TextureLoader()
        self._library = library or MaterialLibrary()

    def load_from_manifest(
        self, manifest: AvatarManifest
    ) -> tuple[tuple[MaterialData, ...], tuple[TextureImage, ...]]:
        """Load materials and collect unique textures."""
        t0 = time.perf_counter()
        logger.info("Material load started for %s", manifest.name)
        materials_block = dict(manifest.materials)
        collected: list[TextureImage] = []
        materials: list[MaterialData] = []

        if not materials_block:
            # Procedural / preset fallbacks from library
            for key in ("graphite", "ceramic", "floor"):
                preset = self._library.get(key)
                materials.append(
                    MaterialData(
                        name=preset.name,
                        base_color=tuple(float(c) for c in preset.base_color),  # type: ignore[arg-type]
                        metallic=float(preset.metallic),
                        roughness=float(preset.roughness),
                    )
                )
            logger.info("Materials from presets (%d)", len(materials))
            return tuple(materials), tuple(collected)

        # Preset references: {"bone": "graphite"}
        simple_presets = {
            k: v
            for k, v in materials_block.items()
            if isinstance(v, str) and k != "pbr"
        }
        for name, preset_key in simple_presets.items():
            preset = self._library.get(str(preset_key))
            materials.append(
                MaterialData(
                    name=str(name),
                    base_color=tuple(float(c) for c in preset.base_color),  # type: ignore[arg-type]
                    metallic=float(preset.metallic),
                    roughness=float(preset.roughness),
                )
            )

        pbr = materials_block.get("pbr")
        if isinstance(pbr, Mapping):
            tex_set, imgs = self._load_pbr_textures(manifest, pbr)
            collected.extend(imgs)
            materials.append(
                MaterialData(
                    name="body",
                    base_color=(0.8, 0.8, 0.8),
                    metallic=0.0,
                    roughness=0.45,
                    textures=tex_set,
                    extras=dict(pbr),
                )
            )

        if not materials:
            materials.append(MaterialData(name="default"))

        logger.info(
            "Materials loaded count=%d textures=%d (%.2f ms)",
            len(materials),
            len(collected),
            (time.perf_counter() - t0) * 1000.0,
        )
        return tuple(materials), tuple(collected)

    def _load_pbr_textures(
        self, manifest: AvatarManifest, pbr: Mapping[str, Any]
    ) -> tuple[TextureSet, list[TextureImage]]:
        imgs: list[TextureImage] = []

        def _slot(key: str, slot: str) -> TextureImage | None:
            rel = pbr.get(key)
            if not rel:
                return None
            tex = self._textures.load_relative(
                manifest.root,
                str(rel),
                name=f"{manifest.name}:{key}",
                slot=slot,
                strict=False,
            )
            imgs.append(tex)
            return tex

        tex_set = TextureSet(
            albedo=_slot("base_color", "albedo") or _slot("albedo", "albedo"),
            normal=_slot("normal", "normal"),
            packed_orm=_slot("srmf", "srmf") or _slot("orm", "orm"),
            scatter=_slot("scatter", "scatter"),
            metallic=_slot("metallic", "metallic"),
            roughness=_slot("roughness", "roughness"),
            ao=_slot("ao", "ao"),
            emissive=_slot("emissive", "emissive"),
        )
        return tex_set, imgs


__all__ = ["MaterialLoader"]
