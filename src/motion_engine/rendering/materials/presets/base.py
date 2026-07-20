"""Material preset helper."""

from __future__ import annotations

from dataclasses import dataclass

from motion_engine.colors import ColorRGB
from motion_engine.rendering.materials.material_library import PBRMaterial


@dataclass(frozen=True, slots=True)
class MaterialPreset:
    key: str
    material: PBRMaterial


def make_preset(
    key: str,
    color: ColorRGB,
    metallic: float,
    roughness: float,
    *,
    specular: float = 0.2,
    specular_power: float = 32.0,
) -> MaterialPreset:
    return MaterialPreset(
        key,
        PBRMaterial(
            name=key,
            base_color=color,
            metallic=metallic,
            roughness=roughness,
            specular=specular,
            specular_power=specular_power,
        ),
    )
