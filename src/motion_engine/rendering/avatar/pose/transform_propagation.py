"""Deterministic forward-kinematics transform propagation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from motion_engine.rendering.avatar.pose.matrix_utils import identity_matrix, matrices_close
from motion_engine.rendering.avatar.pose.types import Mat4


@dataclass(frozen=True, slots=True)
class PropagationResult:
    """Outcome of a full FK pass."""

    world_matrices: tuple[Mat4, ...]
    topo_order: tuple[int, ...]

    @property
    def bone_count(self) -> int:
        return len(self.world_matrices)


def propagate_world_transforms(
    local_matrices: list[Mat4],
    parent_indices: list[int | None],
    *,
    topo_order: list[int] | None = None,
) -> PropagationResult:
    """Compute world = parent_world @ local for every bone.

    Order is deterministic: if ``topo_order`` is omitted, roots (ascending)
    followed by a stable BFS over ascending children.
    """
    n = len(local_matrices)
    if len(parent_indices) != n:
        raise ValueError("parent_indices length mismatch")

    if topo_order is None:
        children: list[list[int]] = [[] for _ in range(n)]
        for i, p in enumerate(parent_indices):
            if p is not None:
                children[p].append(i)
        for kids in children:
            kids.sort()
        roots = sorted(i for i, p in enumerate(parent_indices) if p is None)
        order: list[int] = []
        stack = list(reversed(roots))
        # BFS via queue simulation with sorted children
        from collections import deque

        q: deque[int] = deque(roots)
        while q:
            u = q.popleft()
            order.append(u)
            q.extend(children[u])
        topo_order = order

    world: list[Mat4] = [identity_matrix() for _ in range(n)]
    for i in topo_order:
        p = parent_indices[i]
        local = np.asarray(local_matrices[i], dtype=np.float64).reshape(4, 4)
        if p is None:
            world[i] = local.copy()
        else:
            world[i] = world[p] @ local
    return PropagationResult(
        world_matrices=tuple(world),
        topo_order=tuple(topo_order),
    )


def verify_propagation(
    local_matrices: list[Mat4],
    world_matrices: list[Mat4],
    parent_indices: list[int | None],
    *,
    eps: float = 1e-6,
) -> list[int]:
    """Return indices whose stored world disagrees with recomputed FK."""
    recomputed = propagate_world_transforms(local_matrices, parent_indices)
    bad: list[int] = []
    for i, (a, b) in enumerate(zip(world_matrices, recomputed.world_matrices, strict=True)):
        if not matrices_close(a, b, eps=eps):
            bad.append(i)
    return bad


__all__ = [
    "PropagationResult",
    "propagate_world_transforms",
    "verify_propagation",
]
