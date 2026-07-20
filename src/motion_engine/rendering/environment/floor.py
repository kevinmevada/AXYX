"""Floor mesh helpers for the light photography studio."""

from __future__ import annotations

import logging
from typing import Any, Sequence

from motion_engine.colors import ColorRGB
from motion_engine.rendering.materials.pbr import apply_pbr

logger = logging.getLogger(__name__)

FLOOR_RESOLUTION: int = 1
FLOOR_METALLIC: float = 0.08
FLOOR_ROUGHNESS: float = 0.72
FLOOR_SPECULAR: float = 0.08


def build_flat_floor(
    pv: Any,
    *,
    size: float,
    origin: Sequence[float],
    color: ColorRGB,
    metallic: float = FLOOR_METALLIC,
    roughness: float = FLOOR_ROUGHNESS,
) -> Any:
    """Create a flat studio floor plane (no curved cyclorama)."""
    ox, oy, oz = float(origin[0]), float(origin[1]), float(origin[2])
    return pv.Plane(
        center=(ox, oy, oz),
        direction=(0, 0, 1),
        i_size=size * 1.35,
        j_size=size * 1.35,
        i_resolution=FLOOR_RESOLUTION,
        j_resolution=FLOOR_RESOLUTION,
    )


def style_floor_actor(
    actor: Any,
    *,
    metallic: float = FLOOR_METALLIC,
    roughness: float = FLOOR_ROUGHNESS,
    specular: float = FLOOR_SPECULAR,
) -> None:
    """Apply pale matte PBR to a floor actor."""
    apply_pbr(
        actor,
        metallic=metallic,
        roughness=roughness,
        specular=specular,
        specular_power=12.0,
    )


def build_warm_edge_rings(
    pv: Any,
    *,
    size: float,
    origin: Sequence[float],
    fade_color: ColorRGB,
) -> list[Any]:
    """Soft warm-gray edge discs — never fade to charcoal void."""
    rings: list[Any] = []
    for ring_i, (inner_r, outer_r) in enumerate(((0.62, 0.88), (0.88, 1.20))):
        rings.append(
            pv.Disc(
                center=(
                    float(origin[0]),
                    float(origin[1]),
                    float(origin[2]) + 0.15 + ring_i * 0.03,
                ),
                inner=size * inner_r,
                outer=size * outer_r,
                normal=(0, 0, 1),
                r_res=1,
                c_res=36,
            )
        )
    _ = fade_color
    return rings


__all__ = [
    "FLOOR_RESOLUTION",
    "FLOOR_METALLIC",
    "FLOOR_ROUGHNESS",
    "FLOOR_SPECULAR",
    "build_flat_floor",
    "style_floor_actor",
    "build_warm_edge_rings",
]
