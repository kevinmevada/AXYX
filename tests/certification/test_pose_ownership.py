#!/usr/bin/env python3
"""Ownership certification for BindPose ↔ AnimationPose isolation.

Execute::

    python tests/certification/test_pose_ownership.py

Exit: 0 PASS / 1 FAIL
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motion_engine.rendering.avatar.pose import AnimationPose, BindPoseFactory  # noqa: E402
from tests.pose.helpers import make_chain_skeleton, make_tree_skeleton  # noqa: E402


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def _check_pair(bind_name: str, bind, anim) -> None:
    if bind.bone_count != anim.bone_count:
        _fail(f"{bind_name}: bone_count mismatch")
    for i in range(bind.bone_count):
        bb = bind.bones[i]
        ab = anim.bones[i]
        if ab is bb:
            _fail(f"{bind_name}: shared BonePose at index {i}")
        for label, a, b in (
            ("local", ab.local_matrix, bb.local_matrix),
            ("global", ab.global_matrix, bb.global_matrix),
            ("rest", ab.rest_matrix, bb.rest_matrix),
            ("ibm", ab.inverse_bind_matrix, bb.inverse_bind_matrix),
        ):
            if a is b:
                _fail(f"{bind_name}: shared {label} ndarray at index {i}")
        if ab.metadata is bb.metadata:
            _fail(f"{bind_name}: shared metadata mapping at index {i}")

    # Mutate animation; bind must stay identical.
    snapshots = [
        (
            b.local_matrix.copy(),
            b.global_matrix.copy(),
            b.rest_matrix.copy(),
            b.inverse_bind_matrix.copy(),
            dict(b.metadata),
        )
        for b in bind.bones
    ]
    for i, b in enumerate(anim.bones):
        b.local_matrix.fill(0.0)
        b.global_matrix.fill(1.0)
        b.rest_matrix.fill(2.0)
        b.inverse_bind_matrix.fill(3.0)
        b.metadata["ownership_probe"] = i
    for i, (lm, gm, rm, ibm, meta) in enumerate(snapshots):
        b = bind.bones[i]
        if not np.allclose(b.local_matrix, lm):
            _fail(f"{bind_name}: bind local mutated via animation at {i}")
        if not np.allclose(b.global_matrix, gm):
            _fail(f"{bind_name}: bind global mutated via animation at {i}")
        if not np.allclose(b.rest_matrix, rm):
            _fail(f"{bind_name}: bind rest mutated via animation at {i}")
        if not np.allclose(b.inverse_bind_matrix, ibm):
            _fail(f"{bind_name}: bind ibm mutated via animation at {i}")
        if b.metadata != meta or "ownership_probe" in b.metadata:
            _fail(f"{bind_name}: bind metadata mutated via animation at {i}")


def main() -> int:
    print("AXYX Pose Ownership Certification")
    factory = BindPoseFactory()
    for label, sk in (
        ("chain", make_chain_skeleton(8)),
        ("tree", make_tree_skeleton()),
    ):
        bind = factory.from_skeleton(sk)
        anim = AnimationPose.from_pose(bind)
        _check_pair(label, bind, anim)
        print(f"  OK  {label} ({bind.bone_count} bones)")
    print("Overall: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
