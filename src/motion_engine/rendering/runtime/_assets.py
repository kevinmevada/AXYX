"""Avatar / mesh loading helpers used by the pipeline (no frozen API changes)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from motion_engine.rendering.avatar.models.mesh import MeshData
from motion_engine.rendering.avatar.pose.bind_pose import BindPose
from motion_engine.rendering.avatar.pose.pose_factory import BindPoseFactory
from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
from motion_engine.rendering.avatar.skeleton.factory import AvatarSkeletonFactory
from motion_engine.rendering.avatar.skinning.factory import MeshSkinFactory
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.runtime.exceptions import RuntimePipelineError
from motion_engine.rendering.runtime.types import AvatarKind


def load_fixture_avatar() -> tuple[AvatarSkeleton, BindPose, MeshData, MeshSkin]:
    from tests.skinning.helpers import make_segment_mesh, make_two_bone_skeleton

    skel = make_two_bone_skeleton()
    bind = BindPoseFactory().from_skeleton(skel)
    mesh = make_segment_mesh(16)
    skin = MeshSkinFactory().from_mesh(
        mesh, bone_count=skel.bone_count, bone_names=[b.name for b in skel.bones]
    )
    return skel, bind, mesh, skin


_ARMY_GIRL_CACHE: tuple[AvatarSkeleton, BindPose, MeshData, MeshSkin] | None = None
_ARMY_GIRL_CACHE_PATH: Path | None = None


def resolve_army_girl_fbx(fbx_path: str | Path | None = None) -> Path:
    """Return the first existing Army Girl FBX path."""
    if fbx_path is not None:
        path = Path(fbx_path)
        if path.is_file():
            return path
        raise RuntimePipelineError(f"Army Girl FBX not found: {path}")
    repo = Path(__file__).resolve().parents[4]
    for candidate in (
        repo / "KILI" / "uploads_files_5923911_army_girl.fbx",
        repo / "assets" / "avatars" / "army_girl.fbx",
        repo / "assets" / "uploads_files_5923911_army_girl.fbx",
    ):
        if candidate.is_file():
            return candidate
    raise RuntimePipelineError(
        "Army Girl FBX not found. Place uploads_files_5923911_army_girl.fbx under "
        "KILI/ or assets/avatars/ in the project root."
    )


def load_army_girl_avatar(fbx_path: str | Path | None = None) -> tuple[AvatarSkeleton, BindPose, MeshData, MeshSkin]:
    global _ARMY_GIRL_CACHE, _ARMY_GIRL_CACHE_PATH
    path = resolve_army_girl_fbx(fbx_path)
    if _ARMY_GIRL_CACHE is not None and _ARMY_GIRL_CACHE_PATH == path:
        return _ARMY_GIRL_CACHE
    from experiments.skinning_debug.fbx_import import load_skinned_fbx

    mesh, imported = load_skinned_fbx(path)
    skel = AvatarSkeletonFactory().from_imported(imported)
    bind = BindPoseFactory().from_skeleton(skel)
    skin = MeshSkinFactory().from_mesh(
        mesh, bone_count=skel.bone_count, bone_names=[b.name for b in skel.bones]
    )
    _ARMY_GIRL_CACHE = (skel, bind, mesh, skin)
    _ARMY_GIRL_CACHE_PATH = path
    return _ARMY_GIRL_CACHE


def clear_army_girl_cache() -> None:
    """Drop cached Army Girl assets (tests / hot reload)."""
    global _ARMY_GIRL_CACHE, _ARMY_GIRL_CACHE_PATH
    _ARMY_GIRL_CACHE = None
    _ARMY_GIRL_CACHE_PATH = None


def load_metahuman_avatar(lod: int = 3) -> tuple[AvatarSkeleton, BindPose, MeshData, MeshSkin]:
    from motion_engine.rendering.avatar.loader.avatar_loader import AvatarLoader

    loaded = AvatarLoader().load("avatar.metahuman.default", lod=lod)
    if loaded.skeleton is None or loaded.primary_mesh is None:
        raise RuntimePipelineError("MetaHuman pack missing mesh/skeleton")
    skel = AvatarSkeletonFactory().from_imported(loaded.skeleton)
    bind = BindPoseFactory().from_skeleton(skel)
    mesh = loaded.primary_mesh
    skin = MeshSkinFactory().from_mesh(
        mesh, bone_count=skel.bone_count, bone_names=[b.name for b in skel.bones]
    )
    return skel, bind, mesh, skin


def load_avatar(
    kind: AvatarKind,
    *,
    fbx_path: str | Path | None = None,
    lod: int = 3,
) -> tuple[AvatarSkeleton, BindPose, MeshData, MeshSkin, str]:
    if kind == AvatarKind.FIXTURE:
        skel, bind, mesh, skin = load_fixture_avatar()
        return skel, bind, mesh, skin, "fixture"
    if kind == AvatarKind.ARMY_GIRL:
        try:
            skel, bind, mesh, skin = load_army_girl_avatar(fbx_path)
            return skel, bind, mesh, skin, "army_girl"
        except Exception as exc:  # noqa: BLE001
            # Graceful fallback for CI without assets
            skel, bind, mesh, skin = load_fixture_avatar()
            return skel, bind, mesh, skin, f"fixture_fallback:{exc}"
    if kind == AvatarKind.METAHUMAN:
        try:
            skel, bind, mesh, skin = load_metahuman_avatar(lod)
            return skel, bind, mesh, skin, "metahuman"
        except Exception as exc:  # noqa: BLE001
            skel, bind, mesh, skin = load_fixture_avatar()
            return skel, bind, mesh, skin, f"fixture_fallback:{exc}"
    raise RuntimePipelineError(f"Unsupported avatar kind: {kind}")


def try_load_motion_database(path: str | Path | None) -> Any | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    from motion_engine.loader import load_motion_database

    return load_motion_database(p)


__all__ = [
    "load_fixture_avatar",
    "load_army_girl_avatar",
    "resolve_army_girl_fbx",
    "clear_army_girl_cache",
    "load_metahuman_avatar",
    "load_avatar",
    "try_load_motion_database",
]
