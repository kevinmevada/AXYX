"""Clinical analytics service for session inspection."""

from __future__ import annotations

import logging
from typing import Any

from motion_engine.models import Session
from motion_engine.skeleton import Skeleton
from motion_engine.studio.models.session_model import SessionModel

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Derive clinical / statistical summaries for the inspector.

    Example:
        >>> AnalyticsService().session_overview(session_model)
    """

    def session_overview(self, session: SessionModel) -> dict[str, Any]:
        """Return overview fields for a session model."""
        duration = None
        if (
            session.frame_count is not None
            and session.sampling_rate_hz
            and session.sampling_rate_hz > 0
            and session.frame_count > 1
        ):
            duration = (session.frame_count - 1) / float(session.sampling_rate_hz)
        return {
            "subject_id": session.subject_id,
            "session": session.name,
            "classification": session.classification,
            "frame_count": session.frame_count,
            "sampling_rate_hz": session.sampling_rate_hz,
            "duration_sec": duration,
            "metric_count": len(session.metric_names),
            "metrics": dict(session.metrics),
        }

    def clinical_metrics(self, session: Session) -> dict[str, Any]:
        """Extract clinical metrics from a domain Session."""
        out: dict[str, Any] = {}
        for name, metric in session.clinical_metrics.items():
            out[name] = getattr(metric, "value", str(metric))
        return out

    def skeleton_stats(self, skeleton: Skeleton) -> dict[str, Any]:
        """Return reconstruction statistics for a skeleton."""
        return {
            "name": skeleton.name,
            "subject_id": skeleton.subject_id,
            "session_name": skeleton.session_name,
            "joint_count": len(skeleton.joints),
            "bone_count": len(skeleton.bones),
            "frame_count": skeleton.frame_count,
            "sampling_rate_hz": skeleton.sampling_rate_hz,
            "units": skeleton.units,
            "coordinate_system": skeleton.coordinate_system,
            "missing_markers": list(skeleton.missing_markers),
            "unresolved_joints": list(skeleton.unresolved_joints),
        }

    def dataset_info(
        self,
        *,
        subject_count: int,
        dataset_path: str | None,
    ) -> dict[str, Any]:
        """Return dataset-level inspector info."""
        return {
            "product": "AXYX",
            "subject_count": subject_count,
            "dataset_path": dataset_path,
        }
