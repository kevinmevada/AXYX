"""
Future export interfaces for DCC / robotics / simulation platforms.

These exporters consume :class:`~motion_engine.skeleton.Skeleton` only -
never MATLAB or MotionDatabase internals.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motion_engine.skeleton import Skeleton


class SkeletonExporter(ABC):
    """Base class for skeleton / animation exporters."""

    @abstractmethod
    def export(self, skeleton: Skeleton, path: Path) -> Path:
        """Export ``skeleton`` to ``path`` and return the written path."""


class BlenderExporter(SkeletonExporter):
    """TODO: Export to Blender via bpy / USD / FBX pipeline."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("BlenderExporter is reserved for a future phase.")


class UnityExporter(SkeletonExporter):
    """TODO: Export Unity-friendly FBX / JSON joint streams."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("UnityExporter is reserved for a future phase.")

class OpenSimExporter(SkeletonExporter):
    """TODO: Export OpenSim .trc / .mot compatible kinematics."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("OpenSimExporter is reserved for a future phase.")


class FbxExporter(SkeletonExporter):
    """TODO: Export Autodesk FBX."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("FbxExporter is reserved for a future phase.")


class BvhExporter(SkeletonExporter):
    """TODO: Export Biovision BVH hierarchy + motion."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("BvhExporter is reserved for a future phase.")


class GltfExporter(SkeletonExporter):
    """TODO: Export glTF / GLB skinned animation."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("GltfExporter is reserved for a future phase.")


class UsdExporter(SkeletonExporter):
    """TODO: Export USD / Omniverse-ready stages."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("UsdExporter is reserved for a future phase.")


class RosExporter(SkeletonExporter):
    """TODO: Export ROS JointState / URDF visualization stream."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("RosExporter is reserved for a future phase.")


class OmniverseExporter(SkeletonExporter):
    """TODO: Export NVIDIA Omniverse Nucleus assets."""

    def export(self, skeleton: Skeleton, path: Path) -> Path:
        raise NotImplementedError("OmniverseExporter is reserved for a future phase.")
