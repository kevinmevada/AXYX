"""Translation mapping — root / pelvis / relative."""

from __future__ import annotations

from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper
from motion_engine.rendering.avatar.retarget.types import Vec3


class TranslationMapper:
    """Map source translations into target space with optional scale."""

    def __init__(
        self,
        coords: CoordinateMapper | None = None,
        *,
        uniform_scale: float = 1.0,
    ) -> None:
        self.coords = coords
        self.uniform_scale = float(uniform_scale)

    def map(self, v: Vec3, *, apply_scale: bool = True) -> Vec3:
        if self.coords is not None:
            out = self.coords.map_vector(v, apply_units=True)
        else:
            out = (float(v[0]), float(v[1]), float(v[2]))
        if apply_scale and abs(self.uniform_scale - 1.0) > 1e-15:
            s = self.uniform_scale
            out = (out[0] * s, out[1] * s, out[2] * s)
        return out

    def relative(self, child: Vec3, parent: Vec3) -> Vec3:
        return (child[0] - parent[0], child[1] - parent[1], child[2] - parent[2])

    def scale_limb(self, delta: Vec3, limb_scale: float) -> Vec3:
        s = float(limb_scale)
        return (delta[0] * s, delta[1] * s, delta[2] * s)


__all__ = ["TranslationMapper"]
