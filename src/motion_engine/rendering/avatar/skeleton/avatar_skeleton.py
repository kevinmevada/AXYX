"""Canonical runtime AvatarSkeleton — single source of truth for M2+."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Sequence

import numpy as np

from motion_engine.rendering.avatar.skeleton.bind_data import BindData, bind_data_from_bones
from motion_engine.rendering.avatar.skeleton.bone import Bone
from motion_engine.rendering.avatar.skeleton.constants import DEFAULT_SKELETON_NAME
from motion_engine.rendering.avatar.skeleton.exceptions import BoneNotFoundError
from motion_engine.rendering.avatar.skeleton.hierarchy import (
    HierarchyInfo,
    ancestors_of,
    attach_children,
    bone_path_names,
    build_hierarchy,
    descendants_of,
    lowest_common_ancestor,
    path_between,
    siblings_of,
)
from motion_engine.rendering.avatar.skeleton.lookup import BoneLookup
from motion_engine.rendering.avatar.skeleton.metadata import SkeletonMetadata
from motion_engine.rendering.avatar.skeleton.statistics import (
    SkeletonStatistics,
    compute_statistics,
)
from motion_engine.rendering.avatar.skeleton.transforms import (
    Transform,
    propagate_world,
)
from motion_engine.rendering.avatar.skeleton.traversal import SkeletonTraversal
from motion_engine.rendering.avatar.skeleton.types import Mat4
from motion_engine.rendering.avatar.skeleton.validation import (
    SkeletonValidator,
    ValidationReport,
    validate_bones,
)


@dataclass(frozen=True, slots=True)
class AvatarSkeleton:
    """Authoritative runtime skeleton representation.

    Owns hierarchy, bone storage, queries, validation hooks, statistics,
    metadata, and traversal. Does **not** own rendering, animation, skinning,
    or retargeting state.
    """

    name: str
    bones: tuple[Bone, ...]
    hierarchy: HierarchyInfo
    lookup: BoneLookup
    metadata: SkeletonMetadata
    statistics: SkeletonStatistics
    bind_data: BindData

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_bones(
        cls,
        bones: Sequence[Bone],
        *,
        name: str = DEFAULT_SKELETON_NAME,
        metadata: SkeletonMetadata | None = None,
        validate: bool = True,
        require_inverse_bind: bool = False,
        allow_multiple_roots: bool = True,
    ) -> AvatarSkeleton:
        """Build a runtime skeleton from a bone sequence.

        Attaches children, builds hierarchy/lookup/statistics, optionally
        validates, and stores bind buffers.
        """
        bone_list = attach_children(list(bones))
        # Propagate world from local if caller left identity worlds inconsistently:
        # Prefer authored world matrices; rebuild only when requested via rebuild_world_rest.
        hierarchy = build_hierarchy(tuple(bone_list))
        # Ensure children on bone objects match hierarchy (already done by attach_children).
        bone_tuple = tuple(bone_list)
        lookup = BoneLookup.build(bone_tuple)
        meta = (metadata or SkeletonMetadata(skeleton_name=name)).with_bone_count(len(bone_tuple))
        if not meta.skeleton_name:
            meta = SkeletonMetadata(
                coordinate_system=meta.coordinate_system,
                units=meta.units,
                source_format=meta.source_format,
                importer_version=meta.importer_version,
                bone_count=len(bone_tuple),
                creation_timestamp=meta.creation_timestamp,
                runtime_version=meta.runtime_version,
                skeleton_name=name,
                source_asset_id=meta.source_asset_id,
                extra=meta.extra,
            )
        stats = compute_statistics(bone_tuple, hierarchy)
        bind = bind_data_from_bones(bone_tuple)
        skel = cls(
            name=name,
            bones=bone_tuple,
            hierarchy=hierarchy,
            lookup=lookup,
            metadata=meta,
            statistics=stats,
            bind_data=bind,
        )
        if validate:
            report = SkeletonValidator(
                require_inverse_bind=require_inverse_bind,
                allow_multiple_roots=allow_multiple_roots,
            ).validate(bone_tuple)
            report.raise_if_invalid()
        return skel

    # ------------------------------------------------------------------
    # Basic properties
    # ------------------------------------------------------------------

    @property
    def bone_count(self) -> int:
        """Number of bones."""
        return len(self.bones)

    @property
    def roots(self) -> tuple[int, ...]:
        """Root bone indices."""
        return self.hierarchy.roots

    @property
    def traversal(self) -> SkeletonTraversal:
        """Bound traversal helper."""
        return SkeletonTraversal(self)

    # ------------------------------------------------------------------
    # Rest / bind accessors (spec §4)
    # ------------------------------------------------------------------

    def rest_local(self, index: int) -> Transform:
        """Local rest transform for bone ``index``."""
        return self.bones[index].local_transform

    def rest_world(self, index: int) -> Mat4:
        """World rest matrix for bone ``index``."""
        return self.bones[index].world_matrix

    def inverse_bind(self, index: int) -> Mat4 | None:
        """Inverse bind matrix for bone ``index``."""
        return self.bones[index].inverse_bind

    def rebuild_world_rest(self) -> AvatarSkeleton:
        """Recompute world rest matrices via FK and return a new skeleton."""
        locals_m = [b.local_matrix for b in self.bones]
        parents = list(self.hierarchy.parent)
        worlds = propagate_world(
            locals_m,
            parents,
            topo_order=list(self.hierarchy.topo_order),
        )
        new_bones = [b.with_world(worlds[i]) for i, b in enumerate(self.bones)]
        return AvatarSkeleton.from_bones(
            new_bones,
            name=self.name,
            metadata=self.metadata,
            validate=False,
        )

    # ------------------------------------------------------------------
    # Lookup API
    # ------------------------------------------------------------------

    def find(self, key: str | int) -> Bone:
        """Find bone by name or index (O(1))."""
        return self.lookup.find(key)

    def exists(self, key: str | int) -> bool:
        """Return True if name/index exists."""
        return self.lookup.exists(key)

    def index_of(self, name: str) -> int:
        """O(1) name → index."""
        return self.lookup.index_of(name)

    def bone(self, key: str | int) -> Bone:
        """Alias for :meth:`find`."""
        return self.find(key)

    def try_bone(self, key: str | int) -> Bone | None:
        """Return bone or ``None``."""
        return self.lookup.try_find(key)

    def parent(self, key: str | int) -> Bone | None:
        """Return parent bone or ``None`` for roots."""
        b = self.find(key)
        if b.parent_index is None:
            return None
        return self.bones[b.parent_index]

    def children(self, key: str | int) -> tuple[Bone, ...]:
        """Direct children of ``key``."""
        b = self.find(key)
        return tuple(self.bones[i] for i in b.children)

    def ancestors(self, key: str | int) -> tuple[int, ...]:
        """Ancestor indices from parent to root."""
        idx = self.lookup.index_of(key)
        return tuple(ancestors_of(idx, list(self.hierarchy.parent)))

    def descendants(self, key: str | int) -> tuple[int, ...]:
        """Descendant indices (DFS preorder)."""
        idx = self.lookup.index_of(key)
        return tuple(descendants_of(idx, [list(c) for c in self.hierarchy.children]))

    def siblings(self, key: str | int) -> tuple[Bone, ...]:
        """Sibling bones (excluding self)."""
        idx = self.lookup.index_of(key)
        sibs = siblings_of(
            idx,
            list(self.hierarchy.parent),
            [list(c) for c in self.hierarchy.children],
        )
        return tuple(self.bones[i] for i in sibs)

    def root(self, key: str | int | None = None) -> Bone:
        """Return the root of ``key``'s tree, or the first skeleton root."""
        if key is None:
            if not self.hierarchy.roots:
                raise BoneNotFoundError("root")
            return self.bones[self.hierarchy.roots[0]]
        idx = self.lookup.index_of(key)
        cur = idx
        while self.hierarchy.parent[cur] is not None:
            cur = self.hierarchy.parent[cur]  # type: ignore[assignment]
        return self.bones[cur]

    def is_leaf(self, key: str | int) -> bool:
        """True if bone has no children."""
        return self.find(key).is_leaf

    def is_root(self, key: str | int) -> bool:
        """True if bone is a root."""
        return self.find(key).is_root

    def path(self, key: str | int) -> str:
        """Slash-separated path from root to bone."""
        idx = self.lookup.index_of(key)
        chain = list(reversed(self.ancestors(idx))) + [idx]
        return bone_path_names(chain, self.bones)

    def depth(self, key: str | int) -> int:
        """Depth of bone (root = 0)."""
        return self.hierarchy.depth[self.lookup.index_of(key)]

    def height(self, key: str | int) -> int:
        """Subtree height (leaf = 0)."""
        return self.hierarchy.height[self.lookup.index_of(key)]

    def common_ancestor(self, a: str | int, b: str | int) -> Bone | None:
        """Lowest common ancestor bone, or ``None`` if disconnected."""
        ia = self.lookup.index_of(a)
        ib = self.lookup.index_of(b)
        lca = lowest_common_ancestor(ia, ib, list(self.hierarchy.parent))
        if lca is None:
            return None
        return self.bones[lca]

    def path_between(self, a: str | int, b: str | int) -> tuple[int, ...]:
        """Index path from ``a`` to ``b`` via LCA."""
        ia = self.lookup.index_of(a)
        ib = self.lookup.index_of(b)
        return tuple(path_between(ia, ib, list(self.hierarchy.parent)))

    # ------------------------------------------------------------------
    # Validation / iteration
    # ------------------------------------------------------------------

    def validate(
        self,
        *,
        require_inverse_bind: bool = False,
        allow_multiple_roots: bool = True,
    ) -> ValidationReport:
        """Re-run validation on this skeleton."""
        return validate_bones(
            self.bones,
            require_inverse_bind=require_inverse_bind,
            allow_multiple_roots=allow_multiple_roots,
        )

    def __iter__(self) -> Iterator[Bone]:
        return iter(self.bones)

    def __len__(self) -> int:
        return len(self.bones)

    def __getitem__(self, index: int) -> Bone:
        return self.bones[index]


__all__ = ["AvatarSkeleton"]
