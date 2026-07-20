"""Manifest schema validation."""

from __future__ import annotations

import logging
import re
from typing import Any, Mapping

from motion_engine.rendering.avatar.loader.exceptions import ManifestError, ValidationError

logger = logging.getLogger(__name__)

_SUPPORTED_SCHEMA = frozenset({"1.0.0", "1.0"})
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")

REQUIRED_TOP_LEVEL = ("schema_version", "name", "type")


class ManifestValidator:
    """Validate raw ``avatar.json`` dictionaries before model construction.

    Example:
        >>> ManifestValidator().validate({"schema_version": "1.0.0", "name": "a", "type": "procedural"})
    """

    def validate(self, raw: Mapping[str, Any], *, source: str = "<memory>") -> None:
        """Validate ``raw`` manifest mapping.

        Raises:
            ManifestError: On schema / version / required-field failures.
            ValidationError: On semantically invalid values.
        """
        logger.debug("Validating manifest %s", source)
        if not isinstance(raw, Mapping):
            raise ManifestError(f"Manifest must be a JSON object: {source}")

        for key in REQUIRED_TOP_LEVEL:
            if key not in raw:
                raise ManifestError(f"Missing required field {key!r} in {source}")

        version = str(raw["schema_version"])
        if version not in _SUPPORTED_SCHEMA and not _VERSION_RE.match(version):
            raise ManifestError(f"Invalid schema_version {version!r} in {source}")
        major = int(version.split(".", 1)[0])
        if major != 1:
            raise ManifestError(
                f"Unsupported schema major version {version!r} in {source} "
                f"(supported: 1.x)"
            )

        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(f"Manifest name must be a non-empty string: {source}")

        avatar_type = raw.get("type")
        if not isinstance(avatar_type, str) or not avatar_type.strip():
            raise ValidationError(f"Manifest type must be a non-empty string: {source}")

        for section in ("skeleton", "mesh", "materials", "textures"):
            if section in raw and raw[section] is not None and not isinstance(
                raw[section], Mapping
            ):
                raise ValidationError(
                    f"Manifest field {section!r} must be an object: {source}"
                )

        if "lod" in raw and raw["lod"] is not None and not isinstance(raw["lod"], list):
            raise ValidationError(f"Manifest lod must be a list: {source}")

        logger.info("Manifest validation OK (%s) schema=%s", source, version)


__all__ = ["ManifestValidator", "REQUIRED_TOP_LEVEL"]
