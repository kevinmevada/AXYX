"""Tests for studio infrastructure (DI, events, commands)."""

from __future__ import annotations

from motion_engine.studio.bootstrap import build_container
from motion_engine.studio.commands import CallableCommand, CommandBus
from motion_engine.studio.configuration import StudioConfiguration
from motion_engine.studio.dependency_container import DependencyContainer
from motion_engine.studio.event_bus import EventBus


def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe("trial.loaded", lambda subject_id, session_name: seen.append(session_name))
    bus.publish("trial.loaded", subject_id="S2", session_name="WU01")
    assert seen == ["WU01"]


def test_command_bus_undo() -> None:
    state = {"n": 0}
    bus = CommandBus()
    bus.run(
        CallableCommand(
            label="inc",
            action=lambda: state.__setitem__("n", state["n"] + 1),
            undo_action=lambda: state.__setitem__("n", state["n"] - 1),
        )
    )
    assert state["n"] == 1
    assert bus.undo_last() is True
    assert state["n"] == 0


def test_dependency_container_singleton() -> None:
    container = DependencyContainer()
    counter = {"n": 0}

    def factory() -> dict:
        counter["n"] += 1
        return {"id": counter["n"]}

    container.register("x", factory, singleton=True)
    a = container.resolve("x")
    b = container.resolve("x")
    assert a is b
    assert counter["n"] == 1


def test_build_container_registers_core_services() -> None:
    container = build_container(configuration=StudioConfiguration(renderer_backend="pyvista"))
    assert container.has("motion_service")
    assert container.has("dataset_service")
    assert container.has("export_service")
    assert container.has("renderer_factory")
    factory = container.resolve("renderer_factory")
    assert factory.create().name == "pyvista"
