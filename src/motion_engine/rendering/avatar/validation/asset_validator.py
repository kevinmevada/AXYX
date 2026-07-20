"""Post-load asset validation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from motion_engine.rendering.avatar.loader.exceptions import ValidationError
from motion_engine.rendering.avatar.models import LoadedAvatar, MeshData

logger = logging.getLogger(__name__)

Severity = Literal["info", "warning", "error"]


@dataclass(slots=True)
class Diagnostic:
    """Single validation finding."""

    code: str
    severity: Severity
    message: str
    path: str | None = None


@dataclass(slots=True)
class ValidationReport:
    """Aggregated validation results."""

    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)

    def add(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = "error",
        path: str | None = None,
    ) -> None:
        self.diagnostics.append(
            Diagnostic(code=code, severity=severity, message=message, path=path)
        )

    def raise_if_errors(self) -> None:
        if self.ok:
            return
        errors = [d for d in self.diagnostics if d.severity == "error"]
        summary = "; ".join(f"{d.code}: {d.message}" for d in errors[:5])
        raise ValidationError(f"Asset validation failed: {summary}")


class AssetValidator:
    """Validate a :class:`LoadedAvatar` bundle after loaders finish.

    Example:
        >>> report = AssetValidator().validate(loaded)
        >>> report.raise_if_errors()
    """

    def __init__(
        self, *, require_skeleton: bool = True, require_mesh: bool = True
    ) -> None:
        self.require_skeleton = require_skeleton
        self.require_mesh = require_mesh

    def validate(self, avatar: LoadedAvatar) -> ValidationReport:
        """Run all asset checks and return a report."""
        report = ValidationReport()
        logger.debug("Validating loaded avatar %s", avatar.id)

        if self.require_mesh and not avatar.meshes:
            if avatar.manifest.avatar_type == "procedural":
                report.add(
                    "MESH_OPTIONAL_PROCEDURAL",
                    "Procedural avatar has no binary mesh (generator expected)",
                    severity="info",
                )
            else:
                report.add("MESH_MISSING", "No meshes loaded for digital avatar")
        for mesh in avatar.meshes:
            self._validate_mesh(mesh, report)

        if self.require_skeleton:
            if avatar.skeleton is None or avatar.skeleton.bone_count == 0:
                if avatar.manifest.avatar_type == "procedural":
                    report.add(
                        "SKEL_OPTIONAL_PROCEDURAL",
                        "Procedural avatar without imported skeleton",
                        severity="info",
                    )
                else:
                    report.add("SKEL_EMPTY", "Skeleton missing or empty")
            else:
                names = [b.name for b in avatar.skeleton.bones]
                if len(names) != len(set(names)):
                    report.add("SKEL_DUP_NAME", "Duplicate bone names in skeleton")

        if not avatar.materials and avatar.manifest.avatar_type != "procedural":
            report.add(
                "MATERIAL_MISSING",
                "No materials loaded",
                severity="warning",
            )

        for diag in report.diagnostics:
            if diag.severity == "error":
                logger.error("%s: %s", diag.code, diag.message)
            elif diag.severity == "warning":
                logger.warning("%s: %s", diag.code, diag.message)
            else:
                logger.info("%s: %s", diag.code, diag.message)

        return report

    def _validate_mesh(self, mesh: MeshData, report: ValidationReport) -> None:
        path = str(mesh.source_path) if mesh.source_path else mesh.name
        if mesh.vertex_count == 0:
            report.add("MESH_EMPTY", "Mesh has zero vertices", path=path)
            return
        if mesh.indices.size == 0:
            report.add("MESH_EMPTY", "Mesh has zero indices", path=path)
        if mesh.normals.shape[0] != mesh.vertex_count:
            report.add(
                "MESH_MISSING_NORMALS",
                "Normals count does not match vertices",
                path=path,
            )
        if mesh.uvs.shape[0] != mesh.vertex_count:
            report.add(
                "MESH_MISSING_UVS",
                "UV count does not match vertices",
                severity="warning",
                path=path,
            )
        if not bool(np.isfinite(np.asarray(mesh.positions)).all()):
            report.add("MESH_CORRUPT", "Non-finite positions", path=path)


__all__ = ["Diagnostic", "ValidationReport", "AssetValidator"]
