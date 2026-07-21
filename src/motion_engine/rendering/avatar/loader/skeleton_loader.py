"""Skeleton loader — hierarchy + bind matrices only (no animation)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from motion_engine.rendering.avatar.loader.exceptions import SkeletonLoadError
from motion_engine.rendering.avatar.loader.path_utils import resolve_under_root
from motion_engine.rendering.avatar.models.avatar_manifest import AvatarManifest
from motion_engine.rendering.avatar.models.skeleton import AvatarSkeleton, BoneData

logger = logging.getLogger(__name__)


class SkeletonLoader:
    """Load avatar skeleton hierarchy and bind data.

    Supports:
      * JSON hierarchy caches (MetaHuman ``skeleton.json``)
      * NPZ sidecars embedding ``bone_names`` / ``inv_bind`` / ``bind_world``

    Example:
        >>> skel = SkeletonLoader().load_from_manifest(manifest)
    """

    def load_from_manifest(self, manifest: AvatarManifest) -> AvatarSkeleton | None:
        """Load skeleton declared by ``manifest``, or ``None`` for procedural."""
        t0 = time.perf_counter()
        logger.info("Skeleton load started for %s", manifest.name)
        block = dict(manifest.skeleton)

        if manifest.avatar_type == "procedural" and not block.get("hierarchy_cache"):
            # Optional: skeleton_definition path — M1 leaves None (AXYX skeleton elsewhere)
            logger.info("Procedural avatar — no imported AvatarSkeleton")
            return None

        # Prefer NPZ that embeds full bone palette (research packs)
        lod_rel = manifest.lod_path()
        if lod_rel and lod_rel.endswith(".npz"):
            npz_path = resolve_under_root(manifest.root, lod_rel)
            if npz_path.is_file():
                hierarchy_path = None
                hier = block.get("hierarchy_cache")
                if hier:
                    hierarchy_path = resolve_under_root(manifest.root, str(hier))
                skel = self.load_from_npz(npz_path, hierarchy_json=hierarchy_path)
                logger.info(
                    "Skeleton loaded bones=%d (%.2f ms)",
                    skel.bone_count,
                    (time.perf_counter() - t0) * 1000.0,
                )
                return skel

        hier = block.get("hierarchy_cache") or block.get("path")
        if hier:
            path = resolve_under_root(manifest.root, str(hier))
            skel = self.load_json_hierarchy(path)
            logger.info(
                "Skeleton loaded bones=%d (%.2f ms)",
                skel.bone_count,
                (time.perf_counter() - t0) * 1000.0,
            )
            return skel

        if manifest.avatar_type == "procedural":
            return None
        raise SkeletonLoadError(
            f"Manifest {manifest.name!r} does not declare a skeleton source"
        )

    def load_from_npz(
        self, path: Path, *, hierarchy_json: Path | None = None
    ) -> AvatarSkeleton:
        """Build skeleton from NPZ bone tables + optional JSON parents."""
        path = Path(path)
        if not path.is_file():
            raise SkeletonLoadError(f"Skeleton NPZ not found: {path}")
        try:
            data = np.load(path, allow_pickle=True)
        except Exception as exc:
            raise SkeletonLoadError(f"Corrupted skeleton NPZ {path}: {exc}") from exc
        if "bone_names" not in data.files:
            raise SkeletonLoadError(f"NPZ missing bone_names: {path}")

        names = [str(n) for n in data["bone_names"].tolist()]
        bind_world = (
            np.asarray(data["bind_world"], dtype=np.float64)
            if "bind_world" in data.files
            else None
        )
        inv_bind = (
            np.asarray(data["inv_bind"], dtype=np.float64)
            if "inv_bind" in data.files
            else None
        )

        parents: dict[str, str | None] = {}
        translations: dict[str, tuple[float, float, float]] = {}
        if hierarchy_json is not None and hierarchy_json.is_file():
            parents, translations = self._parse_hierarchy_nodes(hierarchy_json)

        name_to_index = {n: i for i, n in enumerate(names)}
        bones: list[BoneData] = []
        for i, name in enumerate(names):
            parent_index = self._resolve_parent_index(name, parents, name_to_index)
            loc = translations.get(name, (0.0, 0.0, 0.0))
            bw = bind_world[i] if bind_world is not None else None
            ibm = inv_bind[i] if inv_bind is not None else None
            bones.append(
                BoneData(
                    index=i,
                    name=name,
                    parent_index=parent_index,
                    local_translation=loc,
                    bind_world=bw,
                    inverse_bind=ibm,
                )
            )

        # Ensure first bone is treated as root when flat-attached
        if bones and bones[0].parent_index is not None:
            b0 = bones[0]
            bones[0] = BoneData(
                index=0,
                name=b0.name,
                parent_index=None,
                local_translation=b0.local_translation,
                bind_world=b0.bind_world,
                inverse_bind=b0.inverse_bind,
            )

        return AvatarSkeleton(name=path.stem, bones=tuple(bones))

    def load_json_hierarchy(self, path: Path) -> AvatarSkeleton:
        """Load a JSON hierarchy cache (nodes / drive_bones)."""
        path = Path(path)
        if not path.is_file():
            raise SkeletonLoadError(f"Skeleton JSON not found: {path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SkeletonLoadError(f"Invalid skeleton JSON {path}: {exc}") from exc
        parents, translations = self._nodes_from_raw(raw)
        order = list(raw.get("drive_order") or parents.keys())
        if not order:
            raise SkeletonLoadError(f"Skeleton JSON has no bones: {path}")

        name_to_index = {n: i for i, n in enumerate(order)}
        bones: list[BoneData] = []
        bind_world_map = raw.get("drive_bind_world") or {}
        for i, name in enumerate(order):
            parent_index = self._resolve_parent_index(name, parents, name_to_index)
            bw = None
            if name in bind_world_map:
                bw = np.asarray(bind_world_map[name], dtype=np.float64)
            ibm = np.linalg.inv(bw) if bw is not None else None
            bones.append(
                BoneData(
                    index=i,
                    name=name,
                    parent_index=parent_index,
                    local_translation=translations.get(name, (0.0, 0.0, 0.0)),
                    bind_world=bw,
                    inverse_bind=ibm,
                )
            )
        return AvatarSkeleton(name=path.stem, bones=tuple(bones))

    @staticmethod
    def _resolve_parent_index(
        name: str,
        parents: Mapping[str, str | None],
        name_to_index: Mapping[str, int],
    ) -> int | None:
        """Map a bone to its parent index inside the active palette.

        MetaHuman packs often ship a short *drive* hierarchy (``nodes``) plus a
        much larger NPZ skinning palette. Bones with no hierarchy entry must
        **not** be fake-parented to root — that produces a starburst overlay.
        When a declared parent is absent from the palette, walk up ancestors
        until a palette member is found.
        """
        if name not in parents:
            return None
        parent_name = parents[name]
        if parent_name is None:
            return None
        seen: set[str] = set()
        cur: str | None = parent_name
        while cur is not None and cur not in name_to_index and cur not in seen:
            seen.add(cur)
            cur = parents.get(cur)
        if cur is None:
            return None
        return int(name_to_index[cur])

    def _parse_hierarchy_nodes(
        self, path: Path
    ) -> tuple[dict[str, str | None], dict[str, tuple[float, float, float]]]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return self._nodes_from_raw(raw)

    def _nodes_from_raw(
        self, raw: Mapping[str, Any]
    ) -> tuple[dict[str, str | None], dict[str, tuple[float, float, float]]]:
        nodes = raw.get("nodes") or raw.get("drive_bones") or {}
        parents: dict[str, str | None] = {}
        translations: dict[str, tuple[float, float, float]] = {}
        if not isinstance(nodes, Mapping):
            raise SkeletonLoadError("skeleton nodes must be an object")
        for name, node in nodes.items():
            if not isinstance(node, Mapping):
                continue
            parent = node.get("parent")
            parents[str(name)] = None if parent is None else str(parent)
            tr = node.get("translation") or [0.0, 0.0, 0.0]
            translations[str(name)] = (float(tr[0]), float(tr[1]), float(tr[2]))
        return parents, translations


__all__ = ["SkeletonLoader"]
