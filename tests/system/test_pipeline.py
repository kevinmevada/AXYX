"""System tests for Digital Twin Runtime."""

from __future__ import annotations

from pathlib import Path

from motion_engine.rendering.runtime import (
    DigitalTwinRuntime,
    RuntimeFactory,
    RuntimeConfiguration,
    get_preset,
    load_configuration,
    save_configuration,
)
from motion_engine.rendering.runtime.runtime_cache import RuntimeCache
from motion_engine.rendering.runtime.runtime_logging import RuntimeLogger
from motion_engine.rendering.runtime.runtime_manager import RuntimeManager
from motion_engine.rendering.runtime.runtime_profiler import RuntimeProfiler
from motion_engine.rendering.runtime.runtime_statistics import RuntimeStatistics
from motion_engine.rendering.runtime.runtime_validation import RuntimeValidator
from motion_engine.rendering.runtime.types import PipelineFrame, RuntimePhase


def test_runtime_one_click():
    rt = RuntimeFactory().debug()
    rep = rt.one_click(frames=10)
    assert rep.frames == 10
    assert rep.extra["finite_frames"] == 10
    assert rt.phase == RuntimePhase.SHUTDOWN


def test_pipeline_prepare_and_tick():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    rt.prepare()
    assert rt.phase == RuntimePhase.PREPARED
    rt.play()
    fr = rt.tick()
    assert isinstance(fr, PipelineFrame)
    assert fr.finite
    rt.shutdown()


def test_session_selection():
    rt = DigitalTwinRuntime(get_preset("debug"))
    rt.startup()
    rt.select_subject("S2")
    rt.select_trial("WU01")
    assert rt.session.subject_id == "S2"
    assert rt.session.trial_id == "WU01"
    rt.shutdown()


def test_manager_lifecycle():
    mgr = RuntimeManager(get_preset("debug"))
    mgr.startup()
    assert mgr.state.phase == RuntimePhase.READY
    mgr.shutdown()
    assert mgr.state.phase == RuntimePhase.SHUTDOWN


def test_configuration_roundtrip(tmp_path: Path):
    cfg = get_preset("research")
    path = tmp_path / "cfg.json"
    save_configuration(cfg, path)
    cfg2 = load_configuration(path)
    assert cfg2.name == cfg.name
    assert cfg2.fps == cfg.fps


def test_profiler_and_statistics():
    p = RuntimeProfiler(enabled=True)
    with p.measure("retarget"):
        x = sum(range(1000))
    assert x >= 0
    assert "retarget" in p.summary()
    stats = RuntimeStatistics()
    stats.add(
        PipelineFrame(
            index=0,
            time=0.0,
            pose_name="p",
            vertex_count=5,
            bone_count=2,
            finite=True,
            stages_ns={"frame": 1000, "retarget": 400, "skinning": 600},
        )
    )
    rep = stats.report()
    assert rep.frames == 1


def test_logging_records():
    log = RuntimeLogger(level="INFO")
    log.info("hello")
    log.performance("fast")
    assert len(log.records) >= 2


def test_cache_hits():
    c = RuntimeCache()
    assert c.get("avatars", "a") is None
    c.put("avatars", "a", 123)
    assert c.get("avatars", "a") == 123
    c.clear()
    assert c.stats()["avatars"] == 0


def test_validation_context():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.select_mapping("test_two_bone")
    ctx = rt.prepare()
    report = RuntimeValidator().validate_context(ctx, RuntimePhase.PREPARED)
    assert report.ok
    rt.seek(0)
    fr_report = RuntimeValidator().validate_frame(ctx)
    assert fr_report.ok
    rt.shutdown()


def test_resource_cleanup():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_avatar("fixture")
    rt.prepare()
    rt.run_frames(5)
    rt.shutdown()
    assert rt.context is None
    assert rt.manager.cache.stats()["avatars"] == 0
