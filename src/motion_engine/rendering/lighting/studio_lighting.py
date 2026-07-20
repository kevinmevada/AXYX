"""Soft key / fill lighting for the pale photography studio."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def apply_studio_lights(plotter: Any) -> dict[str, Any]:
    """Install soft upper-left key + fill + ambient; return light handles."""
    lights: dict[str, Any] = {}
    if plotter is None:
        return lights
    try:
        import pyvista as pv

        plotter.remove_all_lights()
        key = pv.Light(
            position=(-1.5, -1.0, 2.6),
            focal_point=(0.0, 0.0, 0.55),
            color=(1.0, 0.99, 0.97),
            intensity=0.48,
            positional=False,
        )
        fill = pv.Light(
            position=(1.2, -0.3, 1.5),
            focal_point=(0.0, 0.0, 0.5),
            color=(0.95, 0.96, 0.98),
            intensity=0.22,
            positional=False,
        )
        ambient = pv.Light(light_type="headlight", intensity=0.18)
        for label, light in (("key", key), ("fill", fill), ("ambient", ambient)):
            plotter.add_light(light)
            lights[label] = light
        try:
            plotter.disable_shadows()
        except Exception:
            pass
    except Exception:
        logger.debug("Studio lighting setup failed", exc_info=True)
    return lights


__all__ = ["apply_studio_lights"]
