"""
Dataset validation for the Motion Engine.

Responsibility
--------------
Perform catalog-aware structural validation of a populated
:class:`~motion_engine.models.MotionDatabase` graph. Domain models already
provide lightweight local validation; this module handles cross-subject and
catalog-contract checks.

Status
------
Architecture placeholder. Implementation is deferred.
"""

from __future__ import annotations

# TODO: Implement DatabaseValidator with:
#   - catalog schema reconciliation
#   - session inventory soft checks
#   - sampling-rate consistency
#   - unresolved trajectory layout reporting
#   - gait-event absence as informational (not required)


class DatabaseValidator:
    """Validate a MotionDatabase against catalog contracts.

    TODO: Implement validate(database) -> ValidationReport (extended).
    """

    def validate(self, database: object) -> None:
        """Validate a populated database.

        Raises:
            NotImplementedError: Always, until the validator is implemented.
        """
        raise NotImplementedError(
            "DatabaseValidator.validate() is not implemented yet."
        )
