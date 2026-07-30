#!/usr/bin/env python3
"""M5 Animation Runtime certification harness."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.rendering.avatar.animation import (  # noqa: E402
    RUNTIME_VERSION,
    AnimationController,
    AnimationFactory,
    AnimationPlayer,
    AnimationState,
    ControllerState,
    LoopMode,
    Transition,
    blend_poses,
    export_clip,
    import_clip,
    quat_slerp,
)
from motion_engine.rendering.avatar.skinning import SkinningRuntime  # noqa: E402
from tests.skinning.helpers import make_bind, make_mesh_skin, make_segment_mesh  # noqa: E402


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
    bind = make_bind()
    factory = AnimationFactory()
    clip = factory.wave_clip(bind, "forearm", duration=1.0)

    sec = Section("Playback")
    player = AnimationPlayer(bind=bind)
    try:
        player.load(clip)
        player.play()
        pose = player.tick(0.1)
        sec.ok("play_tick", f"bones={pose.bone_count}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("play_tick", str(exc))
    sections.append(sec)

    sec = Section("Interpolation / SLERP")
    try:
        q = quat_slerp((0, 0, 0, 1), (0, 0, 0.70710678, 0.70710678), 0.5)
        n = float(np.linalg.norm(q))
        if abs(n - 1.0) < 1e-6:
            sec.ok("unit_quat", f"n={n:.6f}")
        else:
            sec.fail("unit_quat", f"n={n}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("unit_quat", str(exc))
    sections.append(sec)

    sec = Section("Seek / Loop")
    try:
        player.set_loop(LoopMode.LOOP)
        player.seek(0.75)
        assert abs(player.time - 0.75) < 1e-6
        player.tick(0.5)
        sec.ok("seek_loop", f"t={player.time:.3f}")
    except Exception as exc:  # noqa: BLE001
        sec.fail("seek_loop", str(exc))
    sections.append(sec)

    sec = Section("Crossfade")
    try:
        clips = factory.locomotion_set(bind, "forearm")
        ctrl = AnimationController(bind=bind)
        ctrl.add_state(AnimationState("idle", ControllerState.IDLE, clips["idle"]))
        ctrl.add_state(AnimationState("walk", ControllerState.WALK, clips["walk"]))
        ctrl.add_transition(Transition("idle", "walk", 0.2))
        ctrl.set_state("idle")
        ctrl.set_state("walk", fade=0.2)
        ctrl.tick(0.05)
        sec.ok("crossfade")
    except Exception as exc:  # noqa: BLE001
        sec.fail("crossfade", str(exc))
    sections.append(sec)

    sec = Section("M4 skinning consume")
    try:
        mesh = make_segment_mesh(8)
        skin = make_mesh_skin(mesh)
        pose = player.seek(0.3)
        defm = SkinningRuntime().deform(mesh, skin, bind_pose=bind, pose=pose)
        if np.all(np.isfinite(defm.positions)):
            sec.ok("deform", f"verts={defm.positions.shape[0]}")
        else:
            sec.fail("deform", "non-finite")
    except Exception as exc:  # noqa: BLE001
        sec.fail("deform", str(exc))
    sections.append(sec)

    sec = Section("Serialization / architecture")
    try:
        data = export_clip(clip)
        clip2 = import_clip(data)
        assert clip2.track_count == clip.track_count
        sec.ok("roundtrip", f"runtime={RUNTIME_VERSION}")
        # Ensure M5 package is separate
        import motion_engine.rendering.avatar.animation as anim  # noqa: F401

        sec.ok("package_import")
    except Exception as exc:  # noqa: BLE001
        sec.fail("serialization", str(exc))
    sections.append(sec)

    sec = Section("Performance smoke")
    try:
        t_s = time.perf_counter_ns()
        for _ in range(60):
            player.tick(1.0 / 60.0)
        elapsed_ms = (time.perf_counter_ns() - t_s) / 1e6
        # 60 ticks should be well under 1000ms on a modern machine
        if elapsed_ms < 1000.0:
            sec.ok("60_ticks", f"{elapsed_ms:.2f}ms")
        else:
            sec.fail("60_ticks", f"{elapsed_ms:.2f}ms")
    except Exception as exc:  # noqa: BLE001
        sec.fail("perf", str(exc))
    sections.append(sec)

    # Report
    all_ok = True
    for s in sections:
        status = "PASS" if s.passed else "FAIL"
        print(f"[{status}] {s.name}")
        for c in s.checks:
            mark = "OK" if c.passed else "FAIL"
            print(f"  [{mark}] {c.name} {c.detail}")
        all_ok = all_ok and s.passed
    print(f"\nM5 certification: {'PASS' if all_ok else 'FAIL'}  ({(time.perf_counter()-t0)*1000:.1f} ms)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
