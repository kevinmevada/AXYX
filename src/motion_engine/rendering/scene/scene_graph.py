"""Lightweight scene graph for future avatar / ground / light nodes."""

from __future__ import annotations

import logging
from typing import Iterator

from motion_engine.rendering.scene.scene_node import RenderNode, SceneNode, TransformNode

logger = logging.getLogger(__name__)


class SceneGraph:
    """Rooted tree of scene nodes.

    Today the PyVista path still uses draw queues; this graph is the
    forward-looking structure avatars, ground, and lights will attach to.
    """

    def __init__(self, name: str = "root") -> None:
        self.root = TransformNode(name=name)

    def add(self, node: SceneNode, *, parent: SceneNode | None = None) -> SceneNode:
        target = parent or self.root
        target.add_child(node)
        logger.debug("SceneGraph: added %r under %r", node.name, target.name)
        return node

    def find(self, name: str) -> SceneNode | None:
        return self.root.find(name)

    def iter_render_nodes(self) -> Iterator[RenderNode]:
        for node in self.root.walk():
            if isinstance(node, RenderNode) and node.visible:
                yield node

    def clear(self) -> None:
        self.root.children.clear()
        logger.debug("SceneGraph cleared")


__all__ = ["SceneGraph", "SceneNode", "TransformNode", "RenderNode"]
