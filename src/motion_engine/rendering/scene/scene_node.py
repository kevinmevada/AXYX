"""Scene graph node base types."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterator
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.floating]


@dataclass(slots=True)
class SceneNode:
    """Hierarchical scene element."""

    name: str
    node_id: str = field(default_factory=lambda: uuid4().hex)
    parent: SceneNode | None = field(default=None, repr=False)
    children: list[SceneNode] = field(default_factory=list, repr=False)
    visible: bool = True
    user_data: dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: SceneNode) -> SceneNode:
        child.parent = self
        self.children.append(child)
        return child

    def remove_child(self, child: SceneNode) -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def walk(self) -> Iterator[SceneNode]:
        yield self
        for child in self.children:
            yield from child.walk()

    def find(self, name: str) -> SceneNode | None:
        for node in self.walk():
            if node.name == name:
                return node
        return None


@dataclass(slots=True)
class TransformNode(SceneNode):
    """Node with a local 4×4 transform (identity by default)."""

    local_matrix: FloatArray = field(
        default_factory=lambda: np.eye(4, dtype=float)
    )

    def world_matrix(self) -> FloatArray:
        """Compose parent chain into a world matrix."""
        matrix = np.asarray(self.local_matrix, dtype=float)
        parent = self.parent
        while parent is not None:
            if isinstance(parent, TransformNode):
                matrix = np.asarray(parent.local_matrix, dtype=float) @ matrix
            parent = parent.parent
        return matrix


@dataclass(slots=True)
class RenderNode(TransformNode):
    """Drawable node — payload is backend-specific (mesh key, actor, …)."""

    drawable: Any | None = None
    material_key: str | None = None
    layer: str = "default"

    def prepare(self, context: Any) -> None:
        """Optional per-frame prep (override in subclasses)."""
        _ = context


__all__ = ["SceneNode", "TransformNode", "RenderNode"]
