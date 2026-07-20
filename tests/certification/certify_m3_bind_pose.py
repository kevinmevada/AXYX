#!/usr/bin/env python3
"""AXYX Phase 1 — Milestone 3 Bind Pose Certification.

Execute::

    python tests/certification/certify_m3_bind_pose.py

Exit: 0 PASS / 1 FAIL
"""

from __future__ import annotations

import ast
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motion_engine.rendering.avatar.pose import (  # noqa: E402
    AnimationPose,
    BindPose,
    BindPoseFactory,
    Pose,
    PoseKind,
    export_json,
    validate_pose,
)
from motion_engine.rendering.avatar.pose.transform_propagation import (  # noqa: E402
    verify_propagation,
)
from tests.pose.helpers import make_chain_skeleton, make_tree_skeleton  # noqa: E402


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


def _report(ctx: CertificationContext) -> bool:
    overall = all(s.passed for s in ctx.sections) and bool(ctx.sections)
    print("=" * 72)
    print("AXYX M3 Bind Pose Certification")
    print("=" * 72)
    for sec in ctx.sections:
        status = "PASS" if sec.passed else "FAIL"
        print(f"\n[{status}] {sec.name}")
        for c in sec.checks:
            mark = "OK  " if c.passed else "FAIL"
            detail = f" — {c.detail}" if c.detail else ""
            print(f"  {mark} {c.name}{detail}")
    print("\n" + "=" * 72)
    print(f"Overall: {'PASS' if overall else 'FAIL'}  ({time.perf_counter() - ctx.started:.2f}s)")
    print("=" * 72)
    return overall


def certify_bind_pose(ctx: CertificationContext) -> None:
    sec = ctx.section("Bind pose correctness")
    try:
        sk = make_tree_skeleton()
        pose = BindPoseFactory().from_skeleton(sk)
        sec.ok("isinstance_pose") if isinstance(pose, Pose) else sec.fail("isinstance_pose")
        sec.ok("kind_bind") if pose.kind is PoseKind.BIND else sec.fail("kind_bind")
        sec.ok("bone_count") if pose.bone_count == sk.bone_count else sec.fail("bone_count")
        sec.ok("immutable") if isinstance(pose, BindPose) and isinstance(pose.bones, tuple) else sec.fail(
            "immutable"
        )
        anim = AnimationPose.from_pose(pose)
        sec.ok("animation_placeholder") if anim.kind is PoseKind.ANIMATION else sec.fail(
            "animation_placeholder"
        )
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", f"{exc}\n{traceback.format_exc()}")


def certify_world(ctx: CertificationContext) -> None:
    sec = ctx.section("World transforms")
    try:
        pose = BindPoseFactory().from_skeleton(make_chain_skeleton(5))
        sec.ok("root_origin") if pose.world_position("root") == (0.0, 0.0, 0.0) else sec.fail(
            "root_origin", str(pose.world_position("root"))
        )
        x = pose.world_position("b4")[0]
        sec.ok("chain_end", f"x={x}") if abs(x - 4.0) < 1e-6 else sec.fail("chain_end", str(x))
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_ibm(ctx: CertificationContext) -> None:
    sec = ctx.section("Matrix inversion / IBM")
    try:
        pose = BindPoseFactory().from_skeleton(make_chain_skeleton(8))
        ok = True
        for b in pose:
            if not np.allclose(b.inverse_bind_matrix @ b.rest_matrix, np.eye(4), atol=1e-5):
                ok = False
                break
        sec.ok("ibm_inverts_rest") if ok else sec.fail("ibm_inverts_rest")
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_propagation(ctx: CertificationContext) -> None:
    sec = ctx.section("Propagation")
    try:
        pose = BindPoseFactory().from_skeleton(make_tree_skeleton())
        bad = verify_propagation(
            [b.local_matrix for b in pose],
            [b.global_matrix for b in pose],
            [b.parent_index for b in pose],
        )
        sec.ok("fk_consistent") if bad == [] else sec.fail("fk_consistent", str(bad))
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_validation(ctx: CertificationContext) -> None:
    sec = ctx.section("Validation")
    try:
        pose = BindPoseFactory().from_skeleton(make_chain_skeleton(6))
        report = validate_pose(pose)
        sec.ok("valid_ok") if report.ok else sec.fail("valid_ok", str(report.errors))
        empty = AnimationPose(_name="e", _bones=[])
        er = validate_pose(empty)
        sec.ok("empty_fails") if not er.ok else sec.fail("empty_fails")
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_serialization(ctx: CertificationContext) -> None:
    sec = ctx.section("Serialization")
    try:
        pose = BindPoseFactory().from_skeleton(make_tree_skeleton())
        raw = export_json(pose)
        sec.ok("json") if '"kind": "bind"' in raw or '"kind":"bind"' in raw else sec.fail(
            "json", raw[:120]
        )
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_statistics(ctx: CertificationContext) -> None:
    sec = ctx.section("Statistics")
    try:
        pose = BindPoseFactory().from_skeleton(make_chain_skeleton(10))
        st = pose.statistics
        sec.ok("bone_count") if st.bone_count == 10 else sec.fail("bone_count")
        sec.ok("depth") if st.hierarchy_depth == 9 else sec.fail("depth", str(st.hierarchy_depth))
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_performance(ctx: CertificationContext) -> None:
    sec = ctx.section("Performance")
    try:
        pose = BindPoseFactory().from_skeleton(make_chain_skeleton(256))
        t0 = time.perf_counter_ns()
        for _ in range(50_000):
            _ = pose.find("b100")
        ms = (time.perf_counter_ns() - t0) / 1e6
        sec.ok("lookup_budget", f"{ms:.2f} ms") if ms < 1000 else sec.fail("lookup_budget", f"{ms}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_architecture(ctx: CertificationContext) -> None:
    sec = ctx.section("Architecture")
    try:
        pkg = SRC_ROOT / "motion_engine" / "rendering" / "avatar" / "pose"
        required = [
            "bind_pose.py",
            "pose.py",
            "pose_factory.py",
            "pose_validation.py",
            "pose_statistics.py",
            "pose_serialization.py",
            "transform_propagation.py",
            "matrix_utils.py",
            "coordinate_system.py",
            "rest_pose.py",
            "bind_matrix.py",
            "pose_cache.py",
            "constants.py",
            "exceptions.py",
            "types.py",
        ]
        missing = [r for r in required if not (pkg / r).exists()]
        sec.ok("modules") if not missing else sec.fail("modules", str(missing))

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
        sec.ok("no_studio_viewer") if not violations else sec.fail("no_studio_viewer", str(violations))

        # skeleton must not import pose
        skel = SRC_ROOT / "motion_engine" / "rendering" / "avatar" / "skeleton"
        circular = False
        for path in skel.rglob("*.py"):
            if "rendering.avatar.pose" in path.read_text(encoding="utf-8"):
                circular = True
                break
        sec.ok("no_circular") if not circular else sec.fail("no_circular")
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def certify_regression(ctx: CertificationContext) -> None:
    sec = ctx.section("Regression")
    try:
        from motion_engine.rendering.avatar.bind_pose import BindPose as LegacyBindPose
        from motion_engine.rendering.avatar.skeleton import AvatarSkeleton

        sec.ok("legacy_distinct") if LegacyBindPose is not BindPose else sec.fail("legacy_distinct")
        sk = make_chain_skeleton(4)
        BindPoseFactory().from_skeleton(sk)
        sec.ok("skeleton_intact") if isinstance(sk, AvatarSkeleton) and sk.find("root") else sec.fail(
            "skeleton_intact"
        )
    except Exception as exc:  # noqa: BLE001
        sec.fail("exception", str(exc))


def main() -> int:
    ctx = CertificationContext()
    certify_bind_pose(ctx)
    certify_world(ctx)
    certify_ibm(ctx)
    certify_propagation(ctx)
    certify_validation(ctx)
    certify_serialization(ctx)
    certify_statistics(ctx)
    certify_performance(ctx)
    certify_architecture(ctx)
    certify_regression(ctx)
    return 0 if _report(ctx) else 1


if __name__ == "__main__":
    raise SystemExit(main())
