"""Hierarchy construction and graph queries for avatar skeletons."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.constants import MAX_HIERARCHY_DEPTH
from motion_engine.rendering.avatar.skeleton.exceptions import SkeletonValidationError


@dataclass(frozen=True, slots=True)
class HierarchyInfo:
    """Precomputed hierarchy tables for O(1)/O(n) queries."""

    children: tuple[tuple[int, ...], ...]
    parent: tuple[int | None, ...]
    roots: tuple[int, ...]
    depth: tuple[int, ...]
    height: tuple[int, ...]
    topo_order: tuple[int, ...]
    dfs_preorder: tuple[int, ...]
    dfs_postorder: tuple[int, ...]


def build_children(parent_indices: list[int | None]) -> list[list[int]]:
    """Build children adjacency lists from parent indices."""
    n = len(parent_indices)
    children: list[list[int]] = [[] for _ in range(n)]
    for i, p in enumerate(parent_indices):
        if p is None:
            continue
        if p < 0 or p >= n:
            raise SkeletonValidationError(
                f"Invalid parent index {p} for bone {i}",
                code="SKEL_BAD_PARENT",
                details={"bone": i, "parent": p},
            )
        if p == i:
            raise SkeletonValidationError(
                f"Bone {i} is its own parent",
                code="SKEL_SELF_PARENT",
                details={"bone": i},
            )
        children[p].append(i)
    # Deterministic sibling order: ascending child index.
    for kids in children:
        kids.sort()
    return children


def find_roots(parent_indices: list[int | None]) -> list[int]:
    """Return indices of bones with ``parent is None``, sorted."""
    return sorted(i for i, p in enumerate(parent_indices) if p is None)


def detect_cycle(parent_indices: list[int | None]) -> list[int]:
    """Return one parent-pointer cycle as bone indices, or an empty list."""
    n = len(parent_indices)
    # White/gray/black along parent edges (each node has out-degree ≤ 1).
    color = [0] * n  # 0=white, 1=gray, 2=black

    def walk(start: int) -> list[int]:
        path: list[int] = []
        cur: int | None = start
        while cur is not None:
            if cur < 0 or cur >= n:
                break
            if color[cur] == 1:
                # ``cur`` is on the active path → cycle.
                return path[path.index(cur) :] + [cur]
            if color[cur] == 2:
                break
            color[cur] = 1
            path.append(cur)
            cur = parent_indices[cur]
        for u in path:
            color[u] = 2
        return []

    for i in range(n):
        if color[i] == 0:
            cyc = walk(i)
            if cyc:
                return cyc
    return []


def topological_order(parent_indices: list[int | None], children: list[list[int]]) -> list[int]:
    """Parent-before-child order (Kahn / BFS from roots). Raises on cycles."""
    n = len(parent_indices)
    indeg = [0] * n
    for i, p in enumerate(parent_indices):
        if p is not None:
            indeg[i] = 1
    # Roots have indegree 0; also treat forest correctly.
    q = deque(sorted(i for i in range(n) if parent_indices[i] is None))
    order: list[int] = []
    seen = 0
    while q:
        u = q.popleft()
        order.append(u)
        seen += 1
        for v in children[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if seen != n:
        raise SkeletonValidationError(
            "Hierarchy contains a cycle or unreachable nodes",
            code="SKEL_CYCLE",
            details={"ordered": seen, "total": n},
        )
    return order


def compute_depths(parent_indices: list[int | None], topo: list[int]) -> list[int]:
    """Depth of each bone (roots = 0)."""
    depth = [0] * len(parent_indices)
    for i in topo:
        p = parent_indices[i]
        depth[i] = 0 if p is None else depth[p] + 1
    return depth


def compute_heights(children: list[list[int]], topo: list[int]) -> list[int]:
    """Height of subtree rooted at each bone (leaf = 0)."""
    n = len(children)
    height = [0] * n
    for i in reversed(topo):
        if not children[i]:
            height[i] = 0
        else:
            height[i] = 1 + max(height[c] for c in children[i])
    return height


def ancestors_of(index: int, parent_indices: list[int | None]) -> list[int]:
    """Return ancestors from parent to root (exclusive of ``index``)."""
    out: list[int] = []
    seen: set[int] = set()
    cur = parent_indices[index]
    while cur is not None:
        if cur in seen:
            raise SkeletonValidationError(
                "Cycle encountered while walking ancestors",
                code="SKEL_CYCLE",
                details={"start": index},
            )
        seen.add(cur)
        out.append(cur)
        cur = parent_indices[cur]
    return out


def descendants_of(index: int, children: list[list[int]]) -> list[int]:
    """Return all descendants of ``index`` in DFS preorder (exclusive of self)."""
    out: list[int] = []

    def dfs(u: int) -> None:
        for v in children[u]:
            out.append(v)
            dfs(v)

    dfs(index)
    return out


def siblings_of(index: int, parent_indices: list[int | None], children: list[list[int]]) -> list[int]:
    """Return sibling indices (same parent), excluding ``index``."""
    p = parent_indices[index]
    if p is None:
        # other roots are siblings in a forest sense
        return [i for i, pp in enumerate(parent_indices) if pp is None and i != index]
    return [c for c in children[p] if c != index]


def path_between(a: int, b: int, parent_indices: list[int | None]) -> list[int]:
    """Return bone path from ``a`` to ``b`` via their LCA (inclusive)."""
    anc_a = {a, *ancestors_of(a, parent_indices)}
    # climb from b until hit anc_a
    up_b: list[int] = [b]
    cur: int | None = b
    while cur is not None and cur not in anc_a:
        cur = parent_indices[cur]
        if cur is not None:
            up_b.append(cur)
    if cur is None and a not in anc_a:
        # disconnected
        return []
    lca = cur if cur is not None else a
    # path a -> lca
    down_a: list[int] = [a]
    cur = a
    while cur != lca:
        cur = parent_indices[cur]  # type: ignore[assignment]
        assert cur is not None
        down_a.append(cur)
    # path lca -> b is reverse of up_b until lca
    idx = up_b.index(lca)
    up_segment = list(reversed(up_b[:idx]))
    return down_a + up_segment


def lowest_common_ancestor(a: int, b: int, parent_indices: list[int | None]) -> int | None:
    """Return LCA index, or ``None`` if bones are in disjoint trees."""
    anc = {a, *ancestors_of(a, parent_indices)}
    cur: int | None = b
    while cur is not None:
        if cur in anc:
            return cur
        cur = parent_indices[cur]
    return None


def bone_path_names(indices: list[int], bones: tuple[Bone, ...]) -> str:
    """Format a slash-separated bone path from indices."""
    return "/".join(bones[i].name for i in indices)


def build_hierarchy(bones: tuple[Bone, ...]) -> HierarchyInfo:
    """Build hierarchy tables from a bone tuple (parents already set)."""
    parent = [b.parent_index for b in bones]
    children_lists = build_children(parent)
    roots = find_roots(parent)
    if not roots and bones:
        raise SkeletonValidationError("Skeleton has no root bone", code="SKEL_NO_ROOT")
    cycle = detect_cycle(parent)
    if cycle:
        raise SkeletonValidationError(
            f"Hierarchy cycle detected: {cycle}",
            code="SKEL_CYCLE",
            details={"cycle": cycle},
        )
    topo = topological_order(parent, children_lists)
    depths = compute_depths(parent, topo)
    if depths and max(depths) > MAX_HIERARCHY_DEPTH:
        # still build; validation layer emits warning
        pass
    heights = compute_heights(children_lists, topo)

    # DFS preorder / postorder from sorted roots
    pre: list[int] = []
    post: list[int] = []

    def dfs(u: int) -> None:
        pre.append(u)
        for v in children_lists[u]:
            dfs(v)
        post.append(u)

    for r in roots:
        dfs(r)

    return HierarchyInfo(
        children=tuple(tuple(c) for c in children_lists),
        parent=tuple(parent),
        roots=tuple(roots),
        depth=tuple(depths),
        height=tuple(heights),
        topo_order=tuple(topo),
        dfs_preorder=tuple(pre),
        dfs_postorder=tuple(post),
    )


def attach_children(bones: list[Bone]) -> list[Bone]:
    """Return bones with ``children`` filled from parent indices."""
    parent = [b.parent_index for b in bones]
    children_lists = build_children(parent)
    return [b.with_children(tuple(children_lists[i])) for i, b in enumerate(bones)]


__all__ = [
    "HierarchyInfo",
    "build_children",
    "find_roots",
    "detect_cycle",
    "topological_order",
    "compute_depths",
    "compute_heights",
    "ancestors_of",
    "descendants_of",
    "siblings_of",
    "path_between",
    "lowest_common_ancestor",
    "bone_path_names",
    "build_hierarchy",
    "attach_children",
]
