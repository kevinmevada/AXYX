"""
Scene graph for the Visualization Engine.

Defines renderer-neutral scene nodes. Concrete backends convert these into
Open3D / PyVista / OpenGL / Vulkan primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from motion_engine.colors import ColorRGB, DEFAULT_THEME


@dataclass(slots=True)
class SceneNode:
    """Base scene-graph node."""

    name: str
    visible: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GroundPlane(SceneNode):
    """Infinite / finite ground plane under the skeleton."""

    name: str = "ground"
    size: float = 2000.0
    color: ColorRGB = DEFAULT_THEME.ground


@dataclass(slots=True)
class CoordinateAxes(SceneNode):
    """RGB coordinate triad at the origin (or tracked joint)."""

    name: str = "axes"
    length: float = 200.0
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(slots=True)
class Light(SceneNode):
    """Scene light (architecture for future PBR backends)."""

    name: str = "key_light"
    intensity: float = 1.0
    position: tuple[float, float, float] = (1000.0, 1000.0, 1000.0)


@dataclass(slots=True)
class SkeletonNode(SceneNode):
    """Placeholder node identifying a skeleton attachment in the scene."""

    name: str = "skeleton"
    show_joints: bool = True
    show_bones: bool = True
    show_joint_labels: bool = False
    show_bone_labels: bool = False


@dataclass(slots=True)
class Scene:
    """Top-level scene graph consumed by a :class:`~motion_engine.renderer.Renderer`."""

    ground: GroundPlane = field(default_factory=GroundPlane)
    axes: CoordinateAxes = field(default_factory=CoordinateAxes)
    skeleton_node: SkeletonNode = field(default_factory=SkeletonNode)
    lights: list[Light] = field(default_factory=lambda: [Light()])
    show_grid: bool = True
    show_ground: bool = True
    show_axes: bool = False
    background: ColorRGB = DEFAULT_THEME.background

    # TODO: Add MeshNode, RobotNode, TrajectoryRibbonNode for future layers.
