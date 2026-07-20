"""
Parent-child hierarchy utilities for skeletal graphs.

Status
------
Interface / placeholder. SkeletonBuilder currently builds adjacency from the
YAML definition inside :mod:`motion_engine.skeleton`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HierarchyNode:
    """One node in a directed kinematic tree."""

    name: str
    parent: str | None = None
    children: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Hierarchy:
    """Directed tree of joint names."""

    root: str
    nodes: dict[str, HierarchyNode] = field(default_factory=dict)

    def children_of(self, joint_name: str) -> list[str]:
        """Return child joint names."""
        node = self.nodes.get(joint_name)
        return list(node.children) if node else []

    def ancestors(self, joint_name: str) -> list[str]:
        """Return ancestor names from parent up to root.

        TODO: Implement walk using ``nodes[parent]`` links.
        """
        raise NotImplementedError("Hierarchy.ancestors is reserved for IK/export.")


def build_hierarchy_from_bones(
    root: str,
    bones: list[tuple[str, str]],
) -> Hierarchy:
    """Build a :class:`Hierarchy` from ``(parent_joint, child_joint)`` edges.

    TODO: Extract shared implementation from SkeletonBuilder.
    """
    raise NotImplementedError(
        "build_hierarchy_from_bones will be extracted from skeleton.py"
    )
