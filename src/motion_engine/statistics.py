"""
Aggregate statistics for the Motion Engine.

Responsibility
--------------
Compute database-, subject-, and session-level statistics from a populated
domain model. Must not load MATLAB files or invent units.

Status
------
Architecture placeholder. Implementation is deferred.
"""

from __future__ import annotations

# TODO: Implement StatisticsEngine with:
#   - subject / session counts
#   - classification histograms
#   - frame-count distributions (layout-aware)
#   - variable inventory totals
#   - sampling-rate observations
#   - export helpers aligned with metadata/motion_catalog reports


class StatisticsEngine:
    """Compute aggregate statistics for a MotionDatabase.

    TODO: Implement summarize(database) -> DatabaseStatistics.
    """

    def summarize(self, database: object) -> None:
        """Summarize a populated database.

        Raises:
            NotImplementedError: Always, until statistics are implemented.
        """
        raise NotImplementedError(
            "StatisticsEngine.summarize() is not implemented yet."
        )
