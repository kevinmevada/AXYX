"""Unreal Editor import manifest generation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from motion_engine.unreal.animation_sequence import AnimationSequenceDescriptor
from motion_engine.unreal.asset_builder import UnrealAssetPaths
from motion_engine.unreal.unreal_metadata import UnrealMetadata


@dataclass
class ImportManifest:
    """Machine-readable package describing an Unreal import."""

    version: str
    assets: UnrealAssetPaths
    animation_sequence: AnimationSequenceDescriptor
    metadata: UnrealMetadata
    files: dict[str, str] = field(default_factory=dict)
    import_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "assets": self.assets.to_dict(),
            "animation_sequence": self.animation_sequence.to_dict(),
            "metadata": self.metadata.to_dict(),
            "files": dict(self.files),
            "import_steps": list(self.import_steps),
        }

    def save(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out


DEFAULT_IMPORT_STEPS: list[str] = [
    "Create folder at Content path from assets.package_root",
    "Import animation JSON (or FBX when available) into that folder",
    "Create / assign USkeleton matching animation_sequence.joints",
    "Create UAnimSequence with fps/num_frames from animation_sequence",
    "Enable root motion if animation_sequence.enable_root_motion",
    "Run IK Retargeter: source → MetaHuman target",
    "Bind Control Rig; optionally enable Foot IK / Chaos later",
]
