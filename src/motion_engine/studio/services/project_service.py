"""Project workspace orchestration service."""

from __future__ import annotations

import logging
from pathlib import Path

from motion_engine.studio.models.project_model import ProjectModel
from motion_engine.studio.services.motion_service import MotionService, MotionServiceError
from motion_engine.studio.settings import StudioSettings

logger = logging.getLogger(__name__)


class ProjectService:
    """Coordinate project open / close against :class:`MotionService`.

    Example:
        >>> project = ProjectService(MotionService(), StudioSettings())
        >>> project.open_default()
    """

    def __init__(
        self,
        motion_service: MotionService,
        settings: StudioSettings,
        *,
        model: ProjectModel | None = None,
    ) -> None:
        self.motion = motion_service
        self.settings = settings
        self.model = model or ProjectModel()

    def open_default(self) -> ProjectModel:
        """Open the configured or default Motion Engine dataset."""
        path = self.settings.resolved_dataset_path()
        return self.open(path)

    def open(self, path: str | Path | None = None) -> ProjectModel:
        """Open a dataset and populate the project model."""
        self.model.busy = True
        self.model.error_message = None
        self.model.status_message = "Loading dataset…"
        try:
            database = self.motion.load_database(path)
            self.model.database = database
            self.model.dataset_path = self.motion.dataset_path
            self.model.subject_ids = list(database.list_subjects())
            self.model.status_message = (
                f"Loaded {len(self.model.subject_ids)} subjects"
            )
            if path is not None:
                self.settings.dataset_path = str(Path(path).resolve())
                self.settings.save()
            logger.info("Project opened with %d subjects", self.model.subject_count)
            return self.model
        except MotionServiceError as exc:
            self.model.clear()
            self.model.error_message = str(exc)
            self.model.status_message = "Failed to load dataset"
            raise
        finally:
            self.model.busy = False

    def close(self) -> None:
        """Close the current project."""
        self.model.clear()
        logger.info("Project closed")
