"""Digital avatar — Avatar ABC adapter over LoadedAvatar (bind pose only)."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from motion_engine.rendering.avatar.avatar import Avatar
from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader
from motion_engine.rendering.avatar.models.avatar import LoadedAvatar

logger = logging.getLogger(__name__)


class DigitalAvatar(Avatar):
    """Manager-facing digital human that displays bind / rest pose geometry.

    Milestone 1: load + render static mesh. No animation, skinning, or
    retargeting.

    Example:
        >>> avatar = DigitalAvatar("metahuman")
        >>> avatar.load(source="avatar.metahuman.default", lod=3)
        >>> avatar.is_loaded
        True
    """

    def __init__(
        self, name: str = "metahuman", *, loader: AvatarLoader | None = None
    ) -> None:
        super().__init__(name)
        self._loader = loader or AvatarLoader()
        self._assets: LoadedAvatar | None = None
        self._actor_name = f"digital_avatar_{name}"
        self._uploaded = False

    @property
    def loaded_avatar(self) -> LoadedAvatar | None:
        """Underlying immutable asset bundle."""
        return self._assets

    def load(self, **kwargs: Any) -> None:
        """Load assets via :class:`AvatarLoader`.

        Keyword Args:
            source: Asset id / name / path (default: ``avatar.<name>.default``).
            lod: Optional LOD index.
        """
        source = kwargs.get("source") or f"avatar.{self.name}.default"
        lod = kwargs.get("lod")
        logger.info("DigitalAvatar.load name=%s source=%s", self.name, source)
        self._assets = self._loader.load(source, lod=lod)
        self._loaded = True
        self._uploaded = False

    def update(self, frame: Any) -> None:
        """No-op in Milestone 1 (bind pose only)."""
        _ = frame

    def render(self, backend: Any) -> None:
        """Upload bind-pose mesh once to a PyVista plotter backend."""
        if self._assets is None or self._uploaded:
            return
        mesh = self._assets.primary_mesh
        if mesh is None:
            logger.warning("DigitalAvatar %s has no mesh to render", self.name)
            return
        plotter = getattr(backend, "plotter", None)
        if plotter is None:
            return
        try:
            import pyvista as pv
        except ImportError:
            logger.warning("PyVista unavailable — DigitalAvatar render skipped")
            return
        faces = np.hstack(
            [
                np.full((mesh.triangle_count, 1), 3, dtype=np.int64),
                mesh.indices.reshape(-1, 3).astype(np.int64),
            ]
        ).ravel()
        pdata = pv.PolyData(np.asarray(mesh.positions, dtype=np.float64), faces)
        if mesh.normals.shape[0] == mesh.vertex_count:
            pdata["Normals"] = np.asarray(mesh.normals, dtype=np.float64)
        try:
            plotter.add_mesh(
                pdata,
                name=self._actor_name,
                color=(0.75, 0.72, 0.70),
                smooth_shading=True,
            )
            self._uploaded = True
            logger.info(
                "DigitalAvatar rendered bind pose name=%s tris=%d",
                self.name,
                mesh.triangle_count,
            )
        except Exception:
            logger.warning("DigitalAvatar render failed", exc_info=True)

    def dispose(self) -> None:
        self._assets = None
        self._uploaded = False
        super().dispose()


__all__ = ["DigitalAvatar"]
