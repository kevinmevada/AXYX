"""Kili digital-human avatar backend (Unreal MetaHuman-quality body)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from motion_engine.avatar.base import AvatarBackend
from motion_engine.avatar.pose_driver import KiliPoseDriver
from motion_engine.avatar.skinning import linear_blend_skin
from motion_engine.skeleton import Pose, Skeleton

logger = logging.getLogger(__name__)

ACTOR_NAME = "avatar:kili:body"


class KiliAvatar(AvatarBackend):
    """Skinned Kili body driven by Motion Engine poses.

    Metallic procedural draw calls are suppressed while this backend is active
    (``draws_procedural_skeleton = False``). The metallic backend code path is
    preserved and used as automatic fallback if assets are missing.
    """

    id = "kili"
    draws_procedural_skeleton = False

    def __init__(
        self,
        *,
        asset_root: Path,
        retarget_path: Path,
        lod: int = 1,
        animation_mode: str = "rigid",
    ) -> None:
        self.asset_root = Path(asset_root)
        self.retarget_path = Path(retarget_path)
        self.lod = int(lod)
        self.animation_mode = animation_mode
        self._renderer: Any = None
        self._rest: np.ndarray | None = None
        self._faces: np.ndarray | None = None
        self._uvs: np.ndarray | None = None
        self._normals: np.ndarray | None = None
        self._bone_indices: np.ndarray | None = None
        self._bone_weights: np.ndarray | None = None
        self._inv_bind: np.ndarray | None = None
        self._bind_world: np.ndarray | None = None
        self._bone_names: list[str] = []
        self._driver: KiliPoseDriver | None = None
        self._mesh: Any = None
        self._actor: Any = None
        self._visible = True
        self._loaded = False
        self._texture_path: Path | None = None

    def attach(self, renderer: Any) -> None:
        self._renderer = renderer

    def set_lod(self, lod: int) -> None:
        if lod == self.lod:
            return
        self.lod = int(lod)
        if self._loaded:
            self._load_cache()
            if self._renderer is not None:
                self._ensure_actor()

    def set_visible(self, visible: bool) -> None:
        self._visible = bool(visible)
        if self._actor is not None:
            try:
                self._actor.SetVisibility(1 if self._visible else 0)
            except Exception:
                logger.debug("Kili visibility toggle failed", exc_info=True)

    def load(self, skeleton: Skeleton) -> None:
        self._load_cache()
        if skeleton.poses and self._driver is not None:
            self._driver.calibrate(skeleton.poses[0])
        self._ensure_actor()
        if skeleton.poses:
            self.update(skeleton.poses[0], skeleton=skeleton)

    def _cache_path(self) -> Path:
        return self.asset_root / "cache" / f"body_lod{self.lod}.npz"

    def _load_cache(self) -> None:
        path = self._cache_path()
        if not path.is_file():
            # Prefer any available LOD
            for lod in (1, 2, 3, 0):
                alt = self.asset_root / "cache" / f"body_lod{lod}.npz"
                if alt.is_file():
                    path = alt
                    self.lod = lod
                    break
            else:
                raise FileNotFoundError(
                    f"Kili body cache missing under {self.asset_root / 'cache'}. "
                    "Run scripts/preprocess_kili_lod.py"
                )

        data = np.load(path, allow_pickle=True)
        self._rest = np.asarray(data["positions"], dtype=np.float32)
        self._faces = np.asarray(data["faces"], dtype=np.int32)
        self._uvs = np.asarray(data["uvs"], dtype=np.float32)
        self._normals = np.asarray(data["normals"], dtype=np.float32)
        self._bone_indices = np.asarray(data["bone_indices"], dtype=np.int32)
        self._bone_weights = np.asarray(data["bone_weights"], dtype=np.float32)
        self._inv_bind = np.asarray(data["inv_bind"], dtype=np.float64)
        self._bind_world = np.asarray(data["bind_world"], dtype=np.float64)
        self._bone_names = [str(x) for x in data["bone_names"]]
        bone_parents = (
            np.asarray(data["bone_parents"], dtype=np.int32)
            if "bone_parents" in data
            else None
        )

        skel_path = self.asset_root / "cache" / "skeleton.json"
        if not skel_path.is_file():
            raise FileNotFoundError(f"Missing {skel_path}")
        if not self.retarget_path.is_file():
            raise FileNotFoundError(f"Missing {self.retarget_path}")

        self._driver = KiliPoseDriver(
            retarget_path=self.retarget_path,
            skeleton_path=skel_path,
            bone_names=self._bone_names,
            bind_world=self._bind_world,
            bone_parents=bone_parents,
        )
        self._driver.animation_mode = self.animation_mode
        tex = self.asset_root / "cache" / "textures" / "body_bc.png"
        self._texture_path = tex if tex.is_file() else None
        self._loaded = True
        logger.info(
            "Kili avatar loaded LOD%s (%s verts, %s bones)",
            self.lod,
            self._rest.shape[0],
            len(self._bone_names),
        )

    def _ensure_actor(self) -> None:
        if self._renderer is None or self._rest is None or self._faces is None:
            return
        plotter = getattr(self._renderer, "plotter", None)
        if plotter is None:
            return

        import pyvista as pv

        # Remove previous actor if present
        actors = getattr(self._renderer, "_actors", None)
        if isinstance(actors, dict) and ACTOR_NAME in actors:
            try:
                plotter.remove_actor(actors.pop(ACTOR_NAME), reset_camera=False)
            except Exception:
                logger.debug("Could not remove previous Kili actor", exc_info=True)

        mesh = pv.PolyData(self._rest.copy() * float(self._driver.display_scale if self._driver else 10.0))
        faces = np.hstack(
            [
                np.full((self._faces.shape[0], 1), 3, dtype=np.int32),
                self._faces.astype(np.int32),
            ]
        ).ravel()
        mesh.faces = faces
        if self._uvs is not None and self._uvs.shape[0] == self._rest.shape[0]:
            mesh.active_texture_coordinates = self._uvs.copy()
        if self._normals is not None and self._normals.shape[0] == self._rest.shape[0]:
            mesh.point_data["Normals"] = self._normals.copy()
            mesh["Normals"] = self._normals.copy()

        kwargs: dict[str, Any] = {
            "name": ACTOR_NAME,
            "smooth_shading": True,
            "show_edges": False,
        }
        if self._texture_path is not None:
            try:
                tex = pv.read_texture(str(self._texture_path))
                kwargs["texture"] = tex
            except Exception:
                logger.debug("Kili texture load failed", exc_info=True)
                kwargs["color"] = "#C4A484"
        else:
            kwargs["color"] = "#C4A484"

        actor = plotter.add_mesh(mesh, **kwargs)
        try:
            prop = actor.GetProperty()
            prop.SetInterpolationToPBR()
            prop.SetMetallic(0.08)
            prop.SetRoughness(0.55)
        except Exception:
            logger.debug("PBR property setup failed", exc_info=True)

        self._mesh = mesh
        self._actor = actor
        if isinstance(actors, dict):
            actors[ACTOR_NAME] = actor
        self.set_visible(self._visible)

    def update(self, pose: Pose, *, skeleton: Skeleton) -> None:
        if not self._loaded or self._driver is None:
            return
        if self._mesh is None:
            self._ensure_actor()
        if self._mesh is None:
            return
        assert self._rest is not None
        assert self._inv_bind is not None
        assert self._bone_indices is not None
        assert self._bone_weights is not None

        bone_mats = self._driver.compute_bone_matrices(pose)
        skinned = linear_blend_skin(
            self._rest,
            bone_mats,
            self._inv_bind,
            self._bone_indices,
            self._bone_weights,
        )
        # Avatar internal units are cm; Studio viewport / mocap use mm.
        self._mesh.points = skinned * float(self._driver.display_scale)
        # Soft normals refresh (optional — skip every frame for speed)
        try:
            self._mesh.compute_normals(
                cell_normals=False,
                point_normals=True,
                inplace=True,
                consistent_normals=True,
            )
        except Exception:
            pass

    def clear(self) -> None:
        if self._renderer is None:
            return
        plotter = getattr(self._renderer, "plotter", None)
        actors = getattr(self._renderer, "_actors", None)
        if plotter is not None and isinstance(actors, dict) and ACTOR_NAME in actors:
            try:
                plotter.remove_actor(actors.pop(ACTOR_NAME), reset_camera=False)
            except Exception:
                logger.debug("Kili clear failed", exc_info=True)
        self._mesh = None
        self._actor = None
