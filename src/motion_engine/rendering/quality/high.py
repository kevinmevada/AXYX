"""Render quality profile definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QualityProfile:
    """Named quality bundle — replaces scattered booleans."""

    name: str
    shadows: bool = True
    reflections: bool = True
    ambient_occlusion: bool = False
    msaa: int = 2
    fog: bool = False
    lod_bias: float = 0.0
    max_lights: int = 4
    contact_shadows: bool = True


LOW = QualityProfile(
    name="low",
    shadows=False,
    reflections=False,
    ambient_occlusion=False,
    msaa=0,
    fog=False,
    lod_bias=1.0,
    max_lights=2,
    contact_shadows=True,
)

MEDIUM = QualityProfile(
    name="medium",
    shadows=True,
    reflections=False,
    ambient_occlusion=False,
    msaa=2,
    fog=False,
    lod_bias=0.5,
    max_lights=3,
    contact_shadows=True,
)

HIGH = QualityProfile(
    name="high",
    shadows=True,
    reflections=True,
    ambient_occlusion=False,
    msaa=2,
    fog=False,
    lod_bias=0.0,
    max_lights=4,
    contact_shadows=True,
)

ULTRA = QualityProfile(
    name="ultra",
    shadows=True,
    reflections=True,
    ambient_occlusion=True,
    msaa=4,
    fog=False,
    lod_bias=-0.25,
    max_lights=6,
    contact_shadows=True,
)

PROFILES: dict[str, QualityProfile] = {
    LOW.name: LOW,
    MEDIUM.name: MEDIUM,
    HIGH.name: HIGH,
    ULTRA.name: ULTRA,
}


def get_quality(name: str) -> QualityProfile:
    """Lookup quality profile; unknown names fall back to ``high``."""
    return PROFILES.get(name, HIGH)
