#!/usr/bin/env python3
"""Smoke test: Army Girl avatar retarget + skin from clinical MATLAB gait.

Run::

    python -m experiments.avatar_smoke_test
    python -m experiments.avatar_smoke_test --subject S11 --session WU02
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "src"), str(REPO)]

from motion_engine.animation_clip import AnimationClip  # noqa: E402
from motion_engine.rendering.avatar.retarget import RetargetFactory, RootMotionMode  # noqa: E402
from motion_engine.rendering.avatar.retarget.motion_converter import MotionConverter  # noqa: E402
from motion_engine.rendering.avatar.skinning import SkinningRuntime  # noqa: E402
from motion_engine.rendering.runtime._assets import load_army_girl_avatar  # noqa: E402
from motion_engine.rendering.runtime.studio_viewport import DigitalTwinViewportBridge  # noqa: E402
from motion_engine.studio.services.motion_service import MotionService  # noqa: E402


def _fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Avatar pipeline smoke test")
    parser.add_argument("--subject", default="S11")
    parser.add_argument("--session", default="WU02")
    args = parser.parse_args(argv)

    print("=" * 60)
    print("AXYX Avatar Smoke Test")
    print("=" * 60)

    svc = MotionService()
    svc.load_database()
    sk, _ = svc.load_session(args.subject, args.session, build_clip=True)
    print(f"Session {args.subject}/{args.session}: {sk.n_frames} frames")
    is_calibration = "static" in args.session.lower() or "calib" in args.session.lower()

    # Bind pose sanity
    av, bind, mesh, skin = load_army_girl_avatar()
    from motion_engine.rendering.avatar.skinning.debug.pose_edit import reset_to_bind

    bind_pose = reset_to_bind(bind)
    bind_pts = np.asarray(
        SkinningRuntime().deform(mesh, skin, bind_pose=bind, pose=bind_pose).positions
    )
    bind_h = float(np.ptp(bind_pts[:, 2]))
    print(f"Bind mesh height (Z): {bind_h:.1f}")
    if bind_h < 50:
        return _fail(f"Bind pose height too small ({bind_h:.1f})")

    # Retarget gait check (walking trials only — calibration breaks retarget)
    if not is_calibration:
        clip = AnimationClip.from_skeleton(sk)
        motions = MotionConverter().from_clip_frames(clip)
        factory = RetargetFactory()

        def head_foot_gap(root_mode: RootMotionMode) -> float:
            eng = factory.engine("matlab_clinical_to_army_girl", root_mode=root_mode)
            ctx = eng.prepare(factory.clinical_skeleton(), av, bind, rest_pose=motions[0])
            sess = eng.create_session(ctx)
            pose = eng.retarget(motions[0], ctx, session=sess)
            head = pose.find("head").global_matrix[:3, 3]
            foot = pose.find("foot_l").global_matrix[:3, 3]
            return float(head[2] - foot[2])

        world_gap = head_foot_gap(RootMotionMode.WORLD)
        inplace_gap = head_foot_gap(RootMotionMode.IN_PLACE)
        print(f"Head-foot Z gap  WORLD: {world_gap:.1f}  IN_PLACE: {inplace_gap:.1f}")
        if inplace_gap < 15:
            return _fail(f"IN_PLACE head-foot gap too small ({inplace_gap:.1f})")
        if abs(world_gap) < 5:
            print("  (WORLD mode collapses gait — Studio uses IN_PLACE)")

    # Studio bridge
    bridge = DigitalTwinViewportBridge()
    if not bridge.prepare(sk):
        return _fail(bridge.error or "bridge prepare failed")

    if bridge.use_bind_pose:
        print("Session type: calibration/static → avatar uses neutral bind pose")

    mesh0, lm0 = bridge.frame_package(0)
    if mesh0 is None:
        return _fail("frame 0 mesh missing")
    h0 = float(np.ptp(mesh0[:, 2]))
    print(f"Studio frame 0 height: {h0:.1f}  scale: {bridge._stage_scale:.2f}")
    if h0 < 800:
        return _fail(f"Displayed height too small ({h0:.1f})")

    head = lm0.get("head")
    foot = lm0.get("foot_l")
    if foot is None:
        foot = lm0.get("ball_l")
    if head is None or foot is None:
        return _fail("Missing head/foot landmarks")
    print(f"Landmarks  head Z={head[2]:.0f}  foot Z={foot[2]:.0f}")
    if head[2] <= foot[2]:
        return _fail("Head should be above feet")

    if is_calibration:
        if not bridge.use_bind_pose:
            return _fail("Calibration session should use bind pose")
        print("PASS — calibration shows neutral bind pose")
        return 0

    mesh50, _ = bridge.frame_package(50)
    if mesh50 is None:
        return _fail("frame 50 mesh missing")
    travel = float(np.linalg.norm(mesh50.mean(0) - mesh0.mean(0)))
    print(f"Frame 0→50 root travel: {travel:.1f}")
    print("PASS — avatar pipeline looks sane")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
