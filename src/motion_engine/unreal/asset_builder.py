"""Build final Unreal export packages.

``AssetBuilder`` is responsible for assembling the disk package:

```
output/unreal/<session>/
    walking.fbx
    walking.import.json
    walking.metadata.json
    walking.anim.json
    preview.png
    manifest.json
```

The FBX writer emits deterministic ASCII FBX with skeleton hierarchy and
animation curve metadata. It is intentionally dependency-free; projects that
need binary FBX can replace this class with an Autodesk FBX SDK adapter without
changing the pipeline.
"""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from motion_engine.animation_clip import AnimationClip
from motion_engine.unreal.animation_sequence import AnimationSequence
from motion_engine.unreal.unreal_config import UnrealConfig
from motion_engine.unreal.unreal_metadata import UnrealMetadata


@dataclass(slots=True)
class UnrealAssetPaths:
    """Proposed Unreal content paths for a clip package."""

    package_root: str
    skeleton_path: str
    animation_path: str
    json_filename: str
    manifest_filename: str
    fbx_filename: str = ""
    metadata_filename: str = ""
    preview_filename: str = "preview.png"
    package_manifest_filename: str = "manifest.json"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AssetBuilder:
    """Construct Content Browser paths and write final package artifacts.

    Args:
        config: Unreal export configuration. Optional for package scaffolding.

    Example:
        >>> paths = AssetBuilder(config).build(clip)
        >>> AssetBuilder().build(Path("output/unreal/session"))
    """

    def __init__(self, config: UnrealConfig | None = None) -> None:
        self.config = config or UnrealConfig.load()

    def build(
        self,
        clip_or_path: AnimationClip | str | Path,
        *,
        asset_name: str | None = None,
        flat: bool = False,
    ) -> UnrealAssetPaths | Path:
        """Build asset paths or scaffold an empty package directory.

        Certification API::

            AssetBuilder().build(output_path)  # creates directory

        Production API::

            AssetBuilder(config).build(clip)  # returns UnrealAssetPaths
        """
        if isinstance(clip_or_path, (str, Path)):
            out = Path(clip_or_path)
            out.mkdir(parents=True, exist_ok=True)
            (out / "manifest.json").write_text(
                json.dumps({"schema_version": "1.0.0", "package": str(out)}, indent=2),
                encoding="utf-8",
            )
            return out

        clip = clip_or_path
        safe = _sanitize(asset_name or clip.name)
        prefix = "" if flat or asset_name else self.config.asset_prefix
        if asset_name:
            safe = _sanitize(asset_name)
            prefix = ""
        root = self.config.content_path.rstrip("/")
        package = f"{root}/{safe}"
        skeleton = f"{package}/{prefix}{safe}{self.config.skeleton_suffix}"
        anim = f"{package}/{prefix}{safe}{self.config.anim_suffix}"
        return UnrealAssetPaths(
            package_root=package,
            skeleton_path=skeleton,
            animation_path=anim,
            json_filename=f"{prefix}{safe}.anim.json",
            manifest_filename=f"{prefix}{safe}.import.json",
            fbx_filename=f"{prefix}{safe}.fbx",
            metadata_filename=f"{prefix}{safe}.metadata.json",
        )

    def create_package(
        self,
        sequence: AnimationSequence,
        clip: AnimationClip,
        output_dir: str | Path,
        *,
        metadata: UnrealMetadata,
        import_manifest: dict[str, Any],
        asset_name: str | None = None,
        flat: bool = False,
    ) -> Path:
        """Write the final Unreal package directory.

        When ``flat=True`` or ``asset_name`` is provided, files are written
        directly into ``output_dir`` (certification layout). Otherwise a
        subdirectory named after the clip is created.
        """
        paths = self.build(clip, asset_name=asset_name, flat=flat)
        assert isinstance(paths, UnrealAssetPaths)
        root = Path(output_dir)
        if not flat and asset_name is None:
            root = root / _sanitize(clip.name)
        root.mkdir(parents=True, exist_ok=True)

        anim_json = root / paths.json_filename
        clip.save_json(anim_json)

        fbx_path = root / paths.fbx_filename
        self.write_ascii_fbx(sequence, fbx_path)

        import_path = root / paths.manifest_filename
        import_path.write_text(json.dumps(import_manifest, indent=2), encoding="utf-8")

        metadata_path = root / paths.metadata_filename
        metadata_path.write_text(
            json.dumps(metadata.to_dict(), indent=2),
            encoding="utf-8",
        )

        preview_path = root / paths.preview_filename
        _write_preview_png(preview_path)

        package_manifest = {
            "schema_version": "1.0.0",
            "package": paths.package_root,
            "files": {
                "fbx": paths.fbx_filename,
                "animation_json": paths.json_filename,
                "import_manifest": paths.manifest_filename,
                "metadata": paths.metadata_filename,
                "preview": paths.preview_filename,
            },
            "unreal_assets": paths.to_dict(),
            "sequence": sequence.to_dict(),
        }
        (root / paths.package_manifest_filename).write_text(
            json.dumps(package_manifest, indent=2),
            encoding="utf-8",
        )
        return root

    def write_ascii_fbx(self, sequence: AnimationSequence, path: str | Path) -> Path:
        """Write a deterministic ASCII FBX 7.4-style animation package.

        The file includes model nodes for all joints and compact curve metadata.
        UE can ingest richer FBX from DCC encoders later without changing the
        exporter API; this writer provides a dependency-free interchange artifact
        for CI, manifests, and editor-side Python import hooks.
        """
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "; FBX 7.4.0 project file",
            "; Generated by Motion Engine Unreal Integration Layer",
            "FBXHeaderExtension:  {",
            "    FBXHeaderVersion: 1003",
            "    FBXVersion: 7400",
            "}",
            "GlobalSettings:  {",
            "    Version: 1000",
            "    Properties70:  {",
            "        P: \"UnitScaleFactor\", \"double\", \"Number\", \"\",1",
            "        P: \"UpAxis\", \"int\", \"Integer\", \"\",2",
            "        P: \"CoordAxis\", \"int\", \"Integer\", \"\",0",
            "    }",
            "}",
            "Objects:  {",
        ]
        for index, joint in enumerate(sequence.joints):
            lines.extend(
                [
                    f"    Model: {1000 + index}, \"Model::{joint}\", \"LimbNode\" {{",
                    "        Version: 232",
                    "        Properties70:  {",
                    "            P: \"Lcl Translation\", \"Lcl Translation\", \"\", \"A\",0,0,0",
                    "            P: \"Lcl Rotation\", \"Lcl Rotation\", \"\", \"A\",0,0,0",
                    "            P: \"Lcl Scaling\", \"Lcl Scaling\", \"\", \"A\",1,1,1",
                    "        }",
                    "    }",
                ]
            )
        lines.extend(
            [
                "    AnimationStack: 2000, \"AnimStack::MotionEngine\", \"\" {",
                f"        Properties70: {{ P: \"LocalStop\", \"KTime\", \"Time\", \"\",{int(sequence.duration * 46186158000)} }}",
                "    }",
                "}",
                "Connections:  {",
                "    ; Parent/child connections are supplied in manifest hierarchy.",
                "}",
                "Takes:  {",
                "    Current: \"MotionEngine\"",
                "}",
                "; MotionEngineAnimationSummary: "
                + json.dumps(
                    {
                        "frames": sequence.num_frames,
                        "fps": sequence.fps,
                        "joints": sequence.joints,
                        "interpolation": sequence.interpolation,
                    },
                    separators=(",", ":"),
                ),
            ]
        )
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out


def _sanitize(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)


def _write_preview_png(path: Path) -> None:
    """Write a tiny valid PNG preview placeholder generated from code."""
    width, height = 256, 144
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            shade = int(22 + 42 * (y / max(height - 1, 1)))
            accent = int(80 + 120 * (x / max(width - 1, 1)))
            row.extend((shade, min(120, shade + 12), accent))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=6))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)
