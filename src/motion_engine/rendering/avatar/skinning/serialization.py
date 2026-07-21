"""Debug serialization for skinning assets."""

from __future__ import annotations

import json
from typing import Any

from motion_engine.rendering.avatar.skinning.matrix_palette import MatrixPalette
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin
from motion_engine.rendering.avatar.skinning.statistics import SkinningStatistics
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable


def export_weight_table(table: WeightTable) -> dict[str, Any]:
    return {
        "vertex_count": table.vertex_count,
        "max_influences": table.max_influences,
        "joint_indices": table.joint_indices.tolist(),
        "joint_weights": table.joint_weights.tolist(),
    }


def export_matrix_palette(palette: MatrixPalette) -> dict[str, Any]:
    return {
        "bone_count": palette.bone_count,
        "matrices": [m.tolist() for m in palette.matrices],
    }


def export_mesh_skin(skin: MeshSkin) -> dict[str, Any]:
    return {
        "metadata": skin.metadata.to_dict(),
        "palette": {
            "bone_indices": skin.bone_palette.bone_indices.tolist(),
            "names": list(skin.bone_palette.names),
        },
        "weights": export_weight_table(skin.weight_table),
    }


def export_statistics(stats: SkinningStatistics) -> dict[str, Any]:
    return stats.to_dict()


def export_debug_report(skin: MeshSkin, stats: SkinningStatistics | None = None) -> str:
    lines = [
        f"MeshSkin: {skin.metadata.name or '(unnamed)'}",
        f"Vertices: {skin.vertex_count}  Max influences: {skin.max_influences}",
        f"Palette bones: {skin.bone_palette.size}",
    ]
    if stats is not None:
        lines.append(
            f"Avg influences: {stats.average_influences:.3f}  "
            f"skin={stats.skinning_ms:.3f}ms palette={stats.matrix_generation_ms:.3f}ms"
        )
    return "\n".join(lines)


def export_json(obj: dict[str, Any], *, indent: int = 2) -> str:
    return json.dumps(obj, indent=indent, sort_keys=True)


__all__ = [
    "export_weight_table",
    "export_matrix_palette",
    "export_mesh_skin",
    "export_statistics",
    "export_debug_report",
    "export_json",
]
