"""Bone material presets for anatomical skeleton rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BoneMaterial:
    """PBR-ish surface parameters consumed by PyVista ``add_mesh``."""

    name: str
    color: tuple[float, float, float]
    opacity: float = 1.0
    metallic: float = 0.05
    roughness: float = 0.55
    specular: float = 0.35
    specular_power: float = 28.0


MATERIALS: dict[str, BoneMaterial] = {
    "clinical": BoneMaterial(
        "clinical",
        color=(0.93, 0.90, 0.84),
        metallic=0.04,
        roughness=0.62,
        specular=0.28,
    ),
    "ivory": BoneMaterial(
        "ivory",
        color=(0.96, 0.93, 0.86),
        metallic=0.02,
        roughness=0.48,
        specular=0.40,
    ),
    "matte": BoneMaterial(
        "matte",
        color=(0.90, 0.88, 0.84),
        metallic=0.0,
        roughness=0.85,
        specular=0.12,
    ),
    "educational": BoneMaterial(
        "educational",
        color=(0.98, 0.96, 0.92),
        metallic=0.0,
        roughness=0.40,
        specular=0.55,
        specular_power=40.0,
    ),
    "xray": BoneMaterial(
        "xray",
        color=(0.35, 0.55, 0.95),
        opacity=0.42,
        metallic=0.0,
        roughness=0.30,
        specular=0.60,
    ),
    "dark": BoneMaterial(
        "dark",
        color=(0.55, 0.56, 0.58),
        metallic=0.10,
        roughness=0.55,
        specular=0.30,
    ),
    "presentation": BoneMaterial(
        "presentation",
        color=(0.95, 0.91, 0.84),
        metallic=0.06,
        roughness=0.42,
        specular=0.50,
        specular_power=36.0,
    ),
}


def get_material(name: str | None) -> BoneMaterial:
    key = (name or "clinical").strip().lower()
    return MATERIALS.get(key, MATERIALS["clinical"])


def apply_material(kwargs: dict[str, Any], material: BoneMaterial) -> dict[str, Any]:
    """Merge material into ``plotter.add_mesh`` keyword args."""
    out = dict(kwargs)
    out["color"] = material.color
    out["opacity"] = material.opacity
    out["metallic"] = material.metallic
    out["roughness"] = material.roughness
    out["specular"] = material.specular
    out["smooth_shading"] = True
    return out
