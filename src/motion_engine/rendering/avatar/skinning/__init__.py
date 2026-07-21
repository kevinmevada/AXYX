"""M4 Skinning Runtime — MeshSkin + LBS deformation.

Architecture::

    MeshData (immutable geometry)
         +
    MeshSkin (WeightTable + BonePalette + metadata)
         +
    BindPose / AnimationPose
         │
         ▼
    SkinningRuntime
         │
         ▼
    DeformedMesh  →  Renderer (unchanged)

Does not modify M1–M3, Viewer, Studio, or Rendering APIs.
"""

from __future__ import annotations

from motion_engine.rendering.avatar.skinning.bone_palette import BonePalette
from motion_engine.rendering.avatar.skinning.constants import RUNTIME_VERSION
from motion_engine.rendering.avatar.skinning.cpu_skinner import CpuSkinner, SkinningResult
from motion_engine.rendering.avatar.skinning.dual_quaternion_placeholder import (
    CenterOfRotationSkinning,
    DualQuaternionSkinning,
)
from motion_engine.rendering.avatar.skinning.exceptions import (
    SkinningError,
    SkinningFactoryError,
    SkinningNotSupportedError,
    SkinningValidationError,
)
from motion_engine.rendering.avatar.skinning.factory import MeshSkinFactory
from motion_engine.rendering.avatar.skinning.gpu_interface import NullGpuSkinning
from motion_engine.rendering.avatar.skinning.legacy_compat import (
    SkinningWeights,
    apply_linear_blend_skinning,
)
from motion_engine.rendering.avatar.skinning.linear_blend_skinning import LinearBlendSkinning
from motion_engine.rendering.avatar.skinning.matrix_palette import (
    MatrixPalette,
    build_matrix_palette,
)
from motion_engine.rendering.avatar.skinning.mesh_cache import MeshCache, SkinningCache
from motion_engine.rendering.avatar.skinning.mesh_deformer import DeformedMesh, MeshDeformer
from motion_engine.rendering.avatar.skinning.mesh_skin import MeshSkin, SkinningMetadata
from motion_engine.rendering.avatar.skinning.serialization import (
    export_debug_report,
    export_json,
    export_matrix_palette,
    export_mesh_skin,
    export_statistics,
    export_weight_table,
)
from motion_engine.rendering.avatar.skinning.skinning_runtime import SkinningRuntime
from motion_engine.rendering.avatar.skinning.statistics import SkinningStatistics
from motion_engine.rendering.avatar.skinning.types import (
    NormalizationMode,
    SkinningAlgorithm,
)
from motion_engine.rendering.avatar.skinning.weight_normalization import normalize_weights
from motion_engine.rendering.avatar.skinning.weight_table import WeightTable
from motion_engine.rendering.avatar.skinning.weight_validation import (
    WeightValidationReport,
    validate_weight_table,
)

__all__ = [
    "BonePalette",
    "CenterOfRotationSkinning",
    "CpuSkinner",
    "DeformedMesh",
    "DualQuaternionSkinning",
    "LinearBlendSkinning",
    "MatrixPalette",
    "MeshCache",
    "MeshDeformer",
    "MeshSkin",
    "MeshSkinFactory",
    "NormalizationMode",
    "NullGpuSkinning",
    "RUNTIME_VERSION",
    "SkinningAlgorithm",
    "SkinningCache",
    "SkinningError",
    "SkinningFactoryError",
    "SkinningMetadata",
    "SkinningNotSupportedError",
    "SkinningResult",
    "SkinningRuntime",
    "SkinningStatistics",
    "SkinningValidationError",
    "SkinningWeights",
    "WeightTable",
    "WeightValidationReport",
    "apply_linear_blend_skinning",
    "build_matrix_palette",
    "export_debug_report",
    "export_json",
    "export_matrix_palette",
    "export_mesh_skin",
    "export_statistics",
    "export_weight_table",
    "normalize_weights",
    "validate_weight_table",
]
