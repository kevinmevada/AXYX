"""Adapt clinical / mocap / clip sources into MotionSkeleton + MotionPose."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from motion_engine.rendering.avatar.retarget._quat import q_from_to, q_identity, q_normalize
from motion_engine.rendering.avatar.retarget.types import (
    AXYX_COORDS,
    CoordinateSystem,
    JointSample,
    MotionJoint,
    MotionPose,
    MotionSkeleton,
    Quat,
    Vec3,
)

# Default clinical hierarchy (Plug-in Gait / AXYX skeleton_definition)
CLINICAL_HIERARCHY: list[tuple[str, str | None]] = [
    ("Pelvis", None),
    ("LHip", "Pelvis"),
    ("LKnee", "LHip"),
    ("LAnkle", "LKnee"),
    ("LFoot", "LAnkle"),
    ("RHip", "Pelvis"),
    ("RKnee", "RHip"),
    ("RAnkle", "RKnee"),
    ("RFoot", "RAnkle"),
    ("Thorax", "Pelvis"),
    ("Neck", "Thorax"),
    ("Head", "Neck"),
    ("LShoulder", "Thorax"),
    ("LElbow", "LShoulder"),
    ("LWrist", "LElbow"),
    ("LHand", "LWrist"),
    ("RShoulder", "Thorax"),
    ("RElbow", "RShoulder"),
    ("RWrist", "RElbow"),
    ("RHand", "RWrist"),
]


class SkeletonAdapter:
    """Build MotionSkeleton / MotionPose from heterogeneous sources."""

    def clinical_skeleton(
        self,
        *,
        name: str = "matlab_clinical",
        coords: CoordinateSystem = AXYX_COORDS,
        hierarchy: Sequence[tuple[str, str | None]] | None = None,
    ) -> MotionSkeleton:
        hier = list(hierarchy or CLINICAL_HIERARCHY)
        joints = [
            MotionJoint(name=n, parent=p, index=i)
            for i, (n, p) in enumerate(hier)
        ]
        return MotionSkeleton(
            name=name,
            joints=tuple(joints),
            coordinate_system=coords,
            root=hier[0][0] if hier else None,
            metadata={"adapter": "clinical"},
        )

    def from_joint_list(
        self,
        names: Sequence[str],
        parents: Sequence[str | None],
        *,
        name: str = "custom",
        coords: CoordinateSystem = AXYX_COORDS,
    ) -> MotionSkeleton:
        if len(names) != len(parents):
            raise ValueError("names/parents length mismatch")
        joints = [
            MotionJoint(name=str(n), parent=p, index=i)
            for i, (n, p) in enumerate(zip(names, parents))
        ]
        root = next((n for n, p in zip(names, parents) if p is None), names[0] if names else None)
        return MotionSkeleton(
            name=name,
            joints=tuple(joints),
            coordinate_system=coords,
            root=str(root) if root else None,
        )

    def pose_from_positions(
        self,
        skeleton: MotionSkeleton,
        positions: Mapping[str, Vec3 | np.ndarray],
        *,
        time: float = 0.0,
        index: int = 0,
        bone_axis: Vec3 = (0.0, 1.0, 0.0),
    ) -> MotionPose:
        """Build local rotations from world joint positions along hierarchy."""
        world: dict[str, Vec3] = {}
        for name, pos in positions.items():
            p = np.asarray(pos, dtype=np.float64).reshape(3)
            world[name] = (float(p[0]), float(p[1]), float(p[2]))

        # World rotations from bone directions
        world_q: dict[str, Quat] = {}
        for joint in skeleton.joints:
            children = skeleton.children_of(joint.name)
            if joint.name not in world:
                continue
            if children and children[0] in world:
                direction = np.asarray(world[children[0]], dtype=np.float64) - np.asarray(
                    world[joint.name], dtype=np.float64
                )
                world_q[joint.name] = q_from_to(bone_axis, direction)
            elif joint.parent and joint.parent in world_q:
                world_q[joint.name] = world_q[joint.parent]
            else:
                world_q[joint.name] = q_identity()

        # Convert world → local
        from motion_engine.rendering.avatar.retarget._quat import q_conjugate, q_mul

        joints: dict[str, JointSample] = {}
        for joint in skeleton.joints:
            if joint.name not in world:
                continue
            wq = world_q.get(joint.name, q_identity())
            if joint.parent and joint.parent in world_q:
                pq = world_q[joint.parent]
                local_q = q_normalize(q_mul(q_conjugate(pq), wq))
                parent_pos = np.asarray(world[joint.parent], dtype=np.float64)
                local_t = tuple(
                    float(x) for x in (np.asarray(world[joint.name]) - parent_pos)
                )
            else:
                local_q = wq
                local_t = world[joint.name]
            joints[joint.name] = JointSample(
                name=joint.name,
                translation=local_t,  # type: ignore[arg-type]
                rotation_xyzw=local_q,
                world_position=world[joint.name],
                valid=True,
            )

        root_t = None
        if skeleton.root and skeleton.root in world:
            root_t = world[skeleton.root]
        return MotionPose(
            joints=joints,
            time=time,
            index=index,
            root_translation=root_t,
            metadata={"adapter": "positions"},
        )

    def pose_from_transforms(
        self,
        transforms: Mapping[str, Any],
        *,
        time: float = 0.0,
        index: int = 0,
        root_name: str | None = None,
    ) -> MotionPose:
        """Adapt motion_engine.animation_clip.JointTransform-like objects."""
        joints: dict[str, JointSample] = {}
        for name, xf in transforms.items():
            if hasattr(xf, "translation") and hasattr(xf, "rotation"):
                t = tuple(float(x) for x in xf.translation)  # type: ignore[assignment]
                r = tuple(float(x) for x in xf.rotation)  # type: ignore[assignment]
                s = tuple(float(x) for x in getattr(xf, "scale", (1, 1, 1)))  # type: ignore[assignment]
                valid = bool(getattr(xf, "valid", True))
            elif isinstance(xf, dict):
                t = tuple(float(x) for x in xf.get("translation", (0, 0, 0)))  # type: ignore[assignment]
                r = tuple(float(x) for x in xf.get("rotation", (0, 0, 0, 1)))  # type: ignore[assignment]
                s = tuple(float(x) for x in xf.get("scale", (1, 1, 1)))  # type: ignore[assignment]
                valid = bool(xf.get("valid", True))
            else:
                continue
            joints[str(name)] = JointSample(
                name=str(name),
                translation=t,  # type: ignore[arg-type]
                rotation_xyzw=q_normalize(r),  # type: ignore[arg-type]
                scale=s,  # type: ignore[arg-type]
                world_position=t,  # type: ignore[arg-type]
                valid=valid,
            )
        root_t = None
        if root_name and root_name in joints:
            root_t = joints[root_name].translation
        return MotionPose(
            joints=joints,
            time=time,
            index=index,
            root_translation=root_t,
            metadata={"adapter": "transforms"},
        )

    def synthetic_gait_positions(
        self,
        skeleton: MotionSkeleton,
        *,
        phase: float,
        stride: float = 0.7,
        height: float = 1.7,
    ) -> dict[str, Vec3]:
        """Procedural clinical gait positions for tests / demo without MATLAB."""
        t = float(phase) * 2.0 * np.pi
        pelvis = (stride * 0.15 * np.sin(t), 0.0, height * 0.55)
        positions: dict[str, Vec3] = {"Pelvis": (float(pelvis[0]), float(pelvis[1]), float(pelvis[2]))}

        def leg(side: float, phase_off: float) -> None:
            prefix = "L" if side < 0 else "R"
            swing = np.sin(t + phase_off)
            hip = (
                pelvis[0] + side * 0.1,
                pelvis[1] + 0.05 * swing,
                pelvis[2] - 0.05,
            )
            knee = (
                hip[0] + 0.25 * swing * stride,
                hip[1],
                hip[2] - 0.4,
            )
            ankle = (
                knee[0] + 0.15 * max(0.0, swing) * stride,
                knee[1],
                max(0.02, knee[2] - 0.4 + 0.05 * max(0.0, -swing)),
            )
            foot = (ankle[0] + 0.08, ankle[1], 0.0)
            positions[f"{prefix}Hip"] = tuple(float(x) for x in hip)  # type: ignore[assignment]
            positions[f"{prefix}Knee"] = tuple(float(x) for x in knee)  # type: ignore[assignment]
            positions[f"{prefix}Ankle"] = tuple(float(x) for x in ankle)  # type: ignore[assignment]
            positions[f"{prefix}Foot"] = tuple(float(x) for x in foot)  # type: ignore[assignment]

        leg(-1.0, 0.0)
        leg(1.0, np.pi)

        thorax = (pelvis[0], pelvis[1], pelvis[2] + 0.35)
        neck = (thorax[0], thorax[1], thorax[2] + 0.2)
        head = (neck[0], neck[1], neck[2] + 0.15)
        positions["Thorax"] = tuple(float(x) for x in thorax)  # type: ignore[assignment]
        positions["Neck"] = tuple(float(x) for x in neck)  # type: ignore[assignment]
        positions["Head"] = tuple(float(x) for x in head)  # type: ignore[assignment]

        for side, prefix in ((-1.0, "L"), (1.0, "R")):
            sh = (thorax[0], thorax[1] + side * 0.2, thorax[2] + 0.05)
            el = (sh[0] + 0.1 * np.sin(t + (0 if side < 0 else np.pi)), sh[1] + side * 0.05, sh[2] - 0.25)
            wr = (el[0], el[1], el[2] - 0.25)
            positions[f"{prefix}Shoulder"] = tuple(float(x) for x in sh)  # type: ignore[assignment]
            positions[f"{prefix}Elbow"] = tuple(float(x) for x in el)  # type: ignore[assignment]
            positions[f"{prefix}Wrist"] = tuple(float(x) for x in wr)  # type: ignore[assignment]
            positions[f"{prefix}Hand"] = positions[f"{prefix}Wrist"]

        # Ensure all skeleton joints have something
        for j in skeleton.joints:
            positions.setdefault(j.name, positions.get("Pelvis", (0.0, 0.0, 1.0)))
        return positions


__all__ = ["SkeletonAdapter", "CLINICAL_HIERARCHY"]
