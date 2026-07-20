"""
Unreal Engine 5 animation package exporter.

Prepares Unreal-ready JSON + import manifests from AnimationClip assets.
Does not call Unreal Editor APIs - packages are imported Unreal-side.

Example:
    >>> exporter = UnrealExporter()
    >>> package_dir = exporter.export_clip(unreal_ready_clip, "output/unreal")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from motion_engine.animation_clip import (
    AnimationClip,
    AnimationFrame,
    JointTransform,
    RootMotion,
)
from motion_engine.exceptions import MotionEngineError
from motion_engine.loader import load_motion_database
from motion_engine.skeleton import Skeleton, SkeletonBuilder
from motion_engine.unreal.animation_sequence import AnimationSequence, AnimationSequenceDescriptor
from motion_engine.unreal.asset_builder import AssetBuilder
from motion_engine.unreal.coordinate_converter import CoordinateConverter
from motion_engine.unreal.import_manifest import (
    DEFAULT_IMPORT_STEPS,
    ImportManifest,
)
from motion_engine.unreal.skeleton_mapper import SkeletonMapper
from motion_engine.unreal.transform_converter import TransformConverter
from motion_engine.unreal.unreal_config import UnrealConfig
from motion_engine.unreal.unreal_metadata import UnrealMetadata

logger = logging.getLogger(__name__)


@dataclass
class UnrealExportPackage:
    """In-memory Unreal-ready animation package (certification / Editor prep)."""

    clip: AnimationClip
    coordinate_system: str
    metadata: dict[str, Any]
    root_motion: RootMotion | None
    assets: dict[str, Any] = field(default_factory=dict)

    @property
    def n_frames(self) -> int:
        return self.clip.n_frames

    @property
    def n_joints(self) -> int:
        return self.clip.n_joints


class UnrealExportError(MotionEngineError):
    """Raised when an Unreal package cannot be written."""


class UnrealExporter:
    """Write Unreal-ready animation assets to disk.

    The exporter does not perform coordinate conversion or skeleton mapping.
    Feed it an Unreal-ready ``AnimationClip`` from ``UnrealPipeline`` or call
    the convenience methods for simple workflows.
    """

    def __init__(
        self,
        config: UnrealConfig | None = None,
        *,
        config_path: str | Path | None = None,
    ) -> None:
        self.config = config or UnrealConfig.load(config_path)
        self.coordinates = CoordinateConverter.from_config(self.config)
        self.transforms = TransformConverter(self.coordinates)
        self.assets = AssetBuilder(self.config)
        self.skeleton_mapper = SkeletonMapper()

    def prepare(self, clip: AnimationClip) -> UnrealExportPackage:
        """Prepare an in-memory package for an already Unreal-ready clip."""
        report = clip.validate()
        if report["errors"]:
            raise UnrealExportError(f"Invalid clip: {report['errors']}")
        paths = self.assets.build(clip)
        meta = UnrealMetadata.from_clip(clip, self.config)
        return UnrealExportPackage(
            clip=clip,
            coordinate_system="Unreal",
            metadata=meta.to_dict(),
            root_motion=clip.root_motion,
            assets=paths.to_dict(),
        )

    def export_json(self, clip: AnimationClip, path: str | Path) -> Path:
        """Write a single Unreal-frame animation JSON file."""
        package = self.prepare(clip)
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        return package.clip.save_json(out)

    def convert_clip(self, clip: AnimationClip) -> AnimationClip:
        """Return a copy of ``clip`` in Unreal coordinates / units."""
        logger.warning(
            "UnrealExporter.convert_clip is retained for compatibility; "
            "prefer CoordinateConverter / UnrealPipeline for conversion."
        )
        frames: list[AnimationFrame] = []
        for frame in clip.frames:
            xforms: dict[str, JointTransform] = {}
            for name, xf in frame.transforms.items():
                if not xf.valid:
                    xforms[name] = JointTransform(
                        joint_name=name,
                        translation=(0.0, 0.0, 0.0),
                        valid=False,
                    )
                    continue
                xforms[name] = JointTransform(
                    joint_name=name,
                    translation=self.transforms.convert_translation(xf.translation),
                    rotation=self.transforms.convert_quaternion(xf.rotation),
                    scale=xf.scale,
                    valid=True,
                )
            frames.append(
                AnimationFrame(
                    index=frame.index,
                    time_sec=frame.time_sec,
                    transforms=xforms,
                )
            )

        root_motion = None
        if clip.root_motion is not None and self.config.root_motion_enabled:
            translations = self.coordinates.convert_points(clip.root_motion.translations)
            velocities = self.coordinates.convert_points(clip.root_motion.velocities)
            root_motion = RootMotion(
                translations=translations,
                headings_rad=clip.root_motion.headings_rad.copy(),
                velocities=velocities,
                root_joint=clip.root_motion.root_joint,
            )

        converted = AnimationClip(
            name=clip.name,
            frames=frames,
            fps=clip.fps,
            joint_order=list(clip.joint_order),
            bones=list(clip.bones),
            root_joint=clip.root_joint,
            root_motion=root_motion,
            units=self.config.unit_scale.target,
            coordinate_system=self.config.target_coordinate_system,
            metadata={
                **dict(clip.metadata),
                "converted_for": "unreal_ue5",
                "unit_scale_factor": self.config.unit_scale.factor,
            },
            compression=clip.compression,
        )
        return converted

    def export(
        self,
        clip: AnimationClip,
        output_dir: str | Path | None = None,
        *,
        asset_name: str | None = None,
        flat: bool = False,
        output_directory: str | Path | None = None,
    ) -> Path:
        """Write an Unreal-ready package directory and return its path.

        Layout (default)::

            output_dir/<clip>/
                ME_<clip>.anim.json
                ME_<clip>.import.json
                ME_<clip>.metadata.json
                hierarchy.json

        Flat certification layout (``flat=True``, ``asset_name="walking"``)::

            output_dir/
                walking.fbx
                walking.import.json
                walking.metadata.json
        """
        report = clip.validate()
        if report["errors"]:
            raise UnrealExportError(f"Invalid clip: {report['errors']}")

        dest = output_directory if output_directory is not None else output_dir
        from motion_engine.unreal.asset_builder import UnrealAssetPaths

        paths = self.assets.build(clip, asset_name=asset_name, flat=flat)
        if not isinstance(paths, UnrealAssetPaths):
            raise UnrealExportError("AssetBuilder.build(clip) must return UnrealAssetPaths")
        seq = AnimationSequence.from_clip(
            clip,
            skeleton=str(clip.metadata.get("target_skeleton", "unreal")),
            interpolation=self.config.interpolation,
        )
        desc = AnimationSequenceDescriptor.from_clip(
            clip,
            skeleton_asset=paths.skeleton_path,
            enable_root_motion=self.config.enable_root_motion,
            interpolation=self.config.interpolation,
        )
        meta = UnrealMetadata.from_clip(clip, self.config)
        manifest = ImportManifest(
            version="1.0.0",
            assets=paths,
            animation_sequence=desc,
            metadata=meta,
            files={
                "animation_json": paths.json_filename,
                "manifest": paths.manifest_filename,
                "metadata": paths.metadata_filename,
                "hierarchy": "hierarchy.json",
            },
            import_steps=list(DEFAULT_IMPORT_STEPS),
        )
        out_root = self.assets.create_package(
            seq,
            clip,
            dest or "output/unreal",
            metadata=meta,
            import_manifest=manifest.to_dict(),
            asset_name=asset_name,
            flat=flat,
        )
        hierarchy_path = out_root / "hierarchy.json"
        hierarchy_path.write_text(
            json.dumps(
                {
                    "root_joint": clip.root_joint,
                    "joints": clip.joint_order,
                    "bones": self.skeleton_mapper.bone_hierarchy(clip),
                    "parents": self.skeleton_mapper.joint_parent_map(clip),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.info(
            "Unreal package exported → %s (frames=%d joints=%d)",
            out_root,
            clip.n_frames,
            clip.n_joints,
        )
        return out_root

    def export_clip(
        self,
        clip: AnimationClip,
        output_dir: str | Path | None = None,
        *,
        fmt: str = "fbx",
        asset_name: str | None = None,
        flat: bool = False,
        output_directory: str | Path | None = None,
    ) -> Path:
        """Export one Unreal-ready clip.

        Args:
            clip: Converted/mapped animation clip.
            output_dir: Package root.
            fmt: Primary interchange format. ``fbx`` is written today; glTF,
                USD, and BVH are reserved through the public API.
        """
        if fmt.lower() not in {"fbx", "json"}:
            raise UnrealExportError(
                f"Format {fmt!r} is not enabled for UnrealExporter yet"
            )
        return self.export(
            clip,
            output_dir=output_dir,
            asset_name=asset_name,
            flat=flat,
            output_directory=output_directory,
        )

    def export_session(
        self,
        session: Any,
        output_dir: str | Path | None = None,
        *,
        builder: SkeletonBuilder | None = None,
        output_directory: str | Path | None = None,
        asset_name: str = "walking",
    ) -> Path:
        """Convenience export from a Motion Engine session.

        Certification writes a flat package::

            output_directory/walking.fbx
            output_directory/walking.metadata.json
            output_directory/walking.import.json
        """
        skeleton = (builder or SkeletonBuilder()).build(session)
        clip = AnimationClip.from_skeleton(skeleton)
        clip = self.convert_clip(clip)
        dest = output_directory if output_directory is not None else output_dir
        return self.export_clip(
            clip,
            output_directory=dest,
            fmt="fbx",
            asset_name=asset_name,
            flat=True,
        )

    def export_database(
        self,
        subject: str,
        session: str,
        output_dir: str | Path | None = None,
        *,
        database_path: str | Path | None = None,
        output_directory: str | Path | None = None,
    ) -> Path:
        """Convenience export from a database path / default dataset."""
        db = load_motion_database(database_path)
        sess = db.get_subject(subject).get_session(session)
        return self.export_session(
            sess,
            output_dir=output_dir,
            output_directory=output_directory,
        )

    def export_dict(self, clip: AnimationClip) -> dict[str, Any]:
        """In-memory Unreal package description (no disk I/O)."""
        paths = self.assets.build(clip)
        seq = AnimationSequenceDescriptor.from_clip(
            clip,
            skeleton_asset=paths.skeleton_path,
            enable_root_motion=self.config.enable_root_motion,
        )
        meta = UnrealMetadata.from_clip(clip, self.config)
        return {
            "assets": paths.to_dict(),
            "animation_sequence": seq.to_dict(),
            "metadata": meta.to_dict(),
            "clip": clip.to_dict(),
        }


def _safe(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
