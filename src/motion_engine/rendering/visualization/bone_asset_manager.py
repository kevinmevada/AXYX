"""Install and version anatomical bone mesh packs under ``assets/bones``."""

from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
from pathlib import Path
from typing import Callable

import numpy as np

from motion_engine.rendering.avatar.procedural.bone_geometry import (
    _PROFILES,
    build_unit_bone_template,
)

logger = logging.getLogger(__name__)

PACK_VERSION = "1.0.0"
# Optional curated remote pack. Empty = generate local cortical pack.
DEFAULT_PACK_URL = ""
DEFAULT_PACK_SHA256 = ""

ProgressCallback = Callable[[str, float], None]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_bones_dir() -> Path:
    return _repo_root() / "assets" / "bones"


class BoneAssetManager:
    """Ensure anatomical bone assets exist — download or generate once.

    On first launch:
      1. Check ``assets/bones/manifest.json``
      2. If missing/outdated, download approved pack (when URL configured)
         or generate a high-resolution cortical pack from procedural profiles
      3. Verify checksum when provided
      4. Cache forever until version bumps
    """

    def __init__(
        self,
        bones_dir: Path | None = None,
        *,
        pack_url: str = DEFAULT_PACK_URL,
        pack_sha256: str = DEFAULT_PACK_SHA256,
        version: str = PACK_VERSION,
    ) -> None:
        self.bones_dir = Path(bones_dir) if bones_dir else default_bones_dir()
        self.pack_url = pack_url.strip()
        self.pack_sha256 = pack_sha256.strip().lower()
        self.version = version
        self.manifest_path = self.bones_dir / "manifest.json"

    def is_installed(self) -> bool:
        if not self.manifest_path.is_file():
            return False
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        if str(data.get("version", "")) != self.version:
            return False
        meshes = data.get("meshes") or []
        return all((self.bones_dir / name).is_file() for name in meshes)

    def ensure_installed(
        self,
        *,
        progress: ProgressCallback | None = None,
    ) -> bool:
        """Install pack if needed. Returns True when assets are ready."""
        if self.is_installed():
            if progress:
                progress("Bone assets ready", 1.0)
            return True
        self.bones_dir.mkdir(parents=True, exist_ok=True)
        try:
            if self.pack_url:
                ok = self._download_pack(progress=progress)
                if ok:
                    return True
                logger.warning("Bone pack download failed — generating local pack")
            return self._generate_local_pack(progress=progress)
        except Exception:
            logger.exception("Bone asset installation failed")
            if progress:
                progress("Bone install failed", 0.0)
            return False

    def _download_pack(self, *, progress: ProgressCallback | None) -> bool:
        if progress:
            progress("Downloading anatomical bone pack…", 0.05)
        dest = self.bones_dir / "_pack.zip"
        try:
            urllib.request.urlretrieve(self.pack_url, dest)  # noqa: S310
        except Exception:
            logger.warning("Download failed from %s", self.pack_url, exc_info=True)
            return False
        if self.pack_sha256:
            digest = hashlib.sha256(dest.read_bytes()).hexdigest()
            if digest != self.pack_sha256:
                logger.error("Bone pack checksum mismatch")
                dest.unlink(missing_ok=True)
                return False
        if progress:
            progress("Extracting bone pack…", 0.7)
        import zipfile

        with zipfile.ZipFile(dest, "r") as zf:
            zf.extractall(self.bones_dir)
        dest.unlink(missing_ok=True)
        meshes = sorted(p.name for p in self.bones_dir.glob("*.obj"))
        self._write_manifest(meshes, source="download")
        if progress:
            progress("Bone pack installed", 1.0)
        return bool(meshes)

    def _generate_local_pack(self, *, progress: ProgressCallback | None) -> bool:
        """High-resolution cortical shafts as bootstrap anatomical assets."""
        if progress:
            progress("Generating anatomical bone pack…", 0.1)
        try:
            import pyvista as pv
        except Exception:
            logger.error("PyVista required to generate bone pack")
            return False

        meshes: list[str] = []
        keys = list(_PROFILES.keys())
        for i, key in enumerate(keys):
            profile = _PROFILES[key]
            # Higher resolution for presentation-quality shafts.
            hi = type(profile)(
                shaft_radius=profile.shaft_radius,
                epiphysis_boost=profile.epiphysis_boost,
                epiphysis_sigma=profile.epiphysis_sigma,
                axial_slices=max(profile.axial_slices * 2, 16),
                radial_sides=max(profile.radial_sides, 20),
            )
            pts, faces = build_unit_bone_template(hi)
            vtk_faces = np.hstack(
                [np.full((faces.shape[0], 1), 3, dtype=np.int64), faces]
            ).ravel()
            poly = pv.PolyData(pts, vtk_faces)
            poly = poly.compute_normals(
                cell_normals=False, point_normals=True, inplace=False
            )
            name = f"{key}.obj"
            out = self.bones_dir / name
            poly.save(str(out), binary=False)
            meshes.append(name)
            if progress:
                progress(f"Wrote {name}", 0.1 + 0.8 * (i + 1) / max(len(keys), 1))

        self._write_manifest(meshes, source="generated")
        if progress:
            progress("Local bone pack ready", 1.0)
        logger.info("Generated anatomical bone pack v%s (%d meshes)", self.version, len(meshes))
        return True

    def _write_manifest(self, meshes: list[str], *, source: str) -> None:
        payload = {
            "version": self.version,
            "source": source,
            "meshes": meshes,
            "pack_url": self.pack_url or None,
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
