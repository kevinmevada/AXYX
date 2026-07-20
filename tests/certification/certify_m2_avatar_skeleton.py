#!/usr/bin/env python3
"""AXYX Phase 1 — Milestone 2 Avatar Skeleton Certification Suite.

Execute::

    python tests/certification/certify_m2_avatar_skeleton.py

Exit codes:
    0 — Overall PASS
    1 — Overall FAIL
"""

from __future__ import annotations

import ast
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motion_engine.rendering.avatar.models.skeleton import (  # noqa: E402
    AvatarSkeleton as ImportedSkeleton,
)
from motion_engine.rendering.avatar.models.skeleton import BoneData  # noqa: E402
from motion_engine.rendering.avatar.skeleton import (  # noqa: E402
    AvatarSkeleton,
    AvatarSkeletonFactory,
    SkeletonValidationError,
    export_json,
    export_tree,
)
from tests.skeleton.helpers import make_chain_imported, make_tree_imported  # noqa: E402


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class SectionResult:
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
class CertificationContext:
    sections: list[SectionResult] = field(default_factory=list)
    started: float = field(default_factory=time.perf_counter)

    def section(self, name: str) -> SectionResult:
        sec = SectionResult(name=name)
        self.sections.append(sec)
        return sec


def _print_report(ctx: CertificationContext) -> bool:
    overall = all(s.passed for s in ctx.sections) and bool(ctx.sections)
    print("=" * 72)
    print("AXYX M2 Avatar Skeleton Certification")
    print("=" * 72)
    for sec in ctx.sections:
        status = "PASS" if sec.passed else "FAIL"
        print(f"\n[{status}] {sec.name}")
        for c in sec.checks:
            mark = "OK  " if c.passed else "FAIL"
            detail = f" — {c.detail}" if c.detail else ""
            print(f"  {mark} {c.name}{detail}")
    elapsed = time.perf_counter() - ctx.started
    print("\n" + "=" * 72)
    print(f"Overall: {'PASS' if overall else 'FAIL'}  ({elapsed:.2f}s)")
    print("=" * 72)
    return overall


def certify_hierarchy(ctx: CertificationContext) -> None:
    sec = ctx.section("Hierarchy correctness")
    try:
        sk = AvatarSkeletonFactory().from_imported(make_tree_imported())
        sec.ok("construct_tree", f"bones={sk.bone_count}")
        sec.ok("roots", detail=str(sk.roots)) if sk.roots == (0,) else sec.fail(
            "roots", str(sk.roots)
        )
        if sk.find("root").children == (1, 2):
            sec.ok("children_order")
        else:
            sec.fail("children_order", str(sk.find("root").children))
        lca = sk.common_ancestor("left", "right_leaf")
        if lca and lca.name == "root":
            sec.ok("lca")
        else:
            sec.fail("lca", str(lca))
        if sk.path("right_leaf") == "root/right/right_leaf":
            sec.ok("path")
        else:
            sec.fail("path", sk.path("right_leaf"))
    except Exception as exc:  # noqa: BLE001
        sec.fail("hierarchy_exception", f"{exc}\n{traceback.format_exc()}")


def certify_lookup(ctx: CertificationContext) -> None:
    sec = ctx.section("Bone lookup")
    try:
        sk = AvatarSkeletonFactory().from_imported(make_chain_imported(32))
        if sk.find("b10").index == 10:
            sec.ok("find_name")
        else:
            sec.fail("find_name")
        if sk.find(10).name == "b10":
            sec.ok("find_index")
        else:
            sec.fail("find_index")
        if sk.exists("root") and not sk.exists("nope"):
            sec.ok("exists")
        else:
            sec.fail("exists")
        if sk.index_of("b10") == 10:
            sec.ok("index_of_o1_map")
        else:
            sec.fail("index_of_o1_map")
        if "b10" in sk.lookup.by_name:
            sec.ok("lookup_table_present")
        else:
            sec.fail("lookup_table_present")
    except Exception as exc:  # noqa: BLE001
        sec.fail("lookup_exception", str(exc))


def certify_traversal(ctx: CertificationContext) -> None:
    sec = ctx.section("Traversal")
    try:
        sk = AvatarSkeletonFactory().from_imported(make_tree_imported())
        dfs = list(sk.traversal.dfs())
        bfs = list(sk.traversal.bfs())
        if len(dfs) == sk.bone_count == len(bfs):
            sec.ok("visit_all")
        else:
            sec.fail("visit_all", f"dfs={len(dfs)} bfs={len(bfs)}")
        if bfs == [0, 1, 2, 3]:
            sec.ok("bfs_order")
        else:
            sec.fail("bfs_order", str(bfs))
        a = list(sk.traversal.dfs())
        b = list(sk.traversal.dfs())
        sec.ok("deterministic") if a == b else sec.fail("deterministic")
        leaves = set(sk.traversal.leaves())
        sec.ok("leaves", str(leaves)) if leaves == {1, 3} else sec.fail("leaves", str(leaves))
    except Exception as exc:  # noqa: BLE001
        sec.fail("traversal_exception", str(exc))


def certify_validation(ctx: CertificationContext) -> None:
    sec = ctx.section("Validation failures")
    try:
        from motion_engine.rendering.avatar.skeleton import Bone, Transform, validate_bones
        from motion_engine.rendering.avatar.skeleton.transforms import identity_matrix

        empty = validate_bones([])
        sec.ok("empty_error") if not empty.ok else sec.fail("empty_error")

        dup = validate_bones(
            (
                Bone(0, "a", None, world_transform=identity_matrix(), inverse_bind=identity_matrix()),
                Bone(1, "a", 0, world_transform=identity_matrix(), inverse_bind=identity_matrix()),
            )
        )
        sec.ok("dup_name") if any(i.code == "SKEL_DUP_NAME" for i in dup.errors) else sec.fail(
            "dup_name"
        )

        cyc = validate_bones(
            (
                Bone(0, "a", 1, world_transform=identity_matrix(), inverse_bind=identity_matrix()),
                Bone(1, "b", 0, world_transform=identity_matrix(), inverse_bind=identity_matrix()),
            )
        )
        sec.ok("cycle") if any(i.code == "SKEL_CYCLE" for i in cyc.errors) else sec.fail("cycle")

        try:
            AvatarSkeleton.from_bones(
                [
                    Bone(0, "a", 1),
                    Bone(1, "b", 0),
                ],
                validate=True,
            )
            sec.fail("factory_rejects_cycle", "expected raise")
        except SkeletonValidationError:
            sec.ok("factory_rejects_cycle")
    except Exception as exc:  # noqa: BLE001
        sec.fail("validation_exception", str(exc))


def certify_statistics(ctx: CertificationContext) -> None:
    sec = ctx.section("Statistics")
    try:
        sk = AvatarSkeletonFactory().from_imported(make_chain_imported(10))
        st = sk.statistics
        checks = [
            ("bone_count", st.bone_count == 10),
            ("leaf_count", st.leaf_count == 1),
            ("root_count", st.root_count == 1),
            ("depth", st.tree_depth == 9),
            ("no_cycle", st.cycle_count == 0),
        ]
        for name, ok in checks:
            sec.ok(name) if ok else sec.fail(name)
    except Exception as exc:  # noqa: BLE001
        sec.fail("stats_exception", str(exc))


def certify_serialization(ctx: CertificationContext) -> None:
    sec = ctx.section("Serialization")
    try:
        sk = AvatarSkeletonFactory().from_imported(make_tree_imported())
        tree = export_tree(sk)
        sec.ok("tree_export") if "right_leaf" in tree else sec.fail("tree_export")
        raw = export_json(sk)
        sec.ok("json_export") if '"bone_count": 4' in raw or '"bone_count":4' in raw else sec.fail(
            "json_export", raw[:200]
        )
    except Exception as exc:  # noqa: BLE001
        sec.fail("serialization_exception", str(exc))


def certify_performance(ctx: CertificationContext) -> None:
    sec = ctx.section("Performance")
    try:
        sk = AvatarSkeletonFactory().from_imported(make_chain_imported(256))
        t0 = time.perf_counter_ns()
        for _ in range(50_000):
            _ = sk.find("b100")
        lookup_ms = (time.perf_counter_ns() - t0) / 1e6
        sec.ok("lookup_budget", f"{lookup_ms:.2f} ms / 50k") if lookup_ms < 1000 else sec.fail(
            "lookup_budget", f"{lookup_ms:.2f} ms"
        )

        t0 = time.perf_counter_ns()
        for _ in range(100):
            _ = list(sk.traversal.dfs())
        trav_ms = (time.perf_counter_ns() - t0) / 1e6
        sec.ok("traversal_budget", f"{trav_ms:.2f} ms / 100") if trav_ms < 2000 else sec.fail(
            "traversal_budget", f"{trav_ms:.2f} ms"
        )
    except Exception as exc:  # noqa: BLE001
        sec.fail("perf_exception", str(exc))


def certify_architecture(ctx: CertificationContext) -> None:
    sec = ctx.section("Architecture boundaries")
    try:
        pkg = SRC_ROOT / "motion_engine" / "rendering" / "avatar" / "skeleton"
        forbidden = ("motion_engine.studio", "motion_engine.viewer", "PySide6")
        violations: list[str] = []
        for path in pkg.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                mods: list[str] = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                for m in mods:
                    for f in forbidden:
                        if m == f or m.startswith(f + "."):
                            violations.append(f"{path.name}:{m}")
        sec.ok("no_studio_viewer") if not violations else sec.fail(
            "no_studio_viewer", str(violations[:5])
        )

        models_src = (
            SRC_ROOT / "motion_engine" / "rendering" / "avatar" / "models" / "skeleton.py"
        ).read_text(encoding="utf-8")
        sec.ok("no_circular_models") if "rendering.avatar.skeleton" not in models_src else sec.fail(
            "no_circular_models"
        )

        # M1 DTO still distinct
        sec.ok("dto_vs_runtime") if ImportedSkeleton is not AvatarSkeleton else sec.fail(
            "dto_vs_runtime"
        )

        # Required modules exist
        required = [
            "avatar_skeleton.py",
            "bone.py",
            "hierarchy.py",
            "transforms.py",
            "bind_data.py",
            "lookup.py",
            "traversal.py",
            "validation.py",
            "metadata.py",
            "serialization.py",
            "statistics.py",
            "factory.py",
            "constants.py",
            "exceptions.py",
            "types.py",
        ]
        missing = [r for r in required if not (pkg / r).exists()]
        sec.ok("module_layout") if not missing else sec.fail("module_layout", str(missing))
    except Exception as exc:  # noqa: BLE001
        sec.fail("arch_exception", str(exc))


def certify_regression(ctx: CertificationContext) -> None:
    sec = ctx.section("Regression / M1 freeze")
    try:
        fields = set(BoneData.__dataclass_fields__)  # type: ignore[attr-defined]
        needed = {
            "index",
            "name",
            "parent_index",
            "local_translation",
            "bind_world",
            "inverse_bind",
        }
        sec.ok("m1_fields") if needed <= fields else sec.fail("m1_fields", str(fields))

        # Loader path still importable (not modified contract)
        from motion_engine.rendering.avatar.loader.skeleton_loader import SkeletonLoader

        sec.ok("skeleton_loader_import", SkeletonLoader.__name__)

        # Single source of truth: factory produces runtime with queries
        sk = AvatarSkeletonFactory().from_imported(make_chain_imported(5))
        sec.ok("runtime_api") if hasattr(sk, "find") and hasattr(sk, "traversal") else sec.fail(
            "runtime_api"
        )
    except Exception as exc:  # noqa: BLE001
        sec.fail("regression_exception", str(exc))


def main() -> int:
    ctx = CertificationContext()
    certify_hierarchy(ctx)
    certify_lookup(ctx)
    certify_traversal(ctx)
    certify_validation(ctx)
    certify_statistics(ctx)
    certify_serialization(ctx)
    certify_performance(ctx)
    certify_architecture(ctx)
    certify_regression(ctx)
    passed = _print_report(ctx)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
