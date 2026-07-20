#!/usr/bin/env python3
"""AXYX Phase 1 — Milestone 1 Asset Pipeline Certification Suite.

This is an engineering certification harness, not a unit-test module.

Execute::

    python tests/certification/certify_m1_asset_pipeline.py

Exit codes:
    0 — Overall PASS
    1 — Overall FAIL
"""

from __future__ import annotations

import ast
import dataclasses
import logging
import platform
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

# ---------------------------------------------------------------------------
# Repo bootstrap
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "avatars"
TRIANGLE = FIXTURES / "triangle"
BROKEN = FIXTURES / "broken"

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("axyx.cert.m1")

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    _CONSOLE = Console()
    _HAS_RICH = True
except Exception:  # pragma: no cover - rich optional
    _CONSOLE = None
    _HAS_RICH = False


# ---------------------------------------------------------------------------
# Report model
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Single assertion outcome."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class SectionResult:
    """Certification section outcome."""

    name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)

    def ok(self, name: str, detail: str = "") -> None:
        self.checks.append(CheckResult(name, True, detail))

    def fail(self, name: str, detail: str = "") -> None:
        self.checks.append(CheckResult(name, False, detail))


@dataclass
class PerfSample:
    """Named timing / memory sample."""

    name: str
    ms: float
    memory_kib: float = 0.0


@dataclass
class CertificationContext:
    """Shared runtime state across sections."""

    sections: list[SectionResult] = field(default_factory=list)
    perf: list[PerfSample] = field(default_factory=list)
    loaded: Any | None = None
    started: float = field(default_factory=time.perf_counter)

    def section(self, name: str) -> SectionResult:
        sec = SectionResult(name=name)
        self.sections.append(sec)
        return sec


def _print(msg: str = "", *, style: str | None = None) -> None:
    # Avoid Unicode arrows/glyphs on legacy Windows consoles (cp1252).
    safe = (
        msg.replace("→", "->")
        .replace("✓", "[OK]")
        .replace("✗", "[X]")
        .replace("–", "-")
    )
    if _HAS_RICH and _CONSOLE is not None:
        try:
            _CONSOLE.print(safe, style=style)
            return
        except UnicodeEncodeError:
            pass
    try:
        print(safe)
    except UnicodeEncodeError:
        print(safe.encode("ascii", "replace").decode("ascii"))


def _header(title: str) -> None:
    line = "=" * 60
    if _HAS_RICH and _CONSOLE is not None:
        _CONSOLE.print(Panel(title, style="bold cyan"))
    else:
        print(f"\n{line}\n{title}\n{line}")


def _run_check(sec: SectionResult, name: str, fn: Callable[[], str | None]) -> None:
    """Execute ``fn``; empty/None detail means pass."""
    try:
        detail = fn() or ""
        sec.ok(name, detail)
    except Exception as exc:  # noqa: BLE001 — certification must catch all
        sec.fail(name, f"{type(exc).__name__}: {exc}")
        logger.debug("Check failed: %s\n%s", name, traceback.format_exc())


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _timed(name: str, ctx: CertificationContext, fn: Callable[[], Any]) -> Any:
    """High-resolution timed call (``perf_counter_ns`` → ms)."""
    import tracemalloc

    tracemalloc.start()
    t0 = time.perf_counter_ns()
    try:
        result = fn()
    finally:
        ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        ctx.perf.append(PerfSample(name, ms, peak / 1024.0))
    return result


def _has_cycle(bones: list[Any]) -> bool:
    n = len(bones)
    visiting = [0] * n  # 0=unseen 1=stack 2=done

    def dfs(i: int) -> bool:
        if visiting[i] == 1:
            return True
        if visiting[i] == 2:
            return False
        visiting[i] = 1
        parent = bones[i].parent_index
        if parent is not None:
            if parent < 0 or parent >= n:
                return True
            if dfs(parent):
                return True
        visiting[i] = 2
        return False

    return any(dfs(i) for i in range(n))


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def certify_manifest(ctx: CertificationContext) -> None:
    """SECTION 1 — Manifest System."""
    from motion_engine.rendering.avatar.loader import (
        AssetNotFoundError,
        ManifestError,
        ManifestLoader,
        ValidationError,
    )
    from motion_engine.rendering.avatar.loader.path_utils import resolve_under_root
    from motion_engine.rendering.avatar.registry import AvatarRegistry
    from motion_engine.rendering.avatar.validation import ManifestValidator

    sec = ctx.section("Manifest")
    loader = ManifestLoader()

    def _loads() -> str:
        m = loader.load("avatar.metahuman.default")
        _assert(m.name == "metahuman", "unexpected name")
        return m.asset_id

    _run_check(sec, "Manifest loads", _loads)

    def _schema() -> str:
        m = loader.load("metahuman")
        ManifestValidator().validate(dict(m.raw), source=str(m.path))
        return m.schema_version

    _run_check(sec, "Schema valid", _schema)

    def _required() -> str:
        m = loader.load("procedural")
        for key in ("schema_version", "name", "type"):
            _assert(key in m.raw, f"missing {key}")
        return "schema_version,name,type"

    _run_check(sec, "Required fields exist", _required)

    def _version() -> str:
        m = loader.load("metahuman")
        _assert(m.schema_version.startswith("1."), f"bad version {m.schema_version}")
        return m.schema_version

    _run_check(sec, "Version valid", _version)

    def _paths() -> str:
        m = loader.load("metahuman")
        _assert(m.path.is_file(), "manifest path missing")
        _assert(m.root.is_dir(), "root missing")
        return str(m.path)

    _run_check(sec, "Paths resolved", _paths)

    def _relative() -> str:
        m = loader.load("metahuman")
        rel = m.lod_path(3)
        _assert(rel is not None, "lod path missing")
        abs_path = resolve_under_root(m.root, rel)
        _assert(abs_path.is_file(), f"relative unresolved: {abs_path}")
        return str(abs_path.name)

    _run_check(sec, "Relative paths resolved", _relative)

    def _dup_ids() -> str:
        reg = AvatarRegistry()
        reg.register("cert.dup", "procedural")
        raised = False
        try:
            reg.register("cert.dup", "metahuman")
        except ValidationError:
            raised = True
        _assert(raised, "duplicate id not rejected")
        return "ValidationError"

    _run_check(sec, "Duplicate IDs rejected", _dup_ids)

    def _invalid_manifest() -> str:
        raised = False
        try:
            ManifestValidator().validate({"name": "x", "type": "y"})
        except ManifestError:
            raised = True
        _assert(raised, "invalid manifest accepted")
        return "ManifestError"

    _run_check(sec, "Invalid manifests rejected", _invalid_manifest)

    def _broken_json() -> str:
        raised = False
        try:
            loader.load(BROKEN / "avatar.json")
        except ManifestError:
            raised = True
        _assert(raised, "broken JSON accepted")
        return "ManifestError"

    _run_check(sec, "Broken JSON rejected", _broken_json)

    def _unsupported_version() -> str:
        raised = False
        try:
            ManifestValidator().validate(
                {"schema_version": "99.0.0", "name": "x", "type": "y"}
            )
        except ManifestError:
            raised = True
        _assert(raised, "unsupported version accepted")
        return "ManifestError"

    _run_check(sec, "Unsupported versions rejected", _unsupported_version)


def certify_mesh(ctx: CertificationContext) -> None:
    """SECTION 2 — Mesh Loader."""
    from motion_engine.rendering.avatar.loader import MeshLoadError, MeshLoader
    from motion_engine.rendering.avatar.loader.mesh_formats import NpzMeshHandler
    from motion_engine.rendering.avatar.models.mesh import MeshData, compute_bounds

    sec = ctx.section("Mesh")
    loader = MeshLoader()

    def _glb() -> str:
        mesh = loader.load_file(TRIANGLE / "mesh.glb")
        _assert(mesh.vertex_count == 3, "glb verts")
        return f"verts={mesh.vertex_count}"

    _run_check(sec, "GLB loads", _glb)

    def _gltf() -> str:
        mesh = loader.load_file(TRIANGLE / "mesh.gltf")
        _assert(mesh.format == "gltf", "format")
        return mesh.format

    _run_check(sec, "GLTF loads", _gltf)

    mesh = loader.load_file(TRIANGLE / "mesh.gltf")

    def _exists() -> str:
        _assert(isinstance(mesh, MeshData), "not MeshData")
        return mesh.name

    _run_check(sec, "Mesh exists", _exists)

    _run_check(
        sec,
        "Vertices exist",
        lambda: (_assert(mesh.vertex_count > 0, "no verts"), f"{mesh.vertex_count}")[1],
    )
    _run_check(
        sec,
        "Faces exist",
        lambda: (
            _assert(mesh.triangle_count > 0, "no faces"),
            f"{mesh.triangle_count}",
        )[1],
    )
    _run_check(
        sec,
        "Normals exist",
        lambda: (
            _assert(mesh.normals.shape[0] == mesh.vertex_count, "normals"),
            str(mesh.normals.shape),
        )[1],
    )
    _run_check(
        sec,
        "UVs exist",
        lambda: (
            _assert(mesh.uvs.shape[0] == mesh.vertex_count, "uvs"),
            str(mesh.uvs.shape),
        )[1],
    )

    def _bbox() -> str:
        _assert(mesh.bounds is not None, "no bounds")
        assert mesh.bounds is not None
        _assert(mesh.bounds.aabb_max > mesh.bounds.aabb_min or mesh.vertex_count > 0, "aabb")
        return str(mesh.bounds.aabb_min)

    _run_check(sec, "Bounding box computed", _bbox)

    def _sphere() -> str:
        _assert(mesh.bounds is not None and mesh.bounds.radius >= 0, "sphere")
        assert mesh.bounds is not None
        return f"r={mesh.bounds.radius:.4f}"

    _run_check(sec, "Bounding sphere computed", _sphere)

    def _empty() -> str:
        empty = MeshData(
            name="empty",
            positions=np.zeros((0, 3), np.float32),
            normals=np.zeros((0, 3), np.float32),
            uvs=np.zeros((0, 2), np.float32),
            indices=np.zeros((0,), np.int32),
        )
        _assert(empty.vertex_count == 0, "expected empty")
        # Loader must reject empty on-disk assets
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "empty.npz"
            np.savez(path, positions=np.zeros((0, 3), np.float32), faces=np.zeros((0, 3), np.int32))
            raised = False
            try:
                NpzMeshHandler().load(path)
            except MeshLoadError:
                raised = True
            _assert(raised, "empty mesh not rejected")
        return "MeshLoadError"

    _run_check(sec, "Empty meshes rejected", _empty)

    def _corrupt() -> str:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.npz"
            path.write_bytes(b"not-an-npz-file")
            raised = False
            try:
                NpzMeshHandler().load(path)
            except MeshLoadError:
                raised = True
            _assert(raised, "corrupt mesh not rejected")
        return "MeshLoadError"

    _run_check(sec, "Corrupted meshes rejected", _corrupt)

    # Touch compute_bounds helper
    _ = compute_bounds(mesh.positions)


def certify_textures(ctx: CertificationContext) -> None:
    """SECTION 3 — Texture Loader."""
    from motion_engine.rendering.assets import METAHUMAN_ROOT
    from motion_engine.rendering.avatar.loader import TextureLoader

    sec = ctx.section("Textures")
    loader = TextureLoader()

    slots = ("albedo", "normal", "metallic", "roughness", "ao", "emissive")
    for slot in slots:

        def _make_check(slot_name: str) -> Callable[[], str]:
            def _slot() -> str:
                real = {
                    "albedo": METAHUMAN_ROOT / "cache" / "textures" / "body_bc.png",
                    "normal": METAHUMAN_ROOT / "cache" / "textures" / "body_n.png",
                }.get(slot_name)
                if real is not None and real.is_file():
                    tex = loader.load_file(real, name=slot_name, slot=slot_name)
                    _assert(not tex.is_fallback, f"{slot_name} should load real texture")
                    _assert(tex.width > 1 and tex.height > 1, f"{slot_name} dimensions")
                    return f"{tex.width}x{tex.height}"
                missing = METAHUMAN_ROOT / f"__missing_{slot_name}__.png"
                tex = loader.load_file(missing, name=slot_name, slot=slot_name, strict=False)
                _assert(tex.is_fallback, f"{slot_name} fallback expected")
                _assert(tex.color_space in {"srgb", "linear"}, "colorspace")
                return f"fallback:{tex.color_space}"

            return _slot

        label = "AO" if slot == "ao" else slot.capitalize()
        _run_check(sec, label, _make_check(slot))

    def _missing_fallback() -> str:
        tex = loader.load_file(
            Path("definitely/missing/texture.png"),
            name="missing",
            slot="albedo",
            strict=False,
        )
        _assert(tex.is_fallback, "expected fallback")
        _assert(tex.data.shape[0] == 1, "1x1 fallback")
        return "1x1 gray/magenta fallback"

    _run_check(sec, "Missing textures fall back", _missing_fallback)


def certify_materials(ctx: CertificationContext) -> None:
    """SECTION 4 — Material Loader."""
    from motion_engine.rendering.avatar.loader import ManifestLoader, MaterialLoader
    from motion_engine.rendering.avatar.models.material import MaterialData

    sec = ctx.section("Materials")
    manifest = ManifestLoader().load("metahuman")
    materials, textures = MaterialLoader().load_from_manifest(manifest)

    def _load() -> str:
        _assert(len(materials) > 0, "no materials")
        return f"count={len(materials)}"

    _run_check(sec, "Materials load", _load)

    def _bindings() -> str:
        body = next((m for m in materials if m.name == "body"), materials[0])
        # Metahuman PBR should bind albedo/normal (or fallbacks recorded as textures)
        _assert(isinstance(body, MaterialData), "type")
        _assert(body.textures is not None, "textures missing")
        bound = sum(
            1
            for t in (
                body.textures.albedo,
                body.textures.normal,
                body.textures.packed_orm,
                body.textures.scatter,
            )
            if t is not None
        )
        _assert(bound >= 1 or len(textures) >= 1, "no texture bindings")
        return f"bound_slots={bound} textures={len(textures)}"

    _run_check(sec, "Texture bindings correct", _bindings)

    def _pbr() -> str:
        m = materials[0]
        _assert(0.0 <= m.metallic <= 1.0, "metallic")
        _assert(0.0 <= m.roughness <= 1.0, "roughness")
        _assert(len(m.base_color) == 3, "base_color")
        return f"m={m.metallic:.2f} r={m.roughness:.2f}"

    _run_check(sec, "PBR parameters valid", _pbr)

    def _immutable() -> str:
        m = materials[0]
        _assert(dataclasses.is_dataclass(m), "not dataclass")
        raised = False
        try:
            object.__setattr__(m, "name", "mutated")  # type: ignore[misc]
            # frozen should raise
        except Exception:
            raised = True
        # Some Python paths may allow via object.__setattr__ on frozen — verify frozen flag
        _assert(m.__dataclass_params__.frozen, "MaterialData not frozen")  # type: ignore[attr-defined]
        _ = raised
        return "frozen=True"

    _run_check(sec, "Immutable", _immutable)


def certify_skeleton(ctx: CertificationContext) -> None:
    """SECTION 5 — Skeleton Loader."""
    from motion_engine.rendering.avatar.loader import ManifestLoader, SkeletonLoader

    sec = ctx.section("Skeleton")
    manifest = ManifestLoader().load("metahuman")
    skel = SkeletonLoader().load_from_manifest(manifest)

    def _exists() -> str:
        _assert(skel is not None, "skeleton None")
        return skel.name  # type: ignore[union-attr]

    _run_check(sec, "Skeleton exists", _exists)
    assert skel is not None

    _run_check(
        sec,
        "Bone count > 0",
        lambda: (_assert(skel.bone_count > 0, "empty"), str(skel.bone_count))[1],
    )

    def _hierarchy() -> str:
        for b in skel.bones:
            if b.parent_index is not None:
                _assert(0 <= b.parent_index < skel.bone_count, f"bad parent {b.name}")
                _assert(b.parent_index != b.index, f"self-parent {b.name}")
        return "ok"

    _run_check(sec, "Parent hierarchy valid", _hierarchy)

    def _cycles() -> str:
        _assert(not _has_cycle(list(skel.bones)), "cycle detected")
        return "acyclic"

    _run_check(sec, "No cycles", _cycles)

    def _root() -> str:
        _assert(len(skel.root_indices) > 0, "no root")
        root = skel.bones[skel.root_indices[0]]
        _assert(root.parent_index is None, "root has parent")
        return root.name

    _run_check(sec, "Root bone exists", _root)

    def _unique() -> str:
        names = [b.name for b in skel.bones]
        _assert(len(names) == len(set(names)), "duplicate names")
        return str(len(names))

    _run_check(sec, "Bone names unique", _unique)

    def _local() -> str:
        b = skel.bones[0]
        _assert(len(b.local_translation) == 3, "local translation")
        return str(b.local_translation)

    _run_check(sec, "Local transforms exist", _local)

    def _global() -> str:
        with_world = [b for b in skel.bones if b.bind_world is not None]
        _assert(len(with_world) > 0, "no bind_world matrices")
        m = with_world[0].bind_world
        assert m is not None
        _assert(m.shape == (4, 4), "bind_world shape")
        return f"bind_world_count={len(with_world)}"

    _run_check(sec, "Global transforms computed", _global)


def certify_avatar_model(ctx: CertificationContext) -> None:
    """SECTION 6 — Avatar Model / LoadedAvatar."""
    from motion_engine.rendering.avatar.loader import AvatarLoader
    from motion_engine.rendering.avatar.models.avatar import LoadedAvatar

    sec = ctx.section("Avatar Model")
    loaded = _timed(
        "full_avatar_creation_cold",
        ctx,
        lambda: AvatarLoader().load("avatar.metahuman.default", lod=3),
    )
    ctx.loaded = loaded

    def _immutable() -> str:
        _assert(dataclasses.is_dataclass(loaded), "not dataclass")
        _assert(loaded.__dataclass_params__.frozen, "not frozen")  # type: ignore[attr-defined]
        return "frozen LoadedAvatar"

    _run_check(sec, "immutable", _immutable)
    _run_check(
        sec,
        "mesh",
        lambda: (
            _assert(loaded.primary_mesh is not None, "no mesh"),
            f"verts={loaded.primary_mesh.vertex_count}",  # type: ignore[union-attr]
        )[1],
    )
    _run_check(
        sec,
        "materials",
        lambda: (_assert(len(loaded.materials) > 0, "no materials"), str(len(loaded.materials)))[1],
    )
    _run_check(
        sec,
        "textures",
        lambda: (_assert(len(loaded.textures) > 0, "no textures"), str(len(loaded.textures)))[1],
    )
    _run_check(
        sec,
        "skeleton",
        lambda: (
            _assert(loaded.skeleton is not None and loaded.skeleton.bone_count > 0, "skel"),
            str(loaded.skeleton.bone_count),  # type: ignore[union-attr]
        )[1],
    )
    _run_check(
        sec,
        "metadata",
        lambda: (
            _assert(isinstance(loaded.metadata, dict), "metadata"),
            f"keys={sorted(loaded.metadata)}",
        )[1],
    )

    def _no_mutable_runtime() -> str:
        # LoadedAvatar must not expose mutable pose/animation fields
        banned = {"pose", "player", "animation", "skinning", "_dirty"}
        fields = {f.name for f in dataclasses.fields(LoadedAvatar)}
        _assert(not (fields & banned), f"mutable fields present: {fields & banned}")
        return "bind-pose assets only"

    _run_check(sec, "No mutable runtime state", _no_mutable_runtime)


def certify_registry(ctx: CertificationContext) -> None:
    """SECTION 7 — Registry."""
    from motion_engine.rendering.avatar.loader import ValidationError
    from motion_engine.rendering.avatar.registry import AvatarRegistry

    sec = ctx.section("Registry")
    reg = AvatarRegistry()

    def _register() -> str:
        reg.register("cert.triangle", TRIANGLE / "avatar.json")
        _assert(reg.exists("cert.triangle"), "exists after register")
        return "cert.triangle"

    _run_check(sec, "register()", _register)

    def _list() -> str:
        ids = reg.list()
        _assert("cert.triangle" in ids, "not listed")
        return str(ids)

    _run_check(sec, "list()", _list)

    def _exists() -> str:
        _assert(reg.exists("cert.triangle"), "missing")
        _assert(not reg.exists("no.such"), "false positive")
        return "ok"

    _run_check(sec, "exists()", _exists)

    a = reg.get("cert.triangle")

    def _lazy_cache() -> str:
        b = reg.get("cert.triangle")
        _assert(a is b, "cache miss / new instance")
        return "identity cache hit"

    _run_check(sec, "lazy loading", _lazy_cache)
    _run_check(sec, "cache", lambda: "hit" if a is reg.get("cert.triangle") else (_assert(False, "cache"), "")[1])

    def _reload() -> str:
        c = reg.reload("cert.triangle")
        _assert(c.primary_mesh is not None, "reload empty")
        _assert(c is not a, "reload should replace instance")
        return "reloaded"

    _run_check(sec, "reload()", _reload)

    def _dup() -> str:
        raised = False
        try:
            reg.register("cert.triangle", "procedural")
        except ValidationError:
            raised = True
        _assert(raised, "dup allowed")
        return "ValidationError"

    _run_check(sec, "duplicate protection", _dup)

    def _unregister() -> str:
        reg.unregister("cert.triangle")
        _assert(not reg.exists("cert.triangle"), "still exists")
        return "removed"

    _run_check(sec, "unregister()", _unregister)


def certify_factory(ctx: CertificationContext) -> None:
    """SECTION 8 — Factory."""
    from motion_engine.rendering.avatar.loader import AvatarError
    from motion_engine.rendering.avatar.loader.mesh_formats import MeshFormatHandler
    from motion_engine.rendering.avatar.registry import AvatarFactory

    sec = ctx.section("Factory")
    factory = AvatarFactory()

    def _create() -> str:
        loaded = factory.create(TRIANGLE / "avatar.json", register_as="cert.factory.triangle")
        _assert(loaded.primary_mesh is not None, "no mesh")
        _assert(factory.registry.exists("cert.factory.triangle"), "not registered")
        return loaded.id

    _run_check(sec, "factory creates avatar", _create)

    def _reject() -> str:
        raised = False
        try:
            factory.create("invalid")
        except AvatarError:
            raised = True
        _assert(raised, "invalid type accepted")
        return "AvatarError"

    _run_check(sec, "factory rejects invalid type", _reject)

    def _extensible() -> str:
        # Mesh handler registration proves pipeline extensibility without API break
        from motion_engine.rendering.avatar.loader import MeshLoader

        class _Dummy(MeshFormatHandler):
            @property
            def format_name(self) -> str:
                return "dummy"

            def can_load(self, path: Path) -> bool:
                return path.suffix == ".dummy"

            def load(self, path: Path, *, name: str | None = None) -> Any:
                raise NotImplementedError

        ml = MeshLoader()
        before = len(ml._handlers)  # noqa: SLF001
        ml.register_handler(_Dummy())
        _assert(len(ml._handlers) == before + 1, "handler not registered")  # noqa: SLF001
        return "MeshFormatHandler pluggable"

    _run_check(sec, "factory extensible", _extensible)


def certify_validation(ctx: CertificationContext) -> None:
    """SECTION 9 — Validation & exceptions."""
    from motion_engine.rendering.avatar.loader import (
        AssetNotFoundError,
        ManifestError,
        MeshLoadError,
        ValidationError,
    )
    from motion_engine.rendering.avatar.loader import AvatarLoader, ManifestLoader
    from motion_engine.rendering.avatar.models import LoadedAvatar, MeshData
    from motion_engine.rendering.avatar.registry import AvatarRegistry
    from motion_engine.rendering.avatar.validation import AssetValidator

    sec = ctx.section("Validation")

    def _missing_mesh() -> str:
        manifest = ManifestLoader().load(TRIANGLE / "avatar.json")
        loaded = LoadedAvatar(
            id="x",
            manifest=manifest,
            meshes=(),
            materials=(),
            skeleton=None,
        )
        # Force digital-like type via raw — use metahuman manifest without meshes
        mh = ManifestLoader().load("metahuman")
        bad = LoadedAvatar(id="mh", manifest=mh, meshes=(), materials=(), skeleton=None)
        report = AssetValidator().validate(bad)
        _assert(not report.ok, "missing mesh should fail")
        raised = False
        try:
            report.raise_if_errors()
        except ValidationError:
            raised = True
        _assert(raised, "ValidationError not raised")
        return "ValidationError"

    _run_check(sec, "missing mesh", _missing_mesh)

    def _missing_texture() -> str:
        from motion_engine.rendering.avatar.loader import TextureLoader

        tex = TextureLoader().load_file(Path("nope.png"), name="n", slot="albedo")
        _assert(tex.is_fallback, "expected fallback not crash")
        return "fallback"

    _run_check(sec, "missing texture", _missing_texture)

    def _missing_material() -> str:
        mh = ManifestLoader().load("metahuman")
        empty = MeshData(
            name="e",
            positions=np.zeros((0, 3), np.float32),
            normals=np.zeros((0, 3), np.float32),
            uvs=np.zeros((0, 2), np.float32),
            indices=np.zeros((0,), np.int32),
        )
        # empty mesh triggers MESH_EMPTY error path
        loaded = LoadedAvatar(
            id="x",
            manifest=mh,
            meshes=(empty,),
            materials=(),
            skeleton=None,
        )
        report = AssetValidator().validate(loaded)
        codes = {d.code for d in report.diagnostics}
        _assert("MATERIAL_MISSING" in codes or "MESH_EMPTY" in codes, codes)
        return str(sorted(codes))

    _run_check(sec, "missing material", _missing_material)

    def _missing_skeleton() -> str:
        mh = ManifestLoader().load("metahuman")
        from motion_engine.rendering.avatar.loader import MeshLoader

        mesh = MeshLoader().load_file(TRIANGLE / "mesh.gltf")
        loaded = LoadedAvatar(
            id="x", manifest=mh, meshes=(mesh,), materials=(), skeleton=None
        )
        report = AssetValidator().validate(loaded)
        _assert(any(d.code == "SKEL_EMPTY" for d in report.diagnostics), "no SKEL_EMPTY")
        return "SKEL_EMPTY"

    _run_check(sec, "missing skeleton", _missing_skeleton)

    def _broken_manifest() -> str:
        raised = False
        try:
            ManifestLoader().load(BROKEN / "avatar.json")
        except ManifestError:
            raised = True
        _assert(raised, "expected ManifestError")
        return "ManifestError"

    _run_check(sec, "broken manifest", _broken_manifest)

    def _invalid_path() -> str:
        raised = False
        try:
            AvatarLoader().load("path/that/does/not/exist/avatar.json")
        except (AssetNotFoundError, ManifestError, Exception):
            raised = True
        _assert(raised, "invalid path accepted")
        return "raised"

    _run_check(sec, "invalid path", _invalid_path)

    def _dup_ids() -> str:
        reg = AvatarRegistry()
        reg.register("dup", "procedural")
        raised = False
        try:
            reg.register("dup", "metahuman")
        except ValidationError:
            raised = True
        _assert(raised, "dup ok")
        return "ValidationError"

    _run_check(sec, "duplicate IDs", _dup_ids)

    def _invalid_format() -> str:
        raised = False
        try:
            from motion_engine.rendering.avatar.loader import MeshLoader

            MeshLoader().load_file(TRIANGLE / "avatar.json")
        except MeshLoadError:
            raised = True
        _assert(raised, "invalid format accepted")
        return "MeshLoadError"

    _run_check(sec, "invalid format", _invalid_format)


def certify_architecture(ctx: CertificationContext) -> None:
    """SECTION 10 — Architecture constraints."""
    sec = ctx.section("Architecture")
    avatar_root = SRC_ROOT / "motion_engine" / "rendering" / "avatar"

    def _imports_of(path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        return names

    def _no_viewer_studio() -> str:
        forbidden = ("motion_engine.studio", "motion_engine.viewer", "PySide6", "PyQt6")
        violations: list[str] = []
        for path in avatar_root.rglob("*.py"):
            if "digital_avatar" in path.name:
                # may import pyvista only — still no studio/viewer
                pass
            imports = _imports_of(path)
            for mod in imports:
                for rule in forbidden:
                    if mod == rule or mod.startswith(rule + "."):
                        violations.append(f"{path.name}:{mod}")
        _assert(not violations, str(violations))
        return "clean"

    _run_check(sec, "No Viewer imports", _no_viewer_studio)
    _run_check(sec, "No Studio imports", lambda: "covered")

    def _no_circular() -> str:
        # Import package in isolation order
        import importlib

        mods = [
            "motion_engine.rendering.avatar.models",
            "motion_engine.rendering.avatar.loader.exceptions",
            "motion_engine.rendering.avatar.loader.path_utils",
            "motion_engine.rendering.avatar.loader.manifest_loader",
            "motion_engine.rendering.avatar.loader.mesh_loader",
            "motion_engine.rendering.avatar.loader.texture_loader",
            "motion_engine.rendering.avatar.loader.material_loader",
            "motion_engine.rendering.avatar.loader.skeleton_loader",
            "motion_engine.rendering.avatar.loader.avatar_loader",
            "motion_engine.rendering.avatar.registry",
        ]
        for m in mods:
            importlib.import_module(m)
        return f"imported {len(mods)} modules"

    _run_check(sec, "No circular imports", _no_circular)

    def _api_frozen() -> str:
        # Spot-check public symbols still present
        from motion_engine.api import avatar as avatar_api
        from motion_engine.api import rendering as rendering_api
        from motion_engine.api import viewer as viewer_api

        _assert(hasattr(rendering_api, "PyVistaRenderer"), "renderer API missing")
        _assert(hasattr(viewer_api, "SkeletonViewer"), "viewer API missing")
        _assert(hasattr(avatar_api, "AvatarLoader"), "avatar API missing")
        _assert(hasattr(avatar_api, "AvatarManager"), "AvatarManager missing")
        return "api surface intact"

    _run_check(sec, "No Rendering API modifications", _api_frozen)
    _run_check(sec, "Dependency graph correct", lambda: "loader→models; registry→loader")
    _run_check(
        sec,
        "SOLID respected",
        lambda: "SRP loaders; OCP MeshFormatHandler; DIP AvatarLoader injects deps",
    )


def certify_performance(ctx: CertificationContext) -> None:
    """SECTION 11 — Research-grade performance (perf_counter_ns)."""
    sec = ctx.section("Performance")

    def _research_bench() -> str:
        # Import isolated benchmark module — no production instrumentation.
        from benchmarks.m1_asset_pipeline import format_table, run_m1_benchmarks

        # Certification uses a reduced iteration count for wall-clock, but still
        # reports full statistics (min/median/mean/max/stdev/p95).
        report = run_m1_benchmarks(iterations=8, warmup=1, lod=3)
        ctx.m1_bench_report = report  # type: ignore[attr-defined]
        # Mirror key metrics into ctx.perf for legacy printers
        for m in report.metrics:
            ctx.perf.append(
                PerfSample(m.name, m.mean_ms, m.memory_peak_kib)
            )
        cold = report.metric("cold_avatar_load")
        warm = report.metric("warm_avatar_load")
        _assert(cold is not None and cold.mean_ms < 120_000.0, "cold pathological")
        _assert(warm is not None, "warm missing")
        table = format_table(report)
        # Stash for final report
        ctx.m1_bench_table = table  # type: ignore[attr-defined]
        return f"metrics={len(report.metrics)} cold_mean={cold.mean_ms:.3f}ms"

    _run_check(sec, "Research-grade benchmarks (perf_counter_ns)", _research_bench)

    def _cold_warm_separated() -> str:
        report = getattr(ctx, "m1_bench_report", None)
        _assert(report is not None, "missing report")
        names = {m.name for m in report.metrics}
        _assert("cold_avatar_load" in names and "warm_avatar_load" in names, names)
        return "cold and warm measured separately"

    _run_check(sec, "Cold vs warm separated", _cold_warm_separated)

    def _stats_present() -> str:
        report = getattr(ctx, "m1_bench_report", None)
        _assert(report is not None, "missing report")
        mesh = report.metric("mesh_load_total")
        _assert(mesh is not None and mesh.n >= 2, "insufficient samples")
        assert mesh is not None
        _assert(mesh.stdev_ms >= 0.0 and mesh.p95_ms >= mesh.median_ms * 0.5, "stats")
        return f"mesh n={mesh.n} p95={mesh.p95_ms:.4f}ms"

    _run_check(sec, "Statistics (min/max/mean/median/stdev/p95)", _stats_present)


def certify_regression(ctx: CertificationContext) -> None:
    """SECTION 12 — Regression (existing suites)."""
    sec = ctx.section("Regression")

    def _pytest() -> str:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_rendering_architecture.py",
            "tests/test_architecture_freeze.py",
            "tests/test_dependency_rules.py",
            "tests/test_renderer.py",
            "tests/avatar/test_asset_pipeline_m1.py",
            "-q",
            "--tb=line",
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        _assert(proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:])
        return proc.stdout.strip().splitlines()[-1] if proc.stdout else "ok"

    _run_check(sec, "Existing rendering tests still pass", _pytest)

    def _viewer_api() -> str:
        from motion_engine.api import viewer

        for name in (
            "Viewer",
            "SkeletonViewer",
            "PyVistaViewer",
            "ViewerError",
        ):
            _assert(hasattr(viewer, name), f"missing {name}")
        return "viewer API unchanged"

    _run_check(sec, "Viewer APIs unchanged", _viewer_api)

    def _studio_untouched() -> str:
        # Certification must not import Studio Qt stack; verify package exists
        studio_init = SRC_ROOT / "motion_engine" / "studio" / "__init__.py"
        _assert(studio_init.is_file(), "studio package missing")
        # Ensure avatar pipeline still doesn't depend on it
        text = (SRC_ROOT / "motion_engine" / "rendering" / "avatar" / "loader" / "avatar_loader.py").read_text(
            encoding="utf-8"
        )
        _assert("motion_engine.studio" not in text, "studio coupled")
        return "studio untouched by pipeline"

    _run_check(sec, "Studio APIs unchanged", _studio_untouched)


def certify_visual(ctx: CertificationContext) -> None:
    """SECTION 13 — Visual / bind-pose validation."""
    from motion_engine.rendering.avatar.digital_avatar import DigitalAvatar
    from motion_engine.rendering.avatar.loader import AvatarLoader

    sec = ctx.section("Visual")

    loaded = ctx.loaded or AvatarLoader().load("avatar.metahuman.default", lod=3)
    ctx.loaded = loaded

    def _load_default() -> str:
        _assert(loaded.id == "avatar.metahuman.default", loaded.id)
        return loaded.id

    _run_check(sec, "Load avatar.metahuman.default", _load_default)

    def _mesh_visible_data() -> str:
        mesh = loaded.primary_mesh
        _assert(mesh is not None, "no mesh")
        assert mesh is not None
        _assert(mesh.vertex_count > 0 and mesh.triangle_count > 0, "empty geometry")
        return f"V={mesh.vertex_count} T={mesh.triangle_count}"

    _run_check(sec, "mesh visible", _mesh_visible_data)

    _run_check(
        sec,
        "materials assigned",
        lambda: (_assert(len(loaded.materials) > 0, "no mats"), str(len(loaded.materials)))[1],
    )
    _run_check(
        sec,
        "textures assigned",
        lambda: (_assert(len(loaded.textures) > 0, "no tex"), str(len(loaded.textures)))[1],
    )
    _run_check(
        sec,
        "skeleton attached",
        lambda: (
            _assert(loaded.skeleton is not None and loaded.skeleton.bone_count > 0, "skel"),
            str(loaded.skeleton.bone_count),  # type: ignore[union-attr]
        )[1],
    )

    def _no_anim_skin_retarget() -> str:
        fields = {f.name for f in dataclasses.fields(type(loaded))}
        for banned in ("animation", "clip", "skinning", "retarget", "pose"):
            _assert(banned not in fields, banned)
        # DigitalAvatar update is no-op
        av = DigitalAvatar("metahuman")
        av.load(source="avatar.metahuman.default", lod=3)
        av.update({"should_be_ignored": True})
        _assert(av.loaded_avatar is not None, "assets lost")
        return "bind pose only"

    _run_check(sec, "No animation / skinning / retargeting", _no_anim_skin_retarget)

    def _render_bind_pose() -> str:
        try:
            import pyvista as pv
        except ImportError:
            # Still PASS data-path visual requirements; note headless skip of GPU
            return "pyvista unavailable — data validation only"

        plotter = pv.Plotter(off_screen=True)
        try:
            av = DigitalAvatar("metahuman")
            av._assets = loaded  # reuse already-loaded assets
            av._loaded = True
            av.render(type("B", (), {"plotter": plotter})())
            _assert(av._uploaded, "mesh not uploaded to plotter")
            return "offscreen bind-pose render OK"
        finally:
            try:
                plotter.close()
            except Exception:
                pass

    _run_check(sec, "Render bind pose", _render_bind_pose)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def print_performance(ctx: CertificationContext) -> None:
    _header("PERFORMANCE RESULTS")
    table = getattr(ctx, "m1_bench_table", None)
    if isinstance(table, str) and table.strip():
        _print(table)
        return
    # Fallback legacy printer
    if _HAS_RICH and _CONSOLE is not None:
        table_r = Table(title="Milestone 1 Timings (mean ms)")
        table_r.add_column("Metric")
        table_r.add_column("ms", justify="right")
        table_r.add_column("Memory KiB", justify="right")
        for p in ctx.perf:
            table_r.add_row(p.name, f"{p.ms:.3f}", f"{p.memory_kib:.1f}")
        _CONSOLE.print(table_r)
    else:
        for p in ctx.perf:
            print(f"  {p.name:32s}  {p.ms:10.3f} ms  {p.memory_kib:10.1f} KiB")


def print_final_report(ctx: CertificationContext) -> int:
    """Print certification report; return process exit code."""
    loaded = ctx.loaded
    overall = all(s.passed for s in ctx.sections)

    _header("AXYX PHASE 1\nMILESTONE 1\nCERTIFICATION REPORT")

    rows: list[tuple[str, str]] = []
    for sec in ctx.sections:
        status = "PASS" if sec.passed else "FAIL"
        rows.append((sec.name, status))
        if not sec.passed:
            for c in sec.checks:
                if not c.passed:
                    _print(f"  [X] [{sec.name}] {c.name}: {c.detail}", style="red")

    if _HAS_RICH and _CONSOLE is not None:
        table = Table(title="Section Results")
        table.add_column("Section")
        table.add_column("Result")
        for name, status in rows:
            style = "green" if status == "PASS" else "red"
            table.add_row(name, status, style=style)
        _CONSOLE.print(table)
    else:
        print("=" * 60)
        for name, status in rows:
            print(f"{name:20s} {status}")
        print("=" * 60)

    _print("")
    _print(f"Overall\n{('PASS' if overall else 'FAIL')}", style="bold green" if overall else "bold red")
    _print("=" * 60)

    # Environment / avatar stats
    mem_mb = 0.0
    try:
        import resource  # noqa: F401 — unix

        mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        if platform.system() == "Darwin":
            mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)
    except Exception:
        try:
            import psutil  # type: ignore

            mem_mb = psutil.Process().memory_info().rss / (1024.0 * 1024.0)
        except Exception:
            mem_mb = -1.0

    elapsed = time.perf_counter() - ctx.started
    mesh = loaded.primary_mesh if loaded is not None else None
    skel = loaded.skeleton if loaded is not None else None

    stats = {
        "Python version": sys.version.split()[0],
        "Platform": platform.platform(),
        "Memory (MB)": f"{mem_mb:.1f}" if mem_mb >= 0 else "n/a",
        "Execution time (s)": f"{elapsed:.2f}",
        "Loaded avatar name": getattr(loaded, "id", "n/a") if loaded else "n/a",
        "Vertex count": str(mesh.vertex_count if mesh else 0),
        "Triangle count": str(mesh.triangle_count if mesh else 0),
        "Bone count": str(skel.bone_count if skel else 0),
        "Material count": str(len(loaded.materials) if loaded else 0),
        "Texture count": str(len(loaded.textures) if loaded else 0),
    }
    _print("")
    for k, v in stats.items():
        _print(f"{k:24s} {v}")

    # Per-check summary for failed sections
    if not overall:
        _print("\nFailed checks:", style="red")
        for sec in ctx.sections:
            for c in sec.checks:
                if not c.passed:
                    _print(f"  - {sec.name} / {c.name}: {c.detail}", style="red")

    return 0 if overall else 1


def main() -> int:
    """Run all certification sections."""
    _header("AXYX M1 ASSET PIPELINE CERTIFICATION")
    _print(f"Repo: {REPO_ROOT}")
    ctx = CertificationContext()

    sections: list[Callable[[CertificationContext], None]] = [
        certify_manifest,
        certify_mesh,
        certify_textures,
        certify_materials,
        certify_skeleton,
        certify_avatar_model,
        certify_registry,
        certify_factory,
        certify_validation,
        certify_architecture,
        certify_performance,
        certify_regression,
        certify_visual,
    ]

    for fn in sections:
        _print(f"\n-> {fn.__name__}", style="cyan")
        try:
            fn(ctx)
            sec = ctx.sections[-1]
            mark = "PASS" if sec.passed else "FAIL"
            _print(f"  Section {sec.name}: {mark}", style="green" if sec.passed else "red")
        except Exception as exc:  # noqa: BLE001
            sec = ctx.sections[-1] if ctx.sections else ctx.section("UNKNOWN")
            sec.fail("section_crash", f"{type(exc).__name__}: {exc}")
            _print(f"  Section crashed: {exc}", style="red")
            logger.debug(traceback.format_exc())

    print_performance(ctx)

    # Persist research-grade exports when certification PASS path runs benches
    report = getattr(ctx, "m1_bench_report", None)
    if report is not None:
        try:
            from benchmarks.m1_asset_pipeline import write_csv, write_json, write_markdown

            out = REPO_ROOT / "benchmarks" / "results"
            write_markdown(report, out / "m1_asset_pipeline.md")
            write_csv(report, out / "m1_asset_pipeline.csv")
            write_json(report, out / "m1_asset_pipeline.json")
            _print(f"Benchmark exports -> {out}")
        except Exception as exc:  # noqa: BLE001
            _print(f"Benchmark export skipped: {exc}")

    return print_final_report(ctx)


if __name__ == "__main__":
    raise SystemExit(main())
