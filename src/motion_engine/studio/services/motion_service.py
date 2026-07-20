"""Motion data loading service.

Owns database / subject / session / skeleton / clip construction so UI
controllers never talk to MATLAB loaders directly.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from motion_engine.animation_clip import AnimationClip
from motion_engine.exceptions import MotionEngineError
from motion_engine.loader import MotionDatabaseLoader, load_motion_database
from motion_engine.models import MotionDatabase, Session, Subject
from motion_engine.skeleton import Skeleton, SkeletonBuilder
from motion_engine.studio.models.session_model import SessionModel
from motion_engine.studio.models.subject_model import SubjectModel

logger = logging.getLogger(__name__)


class MotionServiceError(MotionEngineError):
    """Raised when motion data cannot be loaded or built."""


class MotionService:
    """Load Motion Engine domain objects for the studio.

    Example:
        >>> service = MotionService()
        >>> db = service.load_database()
        >>> subjects = service.list_subjects()
    """

    def __init__(
        self,
        *,
        builder: SkeletonBuilder | None = None,
        loader: MotionDatabaseLoader | None = None,
    ) -> None:
        self._builder = builder or SkeletonBuilder()
        self._loader = loader or MotionDatabaseLoader()
        self._database: MotionDatabase | None = None
        self._dataset_path: Path | None = None
        self._skeleton: Skeleton | None = None
        self._clip: AnimationClip | None = None
        self._active_subject_id: str | None = None
        self._active_session_name: str | None = None

    @property
    def database(self) -> MotionDatabase | None:
        """Currently loaded database."""
        return self._database

    @property
    def skeleton(self) -> Skeleton | None:
        """Skeleton for the active session."""
        return self._skeleton

    @property
    def clip(self) -> AnimationClip | None:
        """Animation clip for the active session."""
        return self._clip

    @property
    def dataset_path(self) -> Path | None:
        """Resolved dataset path."""
        return self._dataset_path

    def load_database(self, path: str | Path | None = None) -> MotionDatabase:
        """Load the MotionDatabase from disk.

        Args:
            path: Optional MATLAB dataset path. Defaults to the engine default.
        """
        logger.info("Loading MotionDatabase path=%s", path)
        try:
            if path is None:
                database = self._loader.load()
            else:
                database = load_motion_database(path)
        except Exception as exc:  # noqa: BLE001 - surface as service error
            raise MotionServiceError(f"Failed to load dataset: {exc}") from exc
        self._database = database
        self._dataset_path = Path(database.dataset_path) if database.dataset_path else (
            Path(path).resolve() if path else None
        )
        self._skeleton = None
        self._clip = None
        self._active_subject_id = None
        self._active_session_name = None
        logger.info("Loaded %d subjects", len(database.subjects))
        return database

    def list_subjects(self, *, pinned: set[str] | None = None) -> list[SubjectModel]:
        """Return UI subject models sorted by ID."""
        db = self._require_database()
        pinned = pinned or set()
        models: list[SubjectModel] = []
        for subject_id in db.list_subjects():
            subject = db.get_subject(subject_id)
            summary = subject.summary()
            meta = summary.get("metadata") or {}
            models.append(
                SubjectModel(
                    subject_id=subject_id,
                    session_count=int(summary.get("session_count") or 0),
                    classifications=dict(summary.get("classifications") or {}),
                    mass=_as_float(meta.get("mass")),
                    height=_as_float(meta.get("height")),
                    pinned=subject_id in pinned,
                    metadata=dict(meta),
                )
            )
        return models

    def get_subject(self, subject_id: str) -> Subject:
        """Return a domain Subject."""
        return self._require_database().get_subject(subject_id)

    def list_sessions(self, subject_id: str) -> list[SessionModel]:
        """Return all UI session models for a subject exactly as in the dataset."""
        subject = self.get_subject(subject_id)
        models: list[SessionModel] = []
        for name in subject.list_sessions():
            session = subject.get_session(name)
            metrics = {
                key: _metric_value(metric)
                for key, metric in session.clinical_metrics.items()
            }
            models.append(
                SessionModel(
                    subject_id=subject_id,
                    name=session.name,
                    classification=session.classification,
                    frame_count=session.frame_count,
                    sampling_rate_hz=session.sampling_rate_hz,
                    metric_names=sorted(session.clinical_metrics),
                    metrics=metrics,
                    metadata={
                        "trajectory_layout": session.trajectory_layout,
                    },
                )
            )
        return models

    def get_session(self, subject_id: str, session_name: str) -> Session:
        """Return a domain Session."""
        return self.get_subject(subject_id).get_session(session_name)

    def load_session(
        self,
        subject_id: str,
        session_name: str,
        *,
        build_clip: bool = True,
    ) -> tuple[Skeleton, AnimationClip | None]:
        """Build skeleton (and optional clip) for a session.

        Args:
            subject_id: Subject ID.
            session_name: Session name.
            build_clip: When True, also build an :class:`AnimationClip`.
        """
        session = self.get_session(subject_id, session_name)
        logger.info("Building skeleton for %s/%s", subject_id, session_name)
        try:
            skeleton = self._builder.build(session)
        except Exception as exc:  # noqa: BLE001
            raise MotionServiceError(
                f"Failed to build skeleton for {subject_id}/{session_name}: {exc}"
            ) from exc
        clip: AnimationClip | None = None
        if build_clip:
            try:
                clip = AnimationClip.from_skeleton(skeleton)
            except Exception as exc:  # noqa: BLE001
                raise MotionServiceError(
                    f"Failed to build AnimationClip for {subject_id}/{session_name}: {exc}"
                ) from exc
        self._skeleton = skeleton
        self._clip = clip
        self._active_subject_id = subject_id
        self._active_session_name = session_name
        return skeleton, clip

    def _require_database(self) -> MotionDatabase:
        if self._database is None:
            raise MotionServiceError("No database loaded. Call load_database() first.")
        return self._database


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _metric_value(metric: Any) -> Any:
    if hasattr(metric, "value"):
        return metric.value
    for attr in ("values", "data", "scalar"):
        if hasattr(metric, attr):
            value = getattr(metric, attr)
            if value is not None:
                return value
    return str(metric)
