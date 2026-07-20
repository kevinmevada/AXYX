"""Deterministic hierarchy traversal iterators."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton
    from motion_engine.rendering.avatar.skeleton.hierarchy import HierarchyInfo


def iter_dfs_preorder(hierarchy: HierarchyInfo) -> Iterator[int]:
    """Depth-first preorder (roots in ascending index order)."""
    yield from hierarchy.dfs_preorder


def iter_dfs_postorder(hierarchy: HierarchyInfo) -> Iterator[int]:
    """Depth-first postorder."""
    yield from hierarchy.dfs_postorder


def iter_bfs(hierarchy: HierarchyInfo) -> Iterator[int]:
    """Breadth-first order from sorted roots."""
    children = hierarchy.children
    q: deque[int] = deque(hierarchy.roots)
    while q:
        u = q.popleft()
        yield u
        q.extend(children[u])


def iter_leaves(hierarchy: HierarchyInfo) -> Iterator[int]:
    """Yield leaf bone indices in ascending index order."""
    for i, kids in enumerate(hierarchy.children):
        if not kids:
            yield i


def iter_root_to_leaf_paths(hierarchy: HierarchyInfo) -> Iterator[tuple[int, ...]]:
    """Yield every root→leaf path as a tuple of indices."""
    children = hierarchy.children
    for root in hierarchy.roots:
        stack: list[tuple[int, tuple[int, ...]]] = [(root, (root,))]
        while stack:
            u, path = stack.pop()
            kids = children[u]
            if not kids:
                yield path
                continue
            # Push high indices first so low indices are processed first (deterministic).
            for v in reversed(kids):
                stack.append((v, path + (v,)))


def iter_topo(hierarchy: HierarchyInfo) -> Iterator[int]:
    """Parent-before-child topological order."""
    yield from hierarchy.topo_order


class SkeletonTraversal:
    """Traversal helpers bound to an :class:`AvatarSkeleton`."""

    def __init__(self, skeleton: AvatarSkeleton) -> None:
        self._sk = skeleton

    def dfs(self) -> Iterator[int]:
        """Depth-first preorder indices."""
        return iter_dfs_preorder(self._sk.hierarchy)

    def dfs_post(self) -> Iterator[int]:
        """Depth-first postorder indices."""
        return iter_dfs_postorder(self._sk.hierarchy)

    def bfs(self) -> Iterator[int]:
        """Breadth-first indices."""
        return iter_bfs(self._sk.hierarchy)

    def leaves(self) -> Iterator[int]:
        """Leaf indices."""
        return iter_leaves(self._sk.hierarchy)

    def root_to_leaf(self) -> Iterator[tuple[int, ...]]:
        """Root-to-leaf paths."""
        return iter_root_to_leaf_paths(self._sk.hierarchy)

    def topo(self) -> Iterator[int]:
        """Topological (FK) order."""
        return iter_topo(self._sk.hierarchy)


__all__ = [
    "iter_dfs_preorder",
    "iter_dfs_postorder",
    "iter_bfs",
    "iter_leaves",
    "iter_root_to_leaf_paths",
    "iter_topo",
    "SkeletonTraversal",
]
