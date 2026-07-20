"""
Forward / analytical kinematics helpers for the Human Reconstruction Engine.

Status
------
Placeholder. SkeletonBuilder currently reconstructs joint positions directly
from marker / joint-center trajectories. This module will own:

- forward kinematics from local bone transforms
- segment frames
- optional use of MotionDatabase joint-angle channels
- retargeting adapters for humanoid robotics

Do NOT implement IK here in this phase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from motion_engine.skeleton import Pose, Skeleton

FloatArray = NDArray[np.floating[Any]]


class KinematicsEngine:
    """Analytical kinematics utilities over a :class:`Skeleton`.

    TODO:
        - FK from local rotations + bone lengths
        - World-from-local transform composition
        - Joint-angle channel bridging from Session.kinematics.joint_angles
    """

    def forward_pose(self, skeleton: Skeleton, frame_index: int) -> Pose:
        """Compute a pose via forward kinematics.

        Raises:
            NotImplementedError: Always in this phase.
        """
        raise NotImplementedError(
            "KinematicsEngine.forward_pose is deferred (no IK / FK in this phase)."
        )

    def bone_direction(
        self,
        proximal: FloatArray,
        distal: FloatArray,
    ) -> FloatArray:
        """Return a unit vector from proximal to distal.

        TODO: Production-harden with singularity handling.
        """
        raise NotImplementedError("KinematicsEngine.bone_direction is not implemented.")
