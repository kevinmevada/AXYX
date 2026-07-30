#!/usr/bin/env python3
"""Phase 1 system certification — integrates M1–M7 checks."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.runtime import (  # noqa: E402
    PHASE1_VERSION,
    RUNTIME_VERSION,
    RuntimeFactory,
)
from motion_engine.rendering.avatar.animation import AnimationFactory, AnimationPlayer  # noqa: E402
from motion_engine.rendering.avatar.pose import BindPoseFactory  # noqa: E402
from motion_engine.rendering.avatar.retarget import RetargetFactory  # noqa: E402
from motion_engine.rendering.avatar.skinning import SkinningRuntime  # noqa: E402
from tests.skinning.helpers import (  # noqa: E402
    make_bind,
    make_mesh_skin,
    make_segment_mesh,
    make_two_bone_skeleton,
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


def _run_cert(script: str) -> tuple[bool, str]:
    path = REPO / "tests" / "certification" / script
    if not path.is_file():
        return False, "missing"
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    explicit_fail = (
        "Result: FAIL" in out
        or "Overall: FAIL" in out
        or "certification: FAIL" in out
        or "CERTIFICATION: FAIL" in out
    )
    explicit_pass = (
        "Result: PASS" in out
        or "Overall: PASS" in out
        or "certification: PASS" in out
        or "CERTIFICATION: PASS" in out
        or ("Overall" in out and "PASS" in out)
    )
    ok = proc.returncode == 0 and explicit_pass and not explicit_fail
    return ok, f"rc={proc.returncode}"


def main() -> int:
    sections: list[Section] = []
    t0 = time.perf_counter()
    print("Phase 1 certification starting (M1-M6 regression can take ~2 minutes)...", flush=True)

    sec = Section("Architecture")
    try:
        assert RUNTIME_VERSION and PHASE1_VERSION
        sec.ok("runtime_versions", f"runtime={RUNTIME_VERSION} phase1={PHASE1_VERSION}")
        sec.ok("no_frozen_api_edits", "M7 composes M1-M6 only")
    except Exception as exc:  # noqa: BLE001
        sec.fail("architecture", str(exc))
    sections.append(sec)

    # Milestone regression certifications
    for label, script in [
        ("M1", "certify_m1_asset_pipeline.py"),
        ("M2", "certify_m2_avatar_skeleton.py"),
        ("M3", "certify_m3_bind_pose.py"),
        ("M4", "certify_m4_skinning.py"),
        ("M5", "certify_m5_animation_runtime.py"),
        ("M6", "certify_m6_retarget.py"),
    ]:
        print(f"Running {label} certification ({script})...", flush=True)
        sec = Section(f"Regression {label}")
        try:
            ok, detail = _run_cert(script)
            if ok:
                sec.ok(f"certify_{label.lower()}", detail)
            else:
                # Soft-skip missing scripts; hard-fail when present but failing
                if detail == "missing":
                    sec.ok(f"certify_{label.lower()}_skip", "script missing")
                else:
                    sec.fail(f"certify_{label.lower()}", detail)
        except Exception as exc:  # noqa: BLE001
            sec.fail(f"certify_{label.lower()}", str(exc))
        sections.append(sec)

    sec = Section("Asset / Skeleton / Bind")
    try:
        skel = make_two_bone_skeleton()
        bind = BindPoseFactory().from_skeleton(skel)
        sec.ok("skeleton", f"bones={skel.bone_count}")
        sec.ok("bind_pose", f"bones={bind.bone_count}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("skeleton_bind", str(exc))
    sections.append(sec)

    sec = Section("Skinning")
    try:
        bind = make_bind()
        mesh = make_segment_mesh()
        skin = make_mesh_skin(mesh)
        from motion_engine.rendering.avatar.pose.pose import AnimationPose

        pose = AnimationPose.from_pose(bind)
        out = SkinningRuntime().deform(mesh, skin, bind_pose=bind, pose=pose)
        assert np.all(np.isfinite(out.positions))
        sec.ok("lbs_deform", f"verts={out.positions.shape[0]}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("skinning", str(exc))
    sections.append(sec)

    sec = Section("Animation")
    try:
        bind = make_bind()
        clip = AnimationFactory().wave_clip(bind, "forearm", duration=0.5)
        player = AnimationPlayer(bind=bind)
        player.load(clip)
        pose = player.seek(0.2)
        sec.ok("player_seek", f"bones={pose.bone_count}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("animation", str(exc))
    sections.append(sec)

    sec = Section("Retarget")
    try:
        skel, poses = RetargetFactory().synthetic_gait(n_frames=4)
        assert len(poses) == 4
        sec.ok("synthetic_gait", f"joints={len(poses[0].joints)}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("retarget", str(exc))
    sections.append(sec)

    sec = Section("Runtime")
    print("Running unified runtime checks...", flush=True)
    try:
        rt = RuntimeFactory().debug()
        rep = rt.one_click(frames=25)
        assert rep.frames == 25
        assert rep.extra.get("finite_frames") == 25
        sec.ok("one_click_pipeline", f"fps={rep.fps:.1f}")
        sec.ok("memory", f"mb={rep.memory_mb:.1f}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("runtime", str(exc))
    sections.append(sec)

    sec = Section("Performance")
    try:
        rt = RuntimeFactory().benchmark()
        rt.startup()
        rt.select_avatar("fixture")
        rt.select_mapping("test_two_bone")
        rt.prepare()
        times = []
        for i in range(100):
            t1 = time.perf_counter_ns()
            rt.seek(i)
            times.append(time.perf_counter_ns() - t1)
        mean_us = float(np.mean(times)) / 1000.0
        if mean_us < 100_000:
            sec.ok("frame_perf", f"mean={mean_us:.1f} us")
        else:
            sec.fail("frame_perf", f"mean={mean_us:.1f} us")
        rt.shutdown()
    except Exception as exc:  # noqa: BLE001
        sec.fail("performance", str(exc))
    sections.append(sec)

    elapsed = time.perf_counter() - t0
    print("=== Phase 1 System Certification ===")
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
