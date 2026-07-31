"""Tests for VisualizationManager mode switching."""

from __future__ import annotations

from motion_engine.rendering.visualization import (
    AvatarRenderer,
    BoneRenderer,
    StickRenderer,
    VisualizationManager,
    VisualizationMode,
)


def test_mode_parse_aliases() -> None:
    assert VisualizationMode.parse("clinical") is VisualizationMode.STICK
    assert VisualizationMode.parse("anatomy") is VisualizationMode.BONES
    assert VisualizationMode.parse("digital_twin") is VisualizationMode.AVATAR


def test_manager_switches_without_crash() -> None:
    stick_on = []
    avatar_on = []
    mgr = VisualizationManager(
        stick=StickRenderer(on_activate=lambda: stick_on.append(1)),
        bones=BoneRenderer(),
        avatar=AvatarRenderer(on_activate=lambda: avatar_on.append(1)),
    )
    assert mgr.set_mode("stick") is VisualizationMode.STICK
    assert stick_on == [1]
    # Bones without plotter/assets falls back to stick.
    mode = mgr.set_mode("bones")
    assert mode in {VisualizationMode.STICK, VisualizationMode.BONES}
    mgr.set_mode("avatar")
    assert avatar_on == [1]
    mgr.set_mode("stick")
    assert mgr.mode is VisualizationMode.STICK
