"""Named PBR material library with preset registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from motion_engine.colors import ColorRGB, STUDIO_THEME

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PBRMaterial:
    """Simple PBR description used by environment / avatar draw paths."""

    name: str
    base_color: ColorRGB
    metallic: float
    roughness: float
    specular: float = 0.18
    specular_power: float = 32.0


# Import presets after PBRMaterial exists (presets depend on this type).
from motion_engine.rendering.materials.presets import (  # noqa: E402
    PRESETS,
    get_material_preset,
)


class MaterialLibrary:
    """Canonical materials — prefer :meth:`get` over ad-hoc construction."""

    def __init__(self) -> None:
        self._by_name = {k: v.material for k, v in PRESETS.items()}
        self.bone = self._by_name.get("graphite", self._fallback_bone())
        # Current studio theme: red glossy joints (accent, not ceramic preset).
        self.joint = PBRMaterial(
            name="joint_red",
            base_color=STUDIO_THEME.joint,
            metallic=0.88,
            roughness=0.12,
            specular=0.70,
            specular_power=80.0,
        )
        self.floor = self._by_name.get("floor", self._fallback_floor())

    def get(self, name: str) -> PBRMaterial:
        """Lookup by preset key (``titanium``, ``graphite``, ``floor``, …)."""
        if name == "bone":
            return self.bone
        if name == "joint":
            return self.joint
        if name in self._by_name:
            return self._by_name[name]
        return get_material_preset(name).material

    def register(self, name: str, material: PBRMaterial) -> None:
        """Plugin registration for custom materials."""
        self._by_name[name] = material
        logger.info("Registered material %r", name)

    @staticmethod
    def _fallback_bone() -> PBRMaterial:
        return PBRMaterial("graphite", STUDIO_THEME.bone, 0.92, 0.22, 0.55, 48.0)

    @staticmethod
    def _fallback_floor() -> PBRMaterial:
        return PBRMaterial("floor", STUDIO_THEME.ground, 0.08, 0.72, 0.08, 12.0)


__all__ = ["PBRMaterial", "MaterialLibrary"]
