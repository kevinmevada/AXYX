"""Debug serialization for AvatarSkeleton (not runtime persistence)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from motion_engine.rendering.avatar.skeleton.exceptions import SkeletonSerializationError
from motion_engine.rendering.avatar.skeleton.hierarchy import bone_path_names

if TYPE_CHECKING:
    from motion_engine.rendering.avatar.skeleton.avatar_skeleton import AvatarSkeleton


def export_metadata(skeleton: AvatarSkeleton) -> dict[str, Any]:
    """Export metadata dict."""
    return skeleton.metadata.to_dict()


def export_statistics(skeleton: AvatarSkeleton) -> dict[str, Any]:
    """Export statistics dict."""
    return skeleton.statistics.to_dict()


def export_hierarchy(skeleton: AvatarSkeleton) -> dict[str, Any]:
    """Export parent/children tables and roots."""
    return {
        "roots": list(skeleton.hierarchy.roots),
        "parent": list(skeleton.hierarchy.parent),
        "children": [list(c) for c in skeleton.hierarchy.children],
        "depth": list(skeleton.hierarchy.depth),
        "height": list(skeleton.hierarchy.height),
    }


def export_tree(skeleton: AvatarSkeleton) -> str:
    """Return a human-readable ASCII tree."""
    lines: list[str] = []
    children = skeleton.hierarchy.children

    def walk(idx: int, prefix: str, is_last: bool) -> None:
        bone = skeleton.bones[idx]
        branch = "└── " if is_last else "├── "
        lines.append(f"{prefix}{branch}{bone.name} [{idx}]")
        ext = "    " if is_last else "│   "
        kids = children[idx]
        for i, c in enumerate(kids):
            walk(c, prefix + ext, i == len(kids) - 1)

    roots = skeleton.hierarchy.roots
    if not roots:
        return "(empty)"
    lines.append(skeleton.name)
    for i, r in enumerate(roots):
        walk(r, "", i == len(roots) - 1)
    return "\n".join(lines)


def export_debug(skeleton: AvatarSkeleton) -> dict[str, Any]:
    """Full debug dump (JSON-serializable)."""
    bones_out: list[dict[str, Any]] = []
    for b in skeleton.bones:
        bones_out.append(
            {
                "index": b.index,
                "id": int(b.id),
                "name": b.name,
                "parent_index": b.parent_index,
                "children": list(b.children),
                "translation": list(b.translation),
                "rotation_xyzw": list(b.rotation),
                "scale": list(b.scale),
                "has_inverse_bind": b.has_inverse_bind,
                "flags": int(b.flags.value),
                "path": bone_path_names(
                    list(reversed(skeleton.ancestors(b.index))) + [b.index],
                    skeleton.bones,
                )
                if b.parent_index is not None or True
                else b.name,
            }
        )
    return {
        "name": skeleton.name,
        "metadata": export_metadata(skeleton),
        "statistics": export_statistics(skeleton),
        "hierarchy": export_hierarchy(skeleton),
        "bones": bones_out,
        "tree": export_tree(skeleton),
    }


def export_json(skeleton: AvatarSkeleton, *, indent: int = 2) -> str:
    """Serialize debug export to a JSON string."""
    try:
        return json.dumps(export_debug(skeleton), indent=indent, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise SkeletonSerializationError(str(exc)) from exc


__all__ = [
    "export_metadata",
    "export_statistics",
    "export_hierarchy",
    "export_tree",
    "export_debug",
    "export_json",
]
