"""Render settings loaded from ``config/rendering.yaml`` (with safe defaults)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_CONFIG = _REPO_ROOT / "config" / "rendering.yaml"


@dataclass(slots=True)
class RenderSettings:
    """Configurable rendering defaults — no magic constants in call sites."""

    quality: str = "high"
    lighting_preset: str = "studio"
    environment_preset: str = "studio"
    camera_preset: str = "clinical"
    shadows_enabled: bool = True
    reflections_enabled: bool = True
    fog_enabled: bool = False
    msaa_samples: int = 2
    floor_metallic: float = 0.08
    floor_roughness: float = 0.72
    hdri_enabled: bool = True
    material_bone: str = "graphite"
    material_joint: str = "ceramic"
    material_floor: str = "floor"
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def defaults(cls) -> RenderSettings:
        """Built-in defaults matching the current light studio look."""
        return cls()

    @classmethod
    def load(cls, path: Path | None = None) -> RenderSettings:
        """Load from YAML; fall back to defaults on any error."""
        config_path = Path(path) if path is not None else _DEFAULT_CONFIG
        if not config_path.is_file():
            logger.info("Render settings missing at %s — using defaults", config_path)
            return cls.defaults()
        try:
            import yaml  # type: ignore

            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            logger.warning(
                "Failed to parse %s — using defaults", config_path, exc_info=True
            )
            return cls.defaults()
        if not isinstance(raw, dict):
            return cls.defaults()
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        extras = {k: v for k, v in raw.items() if k not in known}
        kwargs = {k: raw[k] for k in known if k in raw and k != "extras"}
        settings = cls(**kwargs)
        settings.extras = extras
        logger.debug("Loaded render settings from %s", config_path)
        return settings


__all__ = ["RenderSettings"]
