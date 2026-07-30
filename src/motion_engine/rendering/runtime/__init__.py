"""AXYX Digital Twin Runtime (Phase 1 — M7).

Integrates frozen M1–M6 into a single research-grade platform pipeline:

```
MotionDatabase → Trial → Retarget → AnimationPose → Skinning → DeformedMesh
```

## Quick start

```python
from motion_engine.rendering.runtime import DigitalTwinRuntime, RuntimeFactory

rt = RuntimeFactory().debug()
report = rt.one_click(avatar="fixture", frames=60)
print(report.fps, report.frame_time_ms)
```

## Hard rules

- Does **not** modify M1–M6 public APIs
- Does **not** mutate AvatarSkeleton / BindPose
- Owns lifecycle, orchestration, profiling, and validation only
"""

from __future__ import annotations

from motion_engine.rendering.runtime.constants import PHASE1_VERSION, RUNTIME_VERSION, SCHEMA_VERSION
from motion_engine.rendering.runtime.exceptions import (
    DigitalTwinRuntimeError,
    RuntimeConfigError,
    RuntimePipelineError,
    RuntimeStateError,
    RuntimeValidationError,
)
from motion_engine.rendering.runtime.runtime import DigitalTwinRuntime, RuntimeFactory
from motion_engine.rendering.runtime.runtime_configuration import (
    RuntimeConfiguration,
    get_preset,
    load_configuration,
    save_configuration,
)
from motion_engine.rendering.runtime.runtime_session import RuntimeSession
from motion_engine.rendering.runtime.types import (
    AvatarKind,
    PipelineFrame,
    PlaybackMode,
    RuntimePhase,
    RuntimeReport,
)

__all__ = [
    "RUNTIME_VERSION",
    "SCHEMA_VERSION",
    "PHASE1_VERSION",
    "DigitalTwinRuntime",
    "RuntimeFactory",
    "RuntimeConfiguration",
    "RuntimeSession",
    "RuntimeReport",
    "PipelineFrame",
    "RuntimePhase",
    "AvatarKind",
    "PlaybackMode",
    "get_preset",
    "load_configuration",
    "save_configuration",
    "DigitalTwinRuntimeError",
    "RuntimeConfigError",
    "RuntimeStateError",
    "RuntimeValidationError",
    "RuntimePipelineError",
]
