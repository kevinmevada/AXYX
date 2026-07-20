"""Position-based hierarchical pose driver for Kili skinning.

Never assigns independent world positions per bone from mocap — that breaks
MetaHuman bone lengths and causes vertex explosions.  Instead:

1. Calibrate frame-0 mocap reference.
2. Apply root translation delta at ``pelvis`` only.
3. Derive limb rotations from mocap direction deltas (parent → child).
4. Propagate through the full 342-bone hierarchy via bind-local offsets.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from numpy.typing import NDArray

from motion_engine.skeleton import Pose

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating[Any]]


def _safe(v: Any) -> FloatArray | None:
    if v is None:
        return None
    arr = np.asarray(v, dtype=float).reshape(3)
    if not np.all(np.isfinite(arr)):
        return None
    return arr


def rotation_align(from_dir: FloatArray, to_dir: FloatArray) -> FloatArray:
    """3×3 rotation mapping ``from_dir`` → ``to_dir`` (Rodrigues)."""
    a = np.asarray(from_dir, dtype=float).reshape(3)
    b = np.asarray(to_dir, dtype=float).reshape(3)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-8 or nb < 1e-8:
        return np.eye(3)
    a, b = a / na, b / nb
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.999999:
        axis = np.array([1.0, 0.0, 0.0])
        if abs(a[0]) > 0.9:
            axis = np.array([0.0, 1.0, 0.0])
        axis -= a * np.dot(axis, a)
        axis /= np.linalg.norm(axis) + 1e-12
        K = np.array(
            [[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]]
        )
        return np.eye(3) + 2.0 * (K @ K)
    s = np.linalg.norm(v)
    if s < 1e-8:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1.0 - c) / (s * s))


def _mat4(R: FloatArray, t: FloatArray) -> FloatArray:
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = np.asarray(t, dtype=float).reshape(3)
    return M


class KiliPoseDriver:
    """Hierarchical retarget: mocap positions → Kili bone matrices."""

    MM_TO_CM = 0.1

    def __init__(
        self,
        *,
        retarget_path: Path,
        skeleton_path: Path,
        bone_names: list[str],
        bind_world: FloatArray,
        bone_parents: NDArray[np.integer[Any]] | None = None,
    ) -> None:
        self.bone_names = list(bone_names)
        self.name_to_index = {n: i for i, n in enumerate(self.bone_names)}
        self.bind_world = np.asarray(bind_world, dtype=np.float64)
        self.n_bones = len(self.bone_names)

        if bone_parents is not None:
            self.bone_parents = np.asarray(bone_parents, dtype=np.int32)
        else:
            self.bone_parents = np.full(self.n_bones, -1, dtype=np.int32)

        self._bind_local = np.zeros((self.n_bones, 4, 4), dtype=np.float64)
        for i in range(self.n_bones):
            p = int(self.bone_parents[i])
            if p >= 0:
                self._bind_local[i] = np.linalg.inv(self.bind_world[p]) @ self.bind_world[i]
            else:
                self._bind_local[i] = self.bind_world[i].copy()

        raw = yaml.safe_load(Path(retarget_path).read_text(encoding="utf-8")) or {}
        self.joint_map: dict[str, str] = {
            str(k): str(v) for k, v in (raw.get("joints") or {}).items()
        }
        self.inferred: dict[str, dict[str, Any]] = dict(raw.get("inferred_bones") or {})

        skel = json.loads(Path(skeleton_path).read_text(encoding="utf-8"))
        self.drive_order: list[str] = list(skel.get("drive_order") or [])
        self.drive_set = set(self.drive_order)
        self.parents: dict[str, str | None] = {
            name: (
                skel["nodes"][name].get("parent")
                if name in skel.get("nodes", {})
                else None
            )
            for name in self.drive_order
        }

        self._reference_mm: dict[str, FloatArray] = {}
        self._calibrated = False
        self._display_offset_cm = np.zeros(3, dtype=np.float64)
        self.display_scale = 10.0  # cm → mm for Studio viewport
        # ``rigid`` = pelvis translation only (stable human silhouette).
        # ``hierarchical`` = limb rotation deltas (experimental, can distort).
        self.animation_mode = "rigid"

    def calibrate(self, pose: Pose) -> None:
        ref = self._extract_mocap_mm(pose)
        self._reference_mm = ref
        self._calibrated = bool(ref)
        pelvis_i = self.name_to_index.get("pelvis")
        if self._calibrated and pelvis_i is not None and "pelvis" in ref:
            bind_pelvis_cm = self.bind_world[pelvis_i][:3, 3]
            ref_pelvis_cm = ref["pelvis"] * self.MM_TO_CM
            self._display_offset_cm = ref_pelvis_cm - bind_pelvis_cm
        else:
            self._display_offset_cm = np.zeros(3, dtype=np.float64)
        logger.debug(
            "Kili calibrated (%s joints, display_offset_cm=%s)",
            len(ref),
            np.round(self._display_offset_cm, 1),
        )

    def _extract_mocap_mm(self, pose: Pose) -> dict[str, FloatArray]:
        out: dict[str, FloatArray] = {}
        for src, dst in self.joint_map.items():
            p = _safe(pose.get_position(src))
            if p is not None:
                out[dst] = p
        for name, spec in self.inferred.items():
            a, b = out.get(str(spec.get("from"))), out.get(str(spec.get("to")))
            if a is not None and b is not None:
                t = float(spec.get("t", 0.5))
                out[name] = (1.0 - t) * a + t * b
        return out

    def _drive_topo_order(self) -> list[str]:
        """Drive bones in parent-before-child order."""
        order: list[str] = []
        seen: set[str] = set()

        def visit(name: str) -> None:
            if name in seen or name not in self.drive_set:
                return
            parent = self.parents.get(name)
            if parent and parent in self.drive_set:
                visit(parent)
            if name not in seen:
                order.append(name)
                seen.add(name)

        for name in self.drive_order:
            visit(name)
        return order

    def compute_bone_matrices(self, pose: Pose) -> FloatArray:
        """Hierarchical retarget preserving MetaHuman bone lengths."""
        if not self._calibrated:
            return self.bind_world.copy()

        if self.animation_mode == "rigid":
            return self._rigid_root_motion(pose)
        return self._hierarchical_motion(pose)

    def _rigid_root_motion(self, pose: Pose) -> FloatArray:
        """Translate entire bind skeleton — pelvis aligned to mocap, then root motion."""
        cur_mm = self._extract_mocap_mm(pose)
        ref_mm = self._reference_mm
        delta_cm = np.zeros(3, dtype=np.float64)
        if "pelvis" in cur_mm and "pelvis" in ref_mm:
            delta_cm = (cur_mm["pelvis"] - ref_mm["pelvis"]) * self.MM_TO_CM
        total_cm = self._display_offset_cm + delta_cm
        shift = _mat4(np.eye(3), total_cm)
        return np.array([shift @ b for b in self.bind_world])

    def _hierarchical_motion(self, pose: Pose) -> FloatArray:
        """Limb rotation deltas + root motion (experimental)."""
        cur_mm = self._extract_mocap_mm(pose)
        ref_mm = self._reference_mm
        matrices = self.bind_world.copy()
        pelvis_delta_cm = np.zeros(3, dtype=np.float64)
        if "pelvis" in cur_mm and "pelvis" in ref_mm:
            pelvis_delta_cm = (cur_mm["pelvis"] - ref_mm["pelvis"]) * self.MM_TO_CM

        root_i = self.name_to_index.get("root")
        if root_i is not None and np.linalg.norm(pelvis_delta_cm) > 0:
            shift = _mat4(np.eye(3), pelvis_delta_cm)
            for i in range(self.n_bones):
                matrices[i] = shift @ self.bind_world[i]

        for name in self._drive_topo_order():
            if name in {"root", "pelvis"}:
                continue
            idx = self.name_to_index.get(name)
            if idx is None:
                continue
            parent_name = self.parents.get(name)
            parent_i = (
                self.name_to_index[parent_name]
                if parent_name and parent_name in self.name_to_index
                else -1
            )
            local = self._bind_local[idx].copy()

            if parent_name and parent_name in ref_mm and name in ref_mm:
                if parent_name in cur_mm and name in cur_mm:
                    ref_dir = (ref_mm[name] - ref_mm[parent_name]) * self.MM_TO_CM
                    cur_dir = (cur_mm[name] - cur_mm[parent_name]) * self.MM_TO_CM
                    if np.linalg.norm(ref_dir) > 1e-3 and np.linalg.norm(cur_dir) > 1e-3:
                        delta_R = rotation_align(ref_dir, cur_dir)
                        local[:3, :3] = delta_R @ local[:3, :3]

            if parent_i >= 0:
                matrices[idx] = matrices[parent_i] @ local

        drive_indices = {
            self.name_to_index[n] for n in self.drive_order if n in self.name_to_index
        }
        for i in self._topological_order():
            if i in drive_indices:
                continue
            p = int(self.bone_parents[i])
            if p >= 0:
                matrices[i] = matrices[p] @ self._bind_local[i]
            else:
                matrices[i] = self.bind_world[i]

        return matrices

    def _topological_order(self) -> list[int]:
        order: list[int] = []
        state = [0] * self.n_bones

        def visit(i: int) -> None:
            if state[i]:
                return
            state[i] = 1
            p = int(self.bone_parents[i])
            if p >= 0:
                visit(p)
            order.append(i)
            state[i] = 2

        for i in range(self.n_bones):
            visit(i)
        return order
