"""Tests for the renderer abstraction layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from motion_engine.camera import CameraState
from motion_engine.colors import DARK_THEME, STUDIO_THEME, get_theme
from motion_engine.renderer import (
    NullRenderer,
    PyVistaRenderer,
    Renderer,
    RendererError,
    create_default_renderer,
)
from motion_engine.scene import Scene


def test_null_renderer_records_draw_calls(tmp_path: Path) -> None:
    r = NullRenderer(theme=DARK_THEME)
    assert isinstance(r, Renderer)
    assert isinstance(r.scene, Scene)
    r.initialize("test")
    r.clear()
    r.set_background(DARK_THEME.background)
    r.draw_ground(1000.0, DARK_THEME.ground)
    r.draw_grid(1000.0, 10, DARK_THEME.grid)
    r.draw_axes((0, 0, 0), 100.0)
    r.draw_sphere((0, 0, 0), 20.0, DARK_THEME.joint, name="j0")
    r.draw_line((0, 0, 0), (0, 0, 100), DARK_THEME.bone, name="b0")
    r.set_camera(CameraState())
    r.render()
    out = r.screenshot(tmp_path / "n.png")
    assert out.exists()
    assert r.poll_events() is True
    r.close()
    assert r.closed is True
    assert "sphere:j0" in r.draw_calls
    assert "line:b0" in r.draw_calls


def test_create_default_renderer_null() -> None:
    r = create_default_renderer(prefer="null")
    assert isinstance(r, NullRenderer)


def test_create_default_renderer_pyvista() -> None:
    r = create_default_renderer(prefer="pyvista", theme=get_theme("studio"))
    assert isinstance(r, PyVistaRenderer)


def test_legacy_backend_names_route_to_pyvista() -> None:
    for prefer in ("open3d", "matplotlib", "vtk", "auto"):
        r = create_default_renderer(prefer=prefer, off_screen=True)
        assert isinstance(r, (PyVistaRenderer, NullRenderer))


def test_pyvista_offscreen_pipeline(tmp_path: Path) -> None:
    try:
        r = PyVistaRenderer(theme=STUDIO_THEME, off_screen=True)
    except RendererError:
        pytest.skip("PyVista unavailable")
    r.initialize("offscreen")
    r.clear()
    r.set_background(STUDIO_THEME.background)
    r.draw_ground(2000.0, STUDIO_THEME.ground, origin=(0.0, 0.0, 0.0))
    r.draw_grid(2000.0, 12, STUDIO_THEME.grid, origin=(0.0, 0.0, 0.0))
    r.draw_axes((0.0, 0.0, 0.0), 150.0)
    r.draw_sphere((0.0, 0.0, 900.0), 30.0, STUDIO_THEME.joint, name="pelvis")
    r.draw_line(
        (0.0, 0.0, 900.0),
        (0.0, 0.0, 1100.0),
        STUDIO_THEME.bone,
        name="spine",
    )
    r.set_camera(CameraState(eye=(-1800, 0, 1000), look_at=(0, 0, 1000)))
    r.render()
    out = r.screenshot(tmp_path / "studio.png", scale=1)
    assert out.exists()
    assert out.stat().st_size > 0
    r.close()


def test_themes_registered() -> None:
    for name in ("studio", "dark", "light", "clinical", "publication"):
        theme = get_theme(name)
        assert theme.name == name
        assert len(theme.joint) == 3
        assert len(theme.background_top) == 3
        assert len(theme.fog) == 3
