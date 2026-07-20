"""
Shared typing aliases for the Motion Engine.

Prefer these aliases in public APIs for clarity and future refactoring.
"""

from __future__ import annotations

from typing import Any, Literal, TypeAlias

# Trajectory storage layout after XYZ-axis detection.
TrajectoryLayout: TypeAlias = Literal["N,3", "3,N"] | None

# Stable subject identifier as stored in the MATLAB dataset (e.g. "S2").
SubjectId: TypeAlias = str

# Original session name preserved from the dataset (e.g. "WU01", "staticCopy").
SessionName: TypeAlias = str

# Semantic session classification label (never used as a rename).
SessionClassification: TypeAlias = str

# Variable / marker / metric names preserved from the dataset.
VariableName: TypeAlias = str

# Opaque MATLAB objects and other unstructured values.
OpaqueValue: TypeAlias = Any

# Mapping helpers used across domain models.
SubjectMap: TypeAlias = dict[SubjectId, Any]
SessionMap: TypeAlias = dict[SessionName, Any]
VariableMap: TypeAlias = dict[VariableName, Any]
