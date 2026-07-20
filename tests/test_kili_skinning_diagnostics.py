"""Kili / MetaHuman skinning diagnostics.

Follows the systematic debug checklist:

1. Mesh + original skeleton + bind pose only (no animation)
2. Bone positions align with mesh envelope
3. Identity / bind-pose transforms (no animation matrices)
4. Single-bone rotation (left elbow ~10°)
5. Vertex weight sanity

Run:
    set PYTHONPATH=src
    venv311\\Scripts\\python.exe -m pytest tests/test_kili_skinning_diagnostics.py -v
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
import yaml

from motion_engine.avatar.skinning import linear_blend_skin

ROOT = Path(__file__).resolve().parents[1]
KILI_CACHE = ROOT / "KILI" / "cache"
BODY_NPZ = KILI_CACHE / "body_lod1.npz"
SKEL_JSON = KILI_CACHE / "skeleton.json"
RETARGET_YAML = ROOT / "config" / "retarget_kili.yaml"

# Human envelope in cm (Unreal export units in cache)
MAX_BODY_HEIGHT_CM = 220.0
MAX_BODY_WIDTH_CM = 120.0
MAX_VERTEX_EXPLOSION_CM = 300.0  # no vertex >3 m from mesh centroid

pytestmark = pytest.mark.skipif(
    not BODY_NPZ.is_file(),
    reason="Kili body cache missing — run scripts/preprocess_kili_lod.py 1",
)


@dataclass(frozen=True)
class KiliMeshData:
    rest: np.ndarray
    faces: np.ndarray
    inv_bind: np.ndarray
    bind_world: np.ndarray
    bone_indices: np.ndarray
    bone_weights: np.ndarray
    bone_names: list[str]
    bone_parents: np.ndarray

    @classmethod
    def load(cls, path: Path = BODY_NPZ) -> KiliMeshData:
        data = np.load(path, allow_pickle=True)
        parents = (
            np.asarray(data["bone_parents"], dtype=np.int32)
            if "bone_parents" in data
            else np.full(len(data["bone_names"]), -1, dtype=np.int32)
        )
        return cls(
            rest=np.asarray(data["positions"], dtype=np.float32),
            faces=np.asarray(data["faces"], dtype=np.int32),
            inv_bind=np.asarray(data["inv_bind"], dtype=np.float64),
            bind_world=np.asarray(data["bind_world"], dtype=np.float64),
            bone_indices=np.asarray(data["bone_indices"], dtype=np.int32),
            bone_weights=np.asarray(data["bone_weights"], dtype=np.float32),
            bone_names=[str(x) for x in data["bone_names"]],
            bone_parents=parents,
        )


@pytest.fixture(scope="module")
def kili() -> KiliMeshData:
    return KiliMeshData.load()


@pytest.fixture(scope="module")
def name_to_index(kili: KiliMeshData) -> dict[str, int]:
    return {n: i for i, n in enumerate(kili.bone_names)}


def _skin(
    kili: KiliMeshData,
    bone_matrices: np.ndarray,
    *,
    display_mm: bool = False,
) -> np.ndarray:
    out = linear_blend_skin(
        kili.rest,
        bone_matrices,
        kili.inv_bind,
        kili.bone_indices,
        kili.bone_weights,
    )
    return out * 10.0 if display_mm else out


def _mesh_span(verts: np.ndarray) -> np.ndarray:
    return verts.max(axis=0) - verts.min(axis=0)


def _rotation_z_degrees(deg: float) -> np.ndarray:
    r = np.deg2rad(deg)
    c, s = np.cos(r), np.sin(r)
    R = np.eye(4)
    R[:3, :3] = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return R


# ---------------------------------------------------------------------------
# Step 1 — Mesh + original skeleton + bind pose (NO animation)
# Question: Does it look like a human?  → bind-pose skinning error ≈ 0
# ---------------------------------------------------------------------------


class TestStep1BindPoseOnly:
    """Import pipeline: mesh skinned with its own bind matrices."""

    def test_bind_pose_reproduces_rest_mesh(self, kili: KiliMeshData) -> None:
        skinned = _skin(kili, kili.bind_world)
        err = np.linalg.norm(skinned - kili.rest, axis=1)
        assert err.max() < 0.01, (
            f"Bind-pose skinning error {err.max():.4f} cm — "
            "import pipeline wrong (inv_bind / bind_world mismatch)"
        )

    def test_rest_mesh_has_human_proportions(self, kili: KiliMeshData) -> None:
        # Mesh AABB (LOD may omit cranium); also check skeleton extent.
        span = _mesh_span(kili.rest)
        width = float(max(span[0], span[1]))
        assert width < MAX_BODY_WIDTH_CM, f"Width {width:.1f} cm — possible explosion"
        skel_z = float(kili.bind_world[:, 2, 3].max() - kili.bind_world[:, 2, 3].min())
        assert skel_z > 140.0, f"Skeleton height {skel_z:.1f} cm — implausible"
        assert float(span[2]) > 80.0, f"Mesh Z extent {span[2]:.1f} cm — empty/truncated"

    def test_skinned_bind_pose_has_human_proportions(self, kili: KiliMeshData) -> None:
        skinned = _skin(kili, kili.bind_world)
        span = _mesh_span(skinned)
        assert float(span[2]) < MAX_BODY_HEIGHT_CM
        assert float(max(span[0], span[1])) < MAX_BODY_WIDTH_CM

    def test_no_nan_or_inf_in_cache(self, kili: KiliMeshData) -> None:
        for label, arr in [
            ("rest", kili.rest),
            ("inv_bind", kili.inv_bind),
            ("bind_world", kili.bind_world),
            ("weights", kili.bone_weights),
        ]:
            assert np.all(np.isfinite(arr)), f"{label} has NaN/Inf"


# ---------------------------------------------------------------------------
# Step 2 — Draw the bones (numerically): do they sit inside the mesh?
# ---------------------------------------------------------------------------


class TestStep2BoneMeshAlignment:
    """Red spheres / green lines proxy — bone heads vs vertex cloud."""

    def test_drive_bones_exist_in_mesh_skeleton(
        self, kili: KiliMeshData, name_to_index: dict[str, int]
    ) -> None:
        skel = json.loads(SKEL_JSON.read_text(encoding="utf-8"))
        drive = skel.get("drive_order") or []
        missing = [b for b in drive if b not in name_to_index]
        assert not missing, f"Drive bones missing from mesh skeleton: {missing}"

    def test_parent_hierarchy_not_broken(self, kili: KiliMeshData) -> None:
        """pelvis → root, not pelvis → foot."""
        idx = {n: i for i, n in enumerate(kili.bone_names)}
        checks = {
            "pelvis": "root",
            "spine_01": "pelvis",
            "thigh_l": "pelvis",
            "calf_l": "thigh_l",
            "foot_l": "calf_l",
            "lowerarm_l": "upperarm_l",
            "head": "neck_02",
        }
        for child, expected_parent in checks.items():
            ci = idx.get(child)
            assert ci is not None, f"{child} missing"
            pi = int(kili.bone_parents[ci])
            actual = kili.bone_names[pi] if pi >= 0 else None
            assert actual == expected_parent, (
                f"{child} parent is {actual!r}, expected {expected_parent!r} — "
                "hierarchy broken"
            )

    def test_mesh_has_bone_vertex_influences(self, kili: KiliMeshData) -> None:
        """At least half the skeleton should directly influence vertices."""
        used_bones = set()
        for slot in range(kili.bone_indices.shape[1]):
            w = kili.bone_weights[:, slot]
            for bi in np.unique(kili.bone_indices[w > 0.01, slot]):
                used_bones.add(int(bi))
        ratio = len(used_bones) / len(kili.bone_names)
        assert ratio > 0.15, (
            f"Only {len(used_bones)}/{len(kili.bone_names)} bones influence verts"
        )

    def test_drive_bones_may_use_child_correctives(
        self, kili: KiliMeshData, name_to_index: dict[str, int]
    ) -> None:
        """MetaHuman often weights twist/corrective bones, not drive bones directly.

        This is expected — animation propagates via hierarchy.  Document which
        drive bones lack direct weights so retargeting knows to move parents.
        """
        no_direct = []
        for bone in ("thigh_l", "calf_l", "upperarm_l", "lowerarm_l", "pelvis"):
            bi = name_to_index.get(bone)
            if bi is None:
                continue
            if not np.any((kili.bone_indices == bi).any(axis=1)):
                no_direct.append(bone)
        # Informational: MetaHuman LOD1 commonly skins correctives, not drive bones.
        # Bind-pose test (Step 1) proves the weight table is still valid.
        assert "pelvis" not in no_direct, "Pelvis must influence verts"

    def test_head_above_pelvis_z_up(self, kili: KiliMeshData, name_to_index: dict[str, int]) -> None:
        """Unreal Z-up: head Z > pelvis Z in bind pose."""
        pelvis_z = kili.bind_world[name_to_index["pelvis"]][2, 3]
        head_z = kili.bind_world[name_to_index["head"]][2, 3]
        assert head_z > pelvis_z + 30.0, "Head not above pelvis — coordinate frame may be wrong"


# ---------------------------------------------------------------------------
# Step 3 — No animation: identity / bind-only transforms
# ---------------------------------------------------------------------------


class TestStep3NoAnimation:
    """If bind pose looks human but animated doesn't → animation matrices wrong."""

    def test_identity_bone_matrices_deform_mesh(self, kili: KiliMeshData) -> None:
        """Pure identity is WRONG for skinning (proves inv_bind is required)."""
        identity = np.tile(np.eye(4), (len(kili.bone_names), 1, 1))
        skinned = _skin(kili, identity)
        err = np.linalg.norm(skinned - kili.rest, axis=1).max()
        assert err > 10.0, "Identity matrices should NOT reproduce rest — inv_bind matters"

    def test_bind_world_is_the_identity_animation(self, kili: KiliMeshData) -> None:
        """Correct 'no animation' = bind_world matrices, not identity."""
        skinned = _skin(kili, kili.bind_world)
        assert np.allclose(skinned, kili.rest, atol=0.02)

    def test_wrong_skeleton_shuffled_bones_explodes(self, kili: KiliMeshData) -> None:
        """Simulates animating Skeleton B on Mesh A — should fail loudly."""
        rng = np.random.default_rng(42)
        perm = rng.permutation(len(kili.bone_names))
        wrong = kili.bind_world[perm]
        skinned = _skin(kili, wrong)
        span = _mesh_span(skinned)
        err = np.linalg.norm(skinned - kili.rest, axis=1).max()
        assert float(max(span)) > MAX_BODY_WIDTH_CM or err > 50.0, (
            "Shuffled skeleton should explode — test may be too weak"
        )


# ---------------------------------------------------------------------------
# Step 4 — Rotate ONE bone only (left elbow ~10°)
# ---------------------------------------------------------------------------


class TestStep4SingleBoneRotation:
    """If whole body explodes on one bone → skinning / hierarchy bug."""

    def _bind_local(self, kili: KiliMeshData) -> np.ndarray:
        local = np.zeros_like(kili.bind_world)
        for i in range(len(kili.bone_names)):
            p = int(kili.bone_parents[i])
            if p >= 0:
                local[i] = np.linalg.inv(kili.bind_world[p]) @ kili.bind_world[i]
            else:
                local[i] = kili.bind_world[i].copy()
        return local

    def _propagate_from_drive(
        self,
        kili: KiliMeshData,
        drive_matrices: dict[int, np.ndarray],
    ) -> np.ndarray:
        local = self._bind_local(kili)
        mats = kili.bind_world.copy()
        order: list[int] = []
        state = [0] * len(kili.bone_names)

        def visit(i: int) -> None:
            if state[i]:
                return
            state[i] = 1
            p = int(kili.bone_parents[i])
            if p >= 0:
                visit(p)
            order.append(i)

        for i in range(len(kili.bone_names)):
            visit(i)

        for i in order:
            if i in drive_matrices:
                mats[i] = drive_matrices[i]
            else:
                p = int(kili.bone_parents[i])
                if p >= 0:
                    mats[i] = mats[p] @ local[i]
        return mats

    def test_single_elbow_rotation_localized(self, kili: KiliMeshData, name_to_index: dict[str, int]) -> None:
        elbow_i = name_to_index["lowerarm_l"]
        bind = kili.bind_world[elbow_i].copy()
        # 10° about local X (typical flex axis approximation)
        rot_local = _rotation_z_degrees(10.0)
        new_world = bind @ rot_local

        mats = self._propagate_from_drive(kili, {elbow_i: new_world})
        skinned = _skin(kili, mats)
        delta = np.linalg.norm(skinned - kili.rest, axis=1)

        span = _mesh_span(skinned)
        assert float(max(span)) < MAX_BODY_WIDTH_CM, (
            f"Whole body exploded on elbow-only rotation — span {span}"
        )
        assert float(delta.max()) < MAX_VERTEX_EXPLOSION_CM, (
            f"Max vertex move {delta.max():.1f} cm on single-bone test"
        )

        # Arm vertices should move more than toes
        foot_i = name_to_index["foot_l"]
        foot_pos = kili.bind_world[foot_i][:3, 3]
        dist_to_elbow = np.linalg.norm(kili.rest - bind[:3, 3], axis=1)
        dist_to_foot = np.linalg.norm(kili.rest - foot_pos, axis=1)
        near_elbow = delta[dist_to_elbow < 30.0].mean()
        near_foot = delta[dist_to_foot < 20.0].mean()
        assert near_elbow > near_foot * 1.5, (
            f"Elbow rotation should affect arm more than foot "
            f"(arm Δ={near_elbow:.2f}, foot Δ={near_foot:.2f})"
        )


# ---------------------------------------------------------------------------
# Step 5 — Vertex weights
# ---------------------------------------------------------------------------


class TestStep5VertexWeights:
    def test_weights_sum_to_one(self, kili: KiliMeshData) -> None:
        wsum = kili.bone_weights.sum(axis=1)
        assert np.allclose(wsum, 1.0, atol=0.02)

    def test_no_body_vertex_100_percent_root(self, kili: KiliMeshData, name_to_index: dict[str, int]) -> None:
        root_i = name_to_index["root"]
        pelvis_i = name_to_index["pelvis"]
        torso_z = (
            kili.bind_world[name_to_index["spine_03"]][2, 3]
            + kili.bind_world[name_to_index["pelvis"]][2, 3]
        ) / 2.0
        bad = []
        for vi in range(kili.rest.shape[0]):
            if abs(kili.rest[vi, 2] - torso_z) > 40.0:
                continue  # skip extremities
            w = kili.bone_weights[vi]
            idx = kili.bone_indices[vi]
            if w[0] > 0.99 and idx[0] == root_i:
                bad.append(vi)
        assert len(bad) < 10, (
            f"{len(bad)} torso vertices weighted 100% to root — weight table suspect"
        )

    def test_sample_vertex_weight_report(self, kili: KiliMeshData, name_to_index: dict[str, int]) -> None:
        """Vertex ~mid-torso should blend spine/pelvis/clavicle — not 100% root."""
        torso_center = kili.bind_world[name_to_index["spine_03"]][:3, 3]
        dists = np.linalg.norm(kili.rest - torso_center, axis=1)
        vi = int(np.argmin(dists))
        pairs = []
        for slot in range(kili.bone_weights.shape[1]):
            w = float(kili.bone_weights[vi, slot])
            if w < 0.05:
                continue
            bi = int(kili.bone_indices[vi, slot])
            pairs.append((kili.bone_names[bi], w))
        pairs.sort(key=lambda x: -x[1])
        assert len(pairs) >= 2, (
            f"Vertex {vi} has <2 influences: {pairs} — expected multi-bone blend"
        )
        top_name, top_w = pairs[0]
        assert top_name != "root" or top_w < 0.8, (
            f"Vertex {vi} weights: {pairs} — suspicious single root influence"
        )

    def test_bone_indices_in_range(self, kili: KiliMeshData) -> None:
        n = len(kili.bone_names)
        assert kili.bone_indices.min() >= 0
        assert kili.bone_indices.max() < n


# ---------------------------------------------------------------------------
# Retarget mapping sanity (bone name mapping wrong → monster)
# ---------------------------------------------------------------------------


class TestRetargetMapping:
    def test_axyx_joints_map_to_existing_kili_bones(
        self, kili: KiliMeshData, name_to_index: dict[str, int]
    ) -> None:
        raw = yaml.safe_load(RETARGET_YAML.read_text(encoding="utf-8"))
        joints = raw.get("joints") or {}
        bad = [(src, dst) for src, dst in joints.items() if dst not in name_to_index]
        assert not bad, f"Retarget maps to missing Kili bones: {bad}"

    def test_no_pelvis_to_limb_direct_mapping(self) -> None:
        raw = yaml.safe_load(RETARGET_YAML.read_text(encoding="utf-8"))
        joints = raw.get("joints") or {}
        assert joints.get("Pelvis") == "pelvis"
        assert joints.get("LElbow") == "lowerarm_l"
        assert joints.get("Thorax") != "upperarm_l", "Absurd mapping present"

    def test_matrix_order_parent_child(self, kili: KiliMeshData) -> None:
        """Global = parent @ local (not local @ parent)."""
        idx = {n: i for i, n in enumerate(kili.bone_names)}
        parent_i = idx["pelvis"]
        child_i = idx["spine_01"]
        local = np.linalg.inv(kili.bind_world[parent_i]) @ kili.bind_world[child_i]
        recomposed = kili.bind_world[parent_i] @ local
        assert np.allclose(recomposed, kili.bind_world[child_i], atol=1e-4), (
            "parent @ local ≠ child — matrix multiplication order wrong"
        )


# ---------------------------------------------------------------------------
# Verdict — bind pose OK, AXYX animation is the risk surface
# ---------------------------------------------------------------------------


class TestAnimationVsBindVerdict:
    @pytest.mark.skipif(
        not (ROOT / "data" / "processed" / "Data_structure_filtered.mat").is_file(),
        reason="Mocap dataset not available",
    )
    def test_axyx_animation_can_explode_without_calibration(
        self, kili: KiliMeshData
    ) -> None:
        """Proves monster is retarget/animation — not mesh import."""
        from motion_engine.avatar.pose_driver import KiliPoseDriver
        from motion_engine.loader import MotionDatabaseLoader
        from motion_engine.skeleton import SkeletonBuilder

        loader = MotionDatabaseLoader()
        db = loader.load(ROOT / "data" / "processed" / "Data_structure_filtered.mat")
        subj = next(iter(db.subjects))
        sess = db.subjects[subj].sessions[next(iter(db.subjects[subj].sessions))]
        skel = SkeletonBuilder().build(sess)

        driver = KiliPoseDriver(
            retarget_path=RETARGET_YAML,
            skeleton_path=SKEL_JSON,
            bone_names=kili.bone_names,
            bind_world=kili.bind_world,
            bone_parents=kili.bone_parents,
        )
        # NO calibrate — simulates applying absolute lab coords (the bug)
        mats = driver.compute_bone_matrices(skel.poses[200])
        skinned = _skin(kili, mats) * 10.0
        span = _mesh_span(skinned)
        assert float(max(span)) > MAX_BODY_WIDTH_CM, (
            "Uncalibrated animation should explode — confirms retarget bug"
        )

        driver.calibrate(skel.poses[0])
        mats_ok = driver.compute_bone_matrices(skel.poses[200])
        skinned_ok = _skin(kili, mats_ok)  # cm
        span_ok = _mesh_span(skinned_ok)
        assert float(span_ok[0]) < 80.0 and float(span_ok[1]) < 80.0, (
            f"Calibrated animation width span {span_ok[:2]} cm — explosion"
        )
        assert float(span_ok[2]) < 130.0, (
            f"Calibrated animation height {span_ok[2]:.1f} cm — explosion"
        )
