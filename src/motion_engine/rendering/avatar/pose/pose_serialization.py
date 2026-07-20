"""Debug serialization for poses (not runtime persistence)."""

from __future__ import annotations

import json
from typing import Any

from motion_engine.rendering.avatar.pose.exceptions import PoseSerializationError
from motion_engine.rendering.avatar.pose.pose import Pose


def export_hierarchy(pose: Pose) -> dict[str, Any]:
    """Parent/children tables."""
    return {
        "parents": [b.parent_index for b in pose.bones],
        "children": [list(b.children) for b in pose.bones],
        "roots": [b.index for b in pose.bones if b.parent_index is None],
    }


def export_matrices(pose: Pose) -> dict[str, Any]:
    """Per-bone matrix dump (lists for JSON)."""
    out: list[dict[str, Any]] = []
    for b in pose.bones:
        out.append(
            {
                "index": b.index,
                "name": b.name,
                "local": b.local_matrix.tolist(),
                "global": b.global_matrix.tolist(),
                "rest": b.rest_matrix.tolist(),
                "inverse_bind": b.inverse_bind_matrix.tolist(),
                "world_position": list(b.world_position),
                "translation": list(b.translation),
                "rotation_xyzw": list(b.rotation_xyzw),
                "scale": list(b.scale),
            }
        )
    return {"bones": out}


def export_debug_report(pose: Pose) -> str:
    """Human-readable debug report."""
    lines = [
        f"Pose: {pose.name} [{pose.kind.value}]",
        f"Bones: {pose.bone_count}",
    ]
    if hasattr(pose, "statistics"):
        st = pose.statistics  # type: ignore[attr-defined]
        lines.append(
            f"Depth: {st.hierarchy_depth}  Roots: {st.root_count}  Leaves: {st.leaf_count}"
        )
    lines.append("")
    for b in pose.bones:
        indent = ""
        # crude depth via parent walk
        d = 0
        cur = b.parent_index
        seen: set[int] = set()
        while cur is not None and cur not in seen:
            seen.add(cur)
            d += 1
            cur = pose.bones[cur].parent_index
        indent = "  " * d
        wp = b.world_position
        lines.append(
            f"{indent}{b.name} [{b.index}]  pos=({wp[0]:.4f}, {wp[1]:.4f}, {wp[2]:.4f})"
        )
    return "\n".join(lines)


def export_pose_dict(pose: Pose) -> dict[str, Any]:
    """Full debug dict."""
    data: dict[str, Any] = {
        "name": pose.name,
        "kind": pose.kind.value,
        "bone_count": pose.bone_count,
        "hierarchy": export_hierarchy(pose),
        "matrices": export_matrices(pose),
        "report": export_debug_report(pose),
    }
    if hasattr(pose, "coordinate_system"):
        data["coordinate_system"] = pose.coordinate_system.to_dict()  # type: ignore[attr-defined]
    if hasattr(pose, "rest_info"):
        data["rest_info"] = pose.rest_info.to_dict()  # type: ignore[attr-defined]
    if hasattr(pose, "statistics"):
        data["statistics"] = pose.statistics.to_dict()  # type: ignore[attr-defined]
    return data


def export_json(pose: Pose, *, indent: int = 2) -> str:
    """Serialize debug export to JSON."""
    try:
        return json.dumps(export_pose_dict(pose), indent=indent, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise PoseSerializationError(str(exc)) from exc


__all__ = [
    "export_hierarchy",
    "export_matrices",
    "export_debug_report",
    "export_pose_dict",
    "export_json",
]
