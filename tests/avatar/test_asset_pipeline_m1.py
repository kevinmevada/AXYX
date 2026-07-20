"""Milestone 1 — avatar asset pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from motion_engine.rendering.avatar.loader import (
    AssetNotFoundError,
    AvatarLoader,
    ManifestError,
    ManifestLoader,
    MeshLoader,
    SkeletonLoader,
    TextureLoader,
    ValidationError,
)
from motion_engine.rendering.avatar.loader.mesh_formats import GltfMeshHandler, NpzMeshHandler
from motion_engine.rendering.avatar.registry import AvatarFactory, AvatarRegistry
from motion_engine.rendering.avatar.validation import AssetValidator, ManifestValidator

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "avatars"
TRIANGLE = FIXTURES / "triangle"
BROKEN = FIXTURES / "broken"


def test_manifest_loader_procedural() -> None:
    m = ManifestLoader().load("avatar.procedural.default")
    assert m.name == "procedural"
    assert m.asset_id == "avatar.procedural.default"
    assert m.schema_version.startswith("1.")


def test_manifest_loader_metahuman() -> None:
    m = ManifestLoader().load("metahuman")
    assert m.name == "metahuman"
    assert m.lod_path(3) == "cache/body_lod3.npz"
    assert m.coordinate_system.units == "cm"


def test_manifest_invalid_json() -> None:
    with pytest.raises(ManifestError):
        ManifestLoader().load(BROKEN / "avatar.json")


def test_manifest_missing() -> None:
    with pytest.raises(AssetNotFoundError):
        ManifestLoader().load("does-not-exist-avatar")


def test_manifest_validator_required_fields() -> None:
    with pytest.raises(ManifestError):
        ManifestValidator().validate({"name": "x", "type": "y"})


def test_mesh_gltf_and_glb() -> None:
    gltf = MeshLoader().load_file(TRIANGLE / "mesh.gltf")
    assert gltf.vertex_count == 3
    assert gltf.triangle_count == 1
    assert gltf.bounds is not None
    glb = MeshLoader().load_file(TRIANGLE / "mesh.glb")
    assert glb.vertex_count == 3


def test_mesh_npz_metahuman_lod3() -> None:
    from motion_engine.rendering.assets import METAHUMAN_ROOT

    path = METAHUMAN_ROOT / "cache" / "body_lod3.npz"
    if not path.is_file():
        pytest.skip("metahuman NPZ cache not present")
    mesh = NpzMeshHandler().load(path)
    assert mesh.vertex_count > 0
    assert mesh.triangle_count > 0
    assert mesh.normals.shape[0] == mesh.vertex_count


def test_unsupported_format() -> None:
    with pytest.raises(Exception):
        MeshLoader().load_file(TRIANGLE / "avatar.json")


def test_texture_fallback(tmp_path: Path) -> None:
    tex = TextureLoader().load_file(tmp_path / "missing.png", name="x", slot="albedo")
    assert tex.is_fallback
    assert tex.width == 1


def test_texture_png_metahuman() -> None:
    from motion_engine.rendering.assets import METAHUMAN_ROOT

    path = METAHUMAN_ROOT / "cache" / "textures" / "body_bc.png"
    if not path.is_file():
        pytest.skip("texture cache missing")
    tex = TextureLoader().load_file(path, name="bc", slot="albedo")
    assert not tex.is_fallback
    assert tex.width > 1


def test_skeleton_from_triangle() -> None:
    manifest = ManifestLoader().load(TRIANGLE / "avatar.json")
    skel = SkeletonLoader().load_from_manifest(manifest)
    assert skel is not None
    assert skel.bone_count >= 1
    assert skel.try_bone("root") is not None


def test_skeleton_metahuman_npz() -> None:
    manifest = ManifestLoader().load("metahuman")
    skel = SkeletonLoader().load_from_manifest(manifest)
    assert skel is not None
    assert skel.bone_count > 20
    assert skel.bones[0].inverse_bind is not None


def test_avatar_loader_triangle_integration() -> None:
    loaded = AvatarLoader().load(TRIANGLE / "avatar.json")
    assert loaded.primary_mesh is not None
    assert loaded.skeleton is not None
    assert loaded.materials
    assert loaded.metadata["load_ms"] >= 0


def test_avatar_loader_metahuman_integration() -> None:
    loaded = AvatarLoader().load("avatar.metahuman.default", lod=3)
    assert loaded.id == "avatar.metahuman.default"
    assert loaded.primary_mesh is not None
    assert loaded.skeleton is not None
    assert loaded.skeleton.bone_count == 342
    assert any(not t.is_fallback for t in loaded.textures) or loaded.textures


def test_avatar_loader_procedural() -> None:
    loaded = AvatarLoader().load("procedural")
    assert loaded.manifest.avatar_type == "procedural"
    assert loaded.meshes == ()


def test_registry_lazy_and_duplicate() -> None:
    reg = AvatarRegistry()
    reg.register_path("avatar.triangle.default", TRIANGLE / "avatar.json")
    a = reg.get("avatar.triangle.default")
    b = reg.get("avatar.triangle.default")
    assert a is b
    with pytest.raises(ValidationError):
        reg.register_path("avatar.triangle.default", TRIANGLE / "avatar.json")


def test_factory_create_and_defaults() -> None:
    factory = AvatarFactory()
    loaded = factory.create(TRIANGLE / "avatar.json", register_as="avatar.triangle.default")
    assert factory.registry.get("avatar.triangle.default") is loaded
    factory.register_defaults()
    assert "avatar.procedural.default" in factory.registry.ids()


def test_asset_validator_empty_mesh() -> None:
    from motion_engine.rendering.avatar.models import (
        AvatarManifest,
        CoordinateSystem,
        LoadedAvatar,
        MeshData,
    )

    manifest = ManifestLoader().load(TRIANGLE / "avatar.json")
    empty = MeshData(
        name="empty",
        positions=np.zeros((0, 3), dtype=np.float32),
        normals=np.zeros((0, 3), dtype=np.float32),
        uvs=np.zeros((0, 2), dtype=np.float32),
        indices=np.zeros((0,), dtype=np.int32),
    )
    loaded = LoadedAvatar(
        id="x",
        manifest=manifest,
        meshes=(empty,),
        materials=(),
        skeleton=None,
    )
    report = AssetValidator().validate(loaded)
    assert not report.ok
    with pytest.raises(ValidationError):
        report.raise_if_errors()


def test_gltf_handler_can_load() -> None:
    h = GltfMeshHandler()
    assert h.can_load(Path("a.glb"))
    assert h.can_load(Path("a.gltf"))
    assert not h.can_load(Path("a.npz"))


def test_digital_avatar_load() -> None:
    from motion_engine.rendering.avatar.digital_avatar import DigitalAvatar

    avatar = DigitalAvatar("triangle")
    avatar.load(source=TRIANGLE / "avatar.json")
    assert avatar.is_loaded
    assert avatar.loaded_avatar is not None
    avatar.update(None)
    avatar.dispose()
    assert not avatar.is_loaded


def test_compat_avatar_manifest_soft_api() -> None:
    from motion_engine.rendering.avatar.avatar_manifest import AvatarManifest

    m = AvatarManifest.procedural_default()
    assert m is not None
    assert m.name == "procedural"
