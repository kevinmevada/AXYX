"""End-to-end Unreal integration pipeline.

``MotionDatabase → SkeletonBuilder → AnimationClip → Coordinate Conversion →
Skeleton Mapping → UnrealExporter``

Example:
    >>> pipeline = UnrealPipeline()
    >>> pipeline.export_session(subject="S2", session="WU01", output_dir="output/unreal")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from motion_engine.animation_clip import AnimationClip
from motion_engine.loader import load_motion_database
from motion_engine.skeleton import Skeleton
from motion_engine.skeleton import SkeletonBuilder
from motion_engine.unreal.coordinate_converter import CoordinateConverter
from motion_engine.unreal.metahuman_mapper import MetaHumanMapper
from motion_engine.unreal.skeleton_mapper import SkeletonMapper
from motion_engine.unreal.transform_converter import TransformConverter
from motion_engine.unreal.unreal_config import UnrealConfig
from motion_engine.unreal.unreal_exporter import UnrealExporter

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineValidationResult:
    """Result of :meth:`UnrealPipeline.validate`."""

    success: bool
    errors: list[str]
    warnings: list[str]

    def __bool__(self) -> bool:
        return self.success


class UnrealPipeline:
    """Reusable orchestration subsystem for Unreal-ready exports.

    Args:
        config: Unreal export configuration.
        metahuman_mapping: YAML mapping profile path.
        retarget: Whether to map onto MetaHuman names.
        builder: Optional injected SkeletonBuilder.
        exporter: Optional injected UnrealExporter.

    Example:
        >>> UnrealPipeline().export_session("S2", "WU01")
    """

    def __init__(
        self,
        *,
        config: UnrealConfig | None = None,
        metahuman_mapping: str | Path | None = None,
        retarget: bool = True,
        builder: SkeletonBuilder | None = None,
        exporter: UnrealExporter | None = None,
    ) -> None:
        self.config = config or UnrealConfig.load()
        self.retarget_enabled = retarget
        self.mapper = MetaHumanMapper(metahuman_mapping)
        self.skeleton_mapper = SkeletonMapper().load_mapping(metahuman_mapping)
        self.coordinate_converter = CoordinateConverter.from_config(self.config)
        self.transform_converter = TransformConverter(self.coordinate_converter)
        self.builder = builder or SkeletonBuilder()
        self.exporter = exporter or UnrealExporter(self.config)

    def run(
        self,
        skeleton: Skeleton,
        *,
        output_dir: str | Path | None = None,
        output_directory: str | Path | None = None,
        flat: bool = False,
        asset_name: str | None = None,
    ) -> Path:
        """Build clip, convert/map it, and export Unreal package."""
        clip = AnimationClip.from_skeleton(skeleton)
        clip = self.prepare_clip(clip)
        dest = output_directory if output_directory is not None else output_dir
        package = self.exporter.export(
            clip,
            output_directory=dest,
            flat=flat,
            asset_name=asset_name,
        )
        logger.info("UnrealPipeline complete → %s", package)
        return package

    def run_from_clip(
        self,
        clip: AnimationClip,
        *,
        output_dir: str | Path | None = None,
        retarget: bool | None = None,
        output_directory: str | Path | None = None,
    ) -> Path:
        do_retarget = self.retarget_enabled if retarget is None else retarget
        working = self.prepare_clip(clip, retarget=do_retarget)
        dest = output_directory if output_directory is not None else output_dir
        return self.exporter.export(working, output_directory=dest)

    def prepare_clip(
        self,
        clip: AnimationClip,
        *,
        retarget: bool | None = None,
    ) -> AnimationClip:
        """Coordinate-convert, optionally map, and enforce quaternion continuity."""
        working = self.coordinate_converter.convert_animation(clip)
        do_retarget = self.retarget_enabled if retarget is None else retarget
        if do_retarget:
            working = self.skeleton_mapper.map_skeleton(working)
        working = self.transform_converter.enforce_quaternion_continuity(working)
        return working

    def export_session(
        self,
        subject: str,
        session: str,
        output_dir: str | Path | None = None,
        *,
        database_path: str | Path | None = None,
        output_directory: str | Path | None = None,
        asset_name: str = "walking",
    ) -> Path:
        """Load a database session and export an Unreal package.

        Certification writes files directly into ``output_directory``.
        """
        db = load_motion_database(database_path)
        skeleton = self.builder.build(db.get_subject(subject).get_session(session))
        dest = output_directory if output_directory is not None else output_dir
        return self.run(
            skeleton,
            output_directory=dest,
            flat=True,
            asset_name=asset_name,
        )

    def export_database(
        self,
        database: Any,
        *,
        subject: str,
        session: str,
        output_dir: str | Path | None = None,
        output_directory: str | Path | None = None,
    ) -> Path:
        """Export from an already loaded ``MotionDatabase``-like object."""
        skeleton = self.builder.build(database.get_subject(subject).get_session(session))
        dest = output_directory if output_directory is not None else output_dir
        return self.run(skeleton, output_directory=dest)

    def validate(self) -> PipelineValidationResult:
        """Smoke-validate that the Unreal subsystem is ready for export."""
        errors: list[str] = []
        warnings: list[str] = []
        try:
            UnrealConfig.load()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Unreal config failed: {exc}")
        if self.skeleton_mapper.mapping_count <= 0:
            errors.append("SkeletonMapper has no joint mappings loaded")
        if self.coordinate_converter.scale == 0.0:
            errors.append("CoordinateConverter scale must be non-zero")
        if not self.retarget_enabled:
            warnings.append("Retargeting is disabled")
        return PipelineValidationResult(
            success=not errors,
            errors=errors,
            warnings=warnings,
        )
