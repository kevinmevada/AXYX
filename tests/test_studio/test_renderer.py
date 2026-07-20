"""Tests for studio Renderer ABC / factory / backends."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from motion_engine.studio.renderers import (
    RendererFactory,
    StudioPyVistaRenderer,
    UnrealBackendUnavailable,
    UnrealRenderer,
)
from motion_engine.studio.services.renderer_bridge import RendererBridge


class _FakeHost:
    def __init__(self) -> None:
        self.skeletons: list[object] = []
        self.frames: list[int] = []
        self.resets = 0

    def show_skeleton(self, skeleton) -> None:
        self.skeletons.append(skeleton)

    def set_frame(self, frame: int) -> None:
        self.frames.append(int(frame))

    def reset_camera(self) -> None:
        self.resets += 1


def test_renderer_factory_backends() -> None:
    assert "pyvista" in RendererFactory.available_backends()
    assert "unreal" in RendererFactory.available_backends()
    assert isinstance(RendererFactory("pyvista").create(), StudioPyVistaRenderer)
    assert isinstance(RendererFactory("unreal").create(), UnrealRenderer)


def test_pyvista_renderer_lifecycle() -> None:
    host = _FakeHost()
    renderer = StudioPyVistaRenderer()
    renderer.initialize(host)
    skeleton = SimpleNamespace(subject_id="S2", session_name="WU01")
    renderer.load_animation(skeleton, frame=3)  # type: ignore[arg-type]
    assert host.skeletons == [skeleton]
    assert host.frames[-1] == 3
    renderer.seek(7)
    assert host.frames[-1] == 7
    renderer.reset_camera()
    assert host.resets == 1
    renderer.shutdown()
    assert renderer.is_initialized is False


def test_unreal_renderer_requires_bridge() -> None:
    renderer = UnrealRenderer()
    renderer.initialize(object())
    with pytest.raises(UnrealBackendUnavailable):
        renderer.load_animation(SimpleNamespace(), frame=0)  # type: ignore[arg-type]


def test_renderer_bridge_adapts_service_api() -> None:
    host = _FakeHost()
    bridge = RendererBridge(StudioPyVistaRenderer())
    bridge.bind(host)
    skeleton = SimpleNamespace(subject_id="S1", session_name="WK01")
    bridge.show_skeleton(skeleton)  # type: ignore[arg-type]
    bridge.set_frame(4)
    assert host.frames[-1] == 4
    assert bridge.backend_name == "pyvista"
