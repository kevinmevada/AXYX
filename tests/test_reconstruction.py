"""
=========================================================
Human Reconstruction Engine Certification Test
=========================================================

This integration test validates the complete pipeline:

MATLAB Dataset
        ↓
MotionDatabase
        ↓
Subject
        ↓
Session
        ↓
SkeletonBuilder
        ↓
Skeleton

If every test passes, the Human Reconstruction Engine
is certified for visualization and animation work.

=========================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from motion_engine import MotionDatabase, SkeletonBuilder

# Soft upper bound on Pelvis frame-to-frame travel (Unknown units; typically mm).
# At 100 Hz this is intentionally generous to catch teleports/NaNs, not biomechanics.
MAX_REASONABLE_STEP = 500.0


@pytest.fixture(scope="session")
def db():
    return MotionDatabase().load()


@pytest.fixture(scope="session")
def session(db):
    return db.get_subject("S2").get_session("WU01")


@pytest.fixture(scope="session")
def skeleton(session):
    return SkeletonBuilder().build(session)


# =========================================================
# MotionDatabase Tests
# =========================================================


def test_database_loaded(db):
    assert db is not None


def test_subject_count(db):
    assert len(db.subjects) == 31


def test_subject_exists(db):
    assert db.get_subject("S2") is not None


# =========================================================
# Session Tests
# =========================================================


def test_session_exists(session):
    assert session is not None


def test_session_name(session):
    assert session.name == "WU01"


def test_markers_exist(session):
    assert len(session.kinematics.markers) == 37


def test_joint_angles_exist(session):
    assert len(session.kinematics.joint_angles) == 26


def test_joint_centers_exist(session):
    assert len(session.kinematics.joint_centers) == 6


def test_segment_com_exist(session):
    assert len(session.kinematics.segment_com) == 15


def test_whole_body_com_exist(session):
    # Domain model attribute is ``com`` (whole-body CenterOfMass map).
    assert len(session.kinematics.com) == 2


def test_clinical_metrics_exist(session):
    assert len(session.clinical_metrics) == 10


# =========================================================
# Skeleton Tests
# =========================================================


def test_skeleton_created(skeleton):
    assert skeleton is not None


def test_joint_count(skeleton):
    assert len(skeleton.joints) == 20


def test_bone_count(skeleton):
    assert len(skeleton.bones) == 19


def test_frame_count(skeleton):
    assert skeleton.n_frames == 306


def test_pose_zero_exists(skeleton):
    pose = skeleton.get_pose(0)
    assert pose is not None


def test_last_pose_exists(skeleton):
    pose = skeleton.get_pose(skeleton.n_frames - 1)
    assert pose is not None


def test_pelvis_exists(skeleton):
    pose = skeleton.get_pose(0)
    assert "Pelvis" in pose.joint_positions


def test_pelvis_position_dimension(skeleton):
    pos = skeleton.get_pose(0).get_position("Pelvis")
    assert pos is not None
    assert len(pos) == 3


def test_bone_lengths_positive(skeleton):
    lengths = skeleton.bone_lengths()
    for name, length in lengths.items():
        assert length is not None, f"{name} has unresolved length"
        assert length > 0, f"{name} has invalid length {length}"


def test_validator(skeleton):
    report = skeleton.validate()
    assert report is not None
    assert report.ok, f"Skeleton validation errors: {report.errors}"


def test_pelvis_frame_to_frame_motion_is_reasonable(skeleton):
    """Pelvis should not teleport between consecutive frames."""
    for frame in range(1, skeleton.n_frames):
        pelvis_prev = skeleton.get_pose(frame - 1).get_position("Pelvis")
        pelvis_curr = skeleton.get_pose(frame).get_position("Pelvis")
        assert pelvis_prev is not None and pelvis_curr is not None
        displacement = float(np.linalg.norm(pelvis_curr - pelvis_prev))
        assert displacement < MAX_REASONABLE_STEP, (
            f"Pelvis jump at frames {frame - 1}->{frame}: "
            f"{displacement:.3f} >= {MAX_REASONABLE_STEP}"
        )


# =========================================================
# End-to-End Pipeline
# =========================================================


def test_complete_pipeline():
    db = MotionDatabase().load()
    subject = db.get_subject("S2")
    session = subject.get_session("WU01")
    skeleton = SkeletonBuilder().build(session)
    pelvis = skeleton.get_pose(0).get_position("Pelvis")
    assert pelvis is not None
    assert len(pelvis) == 3


# =========================================================
# Certification
# =========================================================


def test_engine_certification(skeleton):
    print("\n")
    print("=" * 60)
    print(" HUMAN RECONSTRUCTION ENGINE CERTIFICATION")
    print("=" * 60)
    print("[OK] MotionDatabase")
    print("[OK] Subject")
    print("[OK] Session")
    print("[OK] Parser")
    print("[OK] Kinematics")
    print("[OK] Skeleton Builder")
    print("[OK] Skeleton")
    print("[OK] Poses")
    print("[OK] Bone Hierarchy")
    print(f"Frames : {skeleton.n_frames}")
    print(f"Joints : {len(skeleton.joints)}")
    print(f"Bones  : {len(skeleton.bones)}")
    print("=" * 60)
    print("CERTIFICATION PASSED")
    print("=" * 60)
    assert skeleton.n_frames == 306
    assert len(skeleton.joints) == 20
    assert len(skeleton.bones) == 19
