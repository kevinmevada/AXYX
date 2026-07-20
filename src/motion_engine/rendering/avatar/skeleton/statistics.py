"""Automatic skeleton statistics."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.hierarchy import HierarchyInfo, detect_cycle


@dataclass(frozen=True, slots=True)
class SkeletonStatistics:
    """Computed hierarchy / naming statistics."""

    bone_count: int
    leaf_count: int
    internal_count: int
    root_count: int
    average_branching_factor: float
    max_branching: int
    tree_depth: int
    tree_height: int
    longest_chain: int
    cycle_count: int
    unique_name_count: int
    duplicate_name_count: int
    bones_with_ibm: int
    mean_name_length: float
    max_name_length: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize statistics to a plain dict."""
        return asdict(self)


def compute_statistics(bones: tuple[Bone, ...], hierarchy: HierarchyInfo) -> SkeletonStatistics:
    """Compute statistics from bones and hierarchy tables."""
    n = len(bones)
    leaf_count = sum(1 for kids in hierarchy.children if not kids)
    internal_count = n - leaf_count
    root_count = len(hierarchy.roots)
    branch_counts = [len(kids) for kids in hierarchy.children if kids]
    avg_branch = (sum(branch_counts) / len(branch_counts)) if branch_counts else 0.0
    max_branch = max((len(kids) for kids in hierarchy.children), default=0)
    tree_depth = max(hierarchy.depth) if hierarchy.depth else 0
    tree_height = max(hierarchy.height) if hierarchy.height else 0
    longest_chain = tree_depth + 1 if n else 0
    parents = list(hierarchy.parent)
    cycle_count = 1 if detect_cycle(parents) else 0
    names = [b.name for b in bones]
    counts = Counter(names)
    dup = sum(1 for c in counts.values() if c > 1)
    name_lens = [len(nm) for nm in names]
    mean_len = (sum(name_lens) / len(name_lens)) if name_lens else 0.0
    ibm = sum(1 for b in bones if b.inverse_bind is not None)
    return SkeletonStatistics(
        bone_count=n,
        leaf_count=leaf_count,
        internal_count=internal_count,
        root_count=root_count,
        average_branching_factor=avg_branch,
        max_branching=max_branch,
        tree_depth=tree_depth,
        tree_height=tree_height,
        longest_chain=longest_chain,
        cycle_count=cycle_count,
        unique_name_count=len(counts),
        duplicate_name_count=dup,
        bones_with_ibm=ibm,
        mean_name_length=mean_len,
        max_name_length=max(name_lens) if name_lens else 0,
    )


__all__ = ["SkeletonStatistics", "compute_statistics"]
