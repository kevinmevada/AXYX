"""Background task execution on QThreadPool with main-thread signals."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

logger = logging.getLogger(__name__)


class TaskSignals(QObject):
    """Bridge QObject — signals must live on the main thread."""

    finished = Signal(str, object)
    error = Signal(str, object)
    progress = Signal(str, object)


class _TaskWorker(QRunnable):
    """Run ``fn`` off the UI thread and emit results via ``signals``."""

    def __init__(
        self,
        job_id: str,
        fn: Callable[..., Any],
        signals: TaskSignals,
        cancel_flag: Callable[[], bool],
    ) -> None:
        super().__init__()
        self._job_id = job_id
        self._fn = fn
        self._signals = signals
        self._cancel_flag = cancel_flag
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        if self._cancel_flag():
            return
        self._signals.progress.emit(self._job_id, 0)
        try:
            result = self._fn()
            if self._cancel_flag():
                return
            self._signals.progress.emit(self._job_id, 100)
            self._signals.finished.emit(self._job_id, result)
        except Exception as exc:  # noqa: BLE001 — surface to UI handler
            logger.exception("Background task %s failed", self._job_id)
            self._signals.error.emit(self._job_id, exc)


class TaskManager(QObject):
    """Submit callables to QThreadPool; callbacks run on the main thread."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._signals = TaskSignals(self)
        self._cancel_all_flag = False
        self._jobs: dict[str, str] = {}
        self._success: dict[str, Callable[[Any], None]] = {}
        self._error: dict[str, Callable[[Exception], None]] = {}
        self._progress: dict[str, Callable[[Any], None]] = {}
        self._signals.finished.connect(self._on_finished)
        self._signals.error.connect(self._on_error)
        self._signals.progress.connect(self._on_progress)

    def submit(
        self,
        fn: Callable[..., Any],
        *,
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
        on_progress: Callable[[Any], None] | None = None,
        description: str = "",
    ) -> str:
        """Enqueue ``fn`` and return a job id."""
        self._cancel_all_flag = False
        job_id = uuid.uuid4().hex
        self._jobs[job_id] = description or job_id
        self._success[job_id] = on_success
        self._error[job_id] = on_error
        if on_progress is not None:
            self._progress[job_id] = on_progress
        worker = _TaskWorker(job_id, fn, self._signals, lambda: self._cancel_all_flag)
        self._pool.start(worker)
        return job_id

    def cancel_all(self) -> None:
        """Best-effort flag — in-flight workers may still finish."""
        self._cancel_all_flag = True
        self._jobs.clear()
        self._success.clear()
        self._error.clear()
        self._progress.clear()

    def _on_finished(self, job_id: str, result: object) -> None:
        self._jobs.pop(job_id, None)
        handler = self._success.pop(job_id, None)
        self._error.pop(job_id, None)
        self._progress.pop(job_id, None)
        if handler is not None:
            handler(result)

    def _on_error(self, job_id: str, exc: object) -> None:
        self._jobs.pop(job_id, None)
        handler = self._error.pop(job_id, None)
        self._success.pop(job_id, None)
        self._progress.pop(job_id, None)
        if handler is None:
            return
        if isinstance(exc, Exception):
            handler(exc)
        else:
            handler(RuntimeError(str(exc)))

    def _on_progress(self, job_id: str, value: object) -> None:
        handler = self._progress.get(job_id)
        if handler is not None:
            handler(value)
