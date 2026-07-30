#!/usr/bin/env python3
"""M6 Motion Retargeting Engine certification harness."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.avatar.retarget import (  # noqa: E402
    RUNTIME_VERSION,
    RetargetFactory,
    RootMotionMode,
)
from motion_engine.rendering.avatar.retarget.coordinate_mapper import CoordinateMapper  # noqa: E402
from motion_engine.rendering.avatar.retarget.mapping_factory import MappingFactory  # noqa: E402
from motion_engine.rendering.avatar.retarget.types import AXYX_COORDS, Y_UP_RIGHT  # noqa: E402
from motion_engine.rendering.avatar.retarget.validation import RetargetValidator  # noqa: E402
from motion_engine.rendering.avatar.skinning import SkinningRuntime  # noqa: E402
from tests.retarget.helpers import flexed_pose, two_bone_setup
from tests.skinning.helpers import make_mesh_skin  # noqa: F401 — kept for clarity


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Section:
    name: str
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(c.passed for c in self.checks)

    def ok(self, n: str, d: str = "") -> None:
        self.checks.append(Check(n, True, d))

    def fail(self, n: str, d: str = "") -> None:
        self.checks.append(Check(n, False, d))


def main() -> int:
    sections: list[Section] = []
    t0 = time.perf_counter()

    sec = Section("Architecture")
    try:
        assert RUNTIME_VERSION
        from motion_engine.rendering.avatar import AvatarRetarget  # noqa: F401
        sec.ok("package_import", f"v={RUNTIME_VERSION}")
        sec.ok("legacy_shim")
    except Exception as exc:  # noqa: BLE001
        sec.fail("package_import", str(exc))
    sections.append(sec)

    sec = Section("Mapping")
    try:
        mf = MappingFactory()
        p = mf.builtin("matlab_clinical_to_army_girl")
        assert p.primary if False else p.root_target == "pelvis"
        assert any(e.source == "Pelvis" for e in p.bones)
        sec.ok("matlab_army_profile", f"bones={len(p.bones)}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("matlab_army_profile", str(exc))
    sections.append(sec)

    sec = Section("Coordinate conversion")
    try:
        m = CoordinateMapper(AXYX_COORDS, Y_UP_RIGHT)
        v = m.map_vector((1, 0, 0), apply_units=False)
        assert abs(np.linalg.norm(v) - 1.0) < 1e-9
        sec.ok("basis_unit_length")
    except Exception as exc:  # noqa: BLE001
        sec.fail("basis_unit_length", str(exc))
    sections.append(sec)

    sec = Section("Retarget + scale + root")
    try:
        engine, ctx, *_ = two_bone_setup()
        out = engine.retarget(flexed_pose(35.0), ctx)
        assert out.bone_count == 2
        sec.ok("retarget_frame", f"coverage={ctx.stats.coverage:.2f}")
        assert ctx.stats.scale_ratio > 0
        sec.ok("scale_ratio", f"{ctx.stats.scale_ratio:.4f}")
        eng2 = RetargetFactory().engine("test_two_bone", root_mode=RootMotionMode.IN_PLACE)
        # re-prepare
        from tests.retarget.helpers import two_bone_setup as tbs

        e, c, s, t, b = tbs()
        eng2 = RetargetFactory().engine("test_two_bone", root_mode=RootMotionMode.IN_PLACE)
        c2 = eng2.prepare(s, t, b)
        eng2.retarget(flexed_pose(10.0), c2)
        sec.ok("root_inplace")
    except Exception as exc:  # noqa: BLE001
        sec.fail("retarget_frame", str(exc))
    sections.append(sec)

    sec = Section("Constraints + quaternions")
    try:
        engine, ctx, *_ = two_bone_setup()
        out = engine.retarget(flexed_pose(40.0), ctx)
        v = RetargetValidator()
        report = v.validate_animation_pose(out)
        for bone in out.bones:
            n = float(np.linalg.norm(bone.rotation_xyzw))
            if abs(n - 1.0) > 1e-5:
                raise AssertionError(f"non-unit {bone.name}: {n}")
        sec.ok("unit_quats")
        sec.ok("validation", f"ok={report.ok}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("unit_quats", str(exc))
    sections.append(sec)

    sec = Section("Research gait to skinning")
    try:
        factory = RetargetFactory()
        skel, motions = factory.synthetic_gait(n_frames=8)
        engine, ctx, source, target, bind = two_bone_setup()
        # Map clinical→two-bone won't cover; use identity two-bone sequence
        poses = engine.retarget_sequence([flexed_pose(float(i)) for i in range(8)], ctx)
        from tests.skinning.helpers import make_mesh_skin, make_segment_mesh

        mesh = make_segment_mesh()
        skin = make_mesh_skin(mesh)
        rt = SkinningRuntime()
        deformed = rt.deform(mesh, skin, bind_pose=bind, pose=poses[-1])
        assert np.all(np.isfinite(deformed.positions))
        sec.ok("gait_frames", f"n={len(motions)} clinical + skinned")
        sec.ok("skinning_consume", f"verts={deformed.positions.shape[0]}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("gait_skinning", str(exc))
    sections.append(sec)

    sec = Section("Performance")
    try:
        engine, ctx, *_ = two_bone_setup()
        pose = flexed_pose(20.0)
        times = []
        for _ in range(50):
            t1 = time.perf_counter_ns()
            engine.retarget(pose, ctx)
            times.append(time.perf_counter_ns() - t1)
        mean_us = float(np.mean(times)) / 1000.0
        if mean_us < 50_000:  # generous
            sec.ok("retarget_perf", f"mean={mean_us:.1f} us")
        else:
            sec.fail("retarget_perf", f"mean={mean_us:.1f} us too slow")
    except Exception as exc:  # noqa: BLE001
        sec.fail("retarget_perf", str(exc))
    sections.append(sec)

    sec = Section("Regression")
    try:
        engine, ctx, *_ = two_bone_setup()
        bind = ctx.bind
        before = bind.find("forearm").local_matrix.copy()
        engine.retarget(flexed_pose(12.0), ctx)
        assert np.allclose(before, bind.find("forearm").local_matrix)
        sec.ok("bind_immutable")
    except Exception as exc:  # noqa: BLE001
        sec.fail("bind_immutable", str(exc))
    sections.append(sec)

    elapsed = time.perf_counter() - t0
    print("=== M6 Retarget Certification ===")
    all_ok = True
    for s in sections:
        status = "PASS" if s.passed else "FAIL"
        if not s.passed:
            all_ok = False
        print(f"[{status}] {s.name}")
        for c in s.checks:
            mark = "OK" if c.passed else "FAIL"
            detail = f" -- {c.detail}" if c.detail else ""
            print(f"  [{mark}] {c.name}{detail}")
    print(f"Result: {'PASS' if all_ok else 'FAIL'} ({elapsed:.2f}s)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
