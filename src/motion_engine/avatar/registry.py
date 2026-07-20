"""YAML-driven avatar registry."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from motion_engine.avatar.base import AvatarBackend, AvatarInfo, NullAvatar
from motion_engine.exceptions import MotionEngineError

logger = logging.getLogger(__name__)

DEFAULT_AVATARS_YAML = Path("config/avatars.yaml")


class AvatarRegistryError(MotionEngineError):
    """Raised when avatar config or backend construction fails."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class AvatarRegistry:
    """Load ``config/avatars.yaml`` and construct backends."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else _repo_root() / DEFAULT_AVATARS_YAML
        self.default_avatar_id = "metallic"
        self.avatars: dict[str, AvatarInfo] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            logger.warning("Avatar registry missing (%s); metallic only", self.path)
            self.avatars = {
                "metallic": AvatarInfo(
                    id="metallic",
                    display_name="Metallic Procedural Human",
                    backend="metallic",
                    fallback=True,
                )
            }
            self.default_avatar_id = "metallic"
            return
        raw = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        self.default_avatar_id = str(raw.get("default_avatar", "metallic"))
        self.avatars = {}
        for key, entry in (raw.get("avatars") or {}).items():
            info = AvatarInfo(
                id=str(entry.get("id", key)),
                display_name=str(entry.get("display_name", key)),
                backend=str(entry.get("backend", key)),
                enabled=bool(entry.get("enabled", True)),
                fallback=bool(entry.get("fallback", False)),
                asset_root=entry.get("asset_root"),
                manifest=entry.get("manifest"),
                retarget=entry.get("retarget"),
                default_lod=int(entry.get("default_lod", 1)),
                animation_mode=str(entry.get("animation_mode", "rigid")),
                description=str(entry.get("description") or ""),
            )
            self.avatars[info.id] = info

    def create(self, avatar_id: str | None = None) -> AvatarBackend:
        """Instantiate backend for ``avatar_id`` (falls back to metallic)."""
        aid = avatar_id or self.default_avatar_id
        info = self.avatars.get(aid)
        if info is None or not info.enabled:
            logger.warning("Avatar %s unavailable; using metallic fallback", aid)
            info = self.avatars.get("metallic") or AvatarInfo(
                id="metallic",
                display_name="Metallic Procedural Human",
                backend="metallic",
                fallback=True,
            )
        try:
            return self._build(info)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to build avatar %s: %s", info.id, exc)
            if info.id != "metallic":
                return self._build(
                    AvatarInfo(
                        id="metallic",
                        display_name="Metallic Procedural Human",
                        backend="metallic",
                        fallback=True,
                    )
                )
            raise AvatarRegistryError(str(exc)) from exc

    def _build(self, info: AvatarInfo) -> AvatarBackend:
        backend = info.backend.lower()
        if backend in {"metallic", "fallback"}:
            from motion_engine.avatar.metallic_backend import MetallicAvatar

            return MetallicAvatar()
        if backend in {"kili", "digital_human", "metahuman"}:
            from motion_engine.avatar.kili_backend import KiliAvatar

            return KiliAvatar(
                asset_root=_repo_root() / (info.asset_root or "KILI"),
                retarget_path=_repo_root()
                / (info.retarget or "config/retarget_kili.yaml"),
                lod=info.default_lod,
                animation_mode=info.animation_mode,
            )
        if backend in {"null", "none"}:
            return NullAvatar()
        raise AvatarRegistryError(f"Unknown avatar backend: {backend}")


def create_default_avatar(avatar_id: str | None = None) -> AvatarBackend:
    """Convenience: registry default (Kili when available)."""
    return AvatarRegistry().create(avatar_id)
