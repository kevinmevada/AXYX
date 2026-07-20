"""Tests for avatar registry and Kili pose/skinning pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from motion_engine.avatar.pose_driver import rotation_align
from motion_engine.avatar.registry import AvatarRegistry
from motion_engine.avatar.skinning import linear_blend_skin
from motion_engine.skeleton import Pose

ROOT = Path(__file__).resolve().parents[1]


def test_avatar_registry_default_is_kili_or_metallic() -> None:
    reg = AvatarRegistry(ROOT / "config" / "avatars.yaml")
    assert reg.default_avatar_id in {"kili", "metallic"}
    assert "metallic" in reg.avatars
    assert reg.avatars["metallic"].fallback is True


def test_metallic_backend_draws_procedural() -> None:
    avatar = AvatarRegistry(ROOT / "config" / "avatars.yaml").create("metallic")
    assert avatar.id == "metallic"
    assert avatar.draws_procedural_skeleton is True


def test_rotation_align_identity() -> None:
    R = rotation_align(np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 2.0]))
    assert np.allclose(R, np.eye(3), atol=1e-6)


def test_rotation_align_90deg() -> None:
    R = rotation_align(np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
    out = R @ np.array([1.0, 0.0, 0.0])
    assert np.allclose(out, np.array([0.0, 1.0, 0.0]), atol=1e-5)


def test_linear_blend_skin_identity() -> None:
    rest = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32)
    bone = np.eye(4)[None, ...]
    inv = np.eye(4)[None, ...]
    indices = np.zeros((2, 1), dtype=np.int32)
    weights = np.ones((2, 1), dtype=np.float32)
    out = linear_blend_skin(rest, bone, inv, indices, weights)
    assert np.allclose(out, rest, atol=1e-5)


@pytest.mark.skipif(
    not (ROOT / "KILI" / "cache" / "body_lod3.npz").is_file(),
    reason="Kili cache not preprocessed",
)
def test_kili_backend_loads_cache() -> None:
    from motion_engine.avatar.kili_backend import KiliAvatar

    avatar = KiliAvatar(
        asset_root=ROOT / "KILI",
        retarget_path=ROOT / "config" / "retarget_kili.yaml",
        lod=3,
    )
    avatar._load_cache()
    assert avatar._rest is not None
    assert avatar._rest.shape[0] > 0
    assert avatar._driver is not None

    pose = Pose(
        frame_index=0,
        joint_positions={
            "Pelvis": np.array([0.0, 0.0, 920.0]),
            "Thorax": np.array([0.0, -40.0, 1100.0]),
            "Neck": np.array([0.0, 10.0, 1480.0]),
            "Head": np.array([0.0, -10.0, 1590.0]),
            "LHip": np.array([110.0, -27.0, 918.0]),
            "RHip": np.array([-110.0, -27.0, 918.0]),
            "LKnee": np.array([130.0, -18.0, 490.0]),
            "RKnee": np.array([-130.0, -18.0, 490.0]),
            "LAnkle": np.array([148.0, -2.0, 82.0]),
            "RAnkle": np.array([-148.0, -2.0, 82.0]),
            "LFoot": np.array([173.0, -140.0, 10.0]),
            "RFoot": np.array([-173.0, -140.0, 10.0]),
            "LShoulder": np.array([110.0, 15.0, 1420.0]),
            "RShoulder": np.array([-110.0, 15.0, 1420.0]),
            "LElbow": np.array([334.0, 11.0, 1180.0]),
            "RElbow": np.array([-334.0, 11.0, 1180.0]),
            "LWrist": np.array([465.0, -148.0, 1020.0]),
            "RWrist": np.array([-465.0, -148.0, 1020.0]),
        },
    )
    mats = avatar._driver.compute_bone_matrices(pose)
    assert mats.shape[0] == len(avatar._bone_names)
    skinned = linear_blend_skin(
        avatar._rest,
        mats,
        avatar._inv_bind,
        avatar._bone_indices,
        avatar._bone_weights,
    )
    assert skinned.shape == avatar._rest.shape
    assert np.all(np.isfinite(skinned))
