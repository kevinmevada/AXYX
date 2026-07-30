"""Runtime manager — lifecycle, ownership, error propagation."""

from __future__ import annotations

from motion_engine.rendering.runtime.constants import (
    EVENT_ERROR,
    EVENT_STARTED,
    EVENT_STOPPED,
    RUNTIME_VERSION,
)
from motion_engine.rendering.runtime.exceptions import DigitalTwinRuntimeError
from motion_engine.rendering.runtime.runtime_cache import RuntimeCache
from motion_engine.rendering.runtime.runtime_configuration import RuntimeConfiguration
from motion_engine.rendering.runtime.runtime_events import RuntimeEventBus
from motion_engine.rendering.runtime.runtime_logging import RuntimeLogger
from motion_engine.rendering.runtime.runtime_pipeline import RuntimePipeline
from motion_engine.rendering.runtime.runtime_profiler import RuntimeProfiler
from motion_engine.rendering.runtime.runtime_scheduler import RuntimeScheduler
from motion_engine.rendering.runtime.runtime_state import RuntimeState
from motion_engine.rendering.runtime.runtime_statistics import RuntimeStatistics
from motion_engine.rendering.runtime.runtime_validation import RuntimeValidator
from motion_engine.rendering.runtime.types import RuntimePhase


class RuntimeManager:
    """Owns system lifecycle and shared services for DigitalTwinRuntime."""

    def __init__(self, config: RuntimeConfiguration | None = None) -> None:
        self.config = config or RuntimeConfiguration()
        self.state = RuntimeState()
        self.events = RuntimeEventBus()
        self.logger = RuntimeLogger(level=self.config.log_level)
        self.profiler = RuntimeProfiler(enabled=self.config.enable_profiler)
        self.cache = RuntimeCache()
        self.stats = RuntimeStatistics()
        self.validator = RuntimeValidator()
        self.scheduler = RuntimeScheduler(fps=self.config.fps)
        self.pipeline = RuntimePipeline(cache=self.cache, profiler=self.profiler)

    def startup(self) -> None:
        self.logger.info("Digital Twin Runtime starting", category="lifecycle")
        self.profiler.reset()
        self.stats.clear()
        self.cache.clear()
        self.state.transition(RuntimePhase.READY, force=True)
        self.events.emit(EVENT_STARTED, version=RUNTIME_VERSION)
        self.logger.info("Runtime ready", category="lifecycle")

    def shutdown(self) -> None:
        self.logger.info("Digital Twin Runtime shutting down", category="lifecycle")
        self.scheduler.pause()
        self.cache.clear()
        self.state.transition(RuntimePhase.SHUTDOWN, force=True)
        self.events.emit(EVENT_STOPPED)
        self.events.clear()

    def fail(self, exc: BaseException) -> None:
        msg = str(exc)
        self.state.fail(msg)
        self.logger.error(msg, category="error")
        self.events.emit(EVENT_ERROR, message=msg)
        if not isinstance(exc, DigitalTwinRuntimeError):
            raise DigitalTwinRuntimeError(msg) from exc
        raise exc


__all__ = ["RuntimeManager"]
