#!/usr/bin/env python3
"""M4 Skinning certification harness."""

from __future__ import annotations

import ast
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.avatar.skinning import (  # noqa: E402
    SkinningAlgorithm,
    SkinningNotSupportedError,
    SkinningRuntime,
    build_matrix_palette,
)
from tests.skinning.helpers import (  # noqa: E402
    make_bind,
    make_mesh_skin,
    make_segment_mesh,
    rotate_forearm,
)


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

    # deformation
    sec = Section("Correct deformation")
    mesh, bind = make_segment_mesh(8), make_bind()
    skin = make_mesh_skin(mesh)
    rt = SkinningRuntime()
    out = rt.deform(mesh, skin, bind_pose=bind)
    sec.ok("bind_identity") if np.allclose(out.positions, mesh.positions, atol=1e-4) else sec.fail(
        "bind_identity"
    )
    bent = rt.deform(mesh, skin, pose=rotate_forearm(bind, 90))
    sec.ok("bent_moves") if not np.allclose(bent.positions[-1], mesh.positions[-1], atol=1e-3) else sec.fail(
        "bent_moves"
    )
    sec.ok("finite") if np.all(np.isfinite(bent.positions)) else sec.fail("finite")
    sections.append(sec)

    # matrices
    sec = Section("Correct matrices")
    pal = build_matrix_palette(bind)
    sec.ok("bind_skin_I") if all(np.allclose(m, np.eye(4), atol=1e-5) for m in pal.matrices) else sec.fail(
        "bind_skin_I"
    )
    sections.append(sec)

    # weights / validation covered by deform validate
    sec = Section("Weight normalization")
    from motion_engine.rendering.avatar.skinning import NormalizationMode, normalize_weights
    from motion_engine.rendering.avatar.skinning import WeightTable

    t = WeightTable.from_arrays(
        np.array([[0, 1, -1, -1]], np.int32),
        np.array([[1.0, 1.0, 0, 0]], np.float32),
    )
    n = normalize_weights(t)
    sec.ok("auto_unit") if abs(float(n.joint_weights[0, :2].sum()) - 1.0) < 1e-5 else sec.fail("auto_unit")
    sections.append(sec)

    # perf
    sec = Section("Performance")
    big = make_segment_mesh(512)
    big_skin = make_mesh_skin(big)
    t1 = time.perf_counter_ns()
    for _ in range(20):
        rt.deform(big, big_skin, bind_pose=bind)
    ms = (time.perf_counter_ns() - t1) / 1e6
    sec.ok("skin_budget", f"{ms:.1f} ms / 20") if ms < 5000 else sec.fail("skin_budget", str(ms))
    sections.append(sec)

    # validation / dqs
    sec = Section("Validation / extensibility")
    try:
        SkinningRuntime(algorithm=SkinningAlgorithm.DUAL_QUATERNION).deform(mesh, skin, bind_pose=bind)
        sec.fail("dqs_raises")
    except SkinningNotSupportedError:
        sec.ok("dqs_raises")
    sections.append(sec)

    # architecture
    sec = Section("Architecture")
    pkg = REPO / "src" / "motion_engine" / "rendering" / "avatar" / "skinning"
    required = [
        "skinning_runtime.py",
        "linear_blend_skinning.py",
        "mesh_skin.py",
        "weight_table.py",
        "factory.py",
        "cpu_skinner.py",
        "gpu_interface.py",
    ]
    missing = [r for r in required if not (pkg / r).exists()]
    sec.ok("modules") if not missing else sec.fail("modules", str(missing))
    viol = []
    for path in pkg.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                for f in ("motion_engine.studio", "motion_engine.viewer", "PySide6"):
                    if m == f or m.startswith(f + "."):
                        viol.append(f"{path.name}:{m}")
    sec.ok("no_studio") if not viol else sec.fail("no_studio", str(viol))
    sections.append(sec)

    # regression
    sec = Section("Regression")
    before = mesh.positions.copy()
    rt.deform(mesh, skin, bind_pose=bind)
    sec.ok("source_immutable") if np.allclose(mesh.positions, before) else sec.fail("source_immutable")
    sections.append(sec)

    overall = all(s.passed for s in sections)
    print("=" * 72)
    print("AXYX M4 Skinning Certification")
    print("=" * 72)
    for s in sections:
        print(f"\n[{'PASS' if s.passed else 'FAIL'}] {s.name}")
        for c in s.checks:
            print(f"  {'OK  ' if c.passed else 'FAIL'} {c.name}" + (f" — {c.detail}" if c.detail else ""))
    print("\n" + "=" * 72)
    print(f"Overall: {'PASS' if overall else 'FAIL'}  ({time.perf_counter() - t0:.2f}s)")
    print("=" * 72)
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
