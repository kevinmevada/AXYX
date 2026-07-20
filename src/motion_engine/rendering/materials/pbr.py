"""PBR property application for VTK / PyVista actors."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def apply_pbr(
    actor: Any,
    *,
    metallic: float,
    roughness: float,
    specular: float = 0.18,
    specular_power: float = 22.0,
    emission: tuple[float, float, float] | None = None,
) -> None:
    """Apply physically-based material properties with Phong fallback."""
    try:
        prop = actor.GetProperty()
        prop.SetInterpolationToPBR()
        prop.SetMetallic(float(metallic))
        prop.SetRoughness(float(roughness))
        prop.SetSpecular(float(specular))
        prop.SetSpecularPower(float(specular_power))
        if emission is not None:
            if hasattr(prop, "SetEmissiveFactor"):
                prop.SetEmissiveFactor(*emission)
            elif hasattr(prop, "SetEmissive"):
                prop.SetEmissive(True)
    except Exception:
        logger.debug("PBR unavailable; using Phong", exc_info=True)
        prop = actor.GetProperty()
        prop.SetInterpolationToPhong()
        prop.SetSpecular(float(specular))
        prop.SetSpecularPower(float(specular_power))


__all__ = ["apply_pbr"]
