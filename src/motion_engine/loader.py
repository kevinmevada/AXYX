"""
MATLAB dataset loader for the Motion Engine.

Loads ``.mat`` files from disk and hands the result to
:mod:`motion_engine.parser`. This module performs I/O only; structure
translation lives entirely in the parser.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import scipy.io

from motion_engine.constants import DEFAULT_CATALOG_RELATIVE_PATH
from motion_engine.exceptions import LoaderError
from motion_engine.models import MotionDatabase
from motion_engine.parser import parse_database
from motion_engine.utils import resolve_catalog_path, resolve_dataset_path

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Load a motion-capture MATLAB file from disk."""

    def __init__(
        self,
        *,
        catalog_path: str | Path | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        self.catalog_path = catalog_path
        self.log = log or logger

    def load_raw(self, path: str | Path | None = None) -> dict[str, Any]:
        """Load a ``.mat`` file into a raw scipy dictionary.

        Raises:
            LoaderError: If the path is missing or the file cannot be read.
        """
        dataset_path = resolve_dataset_path(path)
        self.log.info("Loading MATLAB dataset from %s", dataset_path)
        if not dataset_path.is_file():
            raise LoaderError(f"Dataset missing: {dataset_path}")

        try:
            mat_data = scipy.io.loadmat(str(dataset_path))
        except Exception as exc:  # noqa: BLE001 - wrap for SDK boundary
            raise LoaderError(f"Failed to load MATLAB file {dataset_path}: {exc}") from exc

        if "Dat" not in mat_data:
            raise LoaderError(f"Dat missing in MATLAB file: {dataset_path}")

        self.log.info("MATLAB dataset loaded successfully from %s", dataset_path)
        return mat_data

    def load(self, path: str | Path | None = None) -> MotionDatabase:
        """Load and parse a MATLAB dataset into a :class:`MotionDatabase`."""
        dataset_path = resolve_dataset_path(path)
        mat_data = self.load_raw(dataset_path)
        catalog = (
            resolve_catalog_path(self.catalog_path)
            if self.catalog_path is not None
            else resolve_catalog_path(DEFAULT_CATALOG_RELATIVE_PATH)
        )
        database = parse_database(
            mat_data,
            dataset_path=dataset_path,
            catalog_path=catalog if catalog.is_dir() else None,
            log=self.log,
        )
        return database


def load_motion_database(
    path: str | Path | None = None,
    *,
    catalog_path: str | Path | None = None,
) -> MotionDatabase:
    """Convenience function: load + parse a filtered (or custom) MATLAB file."""
    return DatasetLoader(catalog_path=catalog_path).load(path)


class MotionDatabaseLoader(DatasetLoader):
    """Certification / SDK alias for :class:`DatasetLoader`.

    Example:
        >>> db = MotionDatabaseLoader().load()
    """


def _motion_database_load(
    self: MotionDatabase,
    path: str | Path | None = None,
) -> MotionDatabase:
    """Bound implementation for :meth:`MotionDatabase.load`.

    Populates ``self`` from a parsed database so callers can write::

        db = MotionDatabase().load()

    without editing ``models.py``.
    """
    loaded = load_motion_database(path)
    self.subjects = loaded.subjects
    self.dataset_path = loaded.dataset_path
    self.catalog_path = loaded.catalog_path
    return self


def attach_motion_database_load() -> None:
    """Attach the loader implementation onto :class:`MotionDatabase.load`."""
    MotionDatabase.load = _motion_database_load  # type: ignore[method-assign]


# Enable MotionDatabase().load() without modifying models.py.
attach_motion_database_load()
