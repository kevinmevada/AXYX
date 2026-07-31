"""Anatomical skeleton visualization — mesh bones with per-frame transforms."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from motion_engine.rendering.visualization.base_renderer import BaseVisualizationRenderer
from motion_engine.rendering.visualization.bone_asset_loader import BoneAssetLoader
from motion_engine.rendering.visualization.bone_asset_manager import (
    BoneAssetManager,
    default_bones_dir,
)
from motion_engine.rendering.visualization.materials import apply_material, get_material
from motion_engine.rendering.visualization.modes import VisualizationMode
from motion_engine.rendering.visualization.transforms import bone_user_matrix
from motion_engine.skeleton import Pose

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@dataclass(slots=True)
class BoneEntry:
    name: str
    mesh: str
    start_joint: str
    end_joint: str
    rest_rotation: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rest_translation: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: float = 1.0
    visibility: bool = True
    material: str = "clinical"


class BoneRenderer(BaseVisualizationRenderer):
    """Mode 2 — anatomically mapped bone meshes, transforms only each frame."""

    mode = VisualizationMode.BONES

    def __init__(
        self,
        *,
        mapping_path: Path | None = None,
        bones_dir: Path | None = None,
        asset_manager: BoneAssetManager | None = None,
        loader: BoneAssetLoader | None = None,
    ) -> None:
        super().__init__()
        self._mapping_path = mapping_path or (_repo_root() / "config" / "bone_mapping.yaml")
        self._bones_dir = Path(bones_dir) if bones_dir else default_bones_dir()
        self._asset_manager = asset_manager or BoneAssetManager(self._bones_dir)
        self._loader = loader or BoneAssetLoader([self._bones_dir])
        self._entries: list[BoneEntry] = []
        self._actors: dict[str, Any] = {}
        self._radial_scale = 18.0
        self._default_material = "clinical"
        self._show_joints = True
        self._ready = False
        self._xray = False
        self._edge_overlay = False

    @property
    def ready(self) -> bool:
        return self._ready

    def ensure_assets(self) -> bool:
        ok = self._asset_manager.ensure_installed()
        self._loader.add_root(self._bones_dir)
        self._loader.reindex()
        return ok

    def load_mapping(self) -> None:
        path = self._mapping_path
        if not path.is_file():
            logger.warning("bone_mapping.yaml missing: %s", path)
            self._entries = []
            return
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        self._radial_scale = float(data.get("default_radial_scale", 18.0))
        self._default_material = str(data.get("default_material", "clinical"))
        self._show_joints = bool(data.get("show_joints", True))
        bones = data.get("bones") or {}
        entries: list[BoneEntry] = []
        for name, cfg in bones.items():
            if not isinstance(cfg, dict):
                continue
            entries.append(
                BoneEntry(
                    name=str(name),
                    mesh=str(cfg.get("mesh", "")),
                    start_joint=str(cfg.get("start_joint", "")),
                    end_joint=str(cfg.get("end_joint", "")),
                    rest_rotation=list(cfg.get("rest_rotation") or [0, 0, 0]),
                    rest_translation=list(cfg.get("rest_translation") or [0, 0, 0]),
                    scale=float(cfg.get("scale", 1.0)),
                    visibility=bool(cfg.get("visibility", True)),
                    material=str(cfg.get("material") or self._default_material),
                )
            )
        self._entries = entries

    def activate(self) -> None:
        if self._plotter is None:
            logger.warning("BoneRenderer.activate: no plotter bound")
            return
        if not self.ensure_assets():
            logger.warning("Bone assets unavailable — anatomical mode cannot activate")
            self._ready = False
            self._active = False
            return
        self.load_mapping()
        self._build_actors()
        self._set_actors_visible(True)
        self._active = True
        self._ready = True

    def deactivate(self) -> None:
        self._set_actors_visible(False)
        self._active = False

    def clear(self) -> None:
        self._remove_actors()
        self._active = False
        self._ready = False

    def set_xray(self, enabled: bool) -> None:
        self._xray = bool(enabled)
        if self._active:
            self._remove_actors()
            self._build_actors()
            self._set_actors_visible(True)

    def set_edge_overlay(self, enabled: bool) -> None:
        self._edge_overlay = bool(enabled)
        if self._active:
            self._remove_actors()
            self._build_actors()
            self._set_actors_visible(True)

    def render_pose(self, pose: Pose) -> None:
        if not self._active or not self._ready:
            return
        for entry in self._entries:
            if not entry.visibility:
                continue
            actor = self._actors.get(entry.name)
            if actor is None:
                continue
            start = pose.get_position(entry.start_joint)
            end = pose.get_position(entry.end_joint)
            if start is None or end is None:
                actor.SetVisibility(False)
                continue
            if not (np.all(np.isfinite(start)) and np.all(np.isfinite(end))):
                actor.SetVisibility(False)
                continue
            mat = bone_user_matrix(
                start,
                end,
                rest_rotation=entry.rest_rotation,
                rest_translation=entry.rest_translation,
                scale=entry.scale,
                radial_scale=self._radial_scale,
            )
            try:
                actor.user_matrix = mat
                actor.SetVisibility(True)
            except Exception:
                logger.debug("Failed to set bone transform %s", entry.name, exc_info=True)

    def _build_actors(self) -> None:
        assert self._plotter is not None
        self._remove_actors()
        for entry in self._entries:
            if not entry.visibility or not entry.mesh:
                continue
            mesh = self._loader.load(entry.mesh)
            if mesh is None:
                logger.warning("Skipping bone %s — mesh %s missing", entry.name, entry.mesh)
                continue
            material = get_material("xray" if self._xray else entry.material)
            kwargs = apply_material(
                {
                    "name": f"anat:{entry.name}",
                    "reset_camera": False,
                    "smooth_shading": True,
                    "show_edges": self._edge_overlay,
                    "lighting": True,
                    "pbr": True,
                },
                material,
            )
            try:
                actor = self._plotter.add_mesh(mesh, **kwargs)
            except TypeError:
                # Older PyVista without PBR kwargs
                kwargs.pop("pbr", None)
                kwargs.pop("metallic", None)
                kwargs.pop("roughness", None)
                actor = self._plotter.add_mesh(mesh, **kwargs)
            actor.SetVisibility(False)
            self._actors[entry.name] = actor

    def _set_actors_visible(self, visible: bool) -> None:
        for actor in self._actors.values():
            try:
                actor.SetVisibility(bool(visible))
            except Exception:
                pass

    def _remove_actors(self) -> None:
        if self._plotter is None:
            self._actors.clear()
            return
        for name, actor in list(self._actors.items()):
            try:
                self._plotter.remove_actor(actor)
            except Exception:
                try:
                    self._plotter.remove_actor(f"anat:{name}")
                except Exception:
                    pass
        self._actors.clear()
